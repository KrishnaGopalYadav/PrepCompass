import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main
from app.planner_engine import ensure_planning_schema


def client_for(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATABASE_PATH", str(tmp_path / "plan-engine.db"))
    main.initialise_database()
    ensure_planning_schema(main.DATABASE_PATH)
    return TestClient(main.app)


def register(client, email):
    response = client.post("/api/auth/register", json={
        "email": email, "display_name": "Plan Tester", "password": "secure-password-123"
    })
    assert response.status_code == 201


def configure(client, exam_id="upsc_cse"):
    return client.post("/api/planner/setup", json={
        "preparation_start_date": "2026-12-07", "medium": "English",
        "daily_hours": 2.5, "current_level": "beginner",
        "selected_days": [0, 1, 2, 3, 4, 5], "rest_day": "Sunday",
        "exam_targets": [{"exam_id": exam_id, "attempt_year": 2028, "priority": 1}],
    })


def test_generate_plan_respects_days_capacity_and_labels_provisional(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "plan@example.com")
    assert configure(client).status_code == 200

    response = client.post("/api/planner/generate", json={"horizon_days": 14})
    assert response.status_code == 200
    generated = response.json()
    assert generated["scheduled_days"] == 12
    assert generated["planned_minutes"] <= 12 * int(2.5 * 60 * 0.85)
    assert generated["assumptions"]["syllabus_status"] == "provisional"

    plan = client.get("/api/planner/plan").json()
    assert plan["configured"] is True
    assert len(plan["tasks"]) > 0
    assert all(task["syllabus_status"] == "provisional" for task in plan["tasks"])
    assert all(task["task_date"][:10] for task in plan["tasks"])
    assert all(task["estimated_minutes"] <= 127 for task in plan["tasks"])
    first_day = plan["tasks"][0]["task_date"]
    first_day_tasks = [task for task in plan["tasks"] if task["task_date"] == first_day]
    assert len({task["topic_id"] for task in first_day_tasks}) == 1
    assert all(not task["topic_id"].startswith(("forestry-", "geology-")) for task in plan["tasks"])


def test_task_progress_update_and_account_isolation(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "first@example.com")
    assert configure(client).status_code == 200
    assert client.post("/api/planner/generate", json={"horizon_days": 7}).status_code == 200
    task = client.get("/api/planner/plan").json()["tasks"][0]

    updated = client.patch(f"/api/planner/tasks/{task['id']}", json={
        "status": "completed", "actual_minutes": 50, "notes": "Reviewed notes and solved PYQs"
    })
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"

    assert client.post("/api/auth/logout").status_code == 200
    register(client, "second@example.com")
    assert client.get("/api/planner/plan").json() == {
        "configured": False, "has_setup": False, "plan": None, "tasks": []
    }
    forbidden = client.patch(f"/api/planner/tasks/{task['id']}", json={
        "status": "completed", "actual_minutes": 50, "notes": ""
    })
    assert forbidden.status_code == 404


def test_generate_requires_setup_and_valid_horizon(tmp_path, monkeypatch):
    client = client_for(tmp_path, monkeypatch)
    register(client, "empty@example.com")
    assert client.post("/api/planner/generate", json={"horizon_days": 28}).status_code == 422
    assert client.post("/api/planner/generate", json={"horizon_days": 100}).status_code == 422
