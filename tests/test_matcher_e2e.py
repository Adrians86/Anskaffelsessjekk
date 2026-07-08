"""End-to-end: synthetic data with manifest as ground truth.

The manifest lists every deliberately injected deviation. The matcher must
find ALL of them (recall = 1.0) and NOTHING else (precision = 1.0).
This is the portfolio metric: a measurable, reproducible quality gate.
"""
from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import Invoice, Verdict
from core.reporting import check_invoice
from core.synth import scenario_deler, scenario_konsulent


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.mark.parametrize("scenario", [scenario_deler, scenario_konsulent])
def test_precision_and_recall_are_perfect(session, scenario):
    manifest = scenario.generate(session)
    expected = {(m["invoice_number"], m["code"]) for m in manifest["expected_findings"]}

    found: set[tuple[str, str]] = set()
    for inv in session.exec(select(Invoice)).all():
        result = check_invoice(session, inv)
        for f in result.findings:
            found.add((inv.invoice_number, f.code.value))

    missed = expected - found          # recall failures
    unexpected = found - expected      # precision failures
    assert not missed, f"Matcher missed injected deviations: {missed}"
    assert not unexpected, f"Matcher produced false positives: {unexpected}"


def test_demo_scene_email_agreement(session):
    """The 10-minute demo scene: price differs from the contract but matches
    a confirmed e-mail agreement -> TIL_VURDERING with formalization note,
    NOT a false AVVIK."""
    scenario_deler.generate(session)
    inv = session.exec(
        select(Invoice).where(Invoice.invoice_number == "F-1003")
    ).one()
    result = check_invoice(session, inv)
    assert result.verdict == Verdict.TIL_VURDERING
    codes = {f.code.value for f in result.findings}
    assert codes == {"INFORMAL_BASIS"}
    assert "e-post" in result.findings[0].message


def test_verdi_funnet_is_computed(session):
    """Gap G2: the controlling counter. K-2002: (1600-1450) x 80h = 12 000."""
    scenario_konsulent.generate(session)
    inv = session.exec(
        select(Invoice).where(Invoice.invoice_number == "K-2002")
    ).one()
    result = check_invoice(session, inv)
    assert result.verdict == Verdict.AVVIK
    assert result.verdi_funnet == 12000
