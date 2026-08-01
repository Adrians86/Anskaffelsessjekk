"""Arbeidsflate — concise landing: actions + KPIs + top urgent items + worklist link.

W1: the landing page is NOT a wall of invoices. It shows actions, counters, the 3–5 most
pressing items (avvik first), and a link to the dedicated worklist (Arbeidsliste).
"""
from html import escape

import streamlit as st
from db import get_session, money, nok
from sqlmodel import select
from ui_common import verdict_pill

from core.matching.currency import is_foreign
from core.models import AuditLog, Invoice, InvoiceDecision, Supplier
from core.reporting import evaluate_invoice

st.set_page_config(page_title="Arbeidsflate", page_icon="📊", layout="wide")

from chrome import footer, header, page_header  # noqa: E402

header()

page_header(
    "Kontrolloversikt", "Arbeidsflate",
    "Full oversikt over kontrollstatus — hva som krever deg, og hva som er i orden.",
    chip="Syntetiske data · regelverk per 01.07.2026",
)

# Actions first (U7)
_act = st.columns(3)
if _act[0].button("⬆ Last opp faktura (EHF)", use_container_width=True):
    st.switch_page("pages/1_Fakturakontroll.py")
if _act[1].button("✎ Registrer forpliktelse", use_container_width=True):
    st.switch_page("pages/2_Avtaler_og_forpliktelser.py")
if _act[2].button("⚖ Kjør terskelsjekk", use_container_width=True):
    st.switch_page("pages/4_Terskelsjekk.py")
st.markdown("---")


@st.cache_data
def compute_portfolio_stats():
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        counts = {"SAMSVAR": 0, "TIL_VURDERING": 0, "AVVIK": 0}
        total_verdi = 0
        n_foreign = 0

        for inv in invoices:
            result = evaluate_invoice(session, inv)
            counts[result.verdict.value] += 1
            if result.verdi_funnet:
                total_verdi += float(result.verdi_funnet)
            if is_foreign(inv):
                n_foreign += 1

        return {
            "total_invoices": len(invoices),
            "counts": counts,
            "total_verdi": total_verdi,
            "n_foreign": n_foreign,
        }


@st.cache_data
def _urgent_rows():
    """Top 5 urgent invoices (avvik first, then amount desc) for the landing page."""
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        rows = []
        for inv in invoices:
            result = evaluate_invoice(session, inv)
            if result.verdict.value == "SAMSVAR":
                continue
            sup = session.get(Supplier, inv.supplier_id)
            dec = session.exec(
                select(InvoiceDecision)
                .where(InvoiceDecision.invoice_id == inv.id)
                .order_by(InvoiceDecision.created_at.desc(), InvoiceDecision.id.desc())
            ).first()
            if dec is not None and dec.decision in ("godkjent", "avvist"):
                continue
            finding_text = ""
            if result.findings:
                f = result.findings[0]
                prefix = "📧 " if f.code.value == "INFORMAL_BASIS" else ""
                finding_text = prefix + f.message[:55]
            rows.append({
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "supplier_name": sup.name,
                "amount": money(inv.total_ex_vat, inv.currency),
                "amount_raw": float(inv.total_ex_vat),
                "verdict": result.verdict.value,
                "finding": finding_text,
            })
        order = {"AVVIK": 0, "TIL_VURDERING": 1}
        rows.sort(key=lambda r: (order.get(r["verdict"], 2), -r["amount_raw"]))
        return rows[:5]


stats = compute_portfolio_stats()

# KPI editorial strip (variant C)
_verdi_txt = nok(stats["total_verdi"]) if stats["total_verdi"] > 0 else "0 kr"
_kpi_cells = [
    ("", "Kontrollert", str(stats["total_invoices"])),
    ("err", "Avvik", str(stats["counts"]["AVVIK"])),
    ("warn", "Til vurdering", str(stats["counts"]["TIL_VURDERING"])),
    ("ok", "Samsvar", str(stats["counts"]["SAMSVAR"])),
    ("gold", "Verdi funnet", _verdi_txt),
]
st.markdown(
    '<div class="as-kpis">'
    + "".join(
        f'<div class="as-kpi {cls}"><div class="as-kpi-label">{escape(label)}</div>'
        f'<div class="as-kpi-val">{escape(val)}</div></div>'
        for cls, label, val in _kpi_cells
    )
    + '</div>',
    unsafe_allow_html=True,
)

if stats.get("n_foreign"):
    st.info(f"{stats['n_foreign']} faktura(er) i utenlandsk valuta — krever manuell vurdering. "
            "Inngår ikke i «Verdi funnet» (NOK).")

st.markdown("---")

# Portfolio health bar
total = stats["total_invoices"]
if total > 0:
    pct_err = (stats["counts"]["AVVIK"] / total) * 100
    pct_warn = (stats["counts"]["TIL_VURDERING"] / total) * 100
    pct_ok = (stats["counts"]["SAMSVAR"] / total) * 100

    col_bar, col_legend = st.columns([4, 1])
    with col_bar:
        st.write("**Porteføljehelse**")
        bar_html = (
            '<div style="display:flex;height:12px;border-radius:6px;overflow:hidden;margin:8px 0">'
            f'<div style="width:{pct_err}%;background:#C62828"></div>'
            f'<div style="width:{pct_warn}%;background:#B58900"></div>'
            f'<div style="width:{pct_ok}%;background:#2E7D32"></div>'
            '</div>'
        )
        st.markdown(bar_html, unsafe_allow_html=True)
    with col_legend:
        st.caption(
            f"● {stats['counts']['AVVIK']} avvik · "
            f"{stats['counts']['TIL_VURDERING']} til vurdering · "
            f"{stats['counts']['SAMSVAR']} samsvar"
        )

st.markdown("---")

# W1 — Top urgent items (max 5, avvik first) + link to full worklist
urgent = _urgent_rows()

col_title, col_link = st.columns([3, 1])
with col_title:
    st.write("**Krever handling**")
with col_link:
    if st.button("→ Åpne arbeidsliste", type="primary", use_container_width=True):
        st.switch_page("pages/8_Arbeidsliste.py")

if urgent:
    for row in urgent:
        c1, c2, c3, c4, c5 = st.columns([1.2, 2.2, 1.4, 2.5, 0.8])
        with c1:
            st.text(row["invoice_number"])
        with c2:
            st.text(row["supplier_name"])
        with c3:
            st.markdown(verdict_pill(row["verdict"]), unsafe_allow_html=True)
        with c4:
            st.caption(row["finding"])
        with c5:
            if st.button("Åpne →", key=f"home_open_{row['invoice_id']}",
                         use_container_width=True):
                st.session_state.preselect_invoice = row["invoice_id"]
                st.switch_page("pages/1_Fakturakontroll.py")
else:
    st.markdown(
        '<div style="text-align:center;padding:24px 16px;color:#5A6673">'
        '<div style="font-size:32px;margin-bottom:6px">🎯</div>'
        '<div style="font-size:14px;font-weight:600">Alt er kontrollert</div>'
        '<div style="font-size:12px;margin-top:3px">'
        'Ingen fakturaer krever handling akkurat nå.</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# Events feed (compact)
st.markdown('<div class="as-panel-title">Siste hendelser</div>', unsafe_allow_html=True)
with get_session() as session:
    events = session.exec(select(AuditLog).order_by(AuditLog.created_at.desc())).all()[:8]
    if events:
        feed_rows = "".join(
            f'<div class="as-feed-row"><time>{escape(e.created_at.strftime("%H:%M"))}</time>'
            f'{escape(e.actor)}: {escape(e.action)} '
            f'<span style="color:#5A6673">({escape(e.entity)})</span></div>'
            for e in events
        )
    else:
        feed_rows = '<div class="as-feed-row">Ingen hendelser ennå.</div>'
st.markdown(f'<div class="as-feed">{feed_rows}</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer er generert. "
           "Ingen reelle data inngår.")
footer()
