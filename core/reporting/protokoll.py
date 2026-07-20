"""PDF protocol (protokoll) generation for invoice checks — Norwegian language."""
from __future__ import annotations

from datetime import UTC, datetime

from fpdf import FPDF
from sqlmodel import Session

from core.models import Invoice, Order, Supplier
from core.reporting.classify import RULES_VERSION, evaluate_invoice


def build_protokoll(session: Session, invoice: Invoice) -> bytes:
    """Generate a PDF protokoll (draft) for an invoice check.

    Returns bytes ready for download. Norwegian language, no Streamlit imports.
    Pure read: rendering the document uses `evaluate_invoice` and never writes to the
    audit trail (reads never write — ARCHITECTURE.md §5).
    """
    check = evaluate_invoice(session, invoice)
    supplier = session.get(Supplier, invoice.supplier_id)
    order = session.get(Order, invoice.order_id) if invoice.order_id else None

    pdf = FPDF(format="A4", orientation="P", unit="mm")
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Anskaffelsesprotokoll - utkast", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Fakturainfo", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 5, "Fakturanummer:")
    pdf.cell(0, 5, invoice.invoice_number, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(50, 5, "Fakturadato:")
    pdf.cell(0, 5, str(invoice.invoice_date), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(50, 5, "Beløp (ekskl. mva):")
    pdf.cell(0, 5, f"{invoice.total_ex_vat:.2f} {invoice.currency}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Leverandør", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 5, "Navn:")
    pdf.cell(0, 5, supplier.name, new_x="LMARGIN", new_y="NEXT")
    if supplier.org_number:
        pdf.cell(50, 5, "Org.nr:")
        pdf.cell(0, 5, supplier.org_number, new_x="LMARGIN", new_y="NEXT")

    if order:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "Bestilling", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(50, 5, "Referanse:")
        pdf.cell(0, 5, order.reference, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    verdict_text = f"Vurdering: {check.verdict.value}"
    if check.verdict.value == "SAMSVAR":
        pdf.set_text_color(46, 204, 113)
    elif check.verdict.value == "TIL_VURDERING":
        pdf.set_text_color(243, 156, 18)
    else:
        pdf.set_text_color(231, 76, 60)
    pdf.cell(0, 7, verdict_text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if check.verdi_funnet:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(50, 5, "Verdi funnet:")
        pdf.cell(0, 5, f"{check.verdi_funnet:.2f} NOK", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Funn", new_x="LMARGIN", new_y="NEXT")

    if not check.findings:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, "Ingen funn. Fakturaen samsvarer med bestilling, mottak og alle registrerte forpliktelser.")
    else:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_fill_color(240, 240, 240)
        col_widths = [20, 80, 50]
        headers = ["Alvorlighet", "Beskrivelse", "Grunnlag"]
        for h, w in zip(headers, col_widths, strict=True):
            pdf.cell(w, 6, h, border=1, fill=True)
        pdf.ln()

        for finding in check.findings:
            severity = finding.severity.value[:3]
            description = finding.message[:60]
            citation = finding.citation[:50] if finding.citation else "-"

            pdf.cell(col_widths[0], 6, severity, border=1)
            pdf.cell(col_widths[1], 6, description, border=1)
            pdf.cell(col_widths[2], 6, citation, border=1)
            pdf.ln()

    pdf.ln(5)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    pdf.multi_cell(
        0, 4,
        f"Beslutningsstotte - utkast generert av Anskaffelsessjekk {timestamp}. "
        f"Kontrolleres og godkjennes av saksbehandler. Regelversjon: {RULES_VERSION}."
    )
    pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())
