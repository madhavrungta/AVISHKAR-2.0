"""SQLAlchemy and PostGIS database lifecycle helpers."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for database models."""


@lru_cache
def get_engine() -> Engine:
    """Create a lazy SQLAlchemy engine; this function does not connect yet."""

    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory associated with the configured engine."""

    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields one database session per request."""

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def initialize_database() -> None:
    """Enable PostGIS and create the small Phase 1 schema if it is absent."""

    # Import ensures SQLAlchemy metadata includes the model before create_all.
    from app.models.thermal_observation import ThermalObservation  # noqa: F401

    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        Base.metadata.create_all(connection)


def dispose_database() -> None:
    """Dispose the connection pool during application shutdown."""

    get_engine().dispose()
