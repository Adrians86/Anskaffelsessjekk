"""Invoice header and lines; raw source is always retained."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class InvoiceSource(str, Enum):
    EHF = "EHF"
    PDF = "PDF"
    MANUAL = "MANUAL"


class Invoice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    order_id: int | None = Field(default=None, foreign_key="order.id", index=True)
    invoice_number: str = Field(index=True)
    invoice_date: date
    total_ex_vat: Decimal
    currency: str = "NOK"
    source: InvoiceSource = InvoiceSource.MANUAL
    raw_source_path: str | None = None           # original EHF XML / PDF, retained
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InvoiceLine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)
    item_ref: str | None = Field(default=None, index=True)
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
