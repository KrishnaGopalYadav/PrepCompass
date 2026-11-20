import sys
import sqlite3
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main
from app.diagnostics_engine import calculate_study_metrics


def client_for(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATABASE_PATH", str(tmp_path / "diagnostics.db"))
    main.initialise_database()
    main.ensure_planning_schema(main.DATABASE_PATH)
    return TestClient(main.app)


def register(client, email):
    response = client.post("/api/auth/register", json={
        "email": email,
        "display_name": "Diagnostics Tester",
        "password": "secure-password-123",
    })
    assert response.status_code == 201


def add_study_session(client):
    return client.post("/api/study-sessions", json={
        "subject": "Polity",
        "topic": "Fundamental Rights",
        "duration_minutes": 90,
        "studied_on": date.today().isoformat(),
        "notes": "Test session",
    })


def test_diagnostics_generates_and_persists_report(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "diagnostics@example.com")
    assert add_study_session(client).status_code == 201

    async def fake_generate_json(**kwargs):
        assert "metrics" in kwargs["input_data"]
        return {
            "data": {
                "summary": "Consistent recorded study activity.",
                "strengths": ["A study session was recorded."],
                "weaknesses": ["More history is needed."],
                "risks": ["Insufficient evidence for long-term trends."],
                "recommendations": ["Continue recording study sessions."],
            },
            "provider": "groq",
            "model": "test-model",
            "response_id": "test-response",
        }

    monkeypatch.setattr(main, "generate_json", fake_generate_json)

    response = client.post("/api/ai/diagnostics", json={"period_days": 28})
    assert response.status_code == 201

    report = response.json()
    assert report["ai_status"] == "generated"
    assert report["provider"] == "groq"
    assert report["metrics"]["study_activity"]["total_sessions"] == 1
    assert report["metrics"]["study_activity"]["total_minutes"] == 90
    assert report["recommendations"]["strengths"]
    assert report["recommendations"]["limitations"]

    history = client.get("/api/ai/diagnostics")
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1

    detail = client.get(f"/api/ai/diagnostics/{report['id']}")
    assert detail.status_code == 200
    assert detail.json()["metrics"]["study_activity"]["total_minutes"] == 90


def test_diagnostics_returns_metrics_when_ai_fails(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "failure@example.com")
    assert add_study_session(client).status_code == 201

    async def failed_generate_json(**kwargs):
        raise main.AIProviderError("Provider unavailable")

    monkeypatch.setattr(main, "generate_json", failed_generate_json)

    response = client.post("/api/ai/diagnostics", json={"period_days": 14})
    assert response.status_code == 201

    report = response.json()
    assert report["ai_status"] == "unavailable"
    assert report["recommendations"] is None
    assert report["metrics"]["study_activity"]["total_minutes"] == 90

    history = client.get("/api/ai/diagnostics")
    assert history.json()["items"][0]["ai_status"] == "unavailable"


def test_diagnostics_handles_insufficient_data_without_ai(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "empty@example.com")

    async def should_not_run(**kwargs):
        raise AssertionError("AI should not run without study or planner data")

    monkeypatch.setattr(main, "generate_json", should_not_run)

    response = client.post("/api/ai/diagnostics", json={"period_days": 28})
    assert response.status_code == 201
    assert response.json()["ai_status"] == "insufficient_data"
    assert response.json()["recommendations"] is None
    assert response.json()["metrics"]["study_activity"]["total_sessions"] == 0


def test_diagnostics_validates_period(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "validation@example.com")

    assert client.post(
        "/api/ai/diagnostics", json={"period_days": 6}
    ).status_code == 422

    assert client.post(
        "/api/ai/diagnostics", json={"period_days": 91}
    ).status_code == 422


def test_diagnostics_requires_authentication(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)

    assert client.post("/api/ai/diagnostics", json={}).status_code == 401
    assert client.get("/api/ai/diagnostics").status_code == 401
    assert client.get("/api/ai/diagnostics/1").status_code == 401


def test_diagnostics_history_is_isolated_between_accounts(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "first-diagnostics@example.com")
    assert add_study_session(client).status_code == 201

    async def fake_generate_json(**kwargs):
        return {
            "data": {"summary": "Test", "strengths": [], "weaknesses": [],
                     "risks": [], "recommendations": []},
            "provider": "ollama",
            "model": "test-model",
            "response_id": "test-response",
        }

    monkeypatch.setattr(main, "generate_json", fake_generate_json)

    created = client.post("/api/ai/diagnostics", json={})
    assert created.status_code == 201
    diagnostic_id = created.json()["id"]

    assert client.post("/api/auth/logout").status_code == 200
    register(client, "second-diagnostics@example.com")

    assert client.get("/api/ai/diagnostics").json()["items"] == []
    assert client.get(
        f"/api/ai/diagnostics/{diagnostic_id}"
    ).status_code == 404


def test_diagnostic_metrics_cap_consistency_and_report_task_statuses(
    tmp_path, monkeypatch
):
    client = client_for(tmp_path, monkeypatch)
    register(client, "metrics@example.com")

    database_path = main.DATABASE_PATH
    today = date.today()
    user_id = None

    with sqlite3.connect(database_path) as connection:
        user_id = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            ("metrics@example.com",),
        ).fetchone()[0]

        connection.execute(
            """INSERT INTO planner_profiles (
                user_id, preparation_start_date, daily_hours,
                selected_days, updated_at
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                user_id,
                today.isoformat(),
                2.5,
                f"[{today.weekday()}]",
                today.isoformat(),
            ),
        )

        for offset in range(4):
            studied_on = (today - __import__("datetime").timedelta(
                days=offset
            )).isoformat()
            connection.execute(
                """INSERT INTO study_sessions (
                    user_id, subject, topic, duration_minutes,
                    studied_on, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id, "Polity", f"Topic {offset}", 60,
                    studied_on, "", today.isoformat(),
                ),
            )

        cursor = connection.execute(
            """INSERT INTO study_plans (
                user_id, version, start_date, end_date, status,
                assumptions_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, 1, today.isoformat(), today.isoformat(),
                "active", "{}", today.isoformat(),
            ),
        )
        plan_id = cursor.lastrowid

        for sequence, status, actual_minutes in [
            (1, "completed", 60),
            (2, "partial", 30),
            (3, "skipped", 0),
            (4, "planned", 10),
        ]:
            connection.execute(
                """INSERT INTO plan_tasks (
                    plan_id, user_id, task_date, sequence, subject,
                    topic_id, topic, task_type, instruction,
                    estimated_minutes, exam_ids_json, status,
                    actual_minutes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    plan_id, user_id, today.isoformat(), sequence,
                    "Polity", f"topic-{sequence}", f"Topic {sequence}",
                    "study", "Study the topic", 60, "[]",
                    status, actual_minutes, today.isoformat(),
                ),
            )

    metrics = calculate_study_metrics(
        database_path, user_id, period_days=7, today=today
    )

    activity = metrics["study_activity"]
    progress = metrics["planner_progress"]

    # Four distinct study days, despite only one configured study day.
    assert activity["study_days"] == 4
    assert activity["expected_study_days"] == 1
    assert activity["consistency_percent"] == 100.0

    assert progress["scheduled_tasks"] == 4
    assert progress["completed_tasks"] == 1
    assert progress["partial_tasks"] == 1
    assert progress["skipped_tasks"] == 1
    assert progress["completion_percent"] == 25.0
    assert progress["planned_minutes"] == 240
    assert progress["actual_minutes"] == 100
