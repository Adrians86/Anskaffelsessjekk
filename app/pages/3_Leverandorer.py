import streamlit as st
from sqlmodel import select
import pandas as pd

from db import get_session, nok
from chrome import header, footer
from ui_forpliktelser import render_email_commitment
from core.models import AuditLog, Commitment, Contract, ContractLine, Invoice, Supplier
from core.reporting import check_invoice

st.set_page_config(page_title="Leverandører", page_icon="🏢", layout="wide")
header()
st.title("Leverandører")
st.caption("Hvilke leverandører genererer flest avvik — ta det opp med kilden, "
           "ikke bare symptomene. (First Time Right)")


@st.cache_data
def supplier_stats():
    rows = []
    with get_session() as session:
        suppliers = session.exec(select(Supplier)).all()
        for sup in suppliers:
            contracts = session.exec(
                select(Contract).where(Contract.supplier_id == sup.id)
            ).all()
            invoices = session.exec(
                select(Invoice).where(Invoice.supplier_id == sup.id)
            ).all()

            n_findings = 0
            verdi = 0.0
            invoices_with_findings = 0
            for inv in invoices:
                result = check_invoice(session, inv, actor="leverandoroversikt")
                if result.findings:
                    invoices_with_findings += 1
                n_findings += len(result.findings)
                verdi += float(result.verdi_funnet)

            andel = (invoices_with_findings / len(invoices) * 100) if invoices else 0.0
            rows.append({
                "Navn": sup.name,
                "Org.nr": sup.org_number,
                "Avtaler": len(contracts),
                "Fakturaer": len(invoices),
                "Funn": n_findings,
                "_verdi": verdi,
                "Verdi funnet": nok(verdi),
                "Andel m/ funn": f"{andel:.0f} %",
            })
    rows.sort(key=lambda r: r["_verdi"], reverse=True)
    return rows


rows = supplier_stats()

if not rows:
    st.info("Ingen leverandører registrert.")
else:
    df = pd.DataFrame(rows)[
        ["Navn", "Org.nr", "Avtaler", "Fakturaer", "Funn", "Verdi funnet", "Andel m/ funn"]
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)

    total_verdi = sum(r["_verdi"] for r in rows)
    st.caption(f"Total verdi funnet på tvers av leverandører: **{nok(total_verdi)}**")

    # --- V6: Leverandørkort drill-down ----------------------------------------
    st.divider()
    st.subheader("Leverandørkort")
    chosen_name = st.selectbox("Åpne leverandørkort", options=[r["Navn"] for r in rows])

    def _verdict_pill(v: str) -> str:
        colors = {"AVVIK": "#C62828", "TIL_VURDERING": "#B58900", "SAMSVAR": "#2E7D32"}
        label = {"AVVIK": "🔴 AVVIK", "TIL_VURDERING": "🟡 TIL VURDERING",
                 "SAMSVAR": "✓ SAMSVAR"}[v]
        return f'<span style="color:{colors[v]};font-weight:600">{label}</span>'

    with get_session() as session:
        sup = session.exec(select(Supplier).where(Supplier.name == chosen_name)).first()

        # (a) header
        st.markdown(
            f'### {sup.name} '
            '<span style="background:#F1F3F5;color:#6B7280;font-size:11px;font-weight:600;'
            'padding:2px 10px;border-radius:10px;vertical-align:middle">SYNTETISK</span>',
            unsafe_allow_html=True,
        )
        st.caption(f"Org.nr {sup.org_number}")

        # (b) Avtaler
        st.markdown("**Avtaler**")
        contracts = session.exec(
            select(Contract).where(Contract.supplier_id == sup.id)
        ).all()
        if contracts:
            for c in contracts:
                n_lines = len(session.exec(
                    select(ContractLine).where(ContractLine.contract_id == c.id)
                ).all())
                st.markdown(f"- **{c.reference}** · {c.title} · {c.valid_from} → {c.valid_to} · "
                            f"ramme {nok(c.total_value)} · {n_lines} linjer")
        else:
            st.caption("Ingen kontrakter registrert.")

        # (c) Forpliktelser (reuse V1 rendering for e-mail commitments)
        st.markdown("**Forpliktelser**")
        commitments = session.exec(
            select(Commitment).where(Commitment.supplier_id == sup.id)
        ).all()
        if commitments:
            for cm in commitments:
                if cm.source_type.value == "EMAIL":
                    render_email_commitment(cm)
                else:
                    st.info(f"{cm.item_ref}: {cm.condition_type.value} = "
                            f"{nok(cm.value) if cm.value is not None else '—'} · Kilde: {cm.source_ref}")
        else:
            st.caption("Ingen registrerte tilleggsforpliktelser.")

        # (d) Fakturaer
        st.markdown("**Fakturaer**")
        invoices = session.exec(
            select(Invoice).where(Invoice.supplier_id == sup.id).order_by(Invoice.invoice_number)
        ).all()
        sup_verdi = 0.0
        n_with_findings = 0
        for inv in invoices:
            r = check_invoice(session, inv, actor="leverandorkort")
            sup_verdi += float(r.verdi_funnet)
            if r.findings:
                n_with_findings += 1
            col1, col2, col3, col4, col5, col6 = st.columns([1.4, 1.4, 1.5, 2, 1.5, 1])
            col1.text(inv.invoice_number)
            col2.text(str(inv.invoice_date))
            col3.text(nok(inv.total_ex_vat))
            col4.markdown(_verdict_pill(r.verdict.value), unsafe_allow_html=True)
            col5.text(nok(r.verdi_funnet) if r.verdi_funnet else "—")
            if col6.button("Åpne →", key=f"levopen_{inv.id}"):
                st.session_state.preselect_invoice = inv.id
                st.switch_page("pages/1_Fakturakontroll.py")

        # (e) Nøkkeltall
        st.markdown("**Nøkkeltall**")
        andel = (n_with_findings / len(invoices) * 100) if invoices else 0.0
        ftr = (1 - n_with_findings / len(invoices)) * 100 if invoices else 100.0
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Fakturaer", len(invoices))
        k2.metric("Andel m/ funn", f"{andel:.0f} %")
        k3.metric("Verdi funnet", nok(sup_verdi))
        k4.metric("First Time Right", f"{ftr:.0f} %")

        # (f) Siste hendelser for this supplier
        st.markdown("**Siste hendelser**")
        inv_entities = {f"invoice:{inv.id}" for inv in invoices}
        events = [e for e in session.exec(
            select(AuditLog).order_by(AuditLog.created_at.desc())
        ).all() if e.entity in inv_entities][:8]
        if events:
            for e in events:
                st.caption(f"**{e.created_at.strftime('%H:%M')}** — {e.actor}: {e.action} "
                           f"({e.entity}) · {e.detail}")
        else:
            st.caption("Ingen hendelser for denne leverandøren ennå.")

footer()
