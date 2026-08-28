import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.models.industrial_facility import IndustrialFacility
from app.models.facility_association import ThermalFacilityAssociation
from app.models.thermal_observation import ThermalObservation
from app.models.facility_history import FacilityHistoricalBehavior
from app.schemas.facility_history import RunHistoryResponse, HistorySummary

logger = logging.getLogger("firms_app.history_service")

class HistoryService:
    """
    Service layer computing historical thermal baseline profiles per industrial facility.
    """

    @staticmethod
    def classify_activity_tier(total_obs: int) -> str:
        """Classifies facility historical thermal activity into operational persistence tiers."""
        if total_obs >= 15:
            return "HIGHLY_PERSISTENT"
        elif total_obs >= 5:
            return "MODERATELY_ACTIVE"
        elif total_obs >= 1:
            return "SPORADIC"
        else:
            return "NO_HISTORICAL_ANOMALIES"

    def run_historical_aggregation_pipeline(
        self, 
        db: Session, 
        recalculate_all: bool = False
    ) -> RunHistoryResponse:
        """Computes and updates historical behavior profiles for all industrial facilities."""
        if recalculate_all:
            db.query(FacilityHistoricalBehavior).delete()
            db.commit()

        facilities = db.query(IndustrialFacility).all()
        total_facs = len(facilities)

        profiled_cnt = 0
        hp_cnt = 0
        ma_cnt = 0
        sp_cnt = 0
        no_cnt = 0

        now = datetime.datetime.utcnow()

        for fac in facilities:
            existing = db.query(FacilityHistoricalBehavior).filter(
                FacilityHistoricalBehavior.facility_id == fac.id
            ).first()

            if existing and not recalculate_all:
                if existing.activity_tier == "HIGHLY_PERSISTENT": hp_cnt += 1
                elif existing.activity_tier == "MODERATELY_ACTIVE": ma_cnt += 1
                elif existing.activity_tier == "SPORADIC": sp_cnt += 1
                else: no_cnt += 1
                continue

            # Fetch associated thermal observations
            assocs = db.query(ThermalFacilityAssociation).filter(
                ThermalFacilityAssociation.facility_id == fac.id
            ).all()

            obs_ids = [a.observation_id for a in assocs]
            obs_list = db.query(ThermalObservation).filter(
                ThermalObservation.id.in_(obs_ids)
            ).all() if obs_ids else []

            total_obs = len(obs_list)
            activity_tier = self.classify_activity_tier(total_obs)

            if total_obs == 0:
                min_f, max_f, mean_f, med_f, p95_f, p99_f = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                day_c, night_c, dn_ratio = 0, 0, 0.0
                obs_days = 0
                first_obs, last_obs = None, None
            else:
                frp_list = [o.frp for o in obs_list if o.frp is not None]
                if not frp_list:
                    frp_list = [0.0]

                min_f = round(float(np.min(frp_list)), 2)
                max_f = round(float(np.max(frp_list)), 2)
                mean_f = round(float(np.mean(frp_list)), 2)
                med_f = round(float(np.median(frp_list)), 2)
                p95_f = round(float(np.percentile(frp_list, 95)), 2)
                p99_f = round(float(np.percentile(frp_list, 99)), 2)

                obs_days = len(set(o.acq_date for o in obs_list if o.acq_date))
                day_c = len([o for o in obs_list if o.daynight == "D"])
                night_c = len([o for o in obs_list if o.daynight == "N"])
                dn_ratio = round(day_c / night_c, 2) if night_c > 0 else float(day_c)

                timestamps = [o.observation_timestamp for o in obs_list if o.observation_timestamp]
                first_obs = min(timestamps) if timestamps else None
                last_obs = max(timestamps) if timestamps else None

            if existing:
                existing.total_observations = total_obs
                existing.observation_days = obs_days
                existing.min_frp = min_f
                existing.max_frp = max_f
                existing.mean_frp = mean_f
                existing.median_frp = med_f
                existing.p95_frp = p95_f
                existing.p99_frp = p99_f
                existing.day_count = day_c
                existing.night_count = night_c
                existing.day_night_ratio = dn_ratio
                existing.activity_tier = activity_tier
                existing.first_observed = first_obs
                existing.last_observed = last_obs
                existing.updated_at = now
            else:
                profile = FacilityHistoricalBehavior(
                    facility_id=fac.id,
                    total_observations=total_obs,
                    observation_days=obs_days,
                    min_frp=min_f,
                    max_frp=max_f,
                    mean_frp=mean_f,
                    median_frp=med_f,
                    p95_frp=p95_f,
                    p99_frp=p99_f,
                    day_count=day_c,
                    night_count=night_c,
                    day_night_ratio=dn_ratio,
                    activity_tier=activity_tier,
                    first_observed=first_obs,
                    last_observed=last_obs,
                    updated_at=now
                )
                db.add(profile)

            profiled_cnt += 1
            if activity_tier == "HIGHLY_PERSISTENT": hp_cnt += 1
            elif activity_tier == "MODERATELY_ACTIVE": ma_cnt += 1
            elif activity_tier == "SPORADIC": sp_cnt += 1
            else: no_cnt += 1

        db.commit()
        logger.info(f"Historical aggregation pipeline completed: {profiled_cnt} facility profiles updated.")

        return RunHistoryResponse(
            status="success",
            facilities_profiled=profiled_cnt,
            highly_persistent=hp_cnt,
            moderately_active=ma_cnt,
            sporadic=sp_cnt,
            no_historical_anomalies=no_cnt
        )
