import sys
import os
import argparse
import logging

# Add parent directory to sys.path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database import SessionLocal, init_db
from app.services.firms_service import FIRMSDataService, FIRMSIngestionError

logger = logging.getLogger("firms_cli")

def main():
    parser = argparse.ArgumentParser(
        description="SIH 26162 CLI Tool - Thermal anomaly pipeline (FIRMS → risk)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo seed (all 8 phases, no live FIRMS key required)
    subparsers.add_parser(
        "seed",
        help="Load Indian industrial-hub demo data and run all 8 pipeline phases"
    )

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest-firms", help="Ingest thermal observations from NASA FIRMS API")
    ingest_parser.add_argument("--source", type=str, default=settings.FIRMS_SOURCE, help="FIRMS Source (e.g. VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT)")
    ingest_parser.add_argument("--area", type=str, default=settings.FIRMS_AREA, help="Bounding box west,south,east,north or 'world'")
    ingest_parser.add_argument("--days", type=int, default=settings.FIRMS_DAYS, help="Number of days range (1 to 5)")
    ingest_parser.add_argument("--date", type=str, default=None, help="Optional start date YYYY-MM-DD")

    # OSM Ingest command
    osm_parser = subparsers.add_parser("ingest-osm", help="Ingest industrial facilities from OpenStreetMap Overpass API")
    osm_parser.add_argument("--area", type=str, default=settings.FIRMS_AREA, help="Bounding box 'west,south,east,north'")

    # Association command
    assoc_parser = subparsers.add_parser("run-associations", help="Run spatial matching job between thermal points and facilities")
    assoc_parser.add_argument("--max-distance", type=float, default=3000.0, help="Maximum radius threshold in meters")
    assoc_parser.add_argument("--recalculate", action="store_true", help="Recalculate existing associations")

    # Classification command
    clf_parser = subparsers.add_parser("run-classification", help="Run ML candidate source classification engine")
    clf_parser.add_argument("--recalculate", action="store_true", help="Recalculate existing classifications")

    # History aggregation command
    hist_parser = subparsers.add_parser("run-history", help="Run facility historical thermal baseline aggregation")
    hist_parser.add_argument("--recalculate", action="store_true", help="Recalculate all facility historical profiles")

    # Baseline generation command
    base_parser = subparsers.add_parser("generate-baselines", help="Generate facility normal thermal baseline operating bounds")
    base_parser.add_argument("--recalculate", action="store_true", help="Recalculate all facility normal baselines")

    # Anomaly detection command
    anom_parser = subparsers.add_parser("detect-anomalies", help="Run abnormal thermal event detection pipeline over associated observations")
    anom_parser.add_argument("--recalculate", action="store_true", help="Recalculate all abnormal thermal events")

    # Risk evaluation command
    risk_parser = subparsers.add_parser("evaluate-risk", help="Evaluate 4-factor multi-criteria risk scores (0-100) and optical verification confidence")
    risk_parser.add_argument("--recalculate", action="store_true", help="Recalculate all multi-modal risk scores")

    # Status command
    subparsers.add_parser("status", help="Check database and FIRMS API configuration status")

    args = parser.parse_args()

    if not args.command or args.command == "status":
        print("\n=======================================================")
        print("  SIH 26162 - Thermal Pipeline CLI Status")
        print("=======================================================")
        status = settings.get_firms_key_safety_status()
        print(f"API Key Status : {status['message']}")
        print(f"Default Source : {settings.FIRMS_SOURCE}")
        print(f"Default Area   : {settings.FIRMS_AREA}")
        print(f"Database URL   : {settings.DATABASE_URL}")
        print("Demo seed      : python -m app.cli seed")
        print("=======================================================\n")
        return

    if args.command == "seed":
        from app.seed import seed_database
        seed_database()
        return

    if args.command == "ingest-osm":
        print(f"\n🏭 Initiating OpenStreetMap Industrial Facility Ingestion (Area: {args.area})...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.osm_service import OSMDataService, OSMIngestionError
            service = OSMDataService()
            response = service.ingest_osm_facilities(db=db, bbox_str=args.area)
            print("\n✅ OSM Ingestion Completed Successfully!")
            print(f"  Batch ID             : {response.batch_id}")
            print(f"  Facilities Ingested  : {response.facilities_ingested}")
            print(f"  Raw JSON File        : {response.raw_file_path}")
            print(f"  Category Breakdown   : {response.types_summary}\n")
        except Exception as exc:
            print(f"\n❌ OSM Ingestion Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "evaluate-risk":
        print(f"\n🎯 Evaluating 4-Factor Multi-Criteria Risk Scores (0-100)...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.risk_service import RiskService
            service = RiskService()
            response = service.evaluate_risk_scores(db=db, recalculate_all=args.recalculate)
            print("\n✅ Multi-Modal Risk Evaluation Completed Successfully!")
            print(f"  Observations Evaluated  : {response.total_evaluated}")
            print(f"  Critical Verified Risk  : {response.critical_verified}")
            print(f"  High Risk (61-85)       : {response.high_risk}")
            print(f"  Medium Risk (31-60)     : {response.medium_risk}")
            print(f"  Low Risk (0-30)         : {response.low_risk}\n")
        except Exception as exc:
            print(f"\n❌ Multi-Modal Risk Evaluation Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "detect-anomalies":
        print(f"\n🚨 Running Abnormal Thermal Event Detection Engine (FRP > P95)...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.anomaly_service import AnomalyService
            service = AnomalyService()
            response = service.detect_abnormal_events(db=db, recalculate_all=args.recalculate)
            print("\n✅ Anomaly Detection Pipeline Completed Successfully!")
            print(f"  Observations Evaluated : {response.total_evaluated}")
            print(f"  Anomalies Flagged      : {response.anomalies_detected}")
            print(f"  Moderate Spikes (1-1.5x): {response.moderate_spikes}")
            print(f"  High Spikes (1.5-2.5x) : {response.high_spikes}")
            print(f"  Critical Anomalies (>2.5x): {response.critical_anomalies}\n")
        except Exception as exc:
            print(f"\n❌ Anomaly Detection Pipeline Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "generate-baselines":
        print(f"\n📏 Generating Facility Normal Operating Thermal Baselines (P50, P95, P99 bounds)...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.baseline_service import BaselineService
            service = BaselineService()
            response = service.generate_facility_baselines(db=db, recalculate_all=args.recalculate)
            print("\n✅ Baseline Generation Completed Successfully!")
            print(f"  Baselines Generated   : {response.baselines_generated}")
            print(f"  Established Baselines : {response.established_baselines}")
            print(f"  Preliminary Defaults  : {response.preliminary_defaults}\n")
        except Exception as exc:
            print(f"\n❌ Baseline Generation Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "run-history":
        print(f"\n📊 Running Facility Historical Baseline Aggregation Engine...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.history_service import HistoryService
            service = HistoryService()
            response = service.run_historical_aggregation_pipeline(db=db, recalculate_all=args.recalculate)
            print("\n✅ Historical Baseline Pipeline Completed Successfully!")
            print(f"  Facilities Profiled     : {response.facilities_profiled}")
            print(f"  Highly Persistent       : {response.highly_persistent}")
            print(f"  Moderately Active       : {response.moderately_active}")
            print(f"  Sporadic Activity       : {response.sporadic}")
            print(f"  No Historical Anomalies : {response.no_historical_anomalies}\n")
        except Exception as exc:
            print(f"\n❌ Historical Aggregation Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "run-classification":
        print(f"\n🧠 Running ML Candidate Source Classification Engine...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.classification_service import ClassificationService
            service = ClassificationService()
            response = service.run_classification_pipeline(db=db, recalculate_all=args.recalculate)
            print("\n✅ Classification Pipeline Completed Successfully!")
            print(f"  Total Processed        : {response.total_processed}")
            print(f"  Classifications Saved  : {response.classifications_created}")
            print(f"  Industrial Candidates  : {response.industrial_candidates}")
            print(f"  Natural Forest Fires   : {response.natural_forest_candidates}")
            print(f"  Agricultural Fires     : {response.agricultural_candidates}")
            print(f"  Other / Unknown        : {response.other_unknown}\n")
        except Exception as exc:
            print(f"\n❌ Classification Pipeline Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "run-associations":
        print(f"\n🔗 Running Thermal Anomaly -> Industrial Facility Spatial Association Engine (Max Radius: {args.max_distance}m)...")
        init_db()
        db = SessionLocal()
        try:
            from app.services.association_service import AssociationService
            service = AssociationService()
            response = service.run_association_pipeline(
                db=db,
                max_distance_meters=args.max_distance,
                recalculate_all=args.recalculate
            )
            print("\n✅ Association Pipeline Completed Successfully!")
            print(f"  Total Processed    : {response.total_observations_processed}")
            print(f"  Associations Saved : {response.associations_created}")
            print(f"  Direct Matches     : {response.direct_matches}")
            print(f"  Proximate Matches  : {response.proximate_matches}")
            print(f"  Vicinity Matches   : {response.vicinity_matches}")
            print(f"  Unassociated       : {response.unassociated}\n")
        except Exception as exc:
            print(f"\n❌ Association Pipeline Failed: {exc}\n")
            sys.exit(1)
        finally:
            db.close()
        return

    if args.command == "ingest-firms":
        if not settings.is_firms_key_configured:
            print("\n❌ ERROR: FIRMS_MAP_KEY is not configured. Add it to backend/.env.\n")
            sys.exit(1)

        print(f"\n🚀 Initiating NASA FIRMS Ingestion (Source: {args.source}, Area: {args.area}, Days: {args.days})...")
        init_db()
        db = SessionLocal()
        try:
            service = FIRMSDataService()
            response = service.ingest_firms_data(
                db=db,
                source=args.source,
                area=args.area,
                days=args.days,
                date=args.date
            )
            print("\n✅ Ingestion Completed Successfully!")
            print(f"  Batch ID         : {response.batch_id}")
            print(f"  Records Ingested : {response.records_ingested}")
            print(f"  Raw CSV File     : {response.raw_file_path}")
            print(f"  Total Valid      : {response.validation_report.valid_records}")
            print(f"  Total Invalid    : {response.validation_report.invalid_records}")
            print(f"  Total Duplicates : {response.validation_report.duplicates}\n")
        except FIRMSIngestionError as exc:
            print(f"\n❌ Ingestion Failed: {exc}\n")
            sys.exit(1)
        except Exception as exc:
            print(f"\n❌ Unexpected Failure: {exc}\n")
            sys.exit(1)
        finally:
            db.close()

if __name__ == "__main__":
    main()
