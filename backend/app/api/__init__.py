from app.api.health import router as health_router
from app.api.thermal import router as thermal_router
from app.api.ingestion import router as ingestion_router
from app.api.facility import router as facility_router
from app.api.association import router as association_router
from app.api.classification import router as classification_router
from app.api.history import router as history_router
from app.api.baseline import router as baseline_router
from app.api.anomaly import router as anomaly_router
from app.api.risk import router as risk_router

__all__ = [
    "health_router", 
    "thermal_router", 
    "ingestion_router", 
    "facility_router", 
    "association_router",
    "classification_router",
    "history_router",
    "baseline_router",
    "anomaly_router",
    "risk_router"
]
