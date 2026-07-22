"""Valuta v1: foreign-currency detection — flag, don't convert; NOK verdi funnet stays honest."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from core.matching.currency import is_foreign
from core.models import Invoice, InvoiceLine, InvoiceSource, Supplier
from core.reporting import evaluate_invoice
from core.synth import scenario_deler


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        scenario_deler.generate(s)
        yield s


def _eur_invoice(session):
    return session.exec(select(Invoice).where(Invoice.invoice_number == "F-EUR-1")).one()


def test_eur_invoice_yields_currency_mismatch(session):
    inv = _eur_invoice(session)
    assert is_foreign(inv)
    result = evaluate_invoice(session, inv)
    codes = {f.code.value for f in result.findings}
    assert "CURRENCY_MISMATCH" in codes
    assert result.verdict.value == "TIL_VURDERING"   # attention, not AVVIK


def test_no_deviation_from_raw_currency_difference(session):
    """A foreign-currency invoice must not turn a raw amount into a NOK deviation."""
    inv = _eur_invoice(session)
    result = evaluate_invoice(session, inv)
    assert result.verdi_funnet == 0
    assert all(f.deviation_amount == 0 for f in result.findings)


def test_nok_verdi_funnet_unchanged_by_currency_invoice(session):
    """Portfolio verdi funnet (NOK) must ignore the EUR invoice — still 22 310 on demo data."""
    total = sum(float(evaluate_invoice(session, inv).verdi_funnet)
                for inv in session.exec(select(Invoice)).all())
    # deler scenario alone = 10 310 (F-1002 5 810 + F-1004 4 500); EUR invoice adds 0.
    assert total == 10310


def test_price_check_suspended_even_if_amounts_would_flag(session):
    """Even if a EUR amount would look 'above' a NOK contract price, no price finding fires."""
    sup = session.exec(
        select(Supplier).where(Supplier.org_number == "998877665")
    ).one()  # NOK supplier with HYD-1001 @ 12 500 contract
    # A EUR invoice priced 99999 EUR for HYD-1001 must NOT produce PRICE_ABOVE_AGREED.
    inv = Invoice(supplier_id=sup.id, order_id=None, invoice_number="F-EUR-X",
                  invoice_date=date(2026, 7, 10), total_ex_vat=Decimal("99999"),
                  currency="EUR", source=InvoiceSource.EHF)
    session.add(inv)
    session.commit()
    session.refresh(inv)
    session.add(InvoiceLine(invoice_id=inv.id, item_ref="HYD-1001", description="Del HYD-1001",
                            quantity=Decimal("1"), unit_price=Decimal("99999"),
                            line_total=Decimal("99999")))
    session.commit()
    result = evaluate_invoice(session, inv)
    codes = {f.code.value for f in result.findings}
    assert "PRICE_ABOVE_AGREED" not in codes
    assert "CURRENCY_MISMATCH" in codes
    assert result.verdi_funnet == 0
