from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from contextlib import asynccontextmanager
import uuid
import os
import asyncio
from fastapi.staticfiles import StaticFiles

DATABASE_URL = "sqlite:///./app.db"
database = Database(DATABASE_URL)

# ---- Lifespan (startup/shutdown) ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await create_tables()

    task = asyncio.create_task(worker())

    yield

    task.cancel()
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.mount("/files", StaticFiles(directory="./storage"), name="files")

def to_url(path: str) -> str:
    return path.replace("./storage", "/files")

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
        INSERT INTO submissions (job_id, video_filename, video_path, status)
        VALUES (:job_id, :filename, :video_path, :status)
        """,
        {
            "job_id": job_id,
            "filename": video.filename,
            "video_path": video_path,
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
        video_path TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        job_id TEXT UNIQUE,
        keypoints_json TEXT,
        metrics_json TEXT,
        annotated_video_path TEXT,
        smpl_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

def run_model(video_path):
    return {            
        "annotated_video_path": video_path + "_out.mp4",            
        "smpl_path": video_path + ".smpl"
    }

async def worker():
    while True:
        job = await database.fetch_one(
            """
            SELECT id, job_id, video_path
            FROM submissions
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """
        )

        if not job:
            await asyncio.sleep(1)
            continue

        await database.execute(
            """
            UPDATE submissions
            SET status = 'processing'
            WHERE job_id = :job_id
            """,
            {"job_id": job["job_id"]}
        )

        print(f"Processing job: {job['job_id']}")

        result = run_model(job["video_path"])

        await database.execute("""
            INSERT INTO analyses (job_id, annotated_video_path, smpl_path)
            VALUES (:job_id, :video, :smpl)
        """, {
            "job_id": job["job_id"],
            "video": result["annotated_video_path"],
            "smpl": result["smpl_path"]
        })

        await database.execute(
            """
            UPDATE submissions
            SET status = 'done'
            WHERE job_id = :job_id
            """,
            {"job_id": job["job_id"]}
        )

        print(f"Finished job: {job['job_id']}")

@app.get("/completed")
async def get_completed():
    rows = await database.fetch_all("""
        SELECT s.job_id,
               s.video_path,
               a.annotated_video_path,
               a.smpl_path
        FROM submissions s
        LEFT JOIN analyses a ON s.job_id = a.job_id
        WHERE s.status = 'done'
        ORDER BY s.id DESC
    """)

    return [
        {
            "job_id": r["job_id"],
            "video_url": to_url(r["video_path"]),
            "annotated_video_url": to_url(r["annotated_video_path"]) if r["annotated_video_path"] else None,
            "smpl_url": to_url(r["smpl_path"]) if r["smpl_path"] else None
        }
        for r in rows
    ]