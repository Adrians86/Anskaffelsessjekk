"""OCR A–Z (Funksjon 3.5) — read → show → confirm → THEN control.

The safety property under test: a scan is never a control basis on its own. These tests run without
any system binary (CI has no tesseract) because the extraction layer is pure text processing and the
PDF path uses pypdf.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.extraction.ocr import (
    CONF_HIGH,
    CONF_LOW,
    ENGINE_PDF_TEXT,
    ENGINE_TESSERACT,
    ConfirmedLine,
    OcrReadError,
    OcrReading,
    OcrUnavailable,
    build_sample_pdf,
    confirmed_to_parsed,
    corrections_vs_proposal,
    image_ocr_available,
    parse_scanned_invoice,
    read_document,
)
from core.models import AuditLog, InvoiceSource
from core.registry import (
    add_line,
    create_contract,
    create_supplier,
    intake_invoice,
    record_ocr_confirmation,
)

_CLEAN = """Hydraulikk Nord AS
Org.nr: 998 877 665
Fakturanummer: F-2026-77
Fakturadato: 12.07.2026
Valuta: NOK
HYD-1001 Pumpehus 2 11800,00 23600,00
HYD-2002 Slange 1 8300,00 8300,00
Belop eks. mva: 31900,00"""

# The scenario from the brief: 11 800 misread as 1 180 by image OCR.
_MISREAD = _CLEAN.replace("2 11800,00 23600,00", "2 1180,00 23600,00")


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _reading(text: str, engine: str = ENGINE_PDF_TEXT) -> OcrReading:
    return OcrReading(text=text, engine=engine)


# --- O1: engines, and the honest degrade ------------------------------------
def test_pdf_with_text_layer_is_read_without_any_binary():
    reading = read_document(build_sample_pdf(), "faktura.pdf")
    assert reading.engine == ENGINE_PDF_TEXT
    assert reading.is_recognition is False       # extraction, not recognition
    assert "F-2026-77" in reading.text


def test_unsupported_and_empty_files_are_refused():
    with pytest.raises(OcrReadError):
        read_document(b"", "tom.pdf")
    with pytest.raises(OcrReadError):
        read_document(b"data", "regneark.xlsx")


def test_image_without_engine_degrades_honestly_never_guesses():
    available, reason = image_ocr_available()
    if available:                                 # engine present: nothing to degrade
        pytest.skip("tesseract is installed in this environment")
    assert "tesseract" in reason.lower() or "pytesseract" in reason.lower()
    with pytest.raises(OcrUnavailable):           # refuses — does not return a guessed reading
        read_document(b"\xff\xd8\xff\xe0notreallyajpeg", "skann.jpg")


def test_scanned_pdf_without_text_layer_is_refused_not_guessed():
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()                                # a page with no text at all
    with pytest.raises(OcrUnavailable):
        read_document(bytes(pdf.output()), "skann.pdf")


# --- O2: fields, confidence, source lines -----------------------------------
def test_fields_are_read_with_high_confidence_and_source_lines():
    p = parse_scanned_invoice(_reading(_CLEAN))
    assert p.invoice_number.value == "F-2026-77"
    assert p.invoice_number.confidence == CONF_HIGH
    assert p.invoice_date.value == date(2026, 7, 12)
    assert p.supplier_org.value == "998877665"
    assert p.total_ex_vat.value == Decimal("31900.00")
    # every read value can be traced back to the line it came from
    assert "Fakturanummer" in p.invoice_number.source_line


def test_lines_are_read_without_taking_article_digits_as_quantity():
    p = parse_scanned_invoice(_reading(_CLEAN))
    assert [ln.item_ref for ln in p.lines] == ["HYD-1001", "HYD-2002"]
    first = p.lines[0]
    assert (first.quantity, first.unit_price, first.line_total) == (
        Decimal("2"), Decimal("11800.00"), Decimal("23600.00"))


def test_image_recognition_forces_every_money_field_to_low_confidence():
    p = parse_scanned_invoice(_reading(_CLEAN, ENGINE_TESSERACT))
    assert p.total_ex_vat.confidence == CONF_LOW
    assert all(ln.confidence == CONF_LOW for ln in p.lines)
    assert any("bilde" in w.lower() for w in p.warnings)


# --- O3: the cross-check that protects the money ----------------------------
def test_sum_check_passes_on_a_consistent_reading():
    assert parse_scanned_invoice(_reading(_CLEAN)).sum_check().ok is True


def test_sum_check_catches_the_misread_amount():
    """11 800 read as 1 180 stops agreeing with its own line total — and we say which line."""
    p = parse_scanned_invoice(_reading(_MISREAD))
    check = p.sum_check()
    assert check.ok is False
    assert "HYD-1001" in check.message
    assert [ln.item_ref for ln in p.inconsistent_lines] == ["HYD-1001"]


def test_sample_pdf_demonstrates_the_cross_check():
    p = parse_scanned_invoice(read_document(build_sample_pdf(), "s.pdf"))
    assert p.sum_check().ok is False              # the demo document proves the safeguard fires
    assert "KAB-3003" in p.sum_check().message


# --- O4: only CONFIRMED values leave the module, into the SAME chain --------
def test_confirmed_values_build_the_same_parsed_invoice_as_ehf():
    parsed = confirmed_to_parsed(
        invoice_number="F-2026-77", invoice_date=date(2026, 7, 12), currency="NOK",
        supplier_org="998 877 665", supplier_name="Hydraulikk Nord AS",
        lines=[ConfirmedLine("HYD-1001", "Pumpehus", Decimal("2"), Decimal("11800"))])
    from core.extraction.ehf import ParsedInvoice
    assert isinstance(parsed, ParsedInvoice)      # identical type → identical downstream chain
    assert parsed.supplier_org == "998877665"     # normalised to digits, matchable to Supplier
    assert parsed.total_ex_vat == Decimal("23600")


def test_confirmation_requires_the_essentials():
    with pytest.raises(OcrReadError):             # no lines → nothing to control
        confirmed_to_parsed(invoice_number="F-1", invoice_date=date(2026, 7, 1), currency="NOK",
                            supplier_org=None, supplier_name=None, lines=[])
    with pytest.raises(OcrReadError):             # no invoice number → cannot be identified
        confirmed_to_parsed(invoice_number="  ", invoice_date=date(2026, 7, 1), currency="NOK",
                            supplier_org=None, supplier_name=None,
                            lines=[ConfirmedLine("A-1", "x", Decimal("1"), Decimal("1"))])


def test_confirmed_scan_runs_the_normal_verification_and_gets_a_verdict(session):
    sup = create_supplier(session, org_number="998877665", name="Hydraulikk Nord AS")
    k = create_contract(session, supplier_id=sup.id, title="Rammeavtale", reference="RA-DELER",
                        valid_from=date(2026, 1, 1))
    add_line(session, k.id, item_ref="HYD-1001", unit_price=Decimal("11000"))

    p = parse_scanned_invoice(_reading(_CLEAN))
    lines = [ConfirmedLine(ln.item_ref, ln.description, ln.quantity, ln.unit_price)
             for ln in p.lines]
    parsed = confirmed_to_parsed(
        invoice_number="F-2026-77", invoice_date=date(2026, 7, 12), currency="NOK",
        supplier_org="998877665", supplier_name="Hydraulikk Nord AS", lines=lines)
    inv = intake_invoice(session, parsed, source=InvoiceSource.PDF)

    from core.matching import prisliste
    r = prisliste.verify(session, inv)
    assert r.verdict.value == "AVVIK"                      # same engine as EHF/CSV
    assert r.contract.reference == "RA-DELER"
    assert any("11800" in f.message for f in r.findings)   # the confirmed price is what is checked


# --- O5: the audit trail records origin, engine and human corrections -------
def test_corrections_are_diffed_against_the_machine_reading():
    p = parse_scanned_invoice(_reading(_MISREAD))
    fixed = [ConfirmedLine("HYD-1001", "Pumpehus", Decimal("2"), Decimal("11800")),
             ConfirmedLine("HYD-2002", "Slange", Decimal("1"), Decimal("8300"))]
    fixes = corrections_vs_proposal(p, invoice_number="F-2026-77", invoice_date=date(2026, 7, 12),
                                    supplier_org="998877665", lines=fixed)
    assert any("pris HYD-1001" in f and "1180" in f and "11800" in f for f in fixes)


def test_ocr_confirmation_appends_one_audit_row_naming_engine_and_corrections(session):
    create_supplier(session, org_number="998877665", name="Hydraulikk Nord AS")
    parsed = confirmed_to_parsed(
        invoice_number="F-2026-77", invoice_date=date(2026, 7, 12), currency="NOK",
        supplier_org="998877665", supplier_name="Hydraulikk Nord AS",
        lines=[ConfirmedLine("HYD-1001", "Pumpehus", Decimal("2"), Decimal("11800"))])
    inv = intake_invoice(session, parsed, source=InvoiceSource.PDF)
    record_ocr_confirmation(session, inv.id, engine=ENGINE_TESSERACT,
                            corrections=["pris HYD-1001: 1180 → 11800"])
    rows = list(session.exec(
        select(AuditLog).where(AuditLog.action == "invoice.ocr_confirmed")).all())
    assert len(rows) == 1
    assert ENGINE_TESSERACT in rows[0].detail
    assert "1180" in rows[0].detail and "11800" in rows[0].detail


def test_reads_never_write(session):
    create_supplier(session, org_number="998877665", name="Hydraulikk Nord AS")
    before = len(list(session.exec(select(AuditLog)).all()))
    p = parse_scanned_invoice(read_document(build_sample_pdf(), "s.pdf"))
    p.sum_check()
    corrections_vs_proposal(p, invoice_number="F-2026-77", invoice_date=date(2026, 7, 12),
                            supplier_org="998877665", lines=[])
    assert len(list(session.exec(select(AuditLog)).all())) == before   # H1
