"""FastAPI wrapper around the core engine — Droga B Steg 1 (B1).

A thin HTTP layer over the existing core/ functions. The engine is UNCHANGED — this module
only marshals data to/from JSON. Streamlit continues to run independently.

Run: uvicorn api.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, timedelta
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import (
    Contract,
    Invoice,
    InvoiceDecision,
    InvoiceLine,
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
    version="0.1.0",
    description="Read-only API for the procurement control engine.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --- Response models ---

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
    invoices: list[InvoiceRow]
    contracts: list[dict]


# --- Helpers ---

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


# --- Endpoints ---

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
    # default: maned
    if today.month == 12:
        last = today.replace(day=31)
    else:
        last = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return (today.replace(day=1), last)


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(
    periode: str = Query("maned", description="maned|kvartal|ar|egendefinert"),
    fra: date | None = Query(None, description="Start date (egendefinert)"),
    til: date | None = Query(None, description="End date (egendefinert)"),
):
    """Portfolio KPIs and health bar percentages, filtered by period."""
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


@app.get("/api/invoices", response_model=list[InvoiceRow])
def list_invoices(
    verdict: str | None = Query(None, description="Filter: AVVIK, TIL_VURDERING, SAMSVAR"),
    status: str | None = Query(None, description="Filter: ny, under_kontroll, godkjent, avvist"),
    supplier_id: int | None = Query(None),
    search: str | None = Query(None, description="Search invoice_number or supplier name"),
    sort: str = Query("avvik_first", description="Sort: avvik_first, amount_desc, date_desc"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Paginated invoice list with filters and sorting."""
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
        rows = [r for r in rows
                if q in r.invoice_number.lower() or q in r.supplier_name.lower()]

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
    """Full invoice detail with findings (the WHY)."""
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if inv is None:
            raise HTTPException(404, "Faktura ikke funnet")
        result = evaluate_invoice(session, inv)
        sup = session.get(Supplier, inv.supplier_id)
        dec = _latest_decision(session, inv.id)
        status = _invoice_status(result.verdict.value, dec)
        lines = session.exec(
            select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id)
        ).all()
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


@app.get("/api/suppliers", response_model=list[SupplierRow])
def list_suppliers(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Supplier list with counts."""
    with get_session() as session:
        suppliers = session.exec(
            select(Supplier).where(Supplier.is_deleted == False)  # noqa: E712
        ).all()
        rows = []
        for sup in suppliers:
            n_inv = len(session.exec(
                select(Invoice).where(Invoice.supplier_id == sup.id)
            ).all())
            n_con = len(session.exec(
                select(Contract).where(Contract.supplier_id == sup.id)
                .where(Contract.is_deleted == False)  # noqa: E712
            ).all())
            rows.append(SupplierRow(
                id=sup.id,
                name=sup.name,
                org_number=sup.org_number,
                city=getattr(sup, "city", None),
                status=getattr(sup, "status", None),
                n_invoices=n_inv,
                n_contracts=n_con,
            ))
    if search:
        q = search.lower()
        rows = [r for r in rows if q in r.name.lower() or q in r.org_number]
    return rows[offset:offset + limit]


@app.get("/api/suppliers/{supplier_id}", response_model=SupplierDetail)
def get_supplier(supplier_id: int):
    """Supplier card with invoices and contracts."""
    with get_session() as session:
        sup = session.get(Supplier, supplier_id)
        if sup is None or getattr(sup, "is_deleted", False):
            raise HTTPException(404, "Leverandør ikke funnet")
        invoices = session.exec(
            select(Invoice).where(Invoice.supplier_id == sup.id)
        ).all()
        inv_rows = [_build_invoice_row(session, inv) for inv in invoices]
        contracts = session.exec(
            select(Contract).where(Contract.supplier_id == sup.id)
            .where(Contract.is_deleted == False)  # noqa: E712
        ).all()
        con_dicts = [
            {"id": c.id, "reference": c.reference, "title": c.title,
             "valid_from": str(c.valid_from), "status": getattr(c, "status", None)}
            for c in contracts
        ]
        return SupplierDetail(
            id=sup.id,
            name=sup.name,
            org_number=sup.org_number,
            address=getattr(sup, "address", None),
            postal_code=getattr(sup, "postal_code", None),
            city=getattr(sup, "city", None),
            website=getattr(sup, "website", None),
            email=getattr(sup, "email", None),
            phone=getattr(sup, "phone", None),
            status=getattr(sup, "status", None),
            invoices=inv_rows,
            contracts=con_dicts,
        )
