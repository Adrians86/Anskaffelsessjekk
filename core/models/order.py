"""Requisition / order / avrop on a rammeavtale."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class Regime(str, Enum):
    """Legal regime — the FIRST branch of every assessment, before any amounts."""
    FOA = "FOA"          # classic: anskaffelsesloven + forskrift
    FOSA = "FOSA"        # defence and security procurement
    ART123 = "ART123"    # EEA art. 123 exemption -> RAF Del III documentation duty


class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    contract_id: int | None = Field(default=None, foreign_key="contract.id", index=True)
    reference: str = Field(index=True)
    requested_by: str                            # bestiller (gap G5: requester field)
    estimated_value: Decimal                     # NOK, ex. VAT
    regime: Regime = Regime.FOA
    order_date: date
    regime_assessment_id: int | None = None      # CheckResult id of terskelsjekk at order time
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
