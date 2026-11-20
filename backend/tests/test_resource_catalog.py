import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main
from app.resource_catalog import ensure_resource_schema


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATABASE_PATH", str(tmp_path / "resources.db"))
    main.initialise_database()
    ensure_resource_schema(main.DATABASE_PATH)
    return TestClient(main.app)


def register(client, email="resources@example.com"):
    response = client.post("/api/auth/register", json={
        "email": email, "display_name": "Resource User", "password": "safe-password-123"
    })
    assert response.status_code == 201


def test_resource_endpoints_require_authentication(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/resources/sources").status_code == 401
    assert client.get("/api/resources/pyqs").status_code == 401


def test_sources_are_seeded_and_exam_filter_works(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client)
    response = client.get("/api/resources/sources")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 25
    assert any(item["source_id"] == "upsc-pyq-current" for item in payload["items"])
    assert any(item["source_id"] == "prs" and item["authority_level"] == "secondary" for item in payload["items"])

    filtered = client.get("/api/resources/sources?exam_id=upsc_ifos")
    assert filtered.status_code == 200
    assert any("IFoS" in item["exam_scope"] for item in filtered.json()["items"])
    assert client.get("/api/resources/sources?exam_id=unknown").status_code == 422


def test_pyq_collections_preserve_exam_and_stage_boundaries(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    register(client)
    all_items = client.get("/api/resources/pyqs").json()
    assert all_items["count"] >= 7
    assert all(item["acquisition_status"] == "discovery_only" for item in all_items["items"])

    cse_prelims = client.get("/api/resources/pyqs?exam_id=upsc_cse&stage=preliminary")
    assert cse_prelims.status_code == 200
    assert len(cse_prelims.json()["items"]) == 1
    assert cse_prelims.json()["items"][0]["collection_id"] == "upsc-cse-prelims"

    assert client.get("/api/resources/pyqs?stage=invalid").status_code == 422
    assert client.get("/api/resources/pyqs?exam_id=invalid").status_code == 422
