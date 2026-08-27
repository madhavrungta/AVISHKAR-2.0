"""Shared API dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request, status


def require_database(request: Request) -> None:
    """Reject data operations gracefully while PostGIS is offline."""

    if not getattr(request.app.state, "database_ready", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostGIS is unavailable. Start the database and retry.",
        )

