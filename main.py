from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from contextlib import asynccontextmanager
import uuid
import os

DATABASE_URL = "sqlite:///./app.db"
database = Database(DATABASE_URL)

# ---- Lifespan (startup/shutdown) ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await create_tables()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ----
@app.get("/")
def root():
    return {"message": "backend is running"}

@app.post("/upload-video")
async def upload_video(video: UploadFile = File(...)):
    job_id = str(uuid.uuid4())

    print(f"VIDEO RECEIVED: {video.filename}")
    print(f"Job ID: {job_id}")

    storage_dir = "./storage/videos"
    os.makedirs(storage_dir, exist_ok=True)

    file_ext = video.filename.split(".")[-1] if "." in video.filename else "mp4"
    video_path = f"{storage_dir}/{job_id}.{file_ext}"

    content = await video.read()

    with open(video_path, "wb") as f:
        f.write(content)

    await database.execute(
        """
        INSERT INTO submissions (job_id, video_filename, status)
        VALUES (:job_id, :filename, :status)
        """,
        {
            "job_id": job_id,
            "filename": video.filename,
            "status": "pending"
        }
    )

    return {
        "job_id": job_id,
        "status": "received"
    }

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    submission = await database.fetch_one(
        "SELECT status FROM submissions WHERE job_id = :job_id",
        {"job_id": job_id}
    )

    if not submission:
        return {"job_id": job_id, "status": "not_found"}

    return {
        "job_id": job_id,
        "status": submission["status"]
    }

# ---- Database schema ----
async def create_tables():
    await database.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY,
        job_id TEXT UNIQUE,
        video_filename TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        submission_id INTEGER UNIQUE,
        keypoints_json TEXT,
        metrics_json TEXT,
        annotated_video_path TEXT,
        FOREIGN KEY (submission_id) REFERENCES submissions(id)
    )
    """)
