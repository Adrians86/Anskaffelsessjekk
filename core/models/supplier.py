"""Supplier registry entry."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Supplier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    org_number: str = Field(index=True, unique=True)   # Brønnøysund org.nr
    name: str
    categories: str | None = None       # comma-separated service categories / qualifications
    iso_certified: bool = False
    security_cleared: bool = False      # relevant for the forsvar profile
    notes: str | None = None            # free-text saksbehandler notes (editable)
    is_deleted: bool = Field(default=False, index=True)   # soft delete — row + trail kept
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
