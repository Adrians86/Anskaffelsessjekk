"""Synthetic scenario 1: spare parts / vedlikehold.

Generates the full chain with deliberately injected deviations and returns
a manifest — the ground truth for end-to-end tests (precision/recall).
ALL DATA IS SYNTHETIC.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlmodel import Session

from core.models import (
    Commitment, ConditionType, Contract, ContractLine, ContractType,
    Formalization, Invoice, InvoiceLine, InvoiceSource, Order, Receipt,
    Regime, SourceType, Supplier,
)


def generate(session: Session) -> dict[str, Any]:
    sup = Supplier(org_number="998877665", name="Hydraulikk Nord AS (SYNTETISK)")
    session.add(sup); session.commit(); session.refresh(sup)

    contract = Contract(
        supplier_id=sup.id, contract_type=ContractType.RAMMEAVTALE,
        reference="RA-2026-DELER", title="Rammeavtale hydrauliske deler (SYNTETISK)",
        total_value=Decimal("2400000"),
        valid_from=date(2026, 1, 1), valid_to=date(2027, 12, 31),
    )
    session.add(contract); session.commit(); session.refresh(contract)

    prices = {"HYD-1001": "12500", "HYD-2002": "8300", "HYD-3003": "450"}
    for ref, price in prices.items():
        session.add(ContractLine(
            contract_id=contract.id, item_ref=ref,
            description=f"Del {ref}", unit_price=Decimal(price),
            max_quantity=Decimal("50") if ref == "HYD-3003" else None,
        ))

    # E-mail agreement lowering HYD-1001 price — confirmed, pending annex.
    session.add(Commitment(
        supplier_id=sup.id, contract_id=contract.id,
        source_type=SourceType.EMAIL, source_ref="e-post 2026-06-12, J. Hansen",
        source_quote=("Vi bekrefter herved redusert pris 11 800 kr per stk for HYD-1001, "
                      "gjeldende fra 12. juni. Formelt tillegg ettersendes."),
        condition_type=ConditionType.PRICE, item_ref="HYD-1001",
        value=Decimal("11800"), unit="NOK", valid_from=date(2026, 6, 12),
        formalization=Formalization.PENDING_ANNEX,
        extracted_by="llm:claude-sonnet-4-6", confirmed_by_user=True,
    ))
    session.commit()

    manifest: list[dict[str, str]] = []

    def _order_receipt(ref: str, value: str, with_receipt: bool = True) -> Order:
        o = Order(supplier_id=sup.id, contract_id=contract.id, reference=ref,
                  requested_by="bestiller.synt", estimated_value=Decimal(value),
                  regime=Regime.FOSA, order_date=date(2026, 7, 1))
        session.add(o); session.commit(); session.refresh(o)
        if with_receipt:
            session.add(Receipt(order_id=o.id, confirmed_by="verksted",
                                confirmed_at=datetime(2026, 7, 5, tzinfo=timezone.utc)))
            session.commit()
        return o

    def _invoice(number: str, order: Order | None,
                 lines: list[tuple[str, str, str]]) -> None:
        total = sum(Decimal(q) * Decimal(p) for _, q, p in lines)
        inv = Invoice(supplier_id=sup.id, order_id=order.id if order else None,
                      invoice_number=number, invoice_date=date(2026, 7, 10),
                      total_ex_vat=total, source=InvoiceSource.EHF)
        session.add(inv); session.commit(); session.refresh(inv)
        for ref, qty, price in lines:
            session.add(InvoiceLine(invoice_id=inv.id, item_ref=ref,
                                    description=f"Del {ref}", quantity=Decimal(qty),
                                    unit_price=Decimal(price),
                                    line_total=Decimal(qty) * Decimal(price)))
        session.commit()

    # F-1001: clean — contract price, receipt confirmed. Expected: no findings.
    _invoice("F-1001", _order_receipt("AVROP-01", "83000"), [("HYD-2002", "10", "8300")])

    # F-1002: price +7% above contract on HYD-2002. Expected: PRICE_ABOVE_AGREED.
    _invoice("F-1002", _order_receipt("AVROP-02", "88810"), [("HYD-2002", "10", "8881")])
    manifest.append({"invoice_number": "F-1002", "code": "PRICE_ABOVE_AGREED"})

    # F-1003: price matches the CONFIRMED e-mail agreement (11800 < 12500).
    # Expected: INFORMAL_BASIS (samsvar med forbehold — the demo scene).
    _invoice("F-1003", _order_receipt("AVROP-03", "118000"), [("HYD-1001", "10", "11800")])
    manifest.append({"invoice_number": "F-1003", "code": "INFORMAL_BASIS"})

    # F-1004: quantity 60 above agreed max 50 on HYD-3003. Expected: QTY_ABOVE_MAX.
    _invoice("F-1004", _order_receipt("AVROP-04", "27000"), [("HYD-3003", "60", "450")])
    manifest.append({"invoice_number": "F-1004", "code": "QTY_ABOVE_MAX"})

    # F-1005: order exists but mottak NOT confirmed. Expected: MISSING_RECEIPT.
    _invoice("F-1005", _order_receipt("AVROP-05", "41500", with_receipt=False),
             [("HYD-2002", "5", "8300")])
    manifest.append({"invoice_number": "F-1005", "code": "MISSING_RECEIPT"})

    return {"scenario": "deler", "expected_findings": manifest}
