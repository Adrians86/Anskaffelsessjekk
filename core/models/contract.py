"""Contracts (rammeavtale / enkeltkjøp) and their lines."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class ContractType(str, Enum):
    RAMMEAVTALE = "RAMMEAVTALE"
    ENKELTKJOP = "ENKELTKJOP"


class Contract(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    contract_type: ContractType = ContractType.RAMMEAVTALE
    reference: str = Field(index=True)          # internal contract reference
    title: str
    total_value: Decimal | None = None          # estimated total value (NOK, ex. VAT)
    valid_from: date
    valid_to: date | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContractLine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    contract_id: int = Field(foreign_key="contract.id", index=True)
    item_ref: str = Field(index=True)           # article number / service category
    description: str
    unit_price: Decimal                         # agreed price or hourly rate (NOK, ex. VAT)
    unit: str = "pcs"                           # pcs, h, kg ...
    max_quantity: Decimal | None = None         # ceiling per avrop / period, if agreed
