import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[1] / "data" / "prepcompass.db"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3011").rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8011").rstrip("/")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_NAME = "prepcompass_session"
SESSION_DAYS = 30
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@contextmanager
def db_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialise_database():
    with db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL,
                password_hash TEXT,
                google_sub TEXT UNIQUE,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS oauth_states (
                state_hash TEXT PRIMARY KEY,
                code_verifier TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
                studied_on TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(study_sessions)")}
        if "user_id" not in columns:
            connection.execute("ALTER TABLE study_sessions ADD COLUMN user_id INTEGER REFERENCES users(id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_user_date ON study_sessions(user_id, studied_on)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash)")
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now().isoformat(),))
        connection.execute("DELETE FROM oauth_states WHERE expires_at <= ?", (utc_now().isoformat(),))


initialise_database()

app = FastAPI(
    title="PrepCompass API",
    description="Local-first study planning, account and progress API",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:3011"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def validate_browser_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and origin:
        allowed = {FRONTEND_URL, "http://127.0.0.1:3011"}
        if origin.rstrip("/") not in allowed:
            return Response(status_code=403, content="Untrusted request origin")
    return await call_next(request)


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(derived).decode()


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored:
        return False
    try:
        algorithm, salt_text, expected_text = stored.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(expected_text.encode())
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(response: Response, user_id: int):
    token = secrets.token_urlsafe(48)
    now = utc_now()
    with db_connection() as connection:
        connection.execute(
            "INSERT INTO sessions(user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, hash_token(token), (now + timedelta(days=SESSION_DAYS)).isoformat(), now.isoformat()),
        )
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, secure=COOKIE_SECURE,
        samesite="lax", max_age=SESSION_DAYS * 24 * 60 * 60, path="/",
    )


def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, secure=COOKIE_SECURE, samesite="lax")


def current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    with db_connection() as connection:
        row = connection.execute(
            """SELECT u.id, u.email, u.display_name
               FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > ?""",
            (hash_token(token), utc_now().isoformat()),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    return dict(row)


class RegisterPayload(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Display name cannot be blank")
        return value


class LoginPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class StudySessionCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=200)
    duration_minutes: int = Field(gt=0, le=1440)
    studied_on: date = Field(default_factory=date.today)
    notes: str = Field(default="", max_length=2000)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "PrepCompass", "version": "0.2.0"}


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterPayload, response: Response):
    email = str(payload.email).strip().lower()
    with db_connection() as connection:
        existing = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        cursor = connection.execute(
            "INSERT INTO users(email, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (email, payload.display_name, password_hash(payload.password), utc_now().isoformat()),
        )
        user_id = cursor.lastrowid
    issue_session(response, user_id)
    return {"id": user_id, "email": email, "display_name": payload.display_name}


@app.post("/api/auth/login")
def login(payload: LoginPayload, response: Response):
    email = str(payload.email).strip().lower()
    with db_connection() as connection:
        user = connection.execute(
            "SELECT id, email, display_name, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    issue_session(response, user["id"])
    return {"id": user["id"], "email": user["email"], "display_name": user["display_name"]}


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, user=Depends(current_user)):
    token = request.cookies.get(COOKIE_NAME)
    with db_connection() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))
    clear_session(response)
    return {"status": "signed_out"}


@app.get("/api/auth/google/start")
def google_start():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured. Add credentials to backend/.env.")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    with db_connection() as connection:
        connection.execute(
            "INSERT INTO oauth_states(state_hash, code_verifier, expires_at) VALUES (?, ?, ?)",
            (hash_token(state), verifier, (utc_now() + timedelta(minutes=10)).isoformat()),
        )
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    redirect = RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))
    redirect.set_cookie(
        "prepcompass_oauth_state", state, httponly=True, secure=COOKIE_SECURE,
        samesite="lax", max_age=600, path="/api/auth/google",
    )
    return redirect


@app.get("/api/auth/google/callback")
async def google_callback(request: Request, code: str, state: str):
    browser_state = request.cookies.get("prepcompass_oauth_state")
    if not browser_state or not hmac.compare_digest(browser_state, state):
        raise HTTPException(status_code=400, detail="OAuth browser state did not match. Please try again.")
    with db_connection() as connection:
        state_row = connection.execute(
            "SELECT code_verifier FROM oauth_states WHERE state_hash = ? AND expires_at > ?",
            (hash_token(state), utc_now().isoformat()),
        ).fetchone()
        connection.execute("DELETE FROM oauth_states WHERE state_hash = ?", (hash_token(state),))
    if not state_row:
        raise HTTPException(status_code=400, detail="OAuth state is invalid or expired. Please try again.")
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code, "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET, "redirect_uri": redirect_uri,
                "grant_type": "authorization_code", "code_verifier": state_row["code_verifier"],
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Google sign-in could not be completed")
        access_token = token_response.json().get("access_token")
        profile_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Could not verify your Google account")
        profile = profile_response.json()
    if not profile.get("email") or not profile.get("email_verified") or not profile.get("sub"):
        raise HTTPException(status_code=401, detail="Google did not return a verified email address")
    email = profile["email"].strip().lower()
    display_name = (profile.get("name") or email.split("@")[0])[:80]
    with db_connection() as connection:
        user = connection.execute("SELECT id, google_sub FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            if user["google_sub"] and user["google_sub"] != profile["sub"]:
                raise HTTPException(status_code=409, detail="This email is linked to a different Google identity")
            connection.execute("UPDATE users SET google_sub = ? WHERE id = ?", (profile["sub"], user["id"]))
            user_id = user["id"]
        else:
            cursor = connection.execute(
                "INSERT INTO users(email, display_name, google_sub, created_at) VALUES (?, ?, ?, ?)",
                (email, display_name, profile["sub"], utc_now().isoformat()),
            )
            user_id = cursor.lastrowid
    response = RedirectResponse(FRONTEND_URL + "/", status_code=303)
    response.delete_cookie("prepcompass_oauth_state", path="/api/auth/google", httponly=True, secure=COOKIE_SECURE, samesite="lax")
    issue_session(response, user_id)
    return response


@app.get("/api/dashboard")
def dashboard(user=Depends(current_user)):
    today = date.today().isoformat()
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    with db_connection() as connection:
        today_minutes = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE user_id = ? AND studied_on = ?",
            (user["id"], today),
        ).fetchone()[0]
        week_minutes = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE user_id = ? AND studied_on >= ?",
            (user["id"], week_start),
        ).fetchone()[0]
        session_count = connection.execute("SELECT COUNT(*) FROM study_sessions WHERE user_id = ?", (user["id"],)).fetchone()[0]
        recent = connection.execute(
            """SELECT id, subject, topic, duration_minutes, studied_on, notes FROM study_sessions
               WHERE user_id = ? ORDER BY studied_on DESC, id DESC LIMIT 6""",
            (user["id"],),
        ).fetchall()
    return {
        "today": {"date": today, "studied_minutes": today_minutes, "goal_minutes": 150},
        "this_week": {"studied_minutes": week_minutes, "goal_minutes": 1050},
        "total_sessions": session_count,
        "recent_sessions": [dict(row) for row in recent],
    }


@app.get("/api/study-sessions")
def list_study_sessions(limit: int = 50, user=Depends(current_user)):
    limit = max(1, min(limit, 200))
    with db_connection() as connection:
        rows = connection.execute(
            """SELECT id, subject, topic, duration_minutes, studied_on, notes FROM study_sessions
               WHERE user_id = ? ORDER BY studied_on DESC, id DESC LIMIT ?""",
            (user["id"], limit),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/study-sessions", status_code=201)
def create_study_session(payload: StudySessionCreate, user=Depends(current_user)):
    created_at = utc_now().isoformat()
    with db_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO study_sessions (user_id, subject, topic, duration_minutes, studied_on, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user["id"], payload.subject.strip(), payload.topic.strip(), payload.duration_minutes,
             payload.studied_on.isoformat(), payload.notes.strip(), created_at),
        )
        session_id = cursor.lastrowid
        row = connection.execute(
            """SELECT id, subject, topic, duration_minutes, studied_on, notes FROM study_sessions
               WHERE id = ? AND user_id = ?""",
            (session_id, user["id"]),
        ).fetchone()
    return dict(row)
