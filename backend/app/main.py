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
    
    # Auto-seed demonstration data if database is fresh/empty
    from app.database import SessionLocal
    from app.models.industrial_facility import IndustrialFacility
    from app.seed import seed_database
    
    db = SessionLocal()
    try:
        count = db.query(IndustrialFacility).count()
        if count == 0:
            logger.info("Database is empty. Automatically executing demo seed and 8-phase pipeline...")
            seed_database()
            logger.info("Initial demo seed completed successfully.")
    except Exception as e:
        logger.warning(f"Auto-seed check encountered an issue: {e}")
    finally:
        db.close()

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
    allow_origin_regex=r"https://.*\.railway\.app|https://.*\.up\.railway\.app|https://.*\.onrender\.com|https://.*\.web\.app|https://.*\.firebaseapp\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

all_routers = [
    health_router,
    thermal_router,
    ingestion_router,
    facility_router,
    facility_pipeline_router,
    association_router,
    classification_router,
    history_router,
    baseline_router,
    anomaly_router,
    risk_router,
    agent_router,
    impact_router,
    landcover_router,
    persistence_router,
    features_router,
    ground_truth_router,
    shadow_router,
    human_review_router,
]

for r in all_routers:
    app.include_router(r)
    app.include_router(r, prefix="/api")

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
