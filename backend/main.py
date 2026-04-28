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
    # Extract just the filename from full path and construct proper URL
    filename = os.path.basename(path)
    # Determine subfolder based on path
    if "videos" in path:
        return f"/files/videos/{filename}"
    else:
        return f"/files/{filename}"


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
        notes TEXT,
        exercise_type TEXT,

        status TEXT DEFAULT 'pending',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        submission_id INTEGER NOT NULL,
        keypoints_json TEXT,
        metrics_json TEXT,
        annotated_video_path TEXT,
        smpl_path TEXT,
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
    url = "http://142.169.249.42:16339/process_video"

    with open(video_path, "rb") as f:
        files = {
            "file": (
                os.path.basename(video_path),
                f,
                "application/octet-stream"
            )
        }
        response = requests.post(url, files=files)

    if response.status_code != 200:
        print("Model error response:", response.text)
        raise Exception(f"Model failed: {response.status_code}")

    base, ext = os.path.splitext(video_path)
    output_path = base + "_out.mp4"

    with open(output_path, "wb") as f:
        f.write(response.content)

    return {
        "annotated_video_path": output_path,
        "smpl_path": None
    }


async def create_job(
    patient_id: int,
    video: UploadFile,
    age,
    gender,
    height,
    weight,
    notes,
    exercise_type
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
            notes,
            exercise_type,
            status)
        VALUES (
            :patient_id,
            :filename,
            :video_path,
            :age,
            :gender,
            :height,
            :weight,
            :notes,
            :exercise_type,
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
            "notes": notes,
            "exercise_type": exercise_type,
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
               s.exercise_type,
               s.uploaded_at,
               p.name as patient_name,
               a.annotated_video_path,
               a.smpl_path
        FROM submissions s
        LEFT JOIN analyses a ON a.submission_id = s.id
        LEFT JOIN patients p ON p.id = s.patient_id
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

        await database.execute(
            """
            INSERT INTO analyses (submission_id, annotated_video_path, smpl_path)
            VALUES (:submission_id, :video, :smpl)
            """,
            {
                "submission_id": job["id"],
                "video": result["annotated_video_path"],
                "smpl": result["smpl_path"]
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

# Add CORS middleware BEFORE mounting static files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Mount static files
app.mount("/files", StaticFiles(directory=str(STORAGE_DIR)), name="files")


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
    notes: str = Form(None),
    exercise_type: str = Form(None),
    exercise: str = Form(None),  # Fallback field name
    video: UploadFile = File(...)
):
    # Use exercise_type if provided, otherwise fall back to exercise field
    final_exercise_type = exercise_type or exercise

    submission_id, _ = await create_job(
        patient_id,
        video,
        age,
        gender,
        height,
        weight,
        notes,
        final_exercise_type
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


@app.get("/videos")
async def videos():
    rows = await get_completed_videos()

    return [
        {
            "submission_id": r["id"],
            "video_url": to_url(r["video_path"]),
            "annotated_video_url": to_url(r["annotated_video_path"]) if r["annotated_video_path"] else None,
            "smpl_url": to_url(r["smpl_path"]) if r["smpl_path"] else None,
            "exercise_type": r["exercise_type"],
            "uploaded_at": r["uploaded_at"],
            "patient_name": r["patient_name"]
        }
        for r in rows
    ]

@app.post("/patients")
async def create_patient(
    name: str = Form(...),
    user_id: int = Form(...),
    age: int = Form(None),
    gender: str = Form(None),
    height: float = Form(None),
    weight: float = Form(None)
):
    patient_id = await database.execute("""
        INSERT INTO patients (user_id, name, age, gender, height, weight)
        VALUES (:user_id, :name, :age, :gender, :height, :weight)
    """, {
        "user_id": user_id,
        "name": name,
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight
    })

    return {"patient_id": patient_id}

@app.put("/patients/{patient_id}")
async def update_patient_biometrics(
    patient_id: int,
    age: int = Form(None),
    gender: str = Form(None),
    height: float = Form(None),
    weight: float = Form(None)
):
    await database.execute("""
        UPDATE patients
        SET age = :age, gender = :gender, height = :height, weight = :weight
        WHERE id = :patient_id
    """, {
        "patient_id": patient_id,
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight
    })

    return {"success": True, "patient_id": patient_id}

@app.get("/patients")
async def get_patients():
    return await database.fetch_all("""
        SELECT
            p.id,
            p.name,

            p.age,
            p.gender,
            p.height,
            p.weight,

            COUNT(DISTINCT s.id) AS videoCount,
            MAX(s.uploaded_at) AS lastVisit

        FROM patients p

        LEFT JOIN submissions s ON s.patient_id = p.id

        GROUP BY p.id
        ORDER BY lastVisit DESC
    """)

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
            s.notes,
            s.exercise_type,
            s.uploaded_at,
            a.annotated_video_path,
            a.smpl_path
        FROM submissions s
        LEFT JOIN analyses a ON a.submission_id = s.id
        WHERE s.patient_id = :id
        ORDER BY s.id DESC
    """, {"id": patient["id"]})

    return {
        "patient": {
            "id": patient["id"],
            "name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "height": patient["height"],
            "weight": patient["weight"]
        },
        "videos": [
            {
                "submission_id": v["id"],
                "video_url": to_url(v["video_path"]),
                "annotated_video_url": to_url(v["annotated_video_path"]) if v["annotated_video_path"] else None,
                "smpl_url": to_url(v["smpl_path"]) if v["smpl_path"] else None,
                "exercise_type": v["exercise_type"],
                "uploaded_at": v["uploaded_at"],
                "notes": v["notes"]
            }
            for v in videos
        ]
    }
