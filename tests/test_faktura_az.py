"""Faktura A–Z (Funksjon 3) — intake + price-list verification + human decision.

Closes the first full chain: leverandør (F1) + kontrakt/prisliste (F2) → faktura checked against the
price list. Pure core (no UI). Asserts hard rule #7 (write → audit), H1 (reads never write), and the
WHY in findings. Reconciliation is covered by tests/test_grafikk.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.extraction.csv_faktura import CSVParseError, parse_csv
from core.matching import prisliste
from core.matching.findings import Code, Severity
from core.models import AuditLog, InvoiceDecision, InvoiceSource
from core.registry import (
    RegistryError,
    add_line,
    create_contract,
    create_supplier,
    intake_invoice,
    latest_decision,
    record_decision,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _supplier_with_contract(session):
    sup = create_supplier(session, org_number="998877665", name="Hydraulikk Nord AS")
    k = create_contract(session, supplier_id=sup.id, title="Rammeavtale deler",
                        reference="RA-DELER", valid_from=date(2026, 1, 1))
    add_line(session, k.id, item_ref="HYD-1001", unit_price=Decimal("12500"),
             max_quantity=Decimal("50"))
    return sup, k


def _n_audits(session) -> int:
    return len(list(session.exec(select(AuditLog)).all()))


# --- CSV parser (N2) ----------------------------------------------------------
def test_csv_parse_groups_by_invoice_number():
    text = ("fakturanr;dato;orgnr;artikkelnr;antall;pris\n"
            "F-1;2026-07-01;998877665;HYD-1001;2;13000\n"
            "F-1;2026-07-01;998877665;HYD-2002;1;8300\n"
            "F-2;05.07.2026;987654321;KONS;10;1600\n")
    invs = parse_csv(text)
    assert [i.invoice_number for i in invs] == ["F-1", "F-2"]
    assert len(invs[0].lines) == 2
    assert invs[0].supplier_org == "998877665"
    assert invs[0].total_ex_vat == Decimal("34300")     # 2*13000 + 1*8300
    assert invs[1].invoice_date == date(2026, 7, 5)      # DD.MM.YYYY parsed


def test_csv_parse_rejects_missing_columns():
    with pytest.raises(CSVParseError):
        parse_csv("foo;bar\n1;2\n")


# --- Price-list verification with WHY (N3/N4) --------------------------------
def test_verify_price_above_agreed_says_why(session):
    sup, _ = _supplier_with_contract(session)
    inv = intake_invoice(session, parse_csv(
        "fakturanr;orgnr;artikkelnr;antall;pris\nF-9;998877665;HYD-1001;2;13000\n")[0],
        source=InvoiceSource.MANUAL)
    r = prisliste.verify(session, inv)
    assert r.verdict.value == "AVVIK"
    assert r.contract.reference == "RA-DELER"
    assert r.verdi_funnet == Decimal("1000")             # (13000-12500)*2
    f = r.findings[0]
    assert f.code == Code.PRICE_ABOVE_AGREED
    assert "12500" in f.message and "13000" in f.message and "HYD-1001" in f.message
    assert "RA-DELER" in f.message                        # names the contract (the WHY)


def test_verify_qty_above_max(session):
    sup, _ = _supplier_with_contract(session)
    inv = intake_invoice(session, parse_csv(
        "fakturanr;orgnr;artikkelnr;antall;pris\nF-Q;998877665;HYD-1001;60;12500\n")[0],
        source=InvoiceSource.MANUAL)
    r = prisliste.verify(session, inv)
    assert r.verdict.value == "AVVIK"
    assert any(f.code == Code.QTY_ABOVE_MAX for f in r.findings)


def test_verify_item_not_on_price_list_is_warn(session):
    sup, _ = _supplier_with_contract(session)
    inv = intake_invoice(session, parse_csv(
        "fakturanr;orgnr;artikkelnr;antall;pris\nF-X;998877665;UKJENT-9;1;100\n")[0],
        source=InvoiceSource.MANUAL)
    r = prisliste.verify(session, inv)
    assert r.verdict.value == "TIL_VURDERING"
    assert r.findings[0].code == Code.NO_AGREED_BASIS
    assert r.findings[0].severity == Severity.WARN


def test_verify_in_price_returns_samsvar(session):
    sup, _ = _supplier_with_contract(session)
    inv = intake_invoice(session, parse_csv(
        "fakturanr;orgnr;artikkelnr;antall;pris\nF-OK;998877665;HYD-1001;2;12500\n")[0],
        source=InvoiceSource.MANUAL)
    r = prisliste.verify(session, inv)
    assert r.verdict.value == "SAMSVAR"
    assert r.verdi_funnet == Decimal("0")


# --- Intake (idempotent, audited) --------------------------------------------
def test_intake_is_idempotent_and_audited(session):
    _supplier_with_contract(session)
    parsed = parse_csv("fakturanr;orgnr;artikkelnr;antall;pris\nF-1;998877665;HYD-1001;1;12500\n")[0]
    inv1 = intake_invoice(session, parsed, source=InvoiceSource.EHF)
    inv2 = intake_invoice(session, parsed, source=InvoiceSource.EHF)
    assert inv1.id == inv2.id                             # re-import reuses the invoice
    assert len(list(session.exec(
        select(AuditLog).where(AuditLog.action == "invoice.imported")).all())) == 1


# --- Human decision (N6) -----------------------------------------------------
def test_decision_is_appended_latest_wins_and_audited(session):
    _supplier_with_contract(session)
    inv = intake_invoice(session, parse_csv(
        "fakturanr;orgnr;artikkelnr;antall;pris\nF-1;998877665;HYD-1001;2;13000\n")[0],
        source=InvoiceSource.MANUAL)
    record_decision(session, inv.id, "godkjent", reason="ok tross avvik")
    record_decision(session, inv.id, "vent", reason="mangler mottak")
    assert latest_decision(session, inv.id).decision == "vent"
    assert len(list(session.exec(select(InvoiceDecision)).all())) == 2   # append-only
    assert len(list(session.exec(
        select(AuditLog).where(AuditLog.action == "invoice.decided")).all())) == 2
    with pytest.raises(RegistryError):
        record_decision(session, inv.id, "bogus")


def test_reads_never_write(session):
    _supplier_with_contract(session)
    inv = intake_invoice(session, parse_csv(
        "fakturanr;orgnr;artikkelnr;antall;pris\nF-1;998877665;HYD-1001;2;13000\n")[0],
        source=InvoiceSource.MANUAL)
    record_decision(session, inv.id, "godkjent")
    before = _n_audits(session)
    prisliste.verify(session, inv)           # verification is read-only
    prisliste.resolve_contract(session, inv)
    latest_decision(session, inv.id)
    assert _n_audits(session) == before      # H1: no writes on read
