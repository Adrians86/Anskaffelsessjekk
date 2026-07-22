"""Findings — the atomic unit of every check.

A finding is one observed fact about an invoice, with severity and citation.
The verdict of an invoice is derived from its findings, never stated directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Severity(str, Enum):
    INFO = "INFO"            # noted, no action needed
    WARN = "WARN"            # requires human review -> TIL_VURDERING
    DEVIATION = "DEVIATION"  # breach of an agreed condition -> AVVIK


class Code(str, Enum):
    PRICE_ABOVE_AGREED = "PRICE_ABOVE_AGREED"    # unit price above contract/commitment
    QTY_ABOVE_MAX = "QTY_ABOVE_MAX"              # quantity above agreed ceiling
    NO_AGREED_BASIS = "NO_AGREED_BASIS"          # line item not found in any agreement
    INFORMAL_BASIS = "INFORMAL_BASIS"            # price matches an e-mail agreement
                                                 # pending formalization (demo scene!)
    MISSING_ORDER = "MISSING_ORDER"              # invoice not linked to any order
    MISSING_RECEIPT = "MISSING_RECEIPT"          # order has no confirmed mottak
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"      # invoice currency != NOK: price checks suspended,
                                                 # rate is a manual decision (detect + flag only)


@dataclass(frozen=True)
class Finding:
    code: Code
    severity: Severity
    invoice_id: int
    invoice_line_id: int | None
    message: str                       # human-readable, Norwegian (user-facing)
    citation: str                      # the agreement/rule this finding rests on
    expected: str | None = None
    actual: str | None = None
    deviation_amount: Decimal = Decimal("0")   # contributes to 'verdi funnet'
