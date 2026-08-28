import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Use StaticPool to share single SQLite in-memory database across connections in test
engine = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "firms_api_key_configured" in data
    assert "firms_api_key_message" in data

def test_list_thermal_observations_empty():
    response = client.get("/thermal-observations")
    assert response.status_code == 200
    assert response.json() == []

def test_analytics_summary_empty():
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_observations"] == 0
    assert data["max_frp"] is None

def test_ingestion_endpoint_without_key(monkeypatch):
    # Calling POST /ingestion/firms when key is empty should return 400 with key guidance
    from app.config import settings
    monkeypatch.setattr(settings, "FIRMS_MAP_KEY", "")
    response = client.post("/ingestion/firms", json={"source": "VIIRS_SNPP_NRT"})
    assert response.status_code in [400, 502]
    detail = response.json().get("detail", "")
    assert "FIRMS_MAP_KEY" in detail or "Verify" in detail
