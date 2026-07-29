"""Service / product a supplier delivers — an editable catalog entry (full CRUD).

Part of "Leverandør v2". Belongs to core/ and imports nothing from any UI.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class SupplierService(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    name: str
    description: str | None = None
    unit: str | None = None                 # e.g. "stk", "time", "måned"
    unit_price: Decimal | None = None       # optional indicative price (NOK)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
