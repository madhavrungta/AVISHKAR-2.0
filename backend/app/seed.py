import os
import sys
import json
import datetime
import logging
from sqlalchemy.orm import Session

from app.database import init_db, SessionLocal
from app.models.thermal_observation import ThermalObservation
from app.models.industrial_facility import IndustrialFacility
from app.services.association_service import AssociationService
from app.services.classification_service import ClassificationService
from app.services.history_service import HistoryService
from app.services.baseline_service import BaselineService
from app.services.anomaly_service import AnomalyService
from app.services.risk_service import RiskService

logger = logging.getLogger("firms_app.seed")

def seed_database():
    """
    Seeds realistic demonstration data across major Indian industrial hubs:
    - Reliance Jamnagar Refinery (Gujarat)
    - Trombay Power Station (Mumbai, Maharashtra)
    - Tata Steel Jamshedpur (Jharkhand)
    - Vizag Petrochemical Complex (Andhra Pradesh)
    - Mangalore Refinery (Karnataka)
    - Mundra Power Plant (Gujarat)
    
    Plus natural forest fires and agricultural field fires.
    Executes complete 8-phase pipeline.
    """
    print("[+] Seeding realistic demonstration data for SIH Problem 26162 (NTRO)...")
    init_db()
    db: SessionLocal = SessionLocal()

    try:
        # Clear existing data
        db.query(ThermalObservation).delete()
        db.query(IndustrialFacility).delete()
        db.commit()

        batch_id = f"demo_seed_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.datetime.utcnow()

        # 1. Industrial Facilities
        facilities_data = [
            {
                "osm_id": "way/10101",
                "name": "Reliance Jamnagar Oil Refinery",
                "facility_type": "refinery",
                "operator": "Reliance Industries",
                "latitude": 22.3550,
                "longitude": 69.8650,
                "area_sqm": 450000.0,
                "raw_tags": {"landuse": "industrial", "man_made": "petroleum_refinery"}
            },
            {
                "osm_id": "way/10102",
                "name": "Trombay Thermal Power Station",
                "facility_type": "power_plant",
                "operator": "Tata Power",
                "latitude": 19.0020,
                "longitude": 72.8980,
                "area_sqm": 180000.0,
                "raw_tags": {"power": "plant", "plant:source": "coal"}
            },
            {
                "osm_id": "way/10103",
                "name": "Tata Steel Works Jamshedpur",
                "facility_type": "steel_works",
                "operator": "Tata Steel",
                "latitude": 22.7880,
                "longitude": 86.2020,
                "area_sqm": 320000.0,
                "raw_tags": {"industrial": "steel_works"}
            },
            {
                "osm_id": "way/10104",
                "name": "Vizag Petrochemical Complex",
                "facility_type": "chemical",
                "operator": "HPCL",
                "latitude": 17.6980,
                "longitude": 83.2450,
                "area_sqm": 210000.0,
                "raw_tags": {"man_made": "works", "industrial": "chemical"}
            },
            {
                "osm_id": "way/10105",
                "name": "Mangalore Refinery & Petrochemicals",
                "facility_type": "refinery",
                "operator": "MRPL / ONGC",
                "latitude": 12.9750,
                "longitude": 74.8350,
                "area_sqm": 290000.0,
                "raw_tags": {"landuse": "industrial", "man_made": "petroleum_refinery"}
            },
            {
                "osm_id": "way/10106",
                "name": "Mundra Ultra Mega Power Plant",
                "facility_type": "power_plant",
                "operator": "Adani Power",
                "latitude": 22.8250,
                "longitude": 69.5250,
                "area_sqm": 390000.0,
                "raw_tags": {"power": "plant", "plant:output:electricity": "4620MW"}
            }
        ]

        fac_objs = []
        for f in facilities_data:
            fac = IndustrialFacility(
                osm_id=f["osm_id"],
                name=f["name"],
                facility_type=f["facility_type"],
                operator=f["operator"],
                latitude=f["latitude"],
                longitude=f["longitude"],
                area_sqm=f["area_sqm"],
                raw_tags=json.dumps(f["raw_tags"]),
                ingestion_batch_id=batch_id,
                created_at=now
            )
            db.add(fac)
            fac_objs.append(fac)

        db.commit()

        # 2. Thermal Observations (Industrial flares, abnormal spikes, forest fires, agricultural burning)
        observations_data = [
            # Industrial Heat: Reliance Jamnagar Refinery (Normal Flare)
            {"lat": 22.3552, "lon": 69.8653, "frp": 38.5, "ti4": 332.1, "ti5": 296.4, "dn": "N", "date": "2026-08-26", "time": "2130", "sat": "N20"},
            {"lat": 22.3551, "lon": 69.8652, "frp": 42.0, "ti4": 335.0, "ti5": 297.0, "dn": "D", "date": "2026-08-25", "time": "0915", "sat": "SNPP"},
            
            # Abnormal Thermal Spike: Reliance Jamnagar (FRP = 165 MW vs 55 MW P95 baseline)
            {"lat": 22.3554, "lon": 69.8655, "frp": 165.0, "ti4": 367.0, "ti5": 302.0, "dn": "N", "date": "2026-08-26", "time": "2200", "sat": "N21"},

            # Industrial Heat: Trombay Power Station (Normal Operational Heat)
            {"lat": 19.0022, "lon": 72.8983, "frp": 62.0, "ti4": 341.0, "ti5": 298.0, "dn": "D", "date": "2026-08-26", "time": "0845", "sat": "SNPP"},

            # Abnormal Thermal Spike: Trombay Power Station (FRP = 195 MW vs 75 MW P95 baseline -> 2.6x Critical Anomaly)
            {"lat": 19.0025, "lon": 72.8986, "frp": 195.0, "ti4": 372.0, "ti5": 305.0, "dn": "N", "date": "2026-08-26", "time": "2115", "sat": "N20"},

            # Industrial Heat: Tata Steel Jamshedpur (Blast Furnace Heat)
            {"lat": 22.7882, "lon": 86.2023, "frp": 54.0, "ti4": 339.0, "ti5": 297.5, "dn": "N", "date": "2026-08-26", "time": "2045", "sat": "SNPP"},

            # Industrial Heat: Vizag Petrochemical Complex (Normal Chemical Flare)
            {"lat": 17.6983, "lon": 83.2452, "frp": 28.0, "ti4": 328.0, "ti5": 295.0, "dn": "D", "date": "2026-08-26", "time": "0930", "sat": "N20"},

            # Abnormal Thermal Spike: Mangalore Refinery (FRP = 140 MW vs 55 MW P95 baseline -> 2.5x High Spike)
            {"lat": 12.9753, "lon": 74.8354, "frp": 140.0, "ti4": 358.0, "ti5": 300.0, "dn": "N", "date": "2026-08-26", "time": "2215", "sat": "N21"},

            # Industrial Heat: Mundra Ultra Power Plant
            {"lat": 22.8253, "lon": 69.5253, "frp": 78.0, "ti4": 346.0, "ti5": 299.0, "dn": "D", "date": "2026-08-26", "time": "0830", "sat": "SNPP"},

            # Natural / Forest Fire: Western Ghats Reserve Forest (Isolated, FRP = 58 MW, 18km from facilities)
            {"lat": 13.5000, "lon": 75.2500, "frp": 58.0, "ti4": 342.0, "ti5": 296.0, "dn": "N", "date": "2026-08-26", "time": "2100", "sat": "N20"},

            # Natural / Forest Fire: Simlipal Forest Reserve (Isolated, FRP = 82 MW, 45km from facilities)
            {"lat": 21.6500, "lon": 86.3000, "frp": 82.0, "ti4": 351.0, "ti5": 298.0, "dn": "N", "date": "2026-08-26", "time": "2145", "sat": "N21"},

            # Agricultural Crop Burning: Punjab Agricultural Fields (Daytime, FRP = 14 MW, 25km from facilities)
            {"lat": 30.9000, "lon": 75.8500, "frp": 14.0, "ti4": 322.0, "ti5": 294.0, "dn": "D", "date": "2026-08-26", "time": "0900", "sat": "SNPP"},

            # Agricultural Crop Burning: Haryana Open Fields (Daytime, FRP = 11 MW, 30km from facilities)
            {"lat": 29.5000, "lon": 76.2000, "frp": 11.0, "ti4": 319.0, "ti5": 293.0, "dn": "D", "date": "2026-08-26", "time": "0915", "sat": "N20"}
        ]

        obs_objs = []
        for o in observations_data:
            obs = ThermalObservation(
                latitude=o["lat"],
                longitude=o["lon"],
                bright_ti4=o["ti4"],
                bright_ti5=o["ti5"],
                scan=0.38,
                track=0.36,
                acq_date=o["date"],
                acq_time=o["time"],
                satellite=o["sat"],
                instrument="VIIRS",
                confidence="n",
                version="2.0-NRT",
                frp=o["frp"],
                daynight=o["dn"],
                observation_timestamp=now,
                ingestion_timestamp=now,
                source=f"VIIRS_{o['sat']}_NRT",
                ingestion_batch_id=batch_id
            )
            db.add(obs)
            obs_objs.append(obs)

        db.commit()
        print(f"[OK] Ingested {len(fac_objs)} Industrial Facilities & {len(obs_objs)} Satellite Thermal Observations.")

        # 3. Run Phase 3: Spatial Proximity Associations
        print("[+] Executing Phase 3 Spatial Proximity Association Pipeline...")
        assoc_service = AssociationService()
        assoc_res = assoc_service.run_association_pipeline(db=db, max_distance_meters=3000.0, recalculate_all=True)
        print(f"    Created {assoc_res.associations_created} Spatial Proximity Vectors.")

        # 4. Run Phase 4: Candidate Source Classifications
        print("[+] Executing Phase 4 Candidate Source Classifier Engine...")
        clf_service = ClassificationService()
        clf_res = clf_service.run_classification_pipeline(db=db, recalculate_all=True)
        print(f"    Classified {clf_res.classifications_created} Observations into Candidate Categories.")

        # 5. Run Phase 5: Historical Facility Behavior Engine
        print("[+] Executing Phase 5 Historical Facility Behavior Engine...")
        hist_service = HistoryService()
        hist_res = hist_service.run_historical_aggregation_pipeline(db=db, recalculate_all=True)
        print(f"    Profiled {hist_res.facilities_profiled} Facility Historical Thermal Baselines.")

        # 6. Run Phase 6: Facility Normal Baseline Engine
        print("[+] Executing Phase 6 Facility Normal Baseline Engine...")
        base_service = BaselineService()
        base_res = base_service.generate_facility_baselines(db=db, recalculate_all=True)
        print(f"    Generated {base_res.baselines_generated} Normal Operating Envelopes (P50, P95, P99).")

        # 7. Run Phase 7: Abnormal Thermal Event Detection Engine
        print("[+] Executing Phase 7 Abnormal Thermal Event Detection Engine (FRP > P95)...")
        anom_service = AnomalyService()
        anom_res = anom_service.detect_abnormal_events(db=db, recalculate_all=True)
        print(f"    Detected {anom_res.anomalies_detected} Abnormal Thermal Spike Candidates.")

        # 8. Run Phase 8: Multi-Modal Satellite Verification & Risk Scoring Pipeline
        print("[+] Executing Phase 8 Multi-Modal Risk Scoring & Verification Pipeline...")
        risk_service = RiskService()
        risk_res = risk_service.evaluate_risk_scores(db=db, recalculate_all=True)
        print(f"    Evaluated {risk_res.total_evaluated} Multi-Modal Risk Scores.")

        print("\n[SUCCESS] ALL 8 PHASES FULLY SEEDED & POPULATED SUCCESSFULLY!")

    except Exception as exc:
        print(f"[ERROR] Database Seeding Failed: {exc}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
