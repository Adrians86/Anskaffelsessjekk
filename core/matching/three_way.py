"""Three-way match: Order <-> Receipt (mottak) <-> Invoice."""
from __future__ import annotations

from sqlmodel import Session, select

from core.matching.findings import Code, Finding, Severity
from core.models import Invoice, Receipt


def check(session: Session, invoice: Invoice) -> list[Finding]:
    findings: list[Finding] = []
    if invoice.order_id is None:
        findings.append(Finding(
            code=Code.MISSING_ORDER, severity=Severity.WARN,
            invoice_id=invoice.id, invoice_line_id=None,
            message="Fakturaen er ikke knyttet til noen bestilling/avrop.",
            citation="Internkontroll: three-way match (bestilling-mottak-faktura)",
        ))
        return findings

    receipt = session.exec(
        select(Receipt).where(Receipt.order_id == invoice.order_id)
    ).first()
    if receipt is None:
        findings.append(Finding(
            code=Code.MISSING_RECEIPT, severity=Severity.WARN,
            invoice_id=invoice.id, invoice_line_id=None,
            message="Mottak er ikke bekreftet for tilhørende bestilling.",
            citation="Internkontroll: mottakskontroll før fakturagodkjenning",
        ))
    return findings
