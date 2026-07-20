import streamlit as st
from db import get_session, nok
from sqlmodel import select
from texts import RECOMMENDED_ACTIONS
from ui_common import verdict_pill

from core.models import AuditLog, Invoice, Supplier
from core.reporting import evaluate_invoice

st.set_page_config(page_title="Arbeidsflate", page_icon="📊", layout="wide")

from chrome import footer, header  # noqa: E402

header()

st.markdown("## Arbeidsflate")
st.markdown('<span style="font-size:12px;color:#8A94A0">Demo · syntetiske data · regelverk per 01.07.2026</span>', unsafe_allow_html=True)
st.markdown("Full oversikt over kontrollstatus — hva som krever deg, og hva som er i orden.")

@st.cache_data
def compute_portfolio_stats():
    """Compute all portfolio metrics (cached)."""
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        counts = {"SAMSVAR": 0, "TIL_VURDERING": 0, "AVVIK": 0}
        total_verdi = 0

        for inv in invoices:
            result = evaluate_invoice(session, inv)
            counts[result.verdict.value] += 1
            if result.verdi_funnet:
                total_verdi += float(result.verdi_funnet)

        return {
            "total_invoices": len(invoices),
            "counts": counts,
            "total_verdi": total_verdi
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
                "amount": nok(inv.total_ex_vat), "status": result.verdict.value,
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

# KPI strip (5 containers)
cols = st.columns(5)
with cols[0]:
    st.metric("Kontrollert", stats["total_invoices"])
with cols[1]:
    st.metric("Avvik", stats["counts"]["AVVIK"])
with cols[2]:
    st.metric("Til vurdering", stats["counts"]["TIL_VURDERING"])
with cols[3]:
    st.metric("Samsvar", stats["counts"]["SAMSVAR"])
with cols[4]:
    st.metric("Verdi funnet", nok(stats["total_verdi"]) if stats["total_verdi"] > 0 else "0 kr")

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

# Action tiles (3, gold left border)
cols = st.columns(3)
with cols[0]:
    if st.button("⬆ Last opp faktura (EHF)", use_container_width=True):
        st.switch_page("pages/1_Fakturakontroll.py")
    st.caption("Kontroller en faktura mot hele forpliktelsesbildet")

with cols[1]:
    if st.button("✎ Registrer forpliktelse", use_container_width=True):
        st.switch_page("pages/2_Avtaler_og_forpliktelser.py")
    st.caption("Avtale, e-postavtale eller annen betingelse")

with cols[2]:
    if st.button("⚖ Kjør terskelsjekk", use_container_width=True):
        st.switch_page("pages/4_Terskelsjekk.py")
    st.caption("Riktig regime og prosedyre — med paragraf")

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

# "Krever handling" section (WARN or DEVIATION findings as actionable rows)
st.write("**Krever handling**")

items = action_items()
if items:
    for idx, item in enumerate(items[:10]):  # Show first 10
        col1, col2, col3 = st.columns([1, 2, 3])
        with col1:
            st.checkbox("Kvitter", key=f"action_{idx}", label_visibility="collapsed")
        with col2:
            st.text(f"{item['invoice']} — {item['message'][:40]}")
        with col3:
            st.caption(f"**Anbefalt:** {item['recommended']}")
else:
    st.caption("Ingen funn som krever handling — alle fakturaer er i orden.")

st.markdown("---")

# "Siste hendelser" feed (last 8 AuditLog entries)
st.write("**Siste hendelser**")

with get_session() as session:
    events = session.exec(select(AuditLog).order_by(AuditLog.created_at.desc())).all()[:8]

    if events:
        for event in events:
            st.caption(f"**{event.created_at.strftime('%H:%M')}** — {event.actor}: {event.action} ({event.entity})")
    else:
        st.caption("Ingen hendelser ennå.")

st.markdown("---")

st.caption("**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer er generert. Ingen reelle data inngår.")

footer()
