"""H1: reads never write. evaluate_invoice must not touch the audit trail;
check_invoice must persist exactly one CheckResult + one AuditLog; both must agree."""
from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, func, select

from core.models import AuditLog, CheckResult, Invoice
from core.reporting import check_invoice, evaluate_invoice
from core.synth import scenario_deler


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        scenario_deler.generate(s)
        yield s


def _counts(session):
    return (
        session.exec(select(func.count()).select_from(AuditLog)).one(),
        session.exec(select(func.count()).select_from(CheckResult)).one(),
    )


def test_evaluate_writes_nothing(session):
    """evaluate_invoice on every invoice must leave AuditLog and CheckResult unchanged."""
    audit_before, check_before = _counts(session)
    for inv in session.exec(select(Invoice)).all():
        evaluate_invoice(session, inv)
    audit_after, check_after = _counts(session)
    assert audit_after == audit_before
    assert check_after == check_before


def test_check_writes_exactly_one_each(session):
    """check_invoice persists exactly one CheckResult and one AuditLog per call."""
    inv = session.exec(select(Invoice).where(Invoice.invoice_number == "F-1002")).one()
    audit_before, check_before = _counts(session)
    check_invoice(session, inv, actor="test-user")
    audit_after, check_after = _counts(session)
    assert audit_after == audit_before + 1
    assert check_after == check_before + 1
    entry = session.exec(select(AuditLog).order_by(AuditLog.id.desc())).first()
    assert entry.actor == "test-user"
    assert entry.action == "invoice.checked"


def test_both_paths_identical_result(session):
    """For the same invoice, evaluate and check must yield identical verdict/findings/verdi."""
    for inv in session.exec(select(Invoice)).all():
        ev = evaluate_invoice(session, inv)
        ch = check_invoice(session, inv, actor="test-user")
        assert ev.verdict == ch.verdict
        assert ev.verdi_funnet == ch.verdi_funnet
        assert [f.code for f in ev.findings] == [f.code for f in ch.findings]
