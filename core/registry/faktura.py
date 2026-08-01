"""Faktura intake + human decision — Funksjon 3.

Pure core: takes a Session, no UI import (hard rule #1). Every write appends an AuditLog row
(hard rule #7). Persisting a parsed invoice (EHF or CSV) is shared here so single and batch intake
use the exact same path.
"""
from __future__ import annotations

from sqlmodel import Session, select

from core.models import (
    INVOICE_DECISIONS,
    Invoice,
    InvoiceDecision,
    InvoiceLine,
    InvoiceSource,
    Supplier,
)
from core.registry.leverandor import RegistryError, _audit


def intake_invoice(session: Session, parsed, *, source: InvoiceSource = InvoiceSource.EHF,
                   actor: str = "demo-bruker") -> Invoice:
    """Persist a ParsedInvoice (from EHF or CSV): resolve/create supplier by org.nr, then create the
    invoice + lines. Idempotent — an existing invoice with the same number for the same supplier is
    reused (re-import is safe). Appends an «invoice.imported» audit row on create."""
    supplier = None
    if parsed.supplier_org:
        supplier = session.exec(
            select(Supplier).where(Supplier.org_number == parsed.supplier_org)
        ).first()
    if supplier is None:
        supplier = Supplier(
            org_number=parsed.supplier_org or f"UKJENT-{parsed.invoice_number}",
            name=(parsed.supplier_name or "Ukjent leverandør") + " (OPPLASTET)",
        )
        session.add(supplier)
        session.commit()
        session.refresh(supplier)
        _audit(session, actor, "supplier.created", f"supplier:{supplier.id}",
               f"leverandør opprettet ved faktura-inntak: {supplier.name}")
        session.commit()

    existing = session.exec(
        select(Invoice)
        .where(Invoice.supplier_id == supplier.id)
        .where(Invoice.invoice_number == parsed.invoice_number)
    ).first()
    if existing is not None:
        return existing

    inv = Invoice(
        supplier_id=supplier.id, order_id=None, invoice_number=parsed.invoice_number,
        invoice_date=parsed.invoice_date, total_ex_vat=parsed.total_ex_vat,
        currency=parsed.currency, source=source,
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
    _audit(session, actor, "invoice.imported", f"invoice:{inv.id}",
           f"faktura importert ({source.value}): {inv.invoice_number} "
           f"({len(parsed.lines)} linjer)")
    session.commit()
    return inv


def record_decision(session: Session, invoice_id: int, decision: str, *,
                    reason: str | None = None, actor: str = "demo-bruker") -> InvoiceDecision:
    """Record a human decision on an invoice (append-only). The system recommends; the human
    decides (hard rule #3) — a decision is never blocked, only logged."""
    if session.get(Invoice, invoice_id) is None:
        raise RegistryError(f"Ukjent faktura: {invoice_id}")
    if decision not in INVOICE_DECISIONS:
        raise RegistryError(f"Ugyldig beslutning: {decision}")
    row = InvoiceDecision(invoice_id=invoice_id, decision=decision,
                          reason=(reason or None), actor=actor)
    session.add(row)
    session.commit()
    session.refresh(row)
    detail = f"faktura {invoice_id}: {decision}"
    if reason:
        detail += f" — {reason}"
    _audit(session, actor, "invoice.decided", f"invoice:{invoice_id}", detail)
    session.commit()
    return row


def latest_decision(session: Session, invoice_id: int) -> InvoiceDecision | None:
    """The current (most recent) decision on an invoice, or None. Reads never write (H1)."""
    return session.exec(
        select(InvoiceDecision).where(InvoiceDecision.invoice_id == invoice_id)
        .order_by(InvoiceDecision.created_at.desc(), InvoiceDecision.id.desc())
    ).first()


def record_ocr_confirmation(
    session: Session,
    invoice_id: int,
    *,
    engine: str,
    corrections: list[str] | None = None,
    actor: str = "demo-bruker",
) -> None:
    """Record that a scanned invoice was READ by OCR and CONFIRMED by a human (O5).

    The audit row names the engine and every field the human corrected, so a reviewer can later
    see both what the machine claimed and what the human decided it actually said. Append-only
    (hard rule #7); the scan itself never entered control without passing this step.
    """
    if session.get(Invoice, invoice_id) is None:
        raise RegistryError(f"Ukjent faktura: {invoice_id}")
    fixed = corrections or []
    detail = f"skannet faktura lest med {engine} og bekreftet av saksbehandler"
    detail += (" — rettet: " + "; ".join(fixed)) if fixed else " — uten rettelser"
    _audit(session, actor, "invoice.ocr_confirmed", f"invoice:{invoice_id}", detail)
    session.commit()
