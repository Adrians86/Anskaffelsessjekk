"""Supplier registry entry."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Supplier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    org_number: str = Field(index=True, unique=True)   # Brønnøysund org.nr
    name: str
    categories: str | None = None       # comma-separated categories (what the supplier delivers)
    iso_certified: bool = False
    security_cleared: bool = False      # relevant for the forsvar profile
    notes: str | None = None            # free-text saksbehandler notes (editable)
    # v2 firmakort fields (all editable in «Rediger firmadata»).
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str = "Aktiv"               # Aktiv | Inaktiv | Sperret
    cooperation_rating: str | None = None   # own free-text cooperation assessment (K7)
    is_deleted: bool = Field(default=False, index=True)   # soft delete — row + trail kept
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
