from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from databases import Database
from contextlib import asynccontextmanager
from pathlib import Path
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid
import os
import asyncio
import requests
import cv2


# =========================
# ---- CONFIG / STATE ----
# =========================

DATABASE_URL = "sqlite:///./app.db"
database = Database(DATABASE_URL)

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
VIDEO_DIR = STORAGE_DIR / "videos"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# AUTH CONFIG
SECRET_KEY = "super-secret"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# =========================
# ---- AUTH HELPERS ----
# =========================

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")



# =========================
# ---- HELPERS ----
# =========================

def to_url(path: str) -> str:
    if not path:
        return None
    return "/files/" + path


# =========================
# ---- DATABASE SCHEMA ----
# =========================

async def create_tables():
    await database.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY, 
        patient_id INTEGER NOT NULL,
        video_filename TEXT NOT NULL,
        video_path TEXT NOT NULL,

        age INTEGER,
        gender TEXT,
        height REAL,
        weight REAL,
        exercise_type TEXT,
        notes TEXT,

        status TEXT DEFAULT 'pending',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        submission_id INTEGER NOT NULL,
        metrics_json TEXT,
        annotated_video_path TEXT,
        keypoints_csv TEXT,
        slam_path TEXT,
        tracking_path TEXT,
        wham_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (submission_id) REFERENCES submissions(id)
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

# =========================
# ---- CORE LOGIC ----
# =========================


def run_model(video_path):
    base_url = "http://142.169.249.42:16339"

    request_id = Path(video_path).stem

    with open(video_path, "rb") as f:
        files = {"file": (os.path.basename(video_path), f)}
        response = requests.post(f"{base_url}/process_video", files=files)


    if response.status_code != 200:
        raise Exception(response.text)

    base = os.path.splitext(video_path)[0]
    output_dir = base + "_results"
    os.makedirs(output_dir, exist_ok=True)

    def download(name):
        url = f"{base_url}/download/{request_id}/{name}"
        r = requests.get(url)

        print("DOWNLOAD URL:", url)
        print("STATUS:", r.status_code)

        if r.status_code != 200:
            print("BODY:", r.text[:300])
            raise Exception(f"failed: {name}")

        full_path = os.path.join(output_dir, name)
        with open(full_path, "wb") as f:
            f.write(r.content)

        return Path(full_path).relative_to(STORAGE_DIR).as_posix()

    return {
        "annotated_video_path": download("output.mp4"),
        "keypoints_csv": download("keypoints_2d.csv"),
        "slam_path": download("slam_results.pth"),
        "tracking_path": download("tracking_results.pth"),
        "wham_path": download("wham_results.pth"),
    }

async def create_job(
    patient_id: int, 
    video: UploadFile,
    age,
    gender,
    height,
    weight,
    exercise_type,
    notes
):
    print(f"VIDEO RECEIVED: {video.filename}")

    file_ext = video.filename.split(".")[-1] if "." in video.filename else "mp4"
    video_path = str(VIDEO_DIR / f"{uuid.uuid4().hex}.{file_ext}")

    with open(video_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            f.write(chunk)

    submission_id = await database.execute(
        """
        INSERT INTO submissions (
            patient_id, 
            video_filename, 
            video_path, 
            age,
            gender,
            height,
            weight,
            exercise_type,
            notes,
            status)
        VALUES (
            :patient_id,
            :filename, 
            :video_path, 
            :age,
            :gender,
            :height,
            :weight,
            :exercise_type,
            :notes,
            :status)
        """,
        {
            "patient_id": patient_id,
            "filename": video.filename,
            "video_path": video_path,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "exercise_type": exercise_type,
            "notes": notes,
            "status": "pending"
        }
    )

    print("Saved file size:", os.path.getsize(video_path))

    return submission_id, video_path


async def get_status(submission_id: int):
    return await database.fetch_one(
        "SELECT status FROM submissions WHERE id = :id",
        {"id": submission_id}
    )


async def get_completed_videos():
    return await database.fetch_all("""
        SELECT s.id,
               s.video_path,
               a.annotated_video_path,
               a.keypoints_csv,
               a.slam_path,
               a.tracking_path,
               a.wham_path
        FROM submissions s
        LEFT JOIN analyses a ON a.submission_id = s.id
        ORDER BY s.id DESC
    """)


async def process_next_job():
    job = await database.fetch_one(
        """
        SELECT id, video_path
        FROM submissions
        WHERE status = 'pending'
        ORDER BY id ASC
        LIMIT 1
        """
    )

    if not job:
        return

    await database.execute(
        """
        UPDATE submissions
        SET status = 'processing'
        WHERE id = :id
        """,
        {"id": job["id"]}
    )

    print(f"Processing job: {job['id']}")

    video_path = job["video_path"]

    print("File size:", os.path.getsize(video_path))

    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print("Frame count:", frame_count)

    try:
        result = run_model(video_path)

        keypoints_file = STORAGE_DIR / result["keypoints_csv"]

        with open(keypoints_file, "r") as f:
            keypoints_csv = f.read()

        await database.execute(
            """
            INSERT INTO analyses (
                submission_id,
                annotated_video_path,
                keypoints_csv,
                slam_path,
                tracking_path,
                wham_path
            )
            VALUES (
                :submission_id,
                :video,
                :keypoints,
                :slam,
                :tracking,
                :wham
            )
            """,
            {
                "submission_id": job["id"],
                "video": result["annotated_video_path"],
                "keypoints": keypoints_csv,
                "slam": result["slam_path"],
                "tracking": result["tracking_path"],
                "wham": result["wham_path"]
            }
        )


        await database.execute(
            """
            UPDATE submissions
            SET status = 'done'
            WHERE id = :id
            """,
            {"id": job["id"]}
        )

        print(f"Finished job: {job['id']}")

    except Exception as e:
        print("Processing failed:", e)

        await database.execute(
            """
            UPDATE submissions
            SET status = 'failed'
            WHERE id = :id
            """,
            {"id": job["id"]}
        )


# =========================
# ---- WORKER ----
# =========================

async def worker():
    while True:
        await process_next_job()
        await asyncio.sleep(1)


# =========================
# ---- FASTAPI LIFESPAN ----
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await database.execute("PRAGMA foreign_keys = ON") 
    await create_tables()

    task = asyncio.create_task(worker())

    yield

    task.cancel()
    await database.disconnect()


# =========================
# ---- APP SETUP ----
# =========================

app = FastAPI(lifespan=lifespan)

app.mount("/files", StaticFiles(directory=str(STORAGE_DIR)), name="files")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ---- AUTH ROUTES ----
# =========================

@app.post("/register")
async def register(email: str = Form(...), password: str = Form(...)):
    try:
        user_id = await database.execute("""
            INSERT INTO users (email, password_hash)
            VALUES (:email, :password_hash)
        """, {
            "email": email,
            "password_hash": hash_password(password)
        })
        return {"user_id": user_id}
    except Exception:
        return {"error": "email already exists"}


@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    user = await database.fetch_one(
        "SELECT * FROM users WHERE email = :email",
        {"email": email}
    )

    if not user or not verify_password(password, user["password_hash"]):
        return {"error": "invalid credentials"}

    token = create_token(user["id"])
    return {"access_token": token, "user_id": user["id"]}


# =========================
# ---- ROUTES ----
# =========================

@app.get("/")
def root():
    return {"message": "backend is running"}


@app.post("/upload-video")
async def upload_video(
    patient_id: int = Form(...),
    age: int = Form(None),
    gender: str = Form(None),
    height: float = Form(None),
    weight: float = Form(None),
    exercise_type: str = Form(None),
    notes: str = Form(None),
    video: UploadFile = File(...)
):
    submission_id, _ = await create_job(
    patient_id, 
    video,
    age,
    gender,
    height,
    weight,
    exercise_type,
    notes
)
    return {"submission_id": submission_id, "status": "received"}


@app.get("/status/{submission_id}")
async def status(submission_id: int):
    submission = await get_status(submission_id)

    if not submission:
        return {"submission_id": submission_id, "status": "not_found"}

    return {
        "submission_id": submission_id,
        "status": submission["status"]
    }

@app.post("/patients")
async def create_patient(
    user_id: int = Depends(get_current_user),
    name: str = Form(...)
):
    patient_id = await database.execute("""
        INSERT INTO patients (user_id, name)
        VALUES (:user_id, :name)
    """, {"user_id": user_id, "name": name})

    return {"patient_id": patient_id}

@app.get("/patients")
async def get_patients(user_id: int = Depends(get_current_user)):
    return await database.fetch_all("""
        SELECT id, name
        FROM patients
        WHERE user_id = :user_id
        ORDER BY id DESC
    """, {"user_id": user_id})

@app.get("/patients/{patient_id}/videos")
async def patient_videos(patient_id: int):

    patient = await database.fetch_one("""
        SELECT * FROM patients WHERE id = :id
    """, {"id": patient_id})

    if not patient:
        return {"error": "not found"}

    videos = await database.fetch_all("""
        SELECT 
            s.id,
            s.video_path,
            s.age,
            s.gender,
            s.height,
            s.weight,
            s.exercise_type,
            s.notes,
            s.uploaded_at,
            a.annotated_video_path,
            a.keypoints_csv,
            a.slam_path,
            a.tracking_path,
            a.wham_path
        FROM submissions s
        LEFT JOIN analyses a ON a.submission_id = s.id
        WHERE s.patient_id = :id
        ORDER BY s.id DESC
    """, {"id": patient["id"]})

    return {
        "patient": dict(patient),
        "videos": [
            {
                "submission_id": v["id"],
                "video_url": to_url(v["video_path"]),
                "annotated_video_url": to_url(v["annotated_video_path"]) if v["annotated_video_path"] else None,
                "keypoints_url": to_url(v["keypoints_csv"]) if v["keypoints_csv"] else None,
                "slam_url": to_url(v["slam_path"]) if v["slam_path"] else None,
                "tracking_url": to_url(v["tracking_path"]) if v["tracking_path"] else None,
                "wham_url": to_url(v["wham_path"]) if v["wham_path"] else None,
                "biometrics": {
                    "age": v["age"],
                    "gender": v["gender"],
                    "height": v["height"],
                    "weight": v["weight"],
                    "exercise_type": v["exercise_type"],
                    "notes": v["notes"]
                },
            }
            for v in videos
        ]
    }

@app.get("/videos/{submission_id}")
async def video_detail(submission_id: int):
    row = await database.fetch_one("""
        SELECT 
            s.id,
            s.video_path,
            s.age,
            s.gender,
            s.height,
            s.weight,
            s.exercise_type,
            s.notes,
            s.uploaded_at,
            a.annotated_video_path,
            a.keypoints_csv,
            a.slam_path,
            a.tracking_path,
            a.wham_path
        FROM submissions s
        LEFT JOIN analyses a ON a.submission_id = s.id
        WHERE s.id = :id
    """, {"id": submission_id})

    if not row:
        return {"error": "not found"}

    return {
        "submission_id": row["id"],
        "video_url": to_url(row["video_path"]),
        "annotated_video_url": to_url(row["annotated_video_path"]) if row["annotated_video_path"] else None,
        "keypoints_csv": row["keypoints_csv"],
        "slam_url": to_url(row["slam_path"]) if row["slam_path"] else None,
        "tracking_url": to_url(row["tracking_path"]) if row["tracking_path"] else None,
        "wham_url": to_url(row["wham_path"]) if row["wham_path"] else None,
        "biometrics": {
            "age": row["age"],
            "gender": row["gender"],
            "height": row["height"],
            "weight": row["weight"],
            "exercise_type": row["exercise_type"],
            "notes": row["notes"],
        }
    }
    
@app.get("/videos")
async def all_videos(user_id: int = Depends(get_current_user)):
    rows = await database.fetch_all("""
        SELECT 
            s.id,
            s.video_path,
            s.exercise_type,
            s.uploaded_at,
            p.name AS patient_name,
            a.annotated_video_path,
            a.keypoints_csv,
            a.slam_path,
            a.tracking_path,
            a.wham_path
        FROM submissions s
        JOIN patients p ON p.id = s.patient_id
        LEFT JOIN analyses a ON a.submission_id = s.id
        WHERE p.user_id = :user_id
        ORDER BY s.id DESC
    """, {"user_id": user_id})

    return [
        {
            "submission_id": row["id"],
            "patient_name": row["patient_name"],
            "exercise_type": row["exercise_type"],
            "uploaded_at": row["uploaded_at"],
            "video_url": to_url(row["video_path"]),
            "annotated_video_url": to_url(row["annotated_video_path"]) if row["annotated_video_path"] else None,
            "keypoints_csv": row["keypoints_csv"],
            "slam_url": to_url(row["slam_path"]) if row["slam_path"] else None,
            "tracking_url": to_url(row["tracking_path"]) if row["tracking_path"] else None,
            "wham_url": to_url(row["wham_path"]) if row["wham_path"] else None,
        }
        for row in rows
    ]
    
@app.post("/videos/{submission_id}/corrected-keypoints")
async def save_corrected_keypoints(
    submission_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user)
):
    submission = await database.fetch_one("""
        SELECT s.id, s.video_path, p.user_id
        FROM submissions s
        JOIN patients p ON p.id = s.patient_id
        WHERE s.id = :id
    """, {"id": submission_id})

    if not submission:
        raise HTTPException(status_code=404, detail="submission not found")

    if submission["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="not allowed")

    # Your current folders are based on video filename stem, not submission id
    video_stem = Path(submission["video_path"]).stem
    output_dir = VIDEO_DIR / f"{video_stem}_results"

    output_dir.mkdir(parents=True, exist_ok=True)

    save_path = output_dir / "corrected_keypoints_2d.csv"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    relative_path = save_path.relative_to(STORAGE_DIR).as_posix()

    return {
        "message": "corrected keypoints saved",
        "corrected_keypoints_url": to_url(relative_path),
        "corrected_keypoints_path": relative_path
    }