"""Phase 1 API endpoints for thermal observation inspection and ingestion."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_database
from app.config import get_settings
from app.database import get_session
from app.models.thermal_observation import ThermalObservation
from app.schemas.firms import FirmsIngestionRequest, IngestionResult
from app.schemas.thermal_observation import (
    AnalyticsSummary,
    ThermalObservationDetail,
    ThermalObservationPage,
    ThermalObservationRead,
)
from app.services.firms_service import (
    FirmsApiError,
    FirmsConfigurationError,
    FirmsService,
)
from app.services.firms_validation import FirmsSchemaError
from app.services.thermal_observation_repository import get_summary, insert_observations


router = APIRouter()


@router.get(
    "/thermal-observations",
    response_model=ThermalObservationPage,
    dependencies=[Depends(require_database)],
)
def list_thermal_observations(
    limit: int = Query(default=500, ge=1, le=2_000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> ThermalObservationPage:
    """List stored thermal anomalies, newest first, without classification claims."""

    total = session.scalar(select(func.count(ThermalObservation.id))) or 0
    observations = session.scalars(
        select(ThermalObservation)
        .order_by(ThermalObservation.observation_timestamp.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return ThermalObservationPage(
        items=[ThermalObservationRead.model_validate(item) for item in observations],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get(
    "/thermal-observations/{observation_id}",
    response_model=ThermalObservationDetail,
    dependencies=[Depends(require_database)],
)
def get_thermal_observation(
    observation_id: UUID,
    session: Session = Depends(get_session),
) -> ThermalObservationDetail:
    """Return one stored thermal anomaly with all original FIRMS fields."""

    observation = session.get(ThermalObservation, observation_id)
    if observation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation was not found.")
    return ThermalObservationDetail.model_validate(observation)


@router.post(
    "/ingestion/firms",
    response_model=IngestionResult,
    status_code=status.HTTP_201_CREATED,
)
def ingest_firms(
    request: FirmsIngestionRequest,
    raw_request: Request,
    session: Session = Depends(get_session),
) -> IngestionResult:
    """Archive, validate, and persist official NASA FIRMS observations."""

    settings = get_settings()
    if not settings.has_firms_map_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FIRMS_MAP_KEY is not configured. Add it to backend/.env.",
        )
    require_database(raw_request)
    service = FirmsService(settings)
    try:
        prepared = service.prepare_ingestion(request)
        inserted_records = insert_observations(session, prepared.validation.observations)
        session.commit()
    except FirmsConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except (FirmsApiError, FirmsSchemaError) as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    return prepared.result.model_copy(update={"inserted_records": inserted_records})


@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummary,
    dependencies=[Depends(require_database)],
)
def analytics_summary(session: Session = Depends(get_session)) -> AnalyticsSummary:
    """Report stored-observation counts, not a count of confirmed incidents."""

    return get_summary(session)
