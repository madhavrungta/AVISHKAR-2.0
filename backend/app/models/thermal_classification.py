import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ThermalClassification(Base):
    """
    SQLAlchemy model representing the predicted candidate source classification
    for a NASA FIRMS thermal anomaly observation.
    """
    __tablename__ = "thermal_classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    observation_id = Column(Integer, ForeignKey("thermal_observations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    predicted_class = Column(String(50), nullable=False, index=True) # INDUSTRIAL_CANDIDATE, NATURAL_FOREST_CANDIDATE, AGRICULTURAL_CANDIDATE, OTHER_UNKNOWN
    confidence_score = Column(Float, nullable=False, index=True)       # 0.0 to 1.0
    classification_reason = Column(Text, nullable=False)               # Explainable rationale text
    feature_vector_json = Column(Text, nullable=True)                  # Serialized JSON of feature inputs
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    observation = relationship("ThermalObservation", backref="classification", uselist=False)

    __table_args__ = (
        Index("idx_class_score", "predicted_class", "confidence_score"),
    )

    def __repr__(self):
        return f"<ThermalClassification(obs_id={self.observation_id}, class='{self.predicted_class}', conf={self.confidence_score})>"
