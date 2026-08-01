"""Funksjon 6 — Arbeidsliste: dedicated worklist for 100+ invoices.

Compact HTML table (not N Streamlit widgets), pagination 25/page, filters (verdict/supplier/
date/status), search, default sort avvik first then amount descending.
"""
from html import escape

import streamlit as st
from chrome import footer, header, page_header
from db import dato, get_session, money
from sqlmodel import select
from ui_common import verdict_pill

from core.models import Invoice, InvoiceDecision, Supplier
from core.reporting import evaluate_invoice

st.set_page_config(page_title="Arbeidsliste", page_icon="📋", layout="wide")
header()
page_header(
    "Kontroll", "Arbeidsliste",
    "Alle fakturaer — filtrer, søk og kontroller. Avvik øverst.",
)

PAGE_SIZE = 25

_STATUS_LABELS = {
    "ny": ("Ny", "#5A6673", "#F1F3F5"),
    "under_kontroll": ("Under kontroll", "#B58900", "#FCF4DE"),
    "godkjent": ("Godkjent", "#2E7D32", "#E8F4E8"),
    "avvist": ("Avvist", "#C62828", "#FBEAEA"),
}


def _status_chip(status: str) -> str:
    label, fg, bg = _STATUS_LABELS.get(status, (status, "#5A6673", "#F1F3F5"))
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:700;'
            f'padding:2px 8px;border-radius:10px;white-space:nowrap">{escape(label)}</span>')


def _invoice_status(verdict_value: str, decision: InvoiceDecision | None) -> str:
    if decision is not None:
        return decision.decision  # godkjent | avvist | vent → mapped to godkjent/avvist
    if verdict_value in ("AVVIK", "TIL_VURDERING"):
        return "under_kontroll"
    return "ny"


@st.cache_data
def _build_rows():
    with get_session() as session:
        invoices = session.exec(select(Invoice).order_by(Invoice.invoice_number)).all()
        rows = []
        for inv in invoices:
            result = evaluate_invoice(session, inv)
            sup = session.get(Supplier, inv.supplier_id)
            dec = session.exec(
                select(InvoiceDecision)
                .where(InvoiceDecision.invoice_id == inv.id)
                .order_by(InvoiceDecision.created_at.desc(), InvoiceDecision.id.desc())
            ).first()
            status = _invoice_status(result.verdict.value, dec)
            finding_text = ""
            if result.findings:
                f = result.findings[0]
                prefix = "📧 " if f.code.value == "INFORMAL_BASIS" else ""
                finding_text = prefix + f.message[:55]
            rows.append({
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "supplier_name": sup.name,
                "supplier_id": sup.id,
                "amount": money(inv.total_ex_vat, inv.currency),
                "amount_raw": float(inv.total_ex_vat),
                "date": inv.invoice_date,
                "date_str": dato(inv.invoice_date),
                "verdict": result.verdict.value,
                "status": status,
                "finding": finding_text,
                "currency": inv.currency,
            })
        return rows


rows = _build_rows()

# --- Filters ---
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    search = st.text_input("Søk (fakturanr / leverandør)", key="wl_search",
                           placeholder="F-1003, Hydraulikk…")
with fc2:
    verdict_opts = ["Alle", "AVVIK", "TIL_VURDERING", "SAMSVAR"]
    verdict_filter = st.selectbox("Verdikt", verdict_opts, key="wl_verdict")
with fc3:
    status_opts = ["Alle", "ny", "under_kontroll", "godkjent", "avvist"]
    status_labels = {"Alle": "Alle", "ny": "Ny", "under_kontroll": "Under kontroll",
                     "godkjent": "Godkjent", "avvist": "Avvist"}
    status_filter = st.selectbox("Status", status_opts,
                                 format_func=status_labels.get, key="wl_status")
with fc4:
    suppliers = sorted({r["supplier_name"] for r in rows})
    supplier_filter = st.selectbox("Leverandør", ["Alle"] + suppliers, key="wl_supplier")

filtered = rows
if search:
    q = search.lower()
    filtered = [r for r in filtered
                if q in r["invoice_number"].lower() or q in r["supplier_name"].lower()]
if verdict_filter != "Alle":
    filtered = [r for r in filtered if r["verdict"] == verdict_filter]
if status_filter != "Alle":
    filtered = [r for r in filtered if r["status"] == status_filter]
if supplier_filter != "Alle":
    filtered = [r for r in filtered if r["supplier_name"] == supplier_filter]

# Sort: avvik first, then amount descending
_SORT_ORDER = {"AVVIK": 0, "TIL_VURDERING": 1, "SAMSVAR": 2}
filtered.sort(key=lambda r: (_SORT_ORDER.get(r["verdict"], 3), -r["amount_raw"]))

total = len(filtered)
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
page = st.session_state.get("wl_page", 1)
if page > total_pages:
    page = total_pages
page_rows = filtered[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

# --- Summary ---
st.caption(f"Viser {len(page_rows)} av {total} faktura(er) · side {page}/{total_pages}")

if not filtered:
    st.markdown(
        '<div style="text-align:center;padding:40px 20px;color:#5A6673">'
        '<div style="font-size:40px;margin-bottom:8px">🎯</div>'
        '<div style="font-size:16px;font-weight:600">Alt er kontrollert</div>'
        '<div style="font-size:13px;margin-top:4px">'
        'Ingen fakturaer matcher filteret.</div></div>',
        unsafe_allow_html=True,
    )
else:
    # Compact HTML table
    header_html = (
        '<table style="width:100%;border-collapse:collapse;font-size:13px">'
        '<thead><tr style="border-bottom:2px solid #E4E1D8;text-align:left">'
        '<th style="padding:6px 8px">Fakturanr</th>'
        '<th style="padding:6px 8px">Leverandør</th>'
        '<th style="padding:6px 8px">Beløp</th>'
        '<th style="padding:6px 8px">Dato</th>'
        '<th style="padding:6px 8px">Verdikt</th>'
        '<th style="padding:6px 8px">Status</th>'
        '<th style="padding:6px 8px">Viktigste funn</th>'
        '</tr></thead><tbody>'
    )
    row_htmls = []
    for r in page_rows:
        row_htmls.append(
            f'<tr style="border-bottom:1px solid #E4E1D8">'
            f'<td style="padding:6px 8px;font-weight:600">{escape(r["invoice_number"])}</td>'
            f'<td style="padding:6px 8px">{escape(r["supplier_name"])}</td>'
            f'<td style="padding:6px 8px;white-space:nowrap">{escape(r["amount"])}</td>'
            f'<td style="padding:6px 8px;white-space:nowrap">{escape(r["date_str"])}</td>'
            f'<td style="padding:6px 8px">{verdict_pill(r["verdict"])}</td>'
            f'<td style="padding:6px 8px">{_status_chip(r["status"])}</td>'
            f'<td style="padding:6px 8px;color:#5A6673;font-size:12px">'
            f'{escape(r["finding"])}</td>'
            f'</tr>'
        )
    st.markdown(header_html + "".join(row_htmls) + "</tbody></table>", unsafe_allow_html=True)

    # Open buttons — one row per invoice in the visible page
    st.markdown("")
    cols = st.columns(min(len(page_rows), 5))
    for i, r in enumerate(page_rows):
        with cols[i % len(cols)]:
            if st.button(f"Åpne {r['invoice_number']}", key=f"wl_open_{r['invoice_id']}",
                         use_container_width=True):
                st.session_state.preselect_invoice = r["invoice_id"]
                st.switch_page("pages/1_Fakturakontroll.py")

# --- Pagination ---
if total_pages > 1:
    pc1, pc2, pc3 = st.columns([1, 2, 1])
    with pc1:
        if page > 1 and st.button("← Forrige", key="wl_prev"):
            st.session_state.wl_page = page - 1
            st.rerun()
    with pc2:
        new_page = st.number_input("Side", min_value=1, max_value=total_pages,
                                   value=page, key="wl_page_input", label_visibility="collapsed")
        if new_page != page:
            st.session_state.wl_page = new_page
            st.rerun()
    with pc3:
        if page < total_pages and st.button("Neste →", key="wl_next"):
            st.session_state.wl_page = page + 1
            st.rerun()

st.markdown("---")
st.caption("**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer er generert.")
footer()
