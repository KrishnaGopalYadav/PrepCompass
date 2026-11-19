import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main
from app.syllabus_catalog import ensure_syllabus_schema, seed_syllabus_catalog


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATABASE_PATH", str(tmp_path / "syllabus.db"))
    main.initialise_database()
    ensure_syllabus_schema(main.DATABASE_PATH)
    seed_syllabus_catalog(main.DATABASE_PATH)
    return TestClient(main.app)


def register(client, email):
    response = client.post("/api/auth/register", json={
        "email": email, "display_name": "Syllabus User", "password": "safe-password-123"
    })
    assert response.status_code == 201


def add_target(client, exam_id):
    response = client.post("/api/planner/setup", json={
        "preparation_start_date": "2026-12-07", "medium": "English",
        "daily_hours": 2.5, "current_level": "beginner",
        "selected_days": [0, 1, 2, 3, 4, 5], "rest_day": "Sunday",
        "exam_targets": [{"exam_id": exam_id, "attempt_year": 2028, "priority": 1}],
    })
    assert response.status_code == 200


def test_catalog_is_authenticated_source_linked_and_cycle_scoped(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/syllabus/catalog").status_code == 401
    register(client, "catalog@example.com")

    response = client.get("/api/syllabus/catalog?exam_id=upsc_cse&cycle_year=2026")
    assert response.status_code == 200
    data = response.json()
    assert data["catalogue_status"] == "baseline_incomplete"
    assert len(data["items"]) >= 10
    assert all(item["source_id"] == "upsc-cse-2026-notice" for item in data["items"])
    assert all(item["document_url"].startswith("https://") for item in data["items"])
    assert client.get("/api/syllabus/catalog?stage=invalid").status_code == 422


def test_ifos_optional_subject_pair_and_prohibited_combinations(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client, "ifos@example.com")
    add_target(client, "upsc_ifos")

    options = client.get("/api/syllabus/optional-subjects?exam_id=upsc_ifos").json()
    assert options["required_count"] == 2
    codes = {item["subject_code"] for item in options["options"]}
    assert {"forestry", "geology", "botany", "agriculture"} <= codes

    valid = client.put("/api/syllabus/optional-subjects", json={
        "exam_id": "upsc_ifos", "subjects": ["forestry", "geology"]
    })
    assert valid.status_code == 200
    assert set(valid.json()["subjects"]) == {"forestry", "geology"}

    invalid = client.put("/api/syllabus/optional-subjects", json={
        "exam_id": "upsc_ifos", "subjects": ["agriculture", "forestry"]
    })
    assert invalid.status_code == 422


def test_acf_rfo_optional_subjects_and_user_isolation(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client, "acf@example.com")
    add_target(client, "uppsc_acf_rfo")
    saved = client.put("/api/syllabus/optional-subjects", json={
        "exam_id": "uppsc_acf_rfo", "subjects": ["forestry", "geology"]
    })
    assert saved.status_code == 200
    assert set(client.get("/api/syllabus/optional-subjects?exam_id=uppsc_acf_rfo").json()["selected"]) == {"forestry", "geology"}

    client.post("/api/auth/logout")
    register(client, "other@example.com")
    assert client.get("/api/syllabus/optional-subjects?exam_id=uppsc_acf_rfo").status_code == 404


def test_cse_optional_subject_is_one_and_sociology_can_be_saved(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client, "cse@example.com")
    add_target(client, "upsc_cse")

    options = client.get("/api/syllabus/optional-subjects?exam_id=upsc_cse").json()
    assert options["required_count"] == 1
    assert "sociology" in {item["subject_code"] for item in options["options"]}

    saved = client.put("/api/syllabus/optional-subjects", json={
        "exam_id": "upsc_cse", "subjects": ["sociology"]
    })
    assert saved.status_code == 200
    invalid = client.put("/api/syllabus/optional-subjects", json={
        "exam_id": "upsc_cse", "subjects": ["sociology", "geography"]
    })
    assert invalid.status_code == 422
