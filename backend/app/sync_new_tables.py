import logging
import datetime
from app.database import SessionLocal
from app.models.industrial_facility import IndustrialFacility
from app.models.facility import Facility
from app.models.thermal_observation import ThermalObservation
from app.models.facility_association import ThermalFacilityAssociation
from app.models.facility_observation import FacilityObservation
from app.models.facility_baseline import FacilityBaseline
from app.models.facility_history import FacilityHistoricalBehavior
from app.models.ingestion_batch import IngestionBatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_new_tables")

def sync():
    db = SessionLocal()
    try:
        logger.info("Starting synchronization of new Step 1 tables...")
        
        # 1. Sync IngestionBatch
        if db.query(IngestionBatch).count() == 0:
            batch = IngestionBatch(
                id="batch_initial_seed",
                source="VIIRS_SNPP_NRT",
                started_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
                completed_at=datetime.datetime.utcnow(),
                records_received=13,
                records_valid=13,
                records_rejected=0,
                status="completed"
            )
            db.add(batch)
            db.commit()
            logger.info("Synced IngestionBatch.")

        # 2. Sync Facilities
        old_facs = db.query(IndustrialFacility).all()
        for of in old_facs:
            existing = db.query(Facility).filter(Facility.id == of.id).first()
            if not existing:
                nf = Facility(
                    id=of.id,
                    osm_id=of.osm_id,
                    name=of.name,
                    facility_type=of.facility_type,
                    latitude=of.latitude,
                    longitude=of.longitude,
                    geometry=of.geometry,
                    source="OSM Overpass API",
                    created_at=of.created_at,
                    updated_at=of.created_at
                )
                db.add(nf)
        db.commit()
        logger.info(f"Synced {len(old_facs)} Facilities.")

        # 3. Sync FacilityObservations (associations)
        old_assocs = db.query(ThermalFacilityAssociation).all()
        for oa in old_assocs:
            existing = db.query(FacilityObservation).filter(
                FacilityObservation.facility_id == oa.facility_id,
                FacilityObservation.observation_id == oa.observation_id
            ).first()
            if not existing:
                na = FacilityObservation(
                    facility_id=oa.facility_id,
                    observation_id=oa.observation_id,
                    distance_m=oa.distance_meters,
                    association_method=oa.association_type,
                    created_at=oa.created_at
                )
                db.add(na)
        db.commit()
        logger.info(f"Synced {len(old_assocs)} FacilityObservations.")

        # 4. Sync FacilityBaselines
        old_histories = db.query(FacilityHistoricalBehavior).all()
        for oh in old_histories:
            existing = db.query(FacilityBaseline).filter(FacilityBaseline.facility_id == oh.facility_id).first()
            if not existing:
                nb = FacilityBaseline(
                    facility_id=oh.facility_id,
                    baseline_start=datetime.datetime.utcnow() - datetime.timedelta(days=90),
                    baseline_end=datetime.datetime.utcnow(),
                    observation_count=oh.total_observations,
                    median_frp=oh.median_frp,
                    p95_frp=oh.p95_frp,
                    p99_frp=oh.p99_frp,
                    mad_frp=2.5,
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
                db.add(nb)
        db.commit()
        logger.info("Synced FacilityBaselines.")
        
        logger.info("Synchronization complete!")
    finally:
        db.close()

if __name__ == "__main__":
    sync()
