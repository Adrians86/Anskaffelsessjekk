import streamlit as st
from sqlmodel import select

from db import get_session, nok
from core.matching.findings import Severity
from core.models import Invoice, Supplier
from core.reporting import check_invoice, build_protokoll

st.set_page_config(page_title="Fakturakontroll", page_icon="🧾", layout="wide")
st.title("Fakturakontroll")

_SEV_ICON = {Severity.DEVIATION: "🔴", Severity.WARN: "🟡", Severity.INFO: "ℹ️"}

with get_session() as session:
    invoices = session.exec(select(Invoice).order_by(Invoice.invoice_number)).all()
    labels = {}
    for inv in invoices:
        sup = session.get(Supplier, inv.supplier_id)
        labels[inv.id] = f"{inv.invoice_number} — {sup.name} — {nok(inv.total_ex_vat)}"

    chosen = st.selectbox("Velg faktura", options=list(labels), format_func=labels.get)

    if st.button("Kontroller faktura", type="primary"):
        inv = session.get(Invoice, chosen)
        result = check_invoice(session, inv, actor="demo-bruker")

        if result.verdict.value == "SAMSVAR":
            st.success("✅ SAMSVAR", icon="✓")
        elif result.verdict.value == "TIL_VURDERING":
            st.warning("🟡 TIL VURDERING", icon="⚠")
        else:
            st.error("🔴 AVVIK", icon="✗")

        if result.verdi_funnet:
            st.metric("Verdi funnet (avvik)", nok(result.verdi_funnet))

        if not result.findings:
            st.success("Ingen funn. Fakturaen samsvarer med bestilling, mottak og "
                       "alle registrerte forpliktelser.")
        for f in result.findings:
            st.markdown(f"{_SEV_ICON[f.severity]} **{f.message}**")
            with st.expander("Hvorfor?"):
                st.markdown(f"**Grunnlag:** {f.citation}")
                if f.expected is not None:
                    st.markdown(f"**Avtalt:** {f.expected} · **Fakturert:** {f.actual}")
                if f.deviation_amount:
                    st.markdown(f"**Avvik:** {nok(f.deviation_amount)}")
                st.caption(f"Funnkode: {f.code.value} · Alvorlighet: {f.severity.value}")

        st.caption("Anbefaling — beslutningen tas av saksbehandler. "
                   "Kontrollen er logget i revisjonssporet.")

        pdf_bytes = build_protokoll(session, inv)
        st.download_button(
            label="📥 Last ned protokoll (PDF)",
            data=pdf_bytes,
            file_name=f"Anskaffelsesprotokoll_{inv.invoice_number}.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Syntetiske data")
