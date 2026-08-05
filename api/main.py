"""FastAPI wrapper around the core engine — Droga B Steg 1+2.

A thin HTTP layer over the existing core/ functions. The engine is UNCHANGED — this module
only marshals data to/from JSON. Streamlit continues to run independently.

Run: uvicorn api.main:app --reload
"""
from __future__ import annotations

import io
from contextlib import asynccontextmanager
from datetime import date, timedelta
from decimal import Decimal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import (
    SIDE_INTERNAL,
    SIDE_SUPPLIER,
    ConditionType,
    Contract,
    ContractLine,
    ContractType,
    Formalization,
    Invoice,
    InvoiceDecision,
    InvoiceLine,
    SourceType,
    Supplier,
)
from core.reporting import evaluate_invoice
from core.synth import kontakter, scenario_deler, scenario_konsulent

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(_engine)
        with Session(_engine) as s:
            scenario_deler.generate(s)
            scenario_konsulent.generate(s)
            kontakter.seed(s)
    return _engine


def get_session():
    return Session(_get_engine())


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_engine()
    yield


app = FastAPI(
    title="Anskaffelsessjekk API",
    version="0.2.0",
    description="Read/write API for the procurement control engine.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class KpiStats(BaseModel):
    total_invoices: int
    avvik: int
    til_vurdering: int
    samsvar: int
    verdi_funnet: float
    n_foreign: int


class HealthBar(BaseModel):
    pct_avvik: float
    pct_til_vurdering: float
    pct_samsvar: float


class StatsResponse(BaseModel):
    kpi: KpiStats
    health: HealthBar
    periode_fra: date
    periode_til: date


class InvoiceRow(BaseModel):
    id: int
    invoice_number: str
    supplier_name: str
    supplier_id: int
    amount: float
    currency: str
    date: date
    verdict: str
    status: str
    finding: str


class FindingOut(BaseModel):
    severity: str
    code: str
    message: str
    citation: str
    expected: str | None = None
    actual: str | None = None
    deviation_amount: float | None = None


class InvoiceDetail(BaseModel):
    id: int
    invoice_number: str
    supplier_name: str
    supplier_id: int
    amount: float
    currency: str
    date: date
    verdict: str
    status: str
    findings: list[FindingOut]
    lines: list[dict]


class SupplierRow(BaseModel):
    id: int
    name: str
    org_number: str
    city: str | None = None
    status: str | None = None
    n_invoices: int = 0
    n_contracts: int = 0


class SupplierDetail(BaseModel):
    id: int
    name: str
    org_number: str
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    categories: str | None = None
    notes: str | None = None
    invoices: list[InvoiceRow]
    contracts: list[dict]
    contacts: list[dict]
    services: list[dict]
    qualifications: list[dict]


class ContactOut(BaseModel):
    id: int
    name: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    side: str


class ServiceOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    unit: str | None = None
    unit_price: float | None = None


class QualificationOut(BaseModel):
    id: int
    name: str
    valid_to: date | None = None


class ContractOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    title: str
    reference: str
    contract_type: str
    regime: str
    valid_from: date
    valid_to: date | None = None
    total_value: float | None = None
    change_clause: str
    status: str
    lines: list[dict]


class CommitmentOut(BaseModel):
    id: int
    supplier_id: int
    condition_type: str
    source_type: str
    source_ref: str
    item_ref: str | None = None
    value: float | None = None
    unit: str | None = None
    valid_from: date
    valid_to: date | None = None
    formalization: str
    confirmed_by_user: bool
    gyldighet: str | None = None


class TerskelResult(BaseModel):
    regime: str
    consequence: str
    citation: str
    citation_url: str | None = None
    verdi: float
    oppdragsgiver: str
    kontrakttype: str


# ---------------------------------------------------------------------------
# Request body models
# ---------------------------------------------------------------------------

class SupplierCreate(BaseModel):
    name: str
    org_number: str = ""
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    email: str | None = None
    phone: str | None = None
    categories: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    org_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    categories: str | None = None
    notes: str | None = None


class ContactCreate(BaseModel):
    name: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    side: str = SIDE_SUPPLIER


class ContactUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    unit: str | None = None
    unit_price: float | None = None


class QualificationCreate(BaseModel):
    name: str
    valid_to: date | None = None


class ContractCreate(BaseModel):
    supplier_id: int
    title: str
    reference: str
    contract_type: str = "RAMMEAVTALE"
    regime: str = "FOA"
    valid_from: date
    valid_to: date | None = None
    total_value: float | None = None
    change_clause: str = "kun_skriftlig_tillegg"
    status: str = "aktiv"


class ContractUpdate(BaseModel):
    title: str | None = None
    reference: str | None = None
    regime: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    total_value: float | None = None
    change_clause: str | None = None
    status: str | None = None


class LineCreate(BaseModel):
    item_ref: str
    description: str = ""
    unit: str = "stk"
    unit_price: float
    max_quantity: float | None = None
    currency: str = "NOK"


class LineUpdate(BaseModel):
    item_ref: str | None = None
    description: str | None = None
    unit: str | None = None
    unit_price: float | None = None
    max_quantity: float | None = None
    currency: str | None = None


class CommitmentCreate(BaseModel):
    supplier_ids: list[int]
    condition_type: str
    source_type: str = "EMAIL"
    source_ref: str
    item_ref: str | None = None
    value: float | None = None
    unit: str | None = "NOK"
    valid_from: date
    valid_to: date | None = None
    formalization: str = "PENDING_ANNEX"
    contract_id: int | None = None
    source_quote: str | None = None


class CommitmentUpdate(BaseModel):
    condition_type: str | None = None
    source_ref: str | None = None
    item_ref: str | None = None
    value: float | None = None
    unit: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    formalization: str | None = None


class InvoiceDraftLine(BaseModel):
    item_ref: str
    description: str
    quantity: float
    unit_price: float
    line_total: float


class InvoiceDraft(BaseModel):
    invoice_number: str
    supplier_name: str
    supplier_org: str | None = None
    supplier_id: int | None = None
    amount: float
    currency: str
    invoice_date: date | None = None
    lines: list[InvoiceDraftLine]


class SupplierLookupRow(BaseModel):
    id: int
    name: str
    org_number: str


class InvoiceConfirm(BaseModel):
    invoice_number: str
    supplier_id: int
    amount: float
    currency: str = "NOK"
    invoice_date: date
    lines: list[InvoiceDraftLine]


class DecisionCreate(BaseModel):
    action: str
    note: str | None = None


class TerskelRequest(BaseModel):
    verdi: float
    oppdragsgiver: str = "statlig"
    kontrakttype: str = "vare_tjeneste"
    dato: date | None = None
    regime: str = "FOA"


class RegelverkRow(BaseModel):
    id: str
    regime: str
    condition: str
    consequence: str
    citation: str
    citation_url: str
    valid_from: str
    valid_to: str | None = None
    active: bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _invoice_status(verdict_value: str, decision: InvoiceDecision | None) -> str:
    if decision is not None:
        return decision.decision
    if verdict_value in ("AVVIK", "TIL_VURDERING"):
        return "under_kontroll"
    return "ny"


def _latest_decision(session: Session, invoice_id: int) -> InvoiceDecision | None:
    return session.exec(
        select(InvoiceDecision)
        .where(InvoiceDecision.invoice_id == invoice_id)
        .order_by(InvoiceDecision.created_at.desc(), InvoiceDecision.id.desc())
    ).first()


def _build_invoice_row(session: Session, inv: Invoice) -> InvoiceRow:
    result = evaluate_invoice(session, inv)
    sup = session.get(Supplier, inv.supplier_id)
    dec = _latest_decision(session, inv.id)
    status = _invoice_status(result.verdict.value, dec)
    finding_text = ""
    if result.findings:
        f = result.findings[0]
        prefix = "📧 " if f.code.value == "INFORMAL_BASIS" else ""
        finding_text = prefix + f.message[:80]
    return InvoiceRow(
        id=inv.id,
        invoice_number=inv.invoice_number,
        supplier_name=sup.name,
        supplier_id=sup.id,
        amount=float(inv.total_ex_vat),
        currency=inv.currency,
        date=inv.invoice_date,
        verdict=result.verdict.value,
        status=status,
        finding=finding_text,
    )


def _registry_err(e: Exception) -> HTTPException:
    return HTTPException(422, str(e))


def _resolve_period(
    periode: str, fra: date | None, til: date | None, today: date | None = None,
) -> tuple[date, date]:
    today = today or date.today()
    if periode == "egendefinert":
        return (fra or today.replace(day=1), til or today)
    if periode == "kvartal":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=q_start_month, day=1)
        end_month = q_start_month + 2
        if end_month == 12:
            end = today.replace(month=12, day=31)
        else:
            end = today.replace(month=end_month + 1, day=1) - timedelta(days=1)
        return (start, end)
    if periode == "ar":
        return (today.replace(month=1, day=1), today.replace(month=12, day=31))
    if today.month == 12:
        last = today.replace(day=31)
    else:
        last = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return (today.replace(day=1), last)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "service": "Anskaffelsessjekk API", "docs": "/docs"}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/api/stats", response_model=StatsResponse)
def get_stats(
    periode: str = Query("maned", description="maned|kvartal|ar|egendefinert"),
    fra: date | None = Query(None),
    til: date | None = Query(None),
):
    from core.matching.currency import is_foreign
    p_fra, p_til = _resolve_period(periode, fra, til)
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        invoices = [inv for inv in invoices if p_fra <= inv.invoice_date <= p_til]
        counts = {"SAMSVAR": 0, "TIL_VURDERING": 0, "AVVIK": 0}
        total_verdi = Decimal("0")
        n_foreign = 0
        for inv in invoices:
            result = evaluate_invoice(session, inv)
            counts[result.verdict.value] += 1
            total_verdi += result.verdi_funnet
            if is_foreign(inv):
                n_foreign += 1
        total = len(invoices) or 1
        return StatsResponse(
            kpi=KpiStats(
                total_invoices=len(invoices),
                avvik=counts["AVVIK"],
                til_vurdering=counts["TIL_VURDERING"],
                samsvar=counts["SAMSVAR"],
                verdi_funnet=float(total_verdi),
                n_foreign=n_foreign,
            ),
            health=HealthBar(
                pct_avvik=(counts["AVVIK"] / total) * 100,
                pct_til_vurdering=(counts["TIL_VURDERING"] / total) * 100,
                pct_samsvar=(counts["SAMSVAR"] / total) * 100,
            ),
            periode_fra=p_fra,
            periode_til=p_til,
        )


# ---------------------------------------------------------------------------
# Invoices — read
# ---------------------------------------------------------------------------

@app.get("/api/invoices", response_model=list[InvoiceRow])
def list_invoices(
    verdict: str | None = Query(None),
    status: str | None = Query(None),
    supplier_id: int | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("avvik_first"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_session() as session:
        invoices = session.exec(select(Invoice).order_by(Invoice.invoice_number)).all()
        rows = [_build_invoice_row(session, inv) for inv in invoices]
    if verdict:
        rows = [r for r in rows if r.verdict == verdict]
    if status:
        rows = [r for r in rows if r.status == status]
    if supplier_id:
        rows = [r for r in rows if r.supplier_id == supplier_id]
    if search:
        q = search.lower()
        rows = [r for r in rows if q in r.invoice_number.lower() or q in r.supplier_name.lower()]
    sort_order = {"AVVIK": 0, "TIL_VURDERING": 1, "SAMSVAR": 2}
    if sort == "avvik_first":
        rows.sort(key=lambda r: (sort_order.get(r.verdict, 3), -r.amount))
    elif sort == "amount_desc":
        rows.sort(key=lambda r: -r.amount)
    elif sort == "date_desc":
        rows.sort(key=lambda r: r.date, reverse=True)
    return rows[offset:offset + limit]


@app.get("/api/invoices/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: int):
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if inv is None:
            raise HTTPException(404, "Faktura ikke funnet")
        result = evaluate_invoice(session, inv)
        sup = session.get(Supplier, inv.supplier_id)
        dec = _latest_decision(session, inv.id)
        status = _invoice_status(result.verdict.value, dec)
        lines = session.exec(select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id)).all()
        findings_out = [
            FindingOut(
                severity=f.severity.value,
                code=f.code.value,
                message=f.message,
                citation=f.citation,
                expected=str(f.expected) if f.expected is not None else None,
                actual=str(f.actual) if f.actual is not None else None,
                deviation_amount=float(f.deviation_amount) if f.deviation_amount else None,
            )
            for f in result.findings
        ]
        return InvoiceDetail(
            id=inv.id,
            invoice_number=inv.invoice_number,
            supplier_name=sup.name,
            supplier_id=sup.id,
            amount=float(inv.total_ex_vat),
            currency=inv.currency,
            date=inv.invoice_date,
            verdict=result.verdict.value,
            status=status,
            findings=findings_out,
            lines=[
                {"item_ref": ln.item_ref, "description": ln.description,
                 "quantity": float(ln.quantity), "unit_price": float(ln.unit_price),
                 "line_total": float(ln.line_total)}
                for ln in lines
            ],
        )


# ---------------------------------------------------------------------------
# Invoices — write (B4)
# ---------------------------------------------------------------------------

def _match_supplier_by_org(session: Session, org: str | None) -> int | None:
    if not org:
        return None
    sup = session.exec(
        select(Supplier)
        .where(Supplier.org_number == org)
        .where(Supplier.is_deleted == False)  # noqa: E712
    ).first()
    return sup.id if sup else None


@app.post("/api/invoices/upload/ehf", response_model=InvoiceDraft)
async def upload_ehf(file: UploadFile = File(...)):
    """Parse an EHF/UBL file and return a draft (not saved). Human confirms before saving."""
    from core.extraction.ehf import parse_ehf
    content = await file.read()
    try:
        parsed = parse_ehf(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(422, f"Kunne ikke lese EHF-fil: {e}")
    supplier_org = getattr(parsed, "supplier_org", None)
    with get_session() as session:
        matched_id = _match_supplier_by_org(session, supplier_org)
    return InvoiceDraft(
        invoice_number=parsed.invoice_number or "",
        supplier_name=parsed.supplier_name or "",
        supplier_org=supplier_org,
        supplier_id=matched_id,
        amount=float(parsed.total_ex_vat or 0),
        currency=parsed.currency or "NOK",
        invoice_date=parsed.invoice_date,
        lines=[
            InvoiceDraftLine(
                item_ref=ln.item_ref, description=ln.description,
                quantity=float(ln.quantity), unit_price=float(ln.unit_price),
                line_total=float(ln.line_total),
            )
            for ln in (parsed.lines or [])
        ],
    )


@app.post("/api/invoices/upload/csv", response_model=list[InvoiceDraft])
async def upload_csv(file: UploadFile = File(...)):
    """Parse a CSV batch and return list of drafts (not saved)."""
    from core.extraction.csv_faktura import parse_csv_invoices
    content = await file.read()
    try:
        parsed_list = parse_csv_invoices(content.decode("utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(422, f"Kunne ikke lese CSV: {e}")
    with get_session() as session:
        return [
            InvoiceDraft(
                invoice_number=p.invoice_number or "",
                supplier_name=p.supplier_name or "",
                supplier_org=getattr(p, "supplier_org", None),
                supplier_id=_match_supplier_by_org(session, getattr(p, "supplier_org", None)),
                amount=float(p.total_ex_vat or 0),
                currency=p.currency or "NOK",
                invoice_date=p.invoice_date,
                lines=[
                    InvoiceDraftLine(
                        item_ref=ln.item_ref, description=ln.description,
                        quantity=float(ln.quantity), unit_price=float(ln.unit_price),
                        line_total=float(ln.line_total),
                    )
                    for ln in (p.lines or [])
                ],
            )
            for p in parsed_list
        ]


def _parse_text_to_draft(text: str) -> dict:
    """Best-effort regex extraction from raw invoice text."""
    import re

    def find(patterns, default=""):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return default

    invoice_number = find([
        r"fakturanr[.:;]?\s*([A-Z0-9\-/]+)",
        r"invoice\s+no[.:;]?\s*([A-Z0-9\-/]+)",
        r"faktura\s+nr[.:;]?\s*([A-Z0-9\-/]+)",
    ])
    supplier_name = find([
        r"^([A-ZÆØÅ][A-Za-zÆØÅæøå &\-\.]{3,60}(?:AS|ASA|DA|ANS|SA))\b",
        r"leverand[oø]r[.:;]?\s*(.+)",
    ])
    supplier_org = find([
        r"org(?:\.?nr)?[.:;]?\s*(\d{9})",
        r"(\d{9})\s*MVA",
    ])
    date_raw = find([
        r"fakturadato[.:;]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
        r"dato[.:;]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
        r"(\d{4}-\d{2}-\d{2})",
    ])
    # Normalise date to ISO
    invoice_date = None
    if date_raw:
        for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%y", "%Y-%m-%d"):
            try:
                from datetime import datetime
                invoice_date = datetime.strptime(date_raw, fmt).date().isoformat()
                break
            except ValueError:
                pass

    def _to_float(raw: str) -> float:
        """Normalise Norwegian/Polish number format → float. Returns 0.0 on failure."""
        clean = raw.replace(" ", "").replace("\xa0", "")
        clean = re.sub(r"[^\d,.]", "", clean)
        if "," in clean and "." in clean:
            # e.g. "1.234,56" — dot is thousands sep, comma is decimal
            clean = clean.replace(".", "").replace(",", ".")
        elif "," in clean:
            # e.g. "300,00" — comma is decimal sep
            clean = clean.replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return 0.0

    amount_raw = find([
        r"total(?:beløp)?[.:;]?\s*([\d\s.,]+)",
        r"sum[.:;]?\s*([\d\s.,]+)",
        r"å betale[.:;]?\s*([\d\s.,]+)",
        r"beløp[.:;]?\s*([\d\s.,]+)",
    ])
    amount = _to_float(amount_raw) if amount_raw else 0.0

    # Fallback: scan all "number with 2 decimal places" patterns in text, take the largest.
    # Catches amounts without a label (e.g. bare "300,00" or "1 234,56").
    if amount == 0.0:
        candidates = re.findall(r"\d[\d\s\xa0]*[,.]\d{2}", text)
        if candidates:
            amount = max(_to_float(c) for c in candidates)

    currency = "NOK"
    if re.search(r"\bEUR\b", text):
        currency = "EUR"
    elif re.search(r"\bUSD\b", text):
        currency = "USD"

    return dict(
        invoice_number=invoice_number,
        supplier_name=supplier_name,
        supplier_org=supplier_org or None,
        amount=amount,
        currency=currency,
        invoice_date=invoice_date,
        lines=[],
    )


@app.post("/api/invoices/upload/pdf", response_model=InvoiceDraft)
async def upload_pdf(file: UploadFile = File(...)):
    """Parse a PDF or image invoice and return a draft. Raises 422 with no_text_layer if unreadable."""
    content = await file.read()
    filename = (file.filename or "").lower()
    text = ""

    if filename.endswith(".pdf"):
        try:
            import pdfplumber
            import io as _io
            with pdfplumber.open(_io.BytesIO(content)) as pdf:
                parts = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(parts).strip()
        except Exception as e:
            raise HTTPException(422, f"no_text_layer: {e}")
        if not text:
            raise HTTPException(422, "no_text_layer")
    else:
        # Image: JPG / PNG
        try:
            import pytesseract
            from PIL import Image
            import io as _io
            img = Image.open(_io.BytesIO(content))
            text = pytesseract.image_to_string(img, lang="nor+eng").strip()
        except Exception as e:
            raise HTTPException(422, f"no_text_layer: {e}")
        if not text:
            raise HTTPException(422, "no_text_layer")

    fields = _parse_text_to_draft(text)
    with get_session() as session:
        matched_id = _match_supplier_by_org(session, fields["supplier_org"])
    return InvoiceDraft(
        invoice_number=fields["invoice_number"],
        supplier_name=fields["supplier_name"],
        supplier_org=fields["supplier_org"],
        supplier_id=matched_id,
        amount=fields["amount"],
        currency=fields["currency"],
        invoice_date=fields["invoice_date"],
        lines=[],
    )


@app.post("/api/invoices/confirm", response_model=InvoiceRow)
def confirm_invoice(body: InvoiceConfirm):
    """Save a confirmed invoice draft and run the control engine. Returns verdict."""
    from core.extraction.ehf import ParsedInvoice, ParsedLine
    from core.models import InvoiceSource
    from core.registry.faktura import intake_invoice

    parsed = ParsedInvoice(
        invoice_number=body.invoice_number,
        supplier_name="",
        supplier_id=body.supplier_id,
        invoice_date=body.invoice_date,
        total_ex_vat=Decimal(str(body.amount)),
        currency=body.currency,
        lines=[
            ParsedLine(
                item_ref=ln.item_ref, description=ln.description,
                quantity=Decimal(str(ln.quantity)), unit_price=Decimal(str(ln.unit_price)),
                line_total=Decimal(str(ln.line_total)),
            )
            for ln in body.lines
        ],
    )
    with get_session() as session:
        try:
            inv = intake_invoice(session, parsed, source=InvoiceSource.EHF)
        except Exception as e:
            raise _registry_err(e)
        return _build_invoice_row(session, inv)


@app.post("/api/invoices/{invoice_id}/decision", response_model=InvoiceRow)
def add_decision(invoice_id: int, body: DecisionCreate):
    from core.registry.faktura import record_decision
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if inv is None:
            raise HTTPException(404, "Faktura ikke funnet")
        try:
            record_decision(session, invoice_id, body.action, note=body.note or "")
        except Exception as e:
            raise _registry_err(e)
        return _build_invoice_row(session, inv)


# ---------------------------------------------------------------------------
# Suppliers — read
# ---------------------------------------------------------------------------

@app.get("/api/suppliers", response_model=list[SupplierRow])
def list_suppliers(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_session() as session:
        suppliers = session.exec(
            select(Supplier).where(Supplier.is_deleted == False)  # noqa: E712
        ).all()
        rows = []
        for sup in suppliers:
            n_inv = len(session.exec(select(Invoice).where(Invoice.supplier_id == sup.id)).all())
            n_con = len(session.exec(
                select(Contract).where(Contract.supplier_id == sup.id)
                .where(Contract.is_deleted == False)  # noqa: E712
            ).all())
            rows.append(SupplierRow(
                id=sup.id, name=sup.name, org_number=sup.org_number,
                city=getattr(sup, "city", None), status=getattr(sup, "status", None),
                n_invoices=n_inv, n_contracts=n_con,
            ))
    if search:
        q = search.lower()
        rows = [r for r in rows if q in r.name.lower() or q in r.org_number]
    return rows[offset:offset + limit]


@app.get("/api/suppliers/lookup", response_model=list[SupplierLookupRow])
def lookup_suppliers(q: str = Query("", description="Partial name or org.nr")):
    """Lightweight supplier search for frontend dropdowns."""
    with get_session() as session:
        suppliers = session.exec(
            select(Supplier).where(Supplier.is_deleted == False)  # noqa: E712
        ).all()
    if q:
        ql = q.lower()
        suppliers = [s for s in suppliers if ql in s.name.lower() or (s.org_number and ql in s.org_number)]
    return [
        SupplierLookupRow(id=s.id, name=s.name, org_number=s.org_number or "")
        for s in suppliers[:20]
    ]


@app.get("/api/suppliers/{supplier_id}", response_model=SupplierDetail)
def get_supplier(supplier_id: int):
    with get_session() as session:
        sup = session.get(Supplier, supplier_id)
        if sup is None or getattr(sup, "is_deleted", False):
            raise HTTPException(404, "Leverandør ikke funnet")
        from core.models import ContactPerson, Qualification, SupplierService
        invoices = session.exec(select(Invoice).where(Invoice.supplier_id == sup.id)).all()
        inv_rows = [_build_invoice_row(session, inv) for inv in invoices]
        contracts = session.exec(
            select(Contract).where(Contract.supplier_id == sup.id)
            .where(Contract.is_deleted == False)  # noqa: E712
        ).all()
        contacts = session.exec(
            select(ContactPerson).where(ContactPerson.supplier_id == sup.id)
        ).all()
        services = session.exec(
            select(SupplierService).where(SupplierService.supplier_id == sup.id)
        ).all()
        quals = session.exec(
            select(Qualification).where(Qualification.supplier_id == sup.id)
        ).all()
        return SupplierDetail(
            id=sup.id, name=sup.name, org_number=sup.org_number,
            address=getattr(sup, "address", None),
            postal_code=getattr(sup, "postal_code", None),
            city=getattr(sup, "city", None),
            website=getattr(sup, "website", None),
            email=getattr(sup, "email", None),
            phone=getattr(sup, "phone", None),
            status=getattr(sup, "status", None),
            categories=getattr(sup, "categories", None),
            notes=getattr(sup, "notes", None),
            invoices=inv_rows,
            contracts=[
                {"id": c.id, "reference": c.reference, "title": c.title,
                 "valid_from": str(c.valid_from), "status": getattr(c, "status", None)}
                for c in contracts
            ],
            contacts=[
                {"id": c.id, "name": c.name, "role": c.role,
                 "email": c.email, "phone": c.phone, "side": c.side}
                for c in contacts
            ],
            services=[
                {"id": s.id, "name": s.name, "description": s.description,
                 "unit": s.unit, "unit_price": float(s.unit_price) if s.unit_price else None}
                for s in services
            ],
            qualifications=[
                {"id": q.id, "name": q.name, "valid_to": str(q.valid_to) if q.valid_to else None}
                for q in quals
            ],
        )


# ---------------------------------------------------------------------------
# Suppliers — write (B1)
# ---------------------------------------------------------------------------

@app.post("/api/suppliers", response_model=SupplierRow, status_code=201)
def create_supplier(body: SupplierCreate):
    from core.registry.leverandor import RegistryError, create_supplier as _create
    import uuid
    org_number = body.org_number.strip() if body.org_number else ""
    if not org_number:
        # Generate a unique placeholder so core's uniqueness check passes.
        # The user can edit the real org.nr later via the leverandørkort.
        org_number = f"UTEN-{uuid.uuid4().hex[:8].upper()}"
    with get_session() as session:
        try:
            sup = _create(
                session, org_number=org_number, name=body.name,
                categories=body.categories,
            )
            if body.address or body.postal_code or body.city or body.email or body.phone:
                from core.registry.leverandor import update_supplier as _update
                sup = _update(
                    session, sup.id,
                    address=body.address, postal_code=body.postal_code,
                    city=body.city, email=body.email, phone=body.phone,
                )
        except RegistryError as e:
            raise _registry_err(e)
        return SupplierRow(
            id=sup.id, name=sup.name, org_number=sup.org_number,
            city=getattr(sup, "city", None), status=getattr(sup, "status", None),
        )


@app.put("/api/suppliers/{supplier_id}", response_model=SupplierRow)
def update_supplier(supplier_id: int, body: SupplierUpdate):
    from core.registry.leverandor import RegistryError, update_supplier as _update
    with get_session() as session:
        try:
            sup = _update(
                session, supplier_id,
                name=body.name, org_number=body.org_number,
                address=body.address, postal_code=body.postal_code, city=body.city,
                website=body.website, email=body.email, phone=body.phone,
                status=body.status, categories=body.categories, notes=body.notes,
            )
        except RegistryError as e:
            raise _registry_err(e)
        return SupplierRow(
            id=sup.id, name=sup.name, org_number=sup.org_number,
            city=getattr(sup, "city", None), status=getattr(sup, "status", None),
        )


@app.delete("/api/suppliers/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int):
    from core.registry.leverandor import RegistryError, soft_delete_supplier
    with get_session() as session:
        try:
            soft_delete_supplier(session, supplier_id)
        except RegistryError as e:
            raise _registry_err(e)


@app.post("/api/suppliers/{supplier_id}/contacts", response_model=ContactOut, status_code=201)
def add_contact(supplier_id: int, body: ContactCreate):
    from core.registry.leverandor import RegistryError, add_contact as _add
    with get_session() as session:
        try:
            c = _add(session, supplier_id, name=body.name, role=body.role,
                     email=body.email, phone=body.phone, side=body.side)
        except RegistryError as e:
            raise _registry_err(e)
        return ContactOut(id=c.id, name=c.name, role=c.role,
                          email=c.email, phone=c.phone, side=c.side)


@app.put("/api/suppliers/{supplier_id}/contacts/{contact_id}", response_model=ContactOut)
def update_contact(supplier_id: int, contact_id: int, body: ContactUpdate):
    from core.registry.leverandor import RegistryError, update_contact as _update
    with get_session() as session:
        try:
            c = _update(session, contact_id, name=body.name, role=body.role,
                        email=body.email, phone=body.phone)
        except RegistryError as e:
            raise _registry_err(e)
        return ContactOut(id=c.id, name=c.name, role=c.role,
                          email=c.email, phone=c.phone, side=c.side)


@app.delete("/api/suppliers/{supplier_id}/contacts/{contact_id}", status_code=204)
def delete_contact(supplier_id: int, contact_id: int):
    from core.registry.leverandor import RegistryError, delete_contact as _del
    with get_session() as session:
        try:
            _del(session, contact_id)
        except RegistryError as e:
            raise _registry_err(e)


@app.post("/api/suppliers/{supplier_id}/services", response_model=ServiceOut, status_code=201)
def add_service(supplier_id: int, body: ServiceCreate):
    from core.registry.leverandor import RegistryError, add_service as _add
    with get_session() as session:
        try:
            s = _add(session, supplier_id, name=body.name, description=body.description,
                     unit=body.unit, unit_price=Decimal(str(body.unit_price)) if body.unit_price else None)
        except RegistryError as e:
            raise _registry_err(e)
        return ServiceOut(id=s.id, name=s.name, description=s.description,
                          unit=s.unit, unit_price=float(s.unit_price) if s.unit_price else None)


@app.delete("/api/suppliers/{supplier_id}/services/{service_id}", status_code=204)
def delete_service(supplier_id: int, service_id: int):
    from core.registry.leverandor import RegistryError, delete_service as _del
    with get_session() as session:
        try:
            _del(session, service_id)
        except RegistryError as e:
            raise _registry_err(e)


@app.post("/api/suppliers/{supplier_id}/qualifications", response_model=QualificationOut, status_code=201)
def add_qualification(supplier_id: int, body: QualificationCreate):
    from core.registry.leverandor import RegistryError, add_qualification as _add
    with get_session() as session:
        try:
            q = _add(session, supplier_id, name=body.name, valid_to=body.valid_to)
        except RegistryError as e:
            raise _registry_err(e)
        return QualificationOut(id=q.id, name=q.name, valid_to=q.valid_to)


@app.delete("/api/suppliers/{supplier_id}/qualifications/{qual_id}", status_code=204)
def delete_qualification(supplier_id: int, qual_id: int):
    from core.registry.leverandor import RegistryError, delete_qualification as _del
    with get_session() as session:
        try:
            _del(session, qual_id)
        except RegistryError as e:
            raise _registry_err(e)


# ---------------------------------------------------------------------------
# Contracts (B2)
# ---------------------------------------------------------------------------

@app.get("/api/contracts", response_model=list[ContractOut])
def list_contracts(supplier_id: int | None = Query(None)):
    from core.registry.kontrakt import list_contracts as _list, list_lines
    with get_session() as session:
        contracts = _list(session, supplier_id=supplier_id)
        result = []
        for c in contracts:
            sup = session.get(Supplier, c.supplier_id)
            lines = list_lines(session, c.id)
            result.append(ContractOut(
                id=c.id, supplier_id=c.supplier_id,
                supplier_name=sup.name if sup else "",
                title=c.title, reference=c.reference,
                contract_type=c.contract_type.value if hasattr(c.contract_type, "value") else str(c.contract_type),
                regime=c.regime, valid_from=c.valid_from, valid_to=c.valid_to,
                total_value=float(c.total_value) if c.total_value else None,
                change_clause=c.change_clause, status=c.status or "aktiv",
                lines=[
                    {"id": ln.id, "item_ref": ln.item_ref, "description": ln.description,
                     "unit": ln.unit, "unit_price": float(ln.unit_price),
                     "max_quantity": float(ln.max_quantity) if ln.max_quantity else None,
                     "currency": ln.currency}
                    for ln in lines
                ],
            ))
        return result


@app.get("/api/contracts/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int):
    from core.registry.kontrakt import get_contract as _get, list_lines
    with get_session() as session:
        c = _get(session, contract_id)
        if c is None or getattr(c, "is_deleted", False):
            raise HTTPException(404, "Avtale ikke funnet")
        sup = session.get(Supplier, c.supplier_id)
        lines = list_lines(session, c.id)
        return ContractOut(
            id=c.id, supplier_id=c.supplier_id,
            supplier_name=sup.name if sup else "",
            title=c.title, reference=c.reference,
            contract_type=c.contract_type.value if hasattr(c.contract_type, "value") else str(c.contract_type),
            regime=c.regime, valid_from=c.valid_from, valid_to=c.valid_to,
            total_value=float(c.total_value) if c.total_value else None,
            change_clause=c.change_clause, status=c.status or "aktiv",
            lines=[
                {"id": ln.id, "item_ref": ln.item_ref, "description": ln.description,
                 "unit": ln.unit, "unit_price": float(ln.unit_price),
                 "max_quantity": float(ln.max_quantity) if ln.max_quantity else None,
                 "currency": ln.currency}
                for ln in lines
            ],
        )


@app.post("/api/contracts", response_model=ContractOut, status_code=201)
def create_contract(body: ContractCreate):
    from core.registry.kontrakt import RegistryError, create_contract as _create, list_lines
    with get_session() as session:
        try:
            c = _create(
                session, supplier_id=body.supplier_id, title=body.title,
                reference=body.reference,
                contract_type=ContractType(body.contract_type) if body.contract_type else ContractType.RAMMEAVTALE,
                regime=body.regime, valid_from=body.valid_from,
                valid_to=body.valid_to,
                total_value=Decimal(str(body.total_value)) if body.total_value else None,
                change_clause=body.change_clause, status=body.status,
            )
        except (RegistryError, ValueError) as e:
            raise _registry_err(e)
        sup = session.get(Supplier, c.supplier_id)
        return ContractOut(
            id=c.id, supplier_id=c.supplier_id,
            supplier_name=sup.name if sup else "",
            title=c.title, reference=c.reference,
            contract_type=c.contract_type.value if hasattr(c.contract_type, "value") else str(c.contract_type),
            regime=c.regime, valid_from=c.valid_from, valid_to=c.valid_to,
            total_value=float(c.total_value) if c.total_value else None,
            change_clause=c.change_clause, status=c.status or "aktiv",
            lines=[],
        )


@app.put("/api/contracts/{contract_id}", response_model=ContractOut)
def update_contract(contract_id: int, body: ContractUpdate):
    from core.registry.kontrakt import RegistryError, update_contract as _update, list_lines
    with get_session() as session:
        try:
            c = _update(
                session, contract_id, title=body.title, reference=body.reference,
                regime=body.regime, valid_from=body.valid_from,
                valid_to=body.valid_to, update_valid_to=body.valid_to is not None,
                total_value=Decimal(str(body.total_value)) if body.total_value else None,
                update_total_value=body.total_value is not None,
                change_clause=body.change_clause, status=body.status,
            )
        except (Exception,) as e:
            raise _registry_err(e)
        sup = session.get(Supplier, c.supplier_id)
        lines = list_lines(session, c.id)
        return ContractOut(
            id=c.id, supplier_id=c.supplier_id,
            supplier_name=sup.name if sup else "",
            title=c.title, reference=c.reference,
            contract_type=c.contract_type.value if hasattr(c.contract_type, "value") else str(c.contract_type),
            regime=c.regime, valid_from=c.valid_from, valid_to=c.valid_to,
            total_value=float(c.total_value) if c.total_value else None,
            change_clause=c.change_clause, status=c.status or "aktiv",
            lines=[
                {"id": ln.id, "item_ref": ln.item_ref, "description": ln.description,
                 "unit": ln.unit, "unit_price": float(ln.unit_price),
                 "max_quantity": float(ln.max_quantity) if ln.max_quantity else None,
                 "currency": ln.currency}
                for ln in lines
            ],
        )


@app.delete("/api/contracts/{contract_id}", status_code=204)
def delete_contract(contract_id: int):
    from core.registry.kontrakt import RegistryError, soft_delete_contract
    with get_session() as session:
        try:
            soft_delete_contract(session, contract_id)
        except RegistryError as e:
            raise _registry_err(e)


@app.post("/api/contracts/{contract_id}/lines", status_code=201)
def add_line(contract_id: int, body: LineCreate):
    from core.registry.kontrakt import RegistryError, add_line as _add
    with get_session() as session:
        try:
            ln = _add(
                session, contract_id, item_ref=body.item_ref, description=body.description,
                unit=body.unit, unit_price=Decimal(str(body.unit_price)),
                max_quantity=Decimal(str(body.max_quantity)) if body.max_quantity else None,
                currency=body.currency,
            )
        except RegistryError as e:
            raise _registry_err(e)
        return {"id": ln.id, "item_ref": ln.item_ref, "description": ln.description,
                "unit": ln.unit, "unit_price": float(ln.unit_price),
                "max_quantity": float(ln.max_quantity) if ln.max_quantity else None,
                "currency": ln.currency}


@app.put("/api/contracts/{contract_id}/lines/{line_id}")
def update_line(contract_id: int, line_id: int, body: LineUpdate):
    from core.registry.kontrakt import RegistryError, update_line as _update
    with get_session() as session:
        try:
            ln = _update(
                session, line_id, item_ref=body.item_ref, description=body.description,
                unit=body.unit,
                unit_price=Decimal(str(body.unit_price)) if body.unit_price else None,
                max_quantity=Decimal(str(body.max_quantity)) if body.max_quantity else None,
                update_max_quantity=body.max_quantity is not None,
                currency=body.currency,
            )
        except RegistryError as e:
            raise _registry_err(e)
        return {"id": ln.id, "item_ref": ln.item_ref, "description": ln.description,
                "unit": ln.unit, "unit_price": float(ln.unit_price),
                "max_quantity": float(ln.max_quantity) if ln.max_quantity else None,
                "currency": ln.currency}


@app.delete("/api/contracts/{contract_id}/lines/{line_id}", status_code=204)
def delete_line(contract_id: int, line_id: int):
    from core.registry.kontrakt import RegistryError, delete_line as _del
    with get_session() as session:
        try:
            _del(session, line_id)
        except RegistryError as e:
            raise _registry_err(e)


# ---------------------------------------------------------------------------
# Forpliktelser (B3)
# ---------------------------------------------------------------------------

@app.get("/api/forpliktelser", response_model=list[CommitmentOut])
def list_forpliktelser(leverandor_id: int | None = Query(None)):
    from core.registry.forpliktelse import list_commitments
    with get_session() as session:
        items = list_commitments(session, supplier_id=leverandor_id)
        return [
            CommitmentOut(
                id=c.id, supplier_id=c.supplier_id,
                condition_type=c.condition_type.value if hasattr(c.condition_type, "value") else str(c.condition_type),
                source_type=c.source_type.value if hasattr(c.source_type, "value") else str(c.source_type),
                source_ref=c.source_ref,
                item_ref=c.item_ref, value=float(c.value) if c.value else None,
                unit=c.unit, valid_from=c.valid_from, valid_to=c.valid_to,
                formalization=c.formalization.value if hasattr(c.formalization, "value") else str(c.formalization),
                confirmed_by_user=c.confirmed_by_user,
                gyldighet=c.gyldighet,
            )
            for c in items
        ]


@app.post("/api/forpliktelser", response_model=CommitmentOut, status_code=201)
def create_forpliktelse(body: CommitmentCreate):
    from core.registry.forpliktelse import create_commitment
    from core.registry.leverandor import RegistryError
    with get_session() as session:
        try:
            c = create_commitment(
                session,
                supplier_id=body.supplier_ids[0] if body.supplier_ids else 0,
                condition_type=ConditionType(body.condition_type),
                source_type=SourceType(body.source_type),
                source_ref=body.source_ref,
                item_ref=body.item_ref,
                value=Decimal(str(body.value)) if body.value else None,
                unit=body.unit,
                valid_from=body.valid_from, valid_to=body.valid_to,
                formalization=Formalization(body.formalization),
                contract_id=body.contract_id,
                source_quote=body.source_quote,
            )
        except (RegistryError, ValueError) as e:
            raise _registry_err(e)
        return CommitmentOut(
            id=c.id, supplier_id=c.supplier_id,
            condition_type=c.condition_type.value if hasattr(c.condition_type, "value") else str(c.condition_type),
            source_type=c.source_type.value if hasattr(c.source_type, "value") else str(c.source_type),
            source_ref=c.source_ref, item_ref=c.item_ref,
            value=float(c.value) if c.value else None,
            unit=c.unit, valid_from=c.valid_from, valid_to=c.valid_to,
            formalization=c.formalization.value if hasattr(c.formalization, "value") else str(c.formalization),
            confirmed_by_user=c.confirmed_by_user, gyldighet=c.gyldighet,
        )


@app.put("/api/forpliktelser/{commitment_id}", response_model=CommitmentOut)
def update_forpliktelse(commitment_id: int, body: CommitmentUpdate):
    from core.registry.forpliktelse import update_commitment
    from core.registry.leverandor import RegistryError
    with get_session() as session:
        try:
            c = update_commitment(
                session, commitment_id,
                condition_type=ConditionType(body.condition_type) if body.condition_type else None,
                source_ref=body.source_ref, item_ref=body.item_ref,
                update_item_ref=body.item_ref is not None,
                value=Decimal(str(body.value)) if body.value else None,
                update_value=body.value is not None,
                unit=body.unit, valid_from=body.valid_from, valid_to=body.valid_to,
                formalization=Formalization(body.formalization) if body.formalization else None,
            )
        except (RegistryError, ValueError) as e:
            raise _registry_err(e)
        return CommitmentOut(
            id=c.id, supplier_id=c.supplier_id,
            condition_type=c.condition_type.value if hasattr(c.condition_type, "value") else str(c.condition_type),
            source_type=c.source_type.value if hasattr(c.source_type, "value") else str(c.source_type),
            source_ref=c.source_ref, item_ref=c.item_ref,
            value=float(c.value) if c.value else None,
            unit=c.unit, valid_from=c.valid_from, valid_to=c.valid_to,
            formalization=c.formalization.value if hasattr(c.formalization, "value") else str(c.formalization),
            confirmed_by_user=c.confirmed_by_user, gyldighet=c.gyldighet,
        )


@app.delete("/api/forpliktelser/{commitment_id}", status_code=204)
def delete_forpliktelse(commitment_id: int):
    from core.registry.forpliktelse import soft_delete_commitment
    from core.registry.leverandor import RegistryError
    with get_session() as session:
        try:
            soft_delete_commitment(session, commitment_id)
        except RegistryError as e:
            raise _registry_err(e)


# ---------------------------------------------------------------------------
# Terskelsjekk (B5)
# ---------------------------------------------------------------------------

@app.post("/api/terskelsjekk", response_model=list[TerskelResult])
def terskelsjekk(body: TerskelRequest):
    from core.rules.engine import Facts, RulesEngine
    facts = Facts(
        regime=body.regime,
        estimated_value=Decimal(str(body.verdi)),
        assessment_date=body.dato or date.today(),
        oppdragsgiver=body.oppdragsgiver,
        kontrakttype=body.kontrakttype,
    )
    engine = RulesEngine()
    hits = engine.evaluate(facts)
    if not hits:
        return [TerskelResult(
            regime=body.regime,
            consequence="INGEN_REGEL_TRUFFET",
            citation="Ingen terskelregel treffer dette beløpet og de valgte parameterne.",
            citation_url=None,
            verdi=body.verdi,
            oppdragsgiver=body.oppdragsgiver,
            kontrakttype=body.kontrakttype,
        )]
    return [
        TerskelResult(
            regime=h.regime, consequence=h.consequence,
            citation=h.citation, citation_url=h.citation_url,
            verdi=body.verdi, oppdragsgiver=body.oppdragsgiver,
            kontrakttype=body.kontrakttype,
        )
        for h in hits
    ]


# ---------------------------------------------------------------------------
# Regelverk — read-only view of YAML rules
# ---------------------------------------------------------------------------

def _format_condition(when: dict) -> str:
    """Convert a rule when-clause to a readable Norwegian condition string."""
    FIELD_LABELS = {
        "estimated_value": "Estimert verdi",
        "kontrakttype": "Kontrakttype",
        "oppdragsgiver": "Oppdragsgiver",
    }
    OP_SYMBOLS = {"lt": "<", "lte": "≤", "gt": ">", "gte": "≥", "eq": "="}
    VALUE_LABELS = {
        "vare_tjeneste": "varer/tjenester",
        "bygg_anlegg": "bygg og anlegg",
        "saerlige_tjenester": "særlige tjenester",
        "statlig": "statlig",
        "andre": "andre oppdragsgivere",
    }

    def _single(c: dict) -> str:
        field = FIELD_LABELS.get(c.get("field", ""), c.get("field", ""))
        op = OP_SYMBOLS.get(c.get("op", ""), c.get("op", ""))
        v = c.get("value", "")
        if c.get("field") == "estimated_value":
            try:
                v = f"{int(v):,}".replace(",", "\xa0") + " kr"
            except (TypeError, ValueError):
                v = str(v)
        else:
            v = VALUE_LABELS.get(str(v), str(v))
        return f"{field} {op} {v}"

    if not when:
        return "—"
    if "all" in when:
        return " · ".join(_single(c) for c in when["all"])
    if "field" in when:
        return _single(when)
    return "—"


@app.get("/api/regelverk", response_model=list[RegelverkRow])
def get_regelverk():
    """Return all rules from thresholds_2026.yaml as structured, readable JSON."""
    import yaml
    from pathlib import Path

    yaml_path = Path(__file__).parent.parent / "core" / "rules" / "data" / "thresholds_2026.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    today = date.today()
    result = []
    for rule in rules:
        vf = rule.get("valid_from")
        vt = rule.get("valid_to")
        active = vt is None or (hasattr(vt, "year") and vt >= today)
        result.append(RegelverkRow(
            id=rule["id"],
            regime=rule["regime"],
            condition=_format_condition(rule.get("when", {})),
            consequence=rule["consequence"],
            citation=rule.get("citation", ""),
            citation_url=rule.get("citation_url") or "",
            valid_from=str(vf) if vf else "",
            valid_to=str(vt) if vt else None,
            active=active,
        ))
    return result
