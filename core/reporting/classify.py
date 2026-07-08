"""Classification: findings -> verdict. A recommendation, never a decision.

Mapping (hard principle from ARCHITECTURE.md):
- any DEVIATION finding  -> AVVIK
- else any WARN finding  -> TIL_VURDERING
- else                   -> SAMSVAR
Every check is persisted as an append-only CheckResult with its rule hits.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal

from sqlmodel import Session

from core.matching import commitments, three_way
from core.matching.findings import Finding, Severity
from core.models import AuditLog, CheckResult, Invoice, Verdict

RULES_VERSION = "core-rules@0.1.0"


@dataclass(frozen=True)
class InvoiceCheck:
    invoice_id: int
    verdict: Verdict
    findings: list[Finding]
    verdi_funnet: Decimal          # sum of deviation amounts (gap G2)


def _verdict(findings: list[Finding]) -> Verdict:
    severities = {f.severity for f in findings}
    if Severity.DEVIATION in severities:
        return Verdict.AVVIK
    if Severity.WARN in severities:
        return Verdict.TIL_VURDERING
    return Verdict.SAMSVAR


def check_invoice(session: Session, invoice: Invoice, actor: str = "system") -> InvoiceCheck:
    findings = three_way.check(session, invoice) + commitments.check(session, invoice)
    verdict = _verdict(findings)
    verdi = sum((f.deviation_amount for f in findings), Decimal("0"))

    session.add(CheckResult(
        invoice_id=invoice.id, order_id=invoice.order_id, verdict=verdict,
        rule_hits_json=json.dumps([asdict(f) for f in findings], default=str),
        deviation_amount=verdi, rules_version=RULES_VERSION,
    ))
    session.add(AuditLog(
        actor=actor, action="invoice.checked", entity=f"invoice:{invoice.id}",
        detail=f"verdict={verdict.value}, findings={len(findings)}",
        rules_version=RULES_VERSION,
    ))
    session.commit()
    return InvoiceCheck(invoice_id=invoice.id, verdict=verdict,
                        findings=findings, verdi_funnet=verdi)
