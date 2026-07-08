"""Synthetic scenario 2: consultant hire (hours x rates vs rammeavtale).

Validated by the market: organizations dedicate full FTEs to following up
consultant framework agreements. ALL DATA IS SYNTHETIC.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlmodel import Session

from core.models import (
    Contract, ContractLine, ContractType, Invoice, InvoiceLine, InvoiceSource,
    Order, Receipt, Regime, Supplier,
)


def generate(session: Session) -> dict[str, Any]:
    sup = Supplier(org_number="987654321", name="Konsulenthuset Øst AS (SYNTETISK)")
    session.add(sup); session.commit(); session.refresh(sup)

    contract = Contract(
        supplier_id=sup.id, contract_type=ContractType.RAMMEAVTALE,
        reference="RA-2026-KONS", title="Rammeavtale konsulentinnleie (SYNTETISK)",
        total_value=Decimal("4800000"),
        valid_from=date(2026, 1, 1), valid_to=date(2027, 12, 31),
    )
    session.add(contract); session.commit(); session.refresh(contract)
    session.add(ContractLine(contract_id=contract.id, item_ref="KONS-SENIOR",
                             description="Seniorkonsulent", unit_price=Decimal("1450"),
                             unit="h"))
    session.add(ContractLine(contract_id=contract.id, item_ref="KONS-JUNIOR",
                             description="Juniorkonsulent", unit_price=Decimal("980"),
                             unit="h"))
    session.commit()

    manifest: list[dict[str, str]] = []

    def _order(ref: str, value: str) -> Order:
        o = Order(supplier_id=sup.id, contract_id=contract.id, reference=ref,
                  requested_by="bestiller.synt", estimated_value=Decimal(value),
                  regime=Regime.FOA, order_date=date(2026, 7, 1))
        session.add(o); session.commit(); session.refresh(o)
        session.add(Receipt(order_id=o.id, confirmed_by="prosjektleder",
                            confirmed_at=datetime(2026, 7, 31, tzinfo=timezone.utc)))
        session.commit()
        return o

    def _invoice(number: str, order: Order | None,
                 lines: list[tuple[str, str, str]]) -> None:
        total = sum(Decimal(q) * Decimal(p) for _, q, p in lines)
        inv = Invoice(supplier_id=sup.id, order_id=order.id if order else None,
                      invoice_number=number, invoice_date=date(2026, 8, 1),
                      total_ex_vat=total, source=InvoiceSource.PDF)
        session.add(inv); session.commit(); session.refresh(inv)
        for ref, qty, price in lines:
            session.add(InvoiceLine(invoice_id=inv.id, item_ref=ref,
                                    description=ref, quantity=Decimal(qty),
                                    unit_price=Decimal(price),
                                    line_total=Decimal(qty) * Decimal(price)))
        session.commit()

    # K-2001: clean — 40h senior at the agreed 1450/h. Expected: no findings.
    _invoice("K-2001", _order("AVROP-K1", "58000"), [("KONS-SENIOR", "40", "1450")])

    # K-2002: rate 1600/h vs agreed 1450/h. Expected: PRICE_ABOVE_AGREED.
    # 150 NOK/h x 80h = 12 000 NOK verdi funnet — the most common and most
    # expensive deviation type in service procurement.
    _invoice("K-2002", _order("AVROP-K2", "128000"), [("KONS-SENIOR", "80", "1600")])
    manifest.append({"invoice_number": "K-2002", "code": "PRICE_ABOVE_AGREED"})

    # K-2003: invoice with no order reference at all. Expected: MISSING_ORDER
    # and NO_AGREED_BASIS (no contract resolvable without the order link).
    _invoice("K-2003", None, [("KONS-JUNIOR", "20", "980")])
    manifest.append({"invoice_number": "K-2003", "code": "MISSING_ORDER"})
    manifest.append({"invoice_number": "K-2003", "code": "NO_AGREED_BASIS"})

    return {"scenario": "konsulent", "expected_findings": manifest}
