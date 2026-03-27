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
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

