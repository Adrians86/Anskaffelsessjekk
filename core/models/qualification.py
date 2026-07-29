"""Qualification / certification a supplier holds — editable (full CRUD).

Part of "Leverandør v2". A qualification is a name plus an OPTIONAL «valid_to» date: without a date
it is simply a held qualification (a check); with a date, an expired one is shown in red in the UI.
Belongs to core/ and imports nothing from any UI.
"""
from __future__ import annotations

from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class Qualification(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    name: str
    valid_to: date | None = None            # None = no expiry tracked (just a check)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def is_expired(self, on: date | None = None) -> bool:
        """True only when a validity date is set AND it is in the past."""
        if self.valid_to is None:
            return False
        return self.valid_to < (on or date.today())
