import base64
import hashlib
import hmac
import json
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

from app.planner_engine import ensure_planning_schema, generate_rolling_plan
from app.syllabus_catalog import ensure_syllabus_schema, seed_syllabus_catalog

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
        connection.execute("""
            CREATE TABLE IF NOT EXISTS exam_catalog (
                exam_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                short_name TEXT NOT NULL,
                conducting_body TEXT NOT NULL,
                description TEXT NOT NULL,
                syllabus_status TEXT NOT NULL DEFAULT 'pending_verification'
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS planner_profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                preparation_start_date TEXT NOT NULL,
                medium TEXT NOT NULL DEFAULT 'English',
                daily_hours REAL NOT NULL DEFAULT 2.5,
                current_level TEXT NOT NULL DEFAULT 'beginner',
                selected_days TEXT NOT NULL DEFAULT '[0,1,2,3,4,5]',
                rest_day TEXT NOT NULL DEFAULT 'Sunday',
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS candidate_exam_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                exam_id TEXT NOT NULL REFERENCES exam_catalog(exam_id),
                attempt_year INTEGER NOT NULL,
                priority INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, exam_id)
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_exam_targets_user ON candidate_exam_targets(user_id)")
        exams = [
            ("upsc_cse", "UPSC Civil Services Examination", "CSE", "Union Public Service Commission", "Civil services examination with preliminary, mains and interview stages."),
            ("upsc_ifos", "Indian Forest Service Examination", "IFoS", "Union Public Service Commission", "Forest service examination with a common preliminary stage and IFoS-specific mains and interview."),
            ("uppsc_pcs", "UPPSC Combined State / Upper Subordinate Services", "PCS", "Uttar Pradesh Public Service Commission", "Uttar Pradesh state civil services examination; stages and scheme depend on the applicable notification."),
            ("uppsc_acf_rfo", "UPPSC Assistant Conservator of Forest / Range Forest Officer", "ACF / RFO", "Uttar Pradesh Public Service Commission", "Forest services recruitment; eligibility and subject requirements depend on the applicable notification."),
        ]
        connection.executemany("INSERT OR IGNORE INTO exam_catalog(exam_id, name, short_name, conducting_body, description) VALUES (?, ?, ?, ?, ?)", exams)
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now().isoformat(),))
        connection.execute("DELETE FROM oauth_states WHERE expires_at <= ?", (utc_now().isoformat(),))


initialise_database()
ensure_planning_schema(DATABASE_PATH)
ensure_syllabus_schema(DATABASE_PATH)
seed_syllabus_catalog(DATABASE_PATH)

app = FastAPI(
    title="PrepCompass API",
    description="Local-first study planning, account and progress API",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:3011"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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



class ExamTargetInput(BaseModel):
    exam_id: str = Field(min_length=1, max_length=40)
    attempt_year: int = Field(ge=2026, le=2035)
    priority: int = Field(default=1, ge=1, le=4)

class PlannerSetupPayload(BaseModel):
    preparation_start_date: date
    medium: str = Field(default="English", min_length=2, max_length=40)
    daily_hours: float = Field(ge=0.5, le=12)
    current_level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    selected_days: list[int] = Field(min_length=1, max_length=7)
    rest_day: str = Field(default="Sunday", min_length=3, max_length=12)
    exam_targets: list[ExamTargetInput] = Field(min_length=1, max_length=4)

    @field_validator("selected_days")
    @classmethod
    def valid_days(cls, value):
        if any(day < 0 or day > 6 for day in value) or len(set(value)) != len(value):
            raise ValueError("Choose unique weekdays from Monday (0) to Sunday (6)")
        return sorted(value)

    @field_validator("exam_targets")
    @classmethod
    def unique_exams(cls, value):
        ids = [target.exam_id for target in value]
        if len(set(ids)) != len(ids):
            raise ValueError("An exam can only be selected once")
        return value

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


@app.get("/api/auth/google/config")
def google_config():
    return {"enabled": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)}


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


@app.get("/api/syllabus/catalog")
def syllabus_catalog(exam_id: Optional[str] = None, cycle_year: Optional[int] = None,
                     stage: Optional[str] = None, user=Depends(current_user)):
    if stage and stage not in {"preliminary", "mains", "interview"}:
        raise HTTPException(status_code=422, detail="Invalid syllabus stage")
    clauses = []
    values = []
    if exam_id:
        clauses.append("n.exam_id=?")
        values.append(exam_id)
    if cycle_year:
        clauses.append("s.cycle_year=?")
        values.append(cycle_year)
    if stage:
        clauses.append("n.stage=?")
        values.append(stage)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with db_connection() as connection:
        rows = connection.execute(
            f"""SELECT n.node_id, n.exam_id, e.name AS exam_name, n.parent_node_id,
                       n.stage, n.paper_code, n.title, n.description, n.sort_order, n.node_type,
                       n.source_locator, s.source_id, s.cycle_year, s.title AS source_title,
                       s.issuing_body, s.document_url, s.landing_url, s.publication_date,
                       s.verification_status, s.notes AS source_notes
                FROM syllabus_nodes n
                JOIN syllabus_sources s ON s.source_id=n.source_id
                JOIN exam_catalog e ON e.exam_id=n.exam_id
                {where}
                ORDER BY n.exam_id, s.cycle_year DESC, n.stage, n.sort_order, n.node_id""",
            values,
        ).fetchall()
        crosswalks = connection.execute(
            """SELECT c.source_node_id, c.target_node_id, c.relation, c.rationale
               FROM syllabus_crosswalks c"""
        ).fetchall()
    return {"items": [dict(row) for row in rows],
            "crosswalks": [dict(row) for row in crosswalks],
            "catalogue_status": "baseline_incomplete",
            "notice": "Source-cycle syllabus outline only. Confirm the official notification for your target year; unseeded subtopics and resource mappings are not implied to be complete."}


@app.get("/api/syllabus/optional-subjects")
def get_optional_subjects(exam_id: str, user=Depends(current_user)):
    if exam_id not in {"upsc_cse", "upsc_ifos", "uppsc_acf_rfo"}:
        raise HTTPException(status_code=422, detail="No optional-subject catalogue is available for this examination")
    with db_connection() as connection:
        selected_target = connection.execute(
            "SELECT 1 FROM candidate_exam_targets WHERE user_id=? AND exam_id=?",
            (user["id"], exam_id),
        ).fetchone()
        if not selected_target:
            raise HTTPException(status_code=404, detail="This examination is not in your preparation profile")
        options = connection.execute(
            "SELECT subject_code, subject_name FROM optional_subject_catalog WHERE exam_id=? ORDER BY subject_name",
            (exam_id,),
        ).fetchall()
        selected = connection.execute(
            "SELECT subject_code FROM candidate_optional_subjects WHERE user_id=? AND exam_id=? ORDER BY subject_code",
            (user["id"], exam_id),
        ).fetchall()
        conflicts = connection.execute(
            "SELECT subject_a, subject_b, reason FROM optional_subject_conflicts WHERE exam_id=?",
            (exam_id,),
        ).fetchall()
    return {"exam_id": exam_id, "required_count": 1 if exam_id == "upsc_cse" else 2,
            "options": [dict(x) for x in options],
            "selected": [x["subject_code"] for x in selected],
            "prohibited_combinations": [dict(x) for x in conflicts]}


class OptionalSubjectSelection(BaseModel):
    exam_id: str
    subjects: list[str] = Field(min_length=1, max_length=2)


@app.put("/api/syllabus/optional-subjects")
def save_optional_subjects(payload: OptionalSubjectSelection, user=Depends(current_user)):
    if payload.exam_id not in {"upsc_cse", "upsc_ifos", "uppsc_acf_rfo"}:
        raise HTTPException(status_code=422, detail="No optional-subject catalogue is available for this examination")
    required_count = 1 if payload.exam_id == "upsc_cse" else 2
    if len(set(payload.subjects)) != required_count:
        raise HTTPException(status_code=422, detail=f"Choose exactly {required_count} different optional subject(s)")
    now = utc_now().isoformat()
    with db_connection() as connection:
        if not connection.execute(
            "SELECT 1 FROM candidate_exam_targets WHERE user_id=? AND exam_id=?",
            (user["id"], payload.exam_id),
        ).fetchone():
            raise HTTPException(status_code=404, detail="This examination is not in your preparation profile")
        valid = {x["subject_code"] for x in connection.execute(
            "SELECT subject_code FROM optional_subject_catalog WHERE exam_id=?", (payload.exam_id,)
        )}
        invalid = set(payload.subjects) - valid
        if invalid:
            raise HTTPException(status_code=422, detail=f"Unknown optional subject: {sorted(invalid)[0]}")
        chosen = set(payload.subjects)
        for conflict in connection.execute(
            "SELECT subject_a, subject_b, reason FROM optional_subject_conflicts WHERE exam_id=?",
            (payload.exam_id,),
        ):
            if {conflict["subject_a"], conflict["subject_b"]}.issubset(chosen):
                raise HTTPException(status_code=422, detail=conflict["reason"])
        connection.execute(
            "DELETE FROM candidate_optional_subjects WHERE user_id=? AND exam_id=?",
            (user["id"], payload.exam_id),
        )
        connection.executemany(
            "INSERT INTO candidate_optional_subjects(user_id,exam_id,subject_code,updated_at) VALUES(?,?,?,?)",
            [(user["id"], payload.exam_id, code, now) for code in payload.subjects],
        )
    return {"status": "saved", "exam_id": payload.exam_id, "subjects": payload.subjects}


@app.get("/api/planner/catalog")
def planner_catalog(user=Depends(current_user)):
    with db_connection() as connection:
        rows = connection.execute("SELECT exam_id, name, short_name, conducting_body, description, syllabus_status FROM exam_catalog ORDER BY conducting_body, name").fetchall()
    return [dict(row) for row in rows]

@app.get("/api/planner/setup")
def get_planner_setup(user=Depends(current_user)):
    with db_connection() as connection:
        profile = connection.execute("SELECT preparation_start_date, medium, daily_hours, current_level, selected_days, rest_day FROM planner_profiles WHERE user_id = ?", (user["id"],)).fetchone()
        targets = connection.execute("SELECT exam_id, attempt_year, priority FROM candidate_exam_targets WHERE user_id = ? ORDER BY priority, exam_id", (user["id"],)).fetchall()
    return {
        "profile": ({**dict(profile), "selected_days": json.loads(profile["selected_days"])} if profile else None),
        "exam_targets": [dict(row) for row in targets],
    }

@app.post("/api/planner/setup")
def save_planner_setup(payload: PlannerSetupPayload, user=Depends(current_user)):
    now = utc_now().isoformat()
    with db_connection() as connection:
        known = {row["exam_id"] for row in connection.execute("SELECT exam_id FROM exam_catalog")}
        unknown = [target.exam_id for target in payload.exam_targets if target.exam_id not in known]
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown exam selection: {unknown[0]}")
        connection.execute("""
            INSERT INTO planner_profiles(user_id, preparation_start_date, medium, daily_hours, current_level, selected_days, rest_day, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET preparation_start_date=excluded.preparation_start_date, medium=excluded.medium,
                daily_hours=excluded.daily_hours, current_level=excluded.current_level, selected_days=excluded.selected_days,
                rest_day=excluded.rest_day, updated_at=excluded.updated_at
        """, (user["id"], payload.preparation_start_date.isoformat(), payload.medium.strip(), payload.daily_hours,
              payload.current_level, json.dumps(payload.selected_days), payload.rest_day, now))
        connection.execute("DELETE FROM candidate_exam_targets WHERE user_id = ?", (user["id"],))
        connection.executemany(
            "INSERT INTO candidate_exam_targets(user_id, exam_id, attempt_year, priority, created_at) VALUES (?, ?, ?, ?, ?)",
            [(user["id"], target.exam_id, target.attempt_year, target.priority, now) for target in payload.exam_targets],
        )
    return {"status": "saved", "exam_count": len(payload.exam_targets), "message": "Your preparation profile is saved. Open the daily planner to generate your rolling study schedule."}

@app.get("/api/planner/overview")
def planner_overview(user=Depends(current_user)):
    with db_connection() as connection:
        profile = connection.execute("SELECT preparation_start_date, medium, daily_hours, current_level, selected_days, rest_day FROM planner_profiles WHERE user_id = ?", (user["id"],)).fetchone()
        targets = connection.execute("""SELECT c.exam_id, c.attempt_year, c.priority, e.name, e.short_name, e.syllabus_status
            FROM candidate_exam_targets c JOIN exam_catalog e ON e.exam_id = c.exam_id
            WHERE c.user_id = ? ORDER BY c.priority, c.exam_id""", (user["id"],)).fetchall()
    if not profile:
        return {"configured": False, "profile": None, "exam_targets": []}
    return {"configured": True, "profile": {**dict(profile), "selected_days": json.loads(profile["selected_days"])}, "exam_targets": [dict(row) for row in targets]}


class GeneratePlanPayload(BaseModel):
    horizon_days: int = Field(default=28, ge=7, le=56)


class TaskUpdatePayload(BaseModel):
    status: str = Field(pattern="^(planned|in_progress|completed|partial|skipped)$")
    actual_minutes: int = Field(default=0, ge=0, le=1440)
    notes: str = Field(default="", max_length=2000)


@app.post("/api/planner/generate")
def planner_generate(payload: GeneratePlanPayload, user=Depends(current_user)):
    try:
        result = generate_rolling_plan(DATABASE_PATH, user["id"], payload.horizon_days)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/planner/plan")
def planner_get_plan(user=Depends(current_user)):
    with db_connection() as connection:
        plan = connection.execute(
            "SELECT id, version, start_date, end_date, status, assumptions_json, created_at FROM study_plans WHERE user_id=? AND status='active' ORDER BY version DESC LIMIT 1",
            (user["id"],),
        ).fetchone()
        if not plan:
            has_setup = connection.execute(
                "SELECT EXISTS(SELECT 1 FROM planner_profiles p JOIN candidate_exam_targets t ON t.user_id=p.user_id WHERE p.user_id=?)",
                (user["id"],),
            ).fetchone()[0]
            return {"configured": False, "has_setup": bool(has_setup), "plan": None, "tasks": []}
        tasks = connection.execute(
            """SELECT id, task_date, sequence, subject, topic_id, topic, task_type, instruction,
                      estimated_minutes, exam_ids_json, syllabus_status, status, actual_minutes, notes
               FROM plan_tasks WHERE user_id=? AND plan_id=? ORDER BY task_date, sequence""",
            (user["id"], plan["id"]),
        ).fetchall()
    plan_data = dict(plan)
    plan_data["assumptions"] = json.loads(plan_data.pop("assumptions_json"))
    task_data = []
    for row in tasks:
        item = dict(row)
        item["exam_ids"] = json.loads(item.pop("exam_ids_json"))
        task_data.append(item)
    return {"configured": True, "has_setup": True, "plan": plan_data, "tasks": task_data}


@app.patch("/api/planner/tasks/{task_id}")
def planner_update_task(task_id: int, payload: TaskUpdatePayload, user=Depends(current_user)):
    with db_connection() as connection:
        result = connection.execute(
            """UPDATE plan_tasks SET status=?, actual_minutes=?, notes=?,
               completed_at=CASE WHEN ?='completed' THEN ? ELSE NULL END
               WHERE id=? AND user_id=?""",
            (payload.status, payload.actual_minutes, payload.notes.strip(), payload.status,
             utc_now().isoformat(), task_id, user["id"]),
        )
        if result.rowcount != 1:
            raise HTTPException(status_code=404, detail="Task not found")
        row = connection.execute(
            "SELECT id, task_date, topic, status, estimated_minutes, actual_minutes, notes FROM plan_tasks WHERE id=? AND user_id=?",
            (task_id, user["id"]),
        ).fetchone()
    return dict(row)
