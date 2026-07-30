"""Human decision on a controlled invoice — the system recommends, the human decides (hard rule #3).

Append-only: each decision is a new row; the latest by created_at is the current one. The row itself
plus the AuditLog give full traceability (who, when, why).
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

# Decision values.
DECISION_GODKJENT = "godkjent"    # approve for payment
DECISION_AVVIST = "avvist"        # reject
DECISION_VENT = "vent"            # hold / needs more info
INVOICE_DECISIONS = (DECISION_GODKJENT, DECISION_AVVIST, DECISION_VENT)


class InvoiceDecision(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)
    decision: str                       # godkjent | avvist | vent
    reason: str | None = None
    actor: str = "demo-bruker"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
