"""EHF/UBL parser tests + end-to-end: parsed upload produces expected findings."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from core.extraction import build_sample_ehf, parse_ehf
from core.extraction.ehf import EHFParseError
from core.models import Invoice, InvoiceLine, InvoiceSource, Supplier
from core.reporting import check_invoice
from core.synth import scenario_deler


def test_parse_sample_header_fields():
    parsed = parse_ehf(build_sample_ehf())
    assert parsed.invoice_number == "F-1003"
    assert parsed.invoice_date == date(2026, 7, 10)
    assert parsed.currency == "NOK"
    assert parsed.supplier_org == "998877665"
    assert "Hydraulikk Nord" in parsed.supplier_name


def test_parse_sample_line_items():
    parsed = parse_ehf(build_sample_ehf())
    assert len(parsed.lines) == 1
    line = parsed.lines[0]
    assert line.item_ref == "HYD-1001"
    assert line.quantity == Decimal("10")
    assert line.unit_price == Decimal("11800")
    assert line.line_total == Decimal("118000")
    assert parsed.total_ex_vat == Decimal("118000")


def test_parse_is_namespace_tolerant():
    # No namespace prefixes at all — parser must still find fields by local name.
    xml = """<Invoice>
      <ID>X-9</ID><IssueDate>2026-01-05</IssueDate>
      <DocumentCurrencyCode>NOK</DocumentCurrencyCode>
      <AccountingSupplierParty><Party>
        <PartyLegalEntity><CompanyID>999 888 777</CompanyID></PartyLegalEntity>
      </Party></AccountingSupplierParty>
      <InvoiceLine>
        <InvoicedQuantity>2</InvoicedQuantity>
        <LineExtensionAmount>200</LineExtensionAmount>
        <Item><Name>Vare A</Name></Item>
        <Price><PriceAmount>100</PriceAmount></Price>
      </InvoiceLine>
    </Invoice>"""
    parsed = parse_ehf(xml)
    assert parsed.invoice_number == "X-9"
    assert parsed.supplier_org == "999888777"        # digits normalised
    assert parsed.lines[0].item_ref == "Vare A"      # falls back to Name
    assert parsed.lines[0].unit_price == Decimal("100")


def test_parse_rejects_non_invoice():
    with pytest.raises(EHFParseError):
        parse_ehf("<Order><ID>1</ID></Order>")


def test_parse_rejects_xxe_external_entity():
    """XXE: a DTD with an external entity must be rejected, never resolved."""
    malicious = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        '<Invoice><ID>&xxe;</ID><IssueDate>2026-07-10</IssueDate></Invoice>'
    )
    with pytest.raises(EHFParseError):
        parse_ehf(malicious)


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_uploaded_invoice_produces_expected_findings(session):
    """E2E: parse sample -> persist as a fresh (order-less) invoice linked to the
    demo supplier by org number -> check_invoice yields the confirmed e-mail
    agreement scene (INFORMAL_BASIS) plus MISSING_ORDER (upload has no avrop)."""
    scenario_deler.generate(session)
    parsed = parse_ehf(build_sample_ehf())

    supplier = session.exec(
        select(Supplier).where(Supplier.org_number == parsed.supplier_org)
    ).first()
    assert supplier is not None

    inv = Invoice(
        supplier_id=supplier.id, order_id=None,
        invoice_number="F-OPPLASTET", invoice_date=parsed.invoice_date,
        total_ex_vat=parsed.total_ex_vat, currency=parsed.currency,
        source=InvoiceSource.EHF,
    )
    session.add(inv)
    session.commit()
    session.refresh(inv)
    for ln in parsed.lines:
        session.add(InvoiceLine(
            invoice_id=inv.id, item_ref=ln.item_ref, description=ln.description,
            quantity=ln.quantity, unit_price=ln.unit_price, line_total=ln.line_total,
        ))
    session.commit()

    result = check_invoice(session, inv, actor="test-upload")
    codes = {f.code.value for f in result.findings}
    assert "INFORMAL_BASIS" in codes
    assert "MISSING_ORDER" in codes


def test_unknown_org_number_yields_no_agreed_basis(session):
    """Upload from an unknown supplier: create on the fly -> NO_AGREED_BASIS."""
    scenario_deler.generate(session)
    xml = """<Invoice>
      <ID>UK-1</ID><IssueDate>2026-07-10</IssueDate>
      <DocumentCurrencyCode>NOK</DocumentCurrencyCode>
      <AccountingSupplierParty><Party>
        <PartyName><Name>Ukjent Leverandør AS</Name></PartyName>
        <PartyLegalEntity><CompanyID>111222333</CompanyID></PartyLegalEntity>
      </Party></AccountingSupplierParty>
      <InvoiceLine>
        <InvoicedQuantity>1</InvoicedQuantity>
        <LineExtensionAmount>5000</LineExtensionAmount>
        <Item><Name>Konsulenttime</Name>
          <SellersItemIdentification><ID>KONS-X</ID></SellersItemIdentification></Item>
        <Price><PriceAmount>5000</PriceAmount></Price>
      </InvoiceLine>
    </Invoice>"""
    parsed = parse_ehf(xml)
    assert session.exec(
        select(Supplier).where(Supplier.org_number == parsed.supplier_org)
    ).first() is None

    supplier = Supplier(org_number=parsed.supplier_org, name=parsed.supplier_name)
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    inv = Invoice(
        supplier_id=supplier.id, order_id=None, invoice_number=parsed.invoice_number,
        invoice_date=parsed.invoice_date, total_ex_vat=parsed.total_ex_vat,
        currency=parsed.currency, source=InvoiceSource.EHF,
    )
    session.add(inv)
    session.commit()
    session.refresh(inv)
    for ln in parsed.lines:
        session.add(InvoiceLine(
            invoice_id=inv.id, item_ref=ln.item_ref, description=ln.description,
            quantity=ln.quantity, unit_price=ln.unit_price, line_total=ln.line_total,
        ))
    session.commit()

    result = check_invoice(session, inv, actor="test-upload")
    codes = {f.code.value for f in result.findings}
    assert "NO_AGREED_BASIS" in codes
