from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_health_exposes_database_state() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] in {"ready", "unavailable"}


def test_database_backed_list_returns_503_when_database_is_offline() -> None:
    with TestClient(app) as client:
        app.state.database_ready = False
        response = client.get("/thermal-observations")

    assert response.status_code == 503
    assert response.json()["detail"] == "PostGIS is unavailable. Start the database and retry."


def test_ingestion_reports_missing_map_key_before_database_access(monkeypatch) -> None:
    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.post("/ingestion/firms", json={})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "FIRMS_MAP_KEY is not configured. Add it to backend/.env."

