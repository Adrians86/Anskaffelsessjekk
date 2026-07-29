from html import escape

import streamlit as st
from db import get_session, money, nok
from sqlmodel import select
from texts import RECOMMENDED_ACTIONS
from ui_common import verdict_pill

from core.matching.currency import is_foreign
from core.models import AuditLog, Invoice, Supplier
from core.reporting import evaluate_invoice

st.set_page_config(page_title="Arbeidsflate", page_icon="📊", layout="wide")

from chrome import footer, header, page_header  # noqa: E402

header()

page_header(
    "Kontrolloversikt", "Arbeidsflate",
    "Full oversikt over kontrollstatus — hva som krever deg, og hva som er i orden.",
    chip="Syntetiske data · regelverk per 01.07.2026",
)

# U7 — actions first: the three primary tasks right at the top.
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
    """Compute all portfolio metrics (cached)."""
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
def queue_rows():
    """Fakturakø rows (cached, read-only). evaluate_invoice never writes."""
    with get_session() as session:
        invoices = session.exec(select(Invoice).order_by(Invoice.invoice_number)).all()
        rows = []
        for inv in invoices:
            result = evaluate_invoice(session, inv)
            sup = session.get(Supplier, inv.supplier_id)
            finding_text = "—"
            if result.findings:
                f = result.findings[0]
                prefix = "📧 " if f.code.value == "INFORMAL_BASIS" else ""
                finding_text = prefix + f.message[:60]
            rows.append({
                "invoice": inv.invoice_number, "supplier": sup.name,
                "amount": money(inv.total_ex_vat, inv.currency), "status": result.verdict.value,
                "finding": finding_text, "invoice_id": inv.id,
            })
        return rows


@st.cache_data
def action_items():
    """"Krever handling" worklist rows (cached, read-only)."""
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        items = []
        for inv in invoices:
            result = evaluate_invoice(session, inv)
            for finding in result.findings:
                if finding.severity.value in ["WARN", "DEVIATION"]:
                    items.append({
                        "invoice": inv.invoice_number, "message": finding.message,
                        "recommended": RECOMMENDED_ACTIONS.get(
                            finding.code.value, "Vurder med saksbehandler"),
                    })
        return items


stats = compute_portfolio_stats()

# KPI editorial strip (variant C) — one connected strip with hairline dividers, not loose cards.
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

# Porteføljehelse bar (horizontal stacked)
total = stats["total_invoices"]
if total > 0:
    pct_err = (stats["counts"]["AVVIK"] / total) * 100
    pct_warn = (stats["counts"]["TIL_VURDERING"] / total) * 100
    pct_ok = (stats["counts"]["SAMSVAR"] / total) * 100

    col_bar, col_legend = st.columns([4, 1])
    with col_bar:
        st.write("**Porteføljehelse**")
        bar_html = f"""
        <div style="display:flex;height:12px;border-radius:6px;overflow:hidden;margin:8px 0">
            <div style="width:{pct_err}%;background:#C62828"></div>
            <div style="width:{pct_warn}%;background:#B58900"></div>
            <div style="width:{pct_ok}%;background:#2E7D32"></div>
        </div>
        """
        st.markdown(bar_html, unsafe_allow_html=True)
    with col_legend:
        st.caption(f"● {stats['counts']['AVVIK']} avvik · {stats['counts']['TIL_VURDERING']} til vurdering · {stats['counts']['SAMSVAR']} samsvar")

st.markdown("---")

# Fakturakø with tabs
st.write("**Fakturakø**")

rows = queue_rows()

# Tabs for filtering
tab_names = ["Alle", "Avvik", "Til vurdering", "Samsvar"]
tab_filters = [None, "AVVIK", "TIL_VURDERING", "SAMSVAR"]

tabs = st.tabs([f"{name} ({sum(1 for r in rows if r['status'] == f or f is None)})"
                for name, f in zip(tab_names, tab_filters, strict=True)])

for tab_idx, (tab, filter_status) in enumerate(zip(tabs, tab_filters, strict=True)):
    with tab:
        filtered_rows = [r for r in rows if filter_status is None or r["status"] == filter_status]

        for row in filtered_rows[:8]:  # Show first 8
            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2.5, 1.5, 1.2, 2, 0.8])
            with col1:
                st.text(row["invoice"])
            with col2:
                st.text(row["supplier"])
            with col3:
                st.text(row["amount"])
            with col4:
                st.markdown(verdict_pill(row["status"]), unsafe_allow_html=True)
            with col5:
                st.caption(row["finding"])
            with col6:
                if st.button("Åpne →", key=f"open_{tab_idx}_{row['invoice_id']}", use_container_width=True):
                    st.session_state.preselect_invoice = row["invoice_id"]
                    st.switch_page("pages/1_Fakturakontroll.py")

st.markdown("---")

# Worklist ("Krever handling") and "Siste hendelser" side by side (variant C).
col_work, col_feed = st.columns([3, 2], gap="large")

with col_work:
    st.markdown('<div class="as-panel-title">Krever handling</div>', unsafe_allow_html=True)
    items = action_items()
    if items:
        for idx, item in enumerate(items[:10]):  # Show first 10
            c1, c2 = st.columns([0.6, 6])
            with c1:
                st.checkbox("Kvitter", key=f"action_{idx}", label_visibility="collapsed")
            with c2:
                st.markdown(f"**{item['invoice']}** — {item['message'][:44]}")
                st.caption(f"Anbefalt: {item['recommended']}")
    else:
        st.caption("Ingen funn som krever handling — alle fakturaer er i orden.")

with col_feed:
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

st.caption("**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer er generert. Ingen reelle data inngår.")

footer()
