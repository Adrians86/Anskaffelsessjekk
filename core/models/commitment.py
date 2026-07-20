"""Commitment — the core entity of Anskaffelsessjekk.

A commitment is any source of a commercial condition, formal or informal:
a contract clause, an e-mail agreement, a meeting note. Invoices are
verified against the full set of commitments, not only the contract.
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class SourceType(str, Enum):
    CONTRACT = "CONTRACT"
    EMAIL = "EMAIL"
    MEETING_NOTE = "MEETING_NOTE"
    OTHER = "OTHER"


class ConditionType(str, Enum):
    PRICE = "PRICE"
    DISCOUNT = "DISCOUNT"
    QUANTITY = "QUANTITY"
    DEADLINE = "DEADLINE"
    SCOPE = "SCOPE"
    RATE = "RATE"


class Formalization(str, Enum):
    FORMALIZED = "FORMALIZED"          # part of a signed contract / annex
    PENDING_ANNEX = "PENDING_ANNEX"    # agreed informally, annex in progress
    INFORMAL = "INFORMAL"              # e-mail / verbal only


class Commitment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    contract_id: int | None = Field(default=None, foreign_key="contract.id", index=True)

    source_type: SourceType
    source_ref: str                      # e.g. "e-mail 2026-06-12, J. Hansen"
    source_file: str | None = None       # path to attached evidence (.eml / .pdf)
    source_quote: str | None = None      # the excerpt the extraction rests on (shown in UI)
    gyldighet: str | None = None         # gyldighetsvurdering recorded at confirm time
                                         # (GYLDIG / KREVER_FORMALISERING / UGYLDIG); UI-level

    condition_type: ConditionType
    item_ref: str | None = Field(default=None, index=True)  # article no. / service category
    value: Decimal | None = None         # condition value (price, rate, %)
    unit: str | None = None              # NOK, NOK/h, %, pcs

    valid_from: date
    valid_to: date | None = None

    formalization: Formalization = Formalization.FORMALIZED
    extracted_by: str = "manual"         # "manual" | "llm:<model>"
    confirmed_by_user: bool = False      # human-in-the-loop gate: unconfirmed
                                         # LLM extractions never participate in control
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def is_active_on(self, on: date) -> bool:
        """A commitment participates in control only when confirmed and valid."""
        if not self.confirmed_by_user and self.extracted_by != "manual":
            return False
        if on < self.valid_from:
            return False
        return self.valid_to is None or on <= self.valid_to
