import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main


def make_client(tmp_path, monkeypatch):
    database = tmp_path / "prepcompass-test.db"
    monkeypatch.setattr(main, "DATABASE_PATH", str(database))
    main.initialise_database()
    return TestClient(main.app)


def test_private_study_data_is_isolated_between_accounts(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    first = client.post("/api/auth/register", json={
        "email": "first@example.com",
        "display_name": "First User",
        "password": "a-secure-password-123",
    })
    assert first.status_code == 201
    assert client.post("/api/study-sessions", json={
        "subject": "General Studies",
        "topic": "Fundamental Rights",
        "duration_minutes": 60,
        "studied_on": "2026-11-18",
        "notes": "Article 14 to 18",
    }).status_code == 201
    assert client.get("/api/dashboard").json()["total_sessions"] == 1

    assert client.post("/api/auth/logout").status_code == 200
    second = client.post("/api/auth/register", json={
        "email": "second@example.com",
        "display_name": "Second User",
        "password": "another-secure-password-456",
    })
    assert second.status_code == 201
    assert client.get("/api/dashboard").json()["total_sessions"] == 0
    assert client.get("/api/study-sessions").json() == []

    assert client.post("/api/auth/logout").status_code == 200
    assert client.post("/api/auth/login", json={
        "email": "first@example.com",
        "password": "a-secure-password-123",
    }).status_code == 200
    sessions = client.get("/api/study-sessions").json()
    assert len(sessions) == 1
    assert sessions[0]["topic"] == "Fundamental Rights"


def test_protected_endpoints_reject_anonymous_requests(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/study-sessions").status_code == 401
    assert client.post("/api/study-sessions", json={
        "subject": "GS", "topic": "Polity", "duration_minutes": 30,
    }).status_code == 401


def test_duplicate_email_and_weak_password_are_rejected(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    payload = {"email": "candidate@example.com", "display_name": "Candidate", "password": "strong-password"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert client.post("/api/auth/register", json={
        "email": "weak@example.com", "display_name": "Weak", "password": "short",
    }).status_code == 422


def test_existing_study_table_is_migrated_without_claiming_old_rows(tmp_path, monkeypatch):
    import sqlite3

    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.execute("""
        CREATE TABLE study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            studied_on TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    connection.execute(
        "INSERT INTO study_sessions(subject, topic, duration_minutes, studied_on, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("General Studies", "Legacy topic", 30, "2026-11-17", "", "2026-11-17T10:00:00+00:00"),
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(main, "DATABASE_PATH", str(database))
    main.initialise_database()
    connection = sqlite3.connect(database)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(study_sessions)")}
    legacy_owner = connection.execute("SELECT user_id FROM study_sessions WHERE topic = 'Legacy topic'").fetchone()[0]
    connection.close()
    assert "user_id" in columns
    assert legacy_owner is None
