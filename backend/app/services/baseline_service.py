import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.industrial_facility import IndustrialFacility
from app.models.facility_history import FacilityHistoricalBehavior
from app.models.facility_baseline import FacilityNormalBaseline
from app.schemas.facility_baseline import GenerateBaselineResponse, BaselineSummary

logger = logging.getLogger("firms_app.baseline_service")

CATEGORY_DEFAULT_BASELINES = {
    "refinery": {"p50": 25.0, "p95": 55.0, "p99": 85.0},
    "power_plant": {"p50": 35.0, "p95": 75.0, "p99": 110.0},
    "steel_works": {"p50": 30.0, "p95": 65.0, "p99": 95.0},
    "chemical": {"p50": 15.0, "p95": 35.0, "p99": 50.0},
    "industrial": {"p50": 10.0, "p95": 25.0, "p99": 40.0},
}

class BaselineService:
    """
    Service layer establishing expected normal operating thermal envelope 
    (P50, P95, P99 bounds) per industrial facility.
    """

    def generate_facility_baselines(
        self, 
        db: Session, 
        recalculate_all: bool = False
    ) -> GenerateBaselineResponse:
        """Generates normal operating thermal baseline bounds for all monitored facilities."""
        if recalculate_all:
            db.query(FacilityNormalBaseline).delete()
            db.commit()

        facilities = db.query(IndustrialFacility).all()
        total_facs = len(facilities)

        generated_cnt = 0
        established_cnt = 0
        preliminary_cnt = 0

        now = datetime.datetime.utcnow()

        for fac in facilities:
            existing = db.query(FacilityNormalBaseline).filter(
                FacilityNormalBaseline.facility_id == fac.id
            ).first()

            if existing and not recalculate_all:
                if existing.baseline_status == "ESTABLISHED": established_cnt += 1
                else: preliminary_cnt += 1
                continue

            # Check historical behavior profile
            history = db.query(FacilityHistoricalBehavior).filter(
                FacilityHistoricalBehavior.facility_id == fac.id
            ).first()

            fac_cat = fac.facility_type.lower()
            cat_default = CATEGORY_DEFAULT_BASELINES.get(fac_cat, CATEGORY_DEFAULT_BASELINES["industrial"])

            if history and history.total_observations >= 3:
                status = "ESTABLISHED"
                p50 = history.median_frp if history.median_frp > 0 else cat_default["p50"]
                p95 = history.p95_frp if history.p95_frp > 0 else cat_default["p95"]
                p99 = history.p99_frp if history.p99_frp > 0 else cat_default["p99"]
                monthly_freq = round(history.total_observations / max(1.0, history.observation_days / 30.0), 2)
                
                if history.day_count > history.night_count * 1.5:
                    day_night_pref = "DAY_DOMINANT"
                elif history.night_count > history.day_count * 1.5:
                    day_night_pref = "NIGHT_DOMINANT"
                else:
                    day_night_pref = "BALANCED"

                established_cnt += 1
            else:
                status = "PRELIMINARY_DEFAULT"
                p50 = cat_default["p50"]
                p95 = cat_default["p95"]
                p99 = cat_default["p99"]
                monthly_freq = 1.0
                day_night_pref = "BALANCED"
                preliminary_cnt += 1

            if existing:
                existing.baseline_frp_p50 = p50
                existing.baseline_frp_p95 = p95
                existing.baseline_frp_p99 = p99
                existing.monthly_frequency = monthly_freq
                existing.day_night_preference = day_night_pref
                existing.baseline_status = status
                existing.updated_at = now
            else:
                baseline = FacilityNormalBaseline(
                    facility_id=fac.id,
                    baseline_frp_p50=p50,
                    baseline_frp_p95=p95,
                    baseline_frp_p99=p99,
                    monthly_frequency=monthly_freq,
                    day_night_preference=day_night_pref,
                    baseline_status=status,
                    updated_at=now
                )
                db.add(baseline)

            generated_cnt += 1

        db.commit()
        logger.info(f"Facility normal baseline generation completed: {generated_cnt} facility baselines generated/updated.")

        return GenerateBaselineResponse(
            status="success",
            baselines_generated=generated_cnt,
            established_baselines=established_cnt,
            preliminary_defaults=preliminary_cnt
        )
