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

def test_list_classifications_empty():
    response = client.get("/classification")
    assert response.status_code == 200
    assert response.json() == []

def test_run_classification_job_empty():
    response = client.post("/classification/run", json={"recalculate_all": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_processed"] == 0

def test_classification_summary_empty():
    response = client.get("/analytics/classification-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_classifications"] == 0
    assert data["avg_confidence"] == 0.0
