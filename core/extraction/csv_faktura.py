"""Batch invoice intake from CSV — many invoices in one file, grouped by invoice number.

Reuses the EHF ParsedInvoice/ParsedLine dataclasses so downstream code (persist + verify) is
identical for single EHF and batch CSV. Pure core: no UI import. NOT an LLM — plain csv parsing.

Expected columns (case-insensitive, flexible header names):
    fakturanr, dato, orgnr, leverandor, artikkelnr, beskrivelse, antall, pris
One row = one invoice line; rows with the same fakturanr form one invoice.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from core.extraction.ehf import ParsedInvoice, ParsedLine


class CSVParseError(ValueError):
    """Raised when the CSV cannot be parsed into invoices."""


# Accepted header aliases → canonical key.
_ALIASES = {
    "fakturanr": "invoice_number", "fakturanummer": "invoice_number", "invoice": "invoice_number",
    "dato": "date", "fakturadato": "date", "date": "date",
    "orgnr": "org", "org.nr": "org", "organisasjonsnummer": "org", "org": "org",
    "leverandor": "supplier", "leverandør": "supplier", "supplier": "supplier",
    "artikkelnr": "item_ref", "artikkel": "item_ref", "item": "item_ref", "item_ref": "item_ref",
    "beskrivelse": "description", "description": "description", "tekst": "description",
    "antall": "quantity", "mengde": "quantity", "quantity": "quantity",
    "pris": "unit_price", "enhetspris": "unit_price", "price": "unit_price", "unit_price": "unit_price",
    "valuta": "currency", "currency": "currency",
}


def _num(raw: str | None) -> Decimal:
    s = (raw or "").strip().replace(" ", "").replace(" ", "").replace(",", ".")
    if not s:
        return Decimal("0")
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise CSVParseError(f"Ugyldig tall: {raw!r}") from exc


def _date(raw: str | None) -> date:
    s = (raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise CSVParseError(f"Ugyldig dato: {raw!r} (bruk ÅÅÅÅ-MM-DD eller DD.MM.ÅÅÅÅ)")


def _digits(raw: str | None) -> str | None:
    d = "".join(ch for ch in (raw or "") if ch.isdigit())
    return d or None


def parse_csv(source: str | bytes) -> list[ParsedInvoice]:
    """Parse a CSV of invoice lines into a list of ParsedInvoice (one per fakturanr)."""
    text = source.decode("utf-8-sig") if isinstance(source, bytes) else source
    if not text.strip():
        raise CSVParseError("Tom CSV-fil.")
    # Sniff delimiter (support ; and ,).
    sample = text[:2048]
    delim = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not reader.fieldnames:
        raise CSVParseError("Mangler kolonneoverskrifter.")
    colmap = {}
    for raw_name in reader.fieldnames:
        key = _ALIASES.get((raw_name or "").strip().lower())
        if key:
            colmap[key] = raw_name
    for required in ("invoice_number", "item_ref", "unit_price"):
        if required not in colmap:
            raise CSVParseError(
                "Mangler påkrevd kolonne (fakturanr, artikkelnr, pris må finnes).")

    grouped: dict[str, dict] = {}
    order: list[str] = []
    for row in reader:
        inv_no = (row.get(colmap["invoice_number"]) or "").strip()
        if not inv_no:
            continue
        if inv_no not in grouped:
            grouped[inv_no] = {
                "date": _date(row.get(colmap["date"])) if "date" in colmap else date.today(),
                "org": _digits(row.get(colmap["org"])) if "org" in colmap else None,
                "supplier": (row.get(colmap["supplier"]) or "").strip()
                if "supplier" in colmap else None,
                "currency": (row.get(colmap["currency"]) or "NOK").strip().upper()
                if "currency" in colmap else "NOK",
                "lines": [],
            }
            order.append(inv_no)
        qty = _num(row.get(colmap["quantity"])) if "quantity" in colmap else Decimal("1")
        price = _num(row.get(colmap["unit_price"]))
        grouped[inv_no]["lines"].append(ParsedLine(
            item_ref=(row.get(colmap["item_ref"]) or "").strip() or None,
            description=(row.get(colmap["description"]) or "").strip()
            if "description" in colmap else "",
            quantity=qty, unit_price=price, line_total=qty * price,
        ))

    if not order:
        raise CSVParseError("Fant ingen fakturarader.")
    return [
        ParsedInvoice(
            invoice_number=inv_no, invoice_date=g["date"], currency=g["currency"] or "NOK",
            supplier_org=g["org"], supplier_name=g["supplier"] or None, lines=g["lines"],
        )
        for inv_no in order
        for g in [grouped[inv_no]]
    ]
