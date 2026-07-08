"""Append-only audit trail + verdicts. Internkontroll / AI Act requirement:
who, when, what, on which rules version. Rows are never updated or deleted."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class Verdict(str, Enum):
    SAMSVAR = "SAMSVAR"
    TIL_VURDERING = "TIL_VURDERING"
    AVVIK = "AVVIK"


class CheckResult(SQLModel, table=True):
    """Verdict per invoice (or per assessment). A recommendation, never a decision."""
    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int | None = Field(default=None, foreign_key="invoice.id", index=True)
    order_id: int | None = Field(default=None, foreign_key="order.id", index=True)
    verdict: Verdict
    rule_hits_json: str = "[]"                   # serialized RuleHit list (explainability)
    deviation_amount: Decimal = Decimal("0")     # sum -> 'verdi funnet' (gap G2)
    rules_version: str                           # e.g. "thresholds_2026@528bbae"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor: str                                    # username or "system"
    action: str                                   # e.g. "invoice.checked", "commitment.confirmed"
    entity: str                                   # e.g. "invoice:42"
    detail: str | None = None
    rules_version: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
