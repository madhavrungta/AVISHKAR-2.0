import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class IngestionBatch(Base):
    """
    SQLAlchemy model tracking NASA FIRMS API and OSM ingestion runs.
    """
    __tablename__ = "ingestion_batches"

    id = Column(String(100), primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    satellite = Column(String(50), nullable=True)
    requested_start = Column(DateTime, nullable=True)
    requested_end = Column(DateTime, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    records_received = Column(Integer, default=0)
    records_valid = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    status = Column(String(20), default="running", nullable=False) # running, completed, failed
    error_message = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<IngestionBatch(id='{self.id}', source='{self.source}', status='{self.status}', received={self.records_received})>"
