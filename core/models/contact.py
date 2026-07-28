"""Contact person for a supplier — a real, editable sub-entity (full CRUD).

Part of "Leverandør A–Z" (the first function built as a tool, not a view). Belongs to core/
and imports nothing from any UI.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ContactPerson(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    name: str
    role: str | None = None          # e.g. "kundeansvarlig", "fakturakontakt"
    email: str | None = None
    phone: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
