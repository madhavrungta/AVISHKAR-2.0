import logging
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal

from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.models.facility import Facility
from app.models.facility_association import ThermalFacilityAssociation
from app.models.facility_observation import FacilityObservation
from app.models.facility_baseline import FacilityBaseline
from app.models.facility_baseline import FacilityNormalBaseline
from app.models.facility_history import FacilityHistoricalBehavior
from app.models.abnormal_event import AbnormalThermalEvent
from app.models.risk_score import VerificationRiskScore

logger = logging.getLogger("firms_app.agent.tools")

def parse_event_id(event_id: str) -> int:
    """Helper to convert EVT-XXXX strings or raw IDs into integer identifiers."""
    clean = str(event_id).upper().replace("EVT-", "").strip()
    try:
        return int(clean)
    except ValueError:
        raise ValueError(f"Invalid event_id format: {event_id}. Must be numeric or EVT-XXXX.")

def get_event(event_id: str) -> Dict[str, Any]:
    """
    Retrieve event information from the existing database.
    Returns: event_id, status, priority, created_at, facility_id, anomaly_score
    """
    db: Session = SessionLocal()
    try:
        obs_id = parse_event_id(event_id)
        
        # Check abnormal event table
        abnormal = db.query(AbnormalThermalEvent).filter(
            (AbnormalThermalEvent.observation_id == obs_id) | (AbnormalThermalEvent.id == obs_id)
        ).first()

        # Check risk score table
        risk = db.query(VerificationRiskScore).filter(VerificationRiskScore.observation_id == obs_id).first()
        
        # Fallback to direct observation details
        obs = db.query(ThermalObservation).filter(ThermalObservation.id == obs_id).first()

        if not obs:
            logger.warning(f"get_event: Event/Observation #{obs_id} not found.")
            return {"error": f"Event #{event_id} not found."}

        status_str = "Active"
        priority_str = "LOW_RISK"
        anomaly_val = 0.0

        if risk:
            priority_str = f"{risk.risk_level} ({risk.composite_risk_score}/100)"
            anomaly_val = float(risk.composite_risk_score)
        elif abnormal:
            priority_str = abnormal.anomaly_severity
            anomaly_val = float(abnormal.frp_multiplier_ratio)

        facility_id_val = None
        if abnormal:
            facility_id_val = abnormal.facility_id
        else:
            # check associations
            assoc = db.query(FacilityObservation).filter(FacilityObservation.observation_id == obs.id).first()
            if not assoc:
                assoc = db.query(ThermalFacilityAssociation).filter(ThermalFacilityAssociation.observation_id == obs.id).first()
            if assoc:
                facility_id_val = assoc.facility_id

        created_at_val = abnormal.detected_at if abnormal else obs.observation_timestamp

        result = {
            "event_id": f"EVT-{str(obs.id).zfill(4)}",
            "status": status_str,
            "priority": priority_str,
            "created_at": created_at_val.isoformat() if created_at_val else None,
            "facility_id": facility_id_val,
            "anomaly_score": anomaly_val
        }
        logger.info(f"get_event: Successfully fetched details for {event_id}.")
        return result
    except Exception as e:
        logger.error(f"get_event error for {event_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def get_thermal_observations(event_id: str) -> Dict[str, Any]:
    """
    Retrieve the FIRMS observations associated with an event.
    """
    db: Session = SessionLocal()
    try:
        obs_id = parse_event_id(event_id)
        obs = db.query(ThermalObservation).filter(ThermalObservation.id == obs_id).first()

        if not obs:
            logger.warning(f"get_thermal_observations: Observation #{obs_id} not found.")
            return {"error": f"Observation for event {event_id} not found."}

        result = {
            "timestamp": obs.observation_time.isoformat() if obs.observation_time else obs.observation_timestamp.isoformat(),
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "FRP": obs.frp,
            "bright_ti4": obs.bright_ti4,
            "bright_ti5": obs.bright_ti5,
            "confidence": obs.confidence,
            "satellite": obs.satellite,
            "instrument": obs.instrument,
            "daynight": obs.daynight
        }
        logger.info(f"get_thermal_observations: Fetched data for {event_id}.")
        return result
    except Exception as e:
        logger.error(f"get_thermal_observations error for {event_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def get_facility(facility_id: int) -> Dict[str, Any]:
    """
    Retrieve industrial facility details by ID.
    """
    if facility_id is None:
        return {"error": "facility_id parameter is required"}

    db: Session = SessionLocal()
    try:
        # Check both facilities and industrial_facilities
        fac = db.query(Facility).filter(Facility.id == facility_id).first()
        if not fac:
            fac = db.query(IndustrialFacility).filter(IndustrialFacility.id == facility_id).first()

        if not fac:
            logger.warning(f"get_facility: Facility #{facility_id} not found.")
            return {"error": f"Facility #{facility_id} not found."}

        osm_id_val = fac.osm_id if hasattr(fac, "osm_id") else None
        source_val = fac.source if hasattr(fac, "source") else "OSM Overpass API"

        result = {
            "facility_id": fac.id,
            "name": fac.name or "Industrial Facility",
            "facility_type": fac.facility_type,
            "latitude": fac.latitude,
            "longitude": fac.longitude,
            "source": source_val,
            "OSM ID": osm_id_val
        }
        logger.info(f"get_facility: Fetched details for Facility #{facility_id}.")
        return result
    except Exception as e:
        logger.error(f"get_facility error for #{facility_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def get_facility_baseline(facility_id: int) -> Dict[str, Any]:
    """
    Retrieve historical baseline statistics for a facility.
    Returns "baseline unavailable" if no baseline records exist.
    """
    if facility_id is None:
        return {"error": "facility_id parameter is required"}

    db: Session = SessionLocal()
    try:
        # Check new baselines
        base = db.query(FacilityBaseline).filter(FacilityBaseline.facility_id == facility_id).first()
        # Check old baselines
        normal = db.query(FacilityNormalBaseline).filter(FacilityNormalBaseline.facility_id == facility_id).first()
        # Check old historical profiles
        hist = db.query(FacilityHistoricalBehavior).filter(FacilityHistoricalBehavior.facility_id == facility_id).first()

        if not base and not normal and not hist:
            logger.info(f"get_facility_baseline: Baseline for Facility #{facility_id} is unavailable.")
            return {"status": "baseline unavailable"}

        obs_count = base.observation_count if base else (hist.total_observations if hist else 0)
        start_time = base.baseline_start.isoformat() if base and base.baseline_start else None
        end_time = base.baseline_end.isoformat() if base and base.baseline_end else None
        
        med = base.median_frp if base else (normal.baseline_frp_p50 if normal else (hist.median_frp if hist else None))
        p95 = base.p95_frp if base else (normal.baseline_frp_p95 if normal else (hist.p95_frp if hist else None))
        p99 = base.p99_frp if base else (normal.baseline_frp_p99 if normal else (hist.p99_frp if hist else None))
        mad = base.mad_frp if base else (hist.mad_frp if hist and hasattr(hist, "mad_frp") else 2.5)

        result = {
            "observation_count": obs_count,
            "baseline_start": start_time,
            "baseline_end": end_time,
            "median_frp": med,
            "p95_frp": p95,
            "p99_frp": p99,
            "mad_frp": mad
        }
        logger.info(f"get_facility_baseline: Fetched baseline metrics for Facility #{facility_id}.")
        return result
    except Exception as e:
        logger.error(f"get_facility_baseline error for #{facility_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def get_event_timeline(event_id: str) -> Dict[str, Any]:
    """
    Retrieve chronological timeline parameters for the facility linked to the event.
    """
    db: Session = SessionLocal()
    try:
        obs_id = parse_event_id(event_id)
        
        # Resolve facility_id
        fac_id = None
        abnormal = db.query(AbnormalThermalEvent).filter(
            (AbnormalThermalEvent.observation_id == obs_id) | (AbnormalThermalEvent.id == obs_id)
        ).first()

        if abnormal:
            fac_id = abnormal.facility_id
        else:
            assoc = db.query(FacilityObservation).filter(FacilityObservation.observation_id == obs_id).first()
            if not assoc:
                assoc = db.query(ThermalFacilityAssociation).filter(ThermalFacilityAssociation.observation_id == obs_id).first()
            if assoc:
                fac_id = assoc.facility_id

        if not fac_id:
            logger.warning(f"get_event_timeline: No facility associated with Event #{obs_id}.")
            return {"error": "Associated facility not found. Timeline cannot be computed."}

        # Query all observations matching this facility
        query = db.query(ThermalObservation)
        is_new_mapping = db.query(FacilityObservation).filter(FacilityObservation.facility_id == fac_id).count() > 0
        
        if is_new_mapping:
            query = query.join(FacilityObservation, FacilityObservation.observation_id == ThermalObservation.id) \
                         .filter(FacilityObservation.facility_id == fac_id)
        else:
            query = query.join(ThermalFacilityAssociation, ThermalFacilityAssociation.observation_id == ThermalObservation.id) \
                         .filter(ThermalFacilityAssociation.facility_id == fac_id)

        related_obs = query.order_by(ThermalObservation.observation_timestamp.asc()).all()

        timeline_points = []
        for index, r_obs in enumerate(related_obs):
            t_str = r_obs.observation_time.isoformat() if r_obs.observation_time else r_obs.observation_timestamp.isoformat()
            timeline_points.append({
                "timestamp": t_str,
                "FRP": r_obs.frp,
                "observation_sequence": index + 1
            })

        # Calculate basic persistence (hours between first and last)
        persistence_val = 0.0
        if related_obs:
            first_t = related_obs[0].observation_timestamp
            last_t = related_obs[-1].observation_timestamp
            persistence_val = round((last_t - first_t).total_seconds() / 3600.0, 1)

        result = {
            "observation_count": len(related_obs),
            "persistence": f"{persistence_val} hours",
            "timeline": timeline_points
        }
        logger.info(f"get_event_timeline: Fetched timeline for Event #{event_id} (Facility #{fac_id}).")
        return result
    except Exception as e:
        logger.error(f"get_event_timeline error for {event_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def get_context(event_id: str) -> str:
    """
    Placeholder contextual tool, returning explicit unavailable notice.
    """
    logger.info(f"get_context: Context requested for {event_id} (returns unavailable).")
    return "contextual evidence unavailable"
