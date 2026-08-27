"""CLI commands for reproducible Phase 1 FIRMS ingestion."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from app.config import get_settings
from app.database import dispose_database, initialize_database, get_session_factory
from app.logging_config import configure_logging
from app.schemas.firms import FirmsIngestionRequest
from app.services.firms_service import FirmsApiError, FirmsConfigurationError, FirmsService
from app.services.firms_validation import FirmsSchemaError
from app.services.thermal_observation_repository import insert_observations


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD.") from error


def build_parser() -> argparse.ArgumentParser:
    """Build the small explicit CLI surface for Phase 1."""

    parser = argparse.ArgumentParser(description="Ingest official NASA FIRMS thermal anomalies.")
    commands = parser.add_subparsers(dest="command", required=True)
    ingestion = commands.add_parser("firms-ingest", help="Fetch, archive, validate, and store FIRMS CSV.")
    settings = get_settings()
    ingestion.add_argument("--source", default=settings.firms_source)
    ingestion.add_argument("--area", default=settings.firms_area)
    ingestion.add_argument("--days", default=settings.firms_days, type=int)
    ingestion.add_argument("--start-date", type=_parse_date)
    return parser


def run_firms_ingest(args: argparse.Namespace) -> int:
    """Run an ingestion after ensuring that PostGIS is available."""

    settings = get_settings()
    request = FirmsIngestionRequest(
        source=args.source,
        area=args.area,
        days=args.days,
        start_date=args.start_date,
    )
    if not settings.has_firms_map_key:
        raise FirmsConfigurationError("FIRMS_MAP_KEY is not configured. Add it to backend/.env.")
    initialize_database()
    try:
        prepared = FirmsService(settings).prepare_ingestion(request)
        with get_session_factory()() as session:
            inserted_records = insert_observations(session, prepared.validation.observations)
            session.commit()
        outcome = prepared.result.model_copy(update={"inserted_records": inserted_records})
        print(outcome.model_dump_json(indent=2))
        return 0
    finally:
        dispose_database()


def main() -> int:
    """Entrypoint for `python -m app.cli`."""

    settings = get_settings()
    configure_logging(settings.log_level)
    args = build_parser().parse_args()
    try:
        if args.command == "firms-ingest":
            return run_firms_ingest(args)
    except FirmsConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    except (FirmsApiError, FirmsSchemaError) as error:
        print(f"FIRMS ingestion failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Ingestion could not complete: {error}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
