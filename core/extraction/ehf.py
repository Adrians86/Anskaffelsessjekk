"""EHF / UBL 2.1 invoice parser — namespace-tolerant.

EHF (Elektronisk handelsformat) is the mandatory Norwegian public-sector
invoice format, a Norwegian profile of OASIS UBL 2.1. This parser extracts the
header fields and line items needed by the control engine. It matches elements
by local name so it tolerates any namespace prefix or default-namespace layout.

This module belongs to core/ and imports nothing from any UI. It only reads
data — persistence and control are the caller's responsibility.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ParsedLine:
    item_ref: str | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class ParsedInvoice:
    invoice_number: str
    invoice_date: date
    currency: str
    supplier_org: str | None          # digits only, matchable to Supplier.org_number
    supplier_name: str | None
    lines: list[ParsedLine] = field(default_factory=list)

    @property
    def total_ex_vat(self) -> Decimal:
        return sum((ln.line_total for ln in self.lines), Decimal("0"))


class EHFParseError(ValueError):
    """Raised when the XML is not a parseable EHF/UBL invoice."""


def _ln(tag: str) -> str:
    """Local name of a possibly-namespaced tag."""
    return tag.rsplit("}", 1)[-1]


def _find(el: ET.Element, name: str) -> ET.Element | None:
    """First descendant (document order) whose local name matches."""
    for child in el.iter():
        if child is el:
            continue
        if _ln(child.tag) == name:
            return child
    return None


def _text(el: ET.Element | None, name: str, default: str | None = None) -> str | None:
    if el is None:
        return default
    found = _find(el, name)
    if found is not None and found.text and found.text.strip():
        return found.text.strip()
    return default


def _direct_children(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if _ln(c.tag) == name]


def _decimal(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        return Decimal("0")


def _digits(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None


def _parse_date(value: str | None) -> date:
    if not value:
        raise EHFParseError("Fakturaen mangler dato (IssueDate).")
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError as exc:
        raise EHFParseError(f"Ugyldig fakturadato: {value!r}") from exc


def parse_ehf(source: str | bytes) -> ParsedInvoice:
    """Parse an EHF/UBL invoice document into a ParsedInvoice.

    Extracts supplier org number, invoice number, date, currency and line items
    (item_ref from SellersItemIdentification or, failing that, the item Name;
    quantity, unit price and line total).
    """
    try:
        root = ET.fromstring(source.encode() if isinstance(source, str) else source)
    except ET.ParseError as exc:
        raise EHFParseError(f"Kunne ikke lese XML: {exc}") from exc

    if _ln(root.tag) not in {"Invoice", "CreditNote"}:
        raise EHFParseError(
            f"Ikke en EHF/UBL-faktura (rot-element: {_ln(root.tag)})."
        )

    invoice_number = _text(root, "ID")
    if not invoice_number:
        raise EHFParseError("Fakturaen mangler fakturanummer (ID).")

    invoice_date = _parse_date(_text(root, "IssueDate"))
    currency = _text(root, "DocumentCurrencyCode", "NOK") or "NOK"

    supplier_party = _find(root, "AccountingSupplierParty")
    supplier_org = None
    supplier_name = None
    if supplier_party is not None:
        supplier_org = _digits(
            _text(supplier_party, "CompanyID") or _text(supplier_party, "EndpointID")
        )
        supplier_name = (
            _text(supplier_party, "Name")
            or _text(supplier_party, "RegistrationName")
        )

    lines: list[ParsedLine] = []
    for line_el in _direct_children(root, "InvoiceLine") or _direct_children(root, "CreditNoteLine"):
        item = _find(line_el, "Item")
        item_ref = None
        description = ""
        if item is not None:
            sellers = _find(item, "SellersItemIdentification")
            item_ref = _text(sellers, "ID") if sellers is not None else None
            description = _text(item, "Name", "") or ""
            if not item_ref:
                item_ref = description or None

        quantity = _decimal(
            _text(line_el, "InvoicedQuantity") or _text(line_el, "CreditedQuantity")
        )
        line_total = _decimal(_text(line_el, "LineExtensionAmount"))

        price_el = _find(line_el, "Price")
        unit_price = _decimal(_text(price_el, "PriceAmount")) if price_el is not None else Decimal("0")
        if unit_price == 0 and quantity != 0:
            unit_price = (line_total / quantity).quantize(Decimal("0.01"))

        lines.append(ParsedLine(
            item_ref=item_ref,
            description=description or (item_ref or "Fakturalinje"),
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
        ))

    return ParsedInvoice(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        currency=currency,
        supplier_org=supplier_org,
        supplier_name=supplier_name,
        lines=lines,
    )


# Sample EHF built from the F-1003 demo data (Hydraulikk Nord AS, HYD-1001 @ 11 800).
# Uploading it re-runs the confirmed e-mail-agreement scene end-to-end.
_SAMPLE_EHF = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ID>F-1003</cbc:ID>
  <cbc:IssueDate>2026-07-10</cbc:IssueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>NOK</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0192">998877665</cbc:EndpointID>
      <cac:PartyName>
        <cbc:Name>Hydraulikk Nord AS (SYNTETISK)</cbc:Name>
      </cac:PartyName>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Hydraulikk Nord AS (SYNTETISK)</cbc:RegistrationName>
        <cbc:CompanyID schemeID="0192">998877665</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0192">912345678</cbc:EndpointID>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>Demo Innkjøpsenhet (SYNTETISK)</cbc:RegistrationName>
        <cbc:CompanyID schemeID="0192">912345678</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="NOK">118000</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>Hydraulisk del HYD-1001</cbc:Name>
      <cac:SellersItemIdentification>
        <cbc:ID>HYD-1001</cbc:ID>
      </cac:SellersItemIdentification>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="NOK">11800</cbc:PriceAmount>
    </cac:Price>
  </cac:InvoiceLine>
</Invoice>
"""


def build_sample_ehf() -> str:
    """Return a valid EHF/UBL invoice XML string (synthetic F-1003 data)."""
    return _SAMPLE_EHF
