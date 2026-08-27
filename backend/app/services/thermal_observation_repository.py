"""Database persistence and reads for Phase 1 observations."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from geoalchemy2.elements import WKTElement

from app.models.thermal_observation import ThermalObservation
from app.schemas.firms import NormalizedObservation
from app.schemas.thermal_observation import AnalyticsSummary


def insert_observations(session: Session, observations: list[NormalizedObservation]) -> int:
    """Insert distinct records while safely ignoring rows already in PostGIS."""

    if not observations:
        return 0
    values = []
    for observation in observations:
        data = observation.model_dump()
        data["geometry"] = WKTElement(
            f"POINT({observation.longitude} {observation.latitude})", srid=4326
        )
        values.append(data)

    statement = (
        insert(ThermalObservation)
        .values(values)
        .on_conflict_do_nothing(index_elements=["observation_key"])
        .returning(ThermalObservation.id)
    )
    inserted = len(session.execute(statement).scalars().all())
    session.flush()
    return inserted


def get_summary(session: Session) -> AnalyticsSummary:
    """Return compact storage metadata without implying event meaning."""

    total, earliest, latest = session.execute(
        select(
            func.count(ThermalObservation.id),
            func.min(ThermalObservation.observation_timestamp),
            func.max(ThermalObservation.observation_timestamp),
        )
    ).one()
    source_rows = session.execute(
        select(ThermalObservation.source, func.count(ThermalObservation.id)).group_by(
            ThermalObservation.source
        )
    ).all()
    return AnalyticsSummary(
        total_observations=int(total),
        source_counts={source: int(count) for source, count in source_rows},
        earliest_observation=earliest,
        latest_observation=latest,
    )

