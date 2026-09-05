import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base

class MLShadowPrediction(Base):
    """
    Dedicated database model for recording ML shadow inference predictions.
    Maintains full auditability, idempotency, latency, and calibration metadata
    without altering or overriding the authoritative Risk Engine.
    """
    __tablename__ = "ml_shadow_predictions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("thermal_observations.id"), nullable=False, index=True)
    model_version = Column(String, nullable=False, index=True)
    predicted_class = Column(String, nullable=False)
    probability_industrial_fire = Column(Float, nullable=False, default=0.0)
    probability_gas_flare = Column(Float, nullable=False, default=0.0)
    probability_agricultural_burning = Column(Float, nullable=False, default=0.0)
    probability_mining_activity = Column(Float, nullable=False, default=0.0)
    probability_wildfire = Column(Float, nullable=False, default=0.0)
    max_probability = Column(Float, nullable=False, default=0.0)
    existing_risk_level = Column(String, nullable=True)
    existing_risk_score = Column(Float, nullable=True)
    inference_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    feature_schema_version = Column(String, default="4C.1")
    prediction_status = Column(String, default="SUCCESS")  # SUCCESS, FAILED, SKIPPED_DISABLED
    inference_latency_ms = Column(Float, default=0.0)

    # Relationship to parent ThermalObservation
    observation = relationship("ThermalObservation", backref="shadow_predictions")

    __table_args__ = (
        UniqueConstraint("event_id", "model_version", name="uq_shadow_event_model"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "model_version": self.model_version,
            "predicted_class": self.predicted_class,
            "probabilities": {
                "INDUSTRIAL_FIRE": round(self.probability_industrial_fire, 4),
                "GAS_FLARE": round(self.probability_gas_flare, 4),
                "AGRICULTURAL_BURNING": round(self.probability_agricultural_burning, 4),
                "MINING_ACTIVITY": round(self.probability_mining_activity, 4),
                "WILDFIRE": round(self.probability_wildfire, 4)
            },
            "max_probability": round(self.max_probability, 4),
            "existing_risk_level": self.existing_risk_level,
            "existing_risk_score": round(self.existing_risk_score, 2) if self.existing_risk_score is not None else None,
            "prediction_status": self.prediction_status,
            "inference_latency_ms": round(self.inference_latency_ms, 2),
            "feature_schema_version": self.feature_schema_version,
            "inference_timestamp": self.inference_timestamp.isoformat() if self.inference_timestamp else None
        }
