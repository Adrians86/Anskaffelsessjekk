"""Price-list verification — check an invoice's lines against the supplier's contract prisliste.

This is the Funksjon 3 verification path (basis #2). It is ADDITIVE: it does not touch the existing
three_way / commitments matchers, so the demo reconciliation (22 310 kr) is unchanged. The verdict
carries the WHY (which price, which agreed value, which article, which contract).

Pure core: no UI import.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlmodel import Session, select

from core.matching.findings import Code, Finding, Severity
from core.models import Contract, ContractLine, Invoice, InvoiceLine, Verdict

_PRICE_TOLERANCE = Decimal("0")


def resolve_contract(session: Session, invoice: Invoice) -> Contract | None:
    """Which contract this invoice is controlled against: the order's contract when linked,
    otherwise the supplier's active (non-deleted) contract with a price list. Reads only."""
    if invoice.order_id is not None:
        from core.models import Order
        order = session.get(Order, invoice.order_id)
        if order is not None and order.contract_id is not None:
            c = session.get(Contract, order.contract_id)
            if c is not None and not c.is_deleted:
                return c
    candidates = session.exec(
        select(Contract)
        .where(Contract.supplier_id == invoice.supplier_id)
        .where(Contract.is_deleted == False)  # noqa: E712
        .order_by(Contract.reference)
    ).all()
    # Prefer a contract that actually has price lines; then an «aktiv» one; else first.
    with_lines = [c for c in candidates
                  if session.exec(select(ContractLine)
                                  .where(ContractLine.contract_id == c.id)).first() is not None]
    pool = with_lines or list(candidates)
    for c in pool:
        if c.status == "aktiv":
            return c
    return pool[0] if pool else None


def check(session: Session, invoice: Invoice, contract: Contract | None) -> list[Finding]:
    """Findings from comparing invoice lines to the contract's price list. Foreign currency is
    left to the currency matcher (price comparisons suspended)."""
    findings: list[Finding] = []
    if invoice.currency and invoice.currency.upper() != "NOK":
        return findings
    lines = session.exec(
        select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)
    ).all()
    ref = contract.reference if contract else "ingen avtale"

    for line in lines:
        if not line.item_ref:
            continue
        cl = None
        if contract is not None:
            cl = session.exec(
                select(ContractLine)
                .where(ContractLine.contract_id == contract.id)
                .where(ContractLine.item_ref == line.item_ref)
            ).first()
        if cl is None:
            findings.append(Finding(
                code=Code.NO_AGREED_BASIS, severity=Severity.WARN,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=(f"Ingen prislinje for {line.item_ref} i avtale {ref} — "
                         "artikkelen står ikke i prislisten."),
                citation=f"Avtale {ref} (prisliste)",
                expected="(på prisliste)", actual=str(line.unit_price),
            ))
            continue

        agreed = cl.unit_price
        if line.unit_price > agreed + _PRICE_TOLERANCE:
            over = (line.unit_price - agreed) * line.quantity
            findings.append(Finding(
                code=Code.PRICE_ABOVE_AGREED, severity=Severity.DEVIATION,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=(f"Pris {line.unit_price} > avtalt {agreed} for {line.item_ref} "
                         f"(avtale {ref})."),
                citation=f"Prislinje {line.item_ref}, avtale {ref}",
                expected=str(agreed), actual=str(line.unit_price), deviation_amount=over,
            ))
        if (cl.max_quantity is not None and line.quantity > cl.max_quantity):
            over_qty = line.quantity - cl.max_quantity
            findings.append(Finding(
                code=Code.QTY_ABOVE_MAX, severity=Severity.DEVIATION,
                invoice_id=invoice.id, invoice_line_id=line.id,
                message=(f"Mengde {line.quantity} > maks {cl.max_quantity} for {line.item_ref} "
                         f"(avtale {ref})."),
                citation=f"Prislinje {line.item_ref} (maks {cl.max_quantity}), avtale {ref}",
                expected=str(cl.max_quantity), actual=str(line.quantity),
                deviation_amount=over_qty * line.unit_price,
            ))
    return findings


@dataclass(frozen=True)
class PriceListResult:
    invoice_id: int
    verdict: Verdict
    findings: list[Finding]
    contract: Contract | None
    verdi_funnet: Decimal
    n_price_lines: int


def verify(session: Session, invoice: Invoice) -> PriceListResult:
    """Resolve the controlling contract and verify the invoice against its price list. Read-only."""
    contract = resolve_contract(session, invoice)
    findings = check(session, invoice, contract)
    severities = {f.severity for f in findings}
    if Severity.DEVIATION in severities:
        verdict = Verdict.AVVIK
    elif Severity.WARN in severities:
        verdict = Verdict.TIL_VURDERING
    else:
        verdict = Verdict.SAMSVAR
    verdi = sum((f.deviation_amount for f in findings), Decimal("0"))
    n_lines = 0
    if contract is not None:
        n_lines = len(session.exec(
            select(ContractLine).where(ContractLine.contract_id == contract.id)).all())
    return PriceListResult(invoice_id=invoice.id, verdict=verdict, findings=findings,
                           contract=contract, verdi_funnet=verdi, n_price_lines=n_lines)
