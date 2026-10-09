"""Small shared helpers for API and persistence services."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


def model_data(value: BaseModel) -> dict[str, Any]:
    """Convert a Pydantic model to a persistence-friendly Python mapping."""
    return value.model_dump(mode="python")
