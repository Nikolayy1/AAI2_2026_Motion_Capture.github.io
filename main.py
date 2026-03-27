from fastapi import FastAPI
from databases import Database
from contextlib import asynccontextmanager

DATABASE_URL = "sqlite:///./app.db"
database = Database(DATABASE_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "backend is running"}

async def create_tables():
    await database.connect()

    await database.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY,
        doctor_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        parent_folder_id INTEGER,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id),
        FOREIGN KEY (parent_folder_id) REFERENCES folders(id)
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY,
        folder_id INTEGER NOT NULL,
        video_filename TEXT NOT NULL,
        task_type TEXT,
        status TEXT DEFAULT 'pending',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (folder_id) REFERENCES folders(id)
    )
    """)

    await database.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        submission_id INTEGER NOT NULL UNIQUE,
        keypoints_json TEXT,
        metrics_json TEXT,
        annotated_video_path TEXT,
        FOREIGN KEY (submission_id) REFERENCES submissions(id)
    )
    """)

#run once when creating database then comment out
#import asyncio
#asyncio.run(create_tables())
