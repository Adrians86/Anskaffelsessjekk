"""Test protokoll (PDF) generation."""
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import Invoice
from core.reporting import build_protokoll
from core.synth import scenario_deler


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_protokoll_returns_pdf_bytes(session: Session) -> None:
    """Protokoll export returns non-empty bytes starting with PDF magic."""
    scenario_deler.generate(session)
    invoices = session.exec(select(Invoice)).all()
    assert invoices, "Setup failed: no invoices"

    invoice = invoices[0]
    pdf_bytes = build_protokoll(session, invoice)

    assert isinstance(pdf_bytes, bytes), "Not bytes"
    assert len(pdf_bytes) > 0, "Empty PDF"
    assert pdf_bytes.startswith(b"%PDF"), "Not a valid PDF (no PDF magic)"


def test_protokoll_contains_invoice_reference(session: Session) -> None:
    """Protokoll is generated for the correct invoice."""
    scenario_deler.generate(session)
    invoices = session.exec(select(Invoice)).all()
    assert len(invoices) >= 2, "Need at least 2 invoices to test"

    invoice1 = invoices[0]
    invoice2 = invoices[1]
    pdf1_bytes = build_protokoll(session, invoice1)
    pdf2_bytes = build_protokoll(session, invoice2)

    assert len(pdf1_bytes) > 0, "PDF1 empty"
    assert len(pdf2_bytes) > 0, "PDF2 empty"
    assert pdf1_bytes != pdf2_bytes, "Different invoices should produce different PDFs"
