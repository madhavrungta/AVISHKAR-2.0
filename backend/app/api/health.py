import os
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings

router = APIRouter(tags=["Health & Status"])

@router.get("/health", summary="System Health & Configuration Check")
def get_health_status(db: Session = Depends(get_db)):
    """
    Returns system operational status, database connection status,
    NASA FIRMS API key safety status, and n8n orchestration probe status.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    key_safety = settings.get_firms_key_safety_status()

    # n8n Orchestration Live Probe
    n8n_status = "not_configured"
    n8n_url = os.getenv("N8N_URL", "").strip()
    if n8n_url:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{n8n_url}/healthz")
                if res.status_code == 200:
                    n8n_status = "connected"
                else:
                    n8n_status = "error"
        except Exception:
            n8n_status = "disconnected"

    return {
        "status": "online",
        "service": "SIH 26162 - Industrial Fire Detection Engine",
        "version": "0.8.0 (Phase 8)",
        "database_status": db_status,
        "firms_api_key_configured": key_safety["configured"],
        "firms_api_key_message": key_safety["message"],
        "n8n_status": n8n_status,
        "default_source": settings.FIRMS_SOURCE,
        "default_area": settings.FIRMS_AREA
    }

