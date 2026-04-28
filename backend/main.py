from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from databases import Database
from contextlib import asynccontextmanager
from pathlib import Path
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

# =========================
# ---- HELPERS ----
# =========================

def to_url(path: str) -> str:
    return path.replace("./storage", "/files")


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
               a.smpl_path
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

app.mount("/files", StaticFiles(directory=str(STORAGE_DIR)), name="files")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ---- ROUTES (THIN LAYER) ----
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
    video: UploadFile = File(...)
):
    submission_id, _ = await create_job(
    patient_id, 
    video,
    age,
    gender,
    height,
    weight,
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


@app.get("/videos")
async def videos():
    rows = await get_completed_videos()

    return [
        {
            "submission_id": r["id"],
            "video_url": to_url(r["video_path"]),
            "annotated_video_url": to_url(r["annotated_video_path"]) if r["annotated_video_path"] else None,
            "smpl_url": to_url(r["smpl_path"]) if r["smpl_path"] else None
        }
        for r in rows
    ]

@app.post("/patients")
async def create_patient(
    user_id: int = Form(...),
    name: str = Form(...)
):
    patient_id = await database.execute("""
        INSERT INTO patients (user_id, name)
        VALUES (:user_id, :name)
    """, {"user_id": user_id, "name": name})

    return {"patient_id": patient_id}

@app.get("/patients")
async def get_patients():
    return await database.fetch_all("""
        SELECT 
            p.id,
            p.name,

            latest.age,
            latest.gender,
            latest.height,
            latest.weight,

            COUNT(DISTINCT s.id) AS videoCount,
            MAX(s.uploaded_at) AS lastVisit

        FROM patients p

        LEFT JOIN submissions s ON s.patient_id = p.id

        LEFT JOIN submissions latest ON latest.id = (
            SELECT id
            FROM submissions
            WHERE patient_id = p.id
            ORDER BY uploaded_at DESC
            LIMIT 1
        )

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
            s.age,
            s.gender,
            s.height,
            s.weight,
            s.notes,
            s.uploaded_at,
            a.annotated_video_path,
            a.smpl_path
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
                "smpl_url": to_url(v["smpl_path"]) if v["smpl_path"] else None,
                "biometrics": {
                    "age": v["age"],
                    "gender": v["gender"],
                    "height": v["height"],
                    "weight": v["weight"],
                    "notes": v["notes"]
                }
            }
            for v in videos
        ]
    }
