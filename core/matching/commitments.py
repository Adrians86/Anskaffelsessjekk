"""Commitments check: invoice lines vs the full set of agreed conditions.

Resolution order for the effective agreed price of an item:
1. the most recent ACTIVE commitment (contract clause, confirmed e-mail, ...),
2. otherwise the contract line,
3. otherwise there is no agreed basis at all -> finding.

This is where the product differs from plain invoice automation: an e-mail
agreement, once confirmed by a human, is part of the control basis.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from core.matching.findings import Code, Finding, Severity
from core.models import (
    Commitment,
    ConditionType,
    ContractLine,
    Formalization,
    Invoice,
    InvoiceLine,
)

_PRICE_TOLERANCE = Decimal("0.01")


def _active_price_commitment(
    session: Session, invoice: Invoice, item_ref: str, on: date
) -> Commitment | None:
    stmt = (
        select(Commitment)
        .where(Commitment.supplier_id == invoice.supplier_id)
        .where(Commitment.item_ref == item_ref)
        .where(Commitment.condition_type.in_([ConditionType.PRICE, ConditionType.RATE]))
    )
    candidates = [c for c in session.exec(stmt).all() if c.is_active_on(on)]
    return max(candidates, key=lambda c: c.valid_from) if candidates else None


def _contract_line(session: Session, invoice: Invoice, item_ref: str) -> ContractLine | None:
    if invoice.order_id is None:
        return None
    from core.models import Order  # local import to avoid cycles
    order = session.get(Order, invoice.order_id)
    if order is None or order.contract_id is None:
        return None
    return session.exec(
        select(ContractLine)
        .where(ContractLine.contract_id == order.contract_id)
        .where(ContractLine.item_ref == item_ref)
    ).first()


def check(session: Session, invoice: Invoice) -> list[Finding]:
    findings: list[Finding] = []
    # Foreign currency: price/amount comparisons are suspended (a raw EUR↔NOK difference is not a
    # deviation). The currency matcher flags it for manual rate assessment instead.
    if invoice.currency and invoice.currency.upper() != "NOK":
        return findings
    lines = session.exec(
        select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)
    ).all()

    for line in lines:
        if not line.item_ref:
            continue
        commitment = _active_price_commitment(session, invoice, line.item_ref, invoice.invoice_date)
        contract_line = _contract_line(session, invoice, line.item_ref)

        if commitment is not None:
            agreed = commitment.value
            basis = f"{commitment.source_type.value}: {commitment.source_ref}"
        elif contract_line is not None:
            agreed = contract_line.unit_price
            basis = f"Kontraktslinje {line.item_ref}"
        else:
            findings.append(Finding(
                code=Code.NO_AGREED_BASIS, severity=Severity.WARN,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=f"Ingen avtalt betingelse funnet for {line.item_ref}.",
                citation="Forpliktelsesregister: ingen treff",
                actual=str(line.unit_price),
            ))
            continue

        if line.unit_price > agreed + _PRICE_TOLERANCE:
            findings.append(Finding(
                code=Code.PRICE_ABOVE_AGREED, severity=Severity.DEVIATION,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=(f"Fakturert pris {line.unit_price} er høyere enn avtalt "
                         f"{agreed} for {line.item_ref}."),
                citation=basis,
                expected=str(agreed), actual=str(line.unit_price),
                deviation_amount=(line.unit_price - agreed) * line.quantity,
            ))
        elif (commitment is not None
              and commitment.formalization != Formalization.FORMALIZED):
            findings.append(Finding(
                code=Code.INFORMAL_BASIS, severity=Severity.WARN,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=(f"Prisen samsvarer med uformell avtale "
                         f"({commitment.source_ref}) — krever formalisering."),
                citation=basis,
                expected=str(agreed), actual=str(line.unit_price),
            ))

        if (contract_line is not None
                and contract_line.max_quantity is not None
                and line.quantity > contract_line.max_quantity):
            over = line.quantity - contract_line.max_quantity
            findings.append(Finding(
                code=Code.QTY_ABOVE_MAX, severity=Severity.DEVIATION,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=(f"Fakturert mengde {line.quantity} overstiger avtalt "
                         f"maks {contract_line.max_quantity} for {line.item_ref}."),
                citation=f"Kontraktslinje {line.item_ref} (maks {contract_line.max_quantity})",
                expected=str(contract_line.max_quantity), actual=str(line.quantity),
                deviation_amount=over * line.unit_price,
            ))
    return findings
