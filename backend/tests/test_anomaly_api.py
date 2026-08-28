import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

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

def test_list_anomalies_empty():
    response = client.get("/anomalies")
    assert response.status_code == 200
    assert response.json() == []

def test_detect_anomalies_job_empty():
    response = client.post("/anomalies/detect", json={"recalculate_all": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["anomalies_detected"] == 0

def test_anomalies_summary_empty():
    response = client.get("/analytics/anomalies-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_anomalies"] == 0
    assert data["max_multiplier_ratio"] == 0.0
