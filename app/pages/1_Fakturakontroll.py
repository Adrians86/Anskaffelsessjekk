import streamlit as st
from sqlmodel import select

from app.db import get_session, nok
from app.texts import RECOMMENDED_ACTIONS
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

    preselect_id = st.session_state.get("preselect_invoice")
    default_idx = list(labels.keys()).index(preselect_id) if preselect_id in labels else 0
    chosen = st.selectbox("Velg faktura", options=list(labels), format_func=labels.get, index=default_idx)

    auto_run = preselect_id is not None
    button_clicked = st.button("Kontroller faktura", type="primary") or auto_run

    if button_clicked:
        if "preselect_invoice" in st.session_state:
            del st.session_state.preselect_invoice

        inv = session.get(Invoice, chosen)
        result = check_invoice(session, inv, actor="demo-bruker")

        if result.verdict.value == "SAMSVAR":
            st.success("✅ SAMSVAR", icon="✓")
        elif result.verdict.value == "TIL_VURDERING":
            if result.verdi_funnet:
                st.warning(f"🟡 TIL VURDERING — {nok(result.verdi_funnet)} over avtalt", icon="⚠")
            else:
                st.warning("🟡 TIL VURDERING", icon="⚠")
        else:
            st.error(f"🔴 AVVIK — {nok(result.verdi_funnet)}", icon="✗")

        if not result.findings:
            st.success("Ingen funn. Fakturaen samsvarer med bestilling, mottak og "
                       "alle registrerte forpliktelser.")
        for f in result.findings:
            with st.container(border=True):
                if f.code.value == "INFORMAL_BASIS":
                    st.markdown(f"**📧 E-postavtale:** {f.message}")
                else:
                    st.markdown(f"{_SEV_ICON[f.severity]} **{f.message}**")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Grunnlag:** {f.citation}")
                with col2:
                    recommended = RECOMMENDED_ACTIONS.get(f.code.value, "Vurder med saksbehandler")
                    st.markdown(f"**Anbefalt handling:** {recommended}")

                if f.expected is not None:
                    st.markdown(f"**Avtalt:** {f.expected} · **Fakturert:** {f.actual}")
                if f.deviation_amount:
                    st.markdown(f"**Avvik:** {nok(f.deviation_amount)}")

        st.markdown("---")

        pdf_bytes = build_protokoll(session, inv)
        col_pdf, col_email = st.columns(2)
        with col_pdf:
            st.download_button(
                label="Last ned protokoll (PDF)",
                data=pdf_bytes,
                file_name=f"Anskaffelsesprotokoll_{inv.invoice_number}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        with col_email:
            st.link_button(
                "Book 20-min gjennomgang",
                "mailto:asliwa1986@gmail.com?subject=Anskaffelsessjekk%20gjennomgang",
                use_container_width=True
            )

        st.caption("Anbefaling — beslutningen tas av saksbehandler. "
                   "Kontrollen er logget i revisjonssporet.")

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i logistikk og innkjøp · asliwa1986@gmail.com · Syntetiske data")
