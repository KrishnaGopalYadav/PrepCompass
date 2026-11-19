import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main


def make_client(tmp_path, monkeypatch):
    database = tmp_path / "planner-test.db"
    monkeypatch.setattr(main, "DATABASE_PATH", str(database))
    main.initialise_database()
    return TestClient(main.app)


def register(client, email, name):
    response = client.post("/api/auth/register", json={
        "email": email, "display_name": name, "password": "secure-password-123",
    })
    assert response.status_code == 201


def setup_payload(exam_targets=None):
    return {
        "preparation_start_date": "2026-12-07",
        "medium": "English",
        "daily_hours": 2.5,
        "current_level": "beginner",
        "selected_days": [0, 1, 2, 3, 4, 5],
        "rest_day": "Sunday",
        "exam_targets": exam_targets or [
            {"exam_id": "upsc_cse", "attempt_year": 2028, "priority": 1},
            {"exam_id": "upsc_ifos", "attempt_year": 2028, "priority": 2},
        ],
    }


def test_exam_catalog_and_multi_exam_setup_are_saved_per_user(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client, "planner@example.com", "Planner User")

    catalog = client.get("/api/planner/catalog")
    assert catalog.status_code == 200
    assert {item["exam_id"] for item in catalog.json()} == {
        "upsc_cse", "upsc_ifos", "uppsc_pcs", "uppsc_acf_rfo",
    }

    saved = client.post("/api/planner/setup", json=setup_payload())
    assert saved.status_code == 200
    assert saved.json()["exam_count"] == 2

    overview = client.get("/api/planner/overview").json()
    assert overview["configured"] is True
    assert overview["profile"]["daily_hours"] == 2.5
    assert overview["profile"]["selected_days"] == [0, 1, 2, 3, 4, 5]
    assert {(item["exam_id"], item["attempt_year"]) for item in overview["exam_targets"]} == {
        ("upsc_cse", 2028), ("upsc_ifos", 2028),
    }


def test_planner_profile_is_isolated_between_accounts(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client, "one@example.com", "One")
    assert client.post("/api/planner/setup", json=setup_payload()).status_code == 200

    assert client.post("/api/auth/logout").status_code == 200
    register(client, "two@example.com", "Two")
    overview = client.get("/api/planner/overview")
    assert overview.status_code == 200
    assert overview.json() == {"configured": False, "profile": None, "exam_targets": []}


def test_planner_rejects_duplicate_exam_targets_and_invalid_availability(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client, "validation@example.com", "Validation")
    duplicate = setup_payload([
        {"exam_id": "upsc_cse", "attempt_year": 2028, "priority": 1},
        {"exam_id": "upsc_cse", "attempt_year": 2029, "priority": 2},
    ])
    assert client.post("/api/planner/setup", json=duplicate).status_code == 422

    invalid_days = setup_payload()
    invalid_days["selected_days"] = [0, 0, 8]
    assert client.post("/api/planner/setup", json=invalid_days).status_code == 422


def test_planner_endpoints_require_authentication(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/planner/catalog").status_code == 401
    assert client.get("/api/planner/setup").status_code == 401
    assert client.get("/api/planner/overview").status_code == 401
    assert client.post("/api/planner/setup", json=setup_payload()).status_code == 401
