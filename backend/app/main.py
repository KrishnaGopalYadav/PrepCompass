import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[1] / "data" / "prepcompass.db"))
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

def initialise_database():
    with db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
                studied_on TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

initialise_database()

app = FastAPI(
    title="PrepCompass API",
    description="Local-first study planning and progress API",
    version="0.1.0",
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudySessionCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=200)
    duration_minutes: int = Field(gt=0, le=1440)
    studied_on: date = Field(default_factory=date.today)
    notes: str = Field(default="", max_length=2000)

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "PrepCompass", "version": "0.1.0"}

@app.get("/api/dashboard")
def dashboard():
    today = date.today().isoformat()
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    with db_connection() as connection:
        today_minutes = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE studied_on = ?", (today,)
        ).fetchone()[0]
        week_minutes = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE studied_on >= ?", (week_start,)
        ).fetchone()[0]
        session_count = connection.execute("SELECT COUNT(*) FROM study_sessions").fetchone()[0]
        recent = connection.execute(
            "SELECT id, subject, topic, duration_minutes, studied_on, notes FROM study_sessions ORDER BY studied_on DESC, id DESC LIMIT 6"
        ).fetchall()
    return {
        "today": {"date": today, "studied_minutes": today_minutes, "goal_minutes": 150},
        "this_week": {"studied_minutes": week_minutes, "goal_minutes": 1050},
        "total_sessions": session_count,
        "recent_sessions": [dict(row) for row in recent],
    }

@app.get("/api/study-sessions")
def list_study_sessions(limit: int = 50):
    limit = max(1, min(limit, 200))
    with db_connection() as connection:
        rows = connection.execute(
            "SELECT id, subject, topic, duration_minutes, studied_on, notes FROM study_sessions ORDER BY studied_on DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]

@app.post("/api/study-sessions", status_code=201)
def create_study_session(payload: StudySessionCreate):
    created_at = datetime.now(timezone.utc).isoformat()
    with db_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO study_sessions (subject, topic, duration_minutes, studied_on, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (payload.subject.strip(), payload.topic.strip(), payload.duration_minutes,
             payload.studied_on.isoformat(), payload.notes.strip(), created_at),
        )
        session_id = cursor.lastrowid
        row = connection.execute(
            "SELECT id, subject, topic, duration_minutes, studied_on, notes FROM study_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return dict(row)
