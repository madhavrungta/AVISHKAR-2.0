import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.health import router as health_router
from app.api.thermal import router as thermal_router
from app.api.ingestion import router as ingestion_router
from app.api.facility import router as facility_router
from app.api.facility_pipeline import router as facility_pipeline_router
from app.api.association import router as association_router
from app.api.classification import router as classification_router
from app.api.history import router as history_router
from app.api.baseline import router as baseline_router
from app.api.anomaly import router as anomaly_router
from app.api.risk import router as risk_router
from app.api.agent_route import router as agent_router
from app.api.impact import router as impact_router
from app.api.landcover import router as landcover_router
from app.api.persistence import router as persistence_router
from app.api.features import router as features_router
from app.api.ground_truth import router as ground_truth_router
from app.api.shadow import router as shadow_router
from app.api.human_review import router as human_review_router

logger = logging.getLogger("firms_app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SIH 26162 Thermal Anomaly Detection Backend...")
    init_db()
    key_safety = settings.get_firms_key_safety_status()
    logger.info(f"FIRMS API Status: {key_safety['message']}")
    yield

app = FastAPI(
    title="AI-Based Industrial Fire & Persistent Thermal Source Detection API",
    description=(
        "Project SIH 26162 (NTRO) - NASA FIRMS Satellite Thermal Anomaly Ingestion & Processing Engine.\n\n"
        "**SCIENTIFIC NOTICE**: NASA FIRMS points represent **thermal anomalies / active-fire detections**, "
        "not confirmed fires or damage."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.railway\.app|https://.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(thermal_router)
app.include_router(ingestion_router)
app.include_router(facility_router)
app.include_router(facility_pipeline_router)
app.include_router(association_router)
app.include_router(classification_router)
app.include_router(history_router)
app.include_router(baseline_router)
app.include_router(anomaly_router)
app.include_router(risk_router)
app.include_router(agent_router)
app.include_router(impact_router)
app.include_router(landcover_router)
app.include_router(persistence_router)
app.include_router(features_router)
app.include_router(ground_truth_router)
app.include_router(shadow_router)
app.include_router(human_review_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "AI-Based Industrial Thermal Anomaly Engine API (SIH 26162)",
        "phase": "Phase 8 - Multi-Modal Verification & Risk Scoring",
        "documentation": "/docs",
        "health": "/health",
        "demo": "python -m app.seed  |  scripts/demo.ps1 or scripts/demo.sh",
        "scientific_notice": "NASA FIRMS thermal anomaly != confirmed fire"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
