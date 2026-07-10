import streamlit as st
from sqlmodel import select

from app.db import get_session, nok
from core.models import Invoice, Supplier
from core.reporting import check_invoice

st.set_page_config(page_title="Anskaffelsessjekk", page_icon="✅", layout="centered")

st.title("Anskaffelsessjekk")
st.markdown('<div style="border-bottom: 3px solid #B08D2E; margin: -10px 0 20px 0;"></div>', unsafe_allow_html=True)

st.markdown("**Kontroll av fakturaer mot rammeavtaler, e-postavtaler og regelverket 2026 — med full sporbarhet.**")

st.markdown("---")

with get_session() as session:
    invoices = session.exec(select(Invoice)).all()
    f1003 = next((inv for inv in invoices if inv.invoice_number == "F-1003"), None)

    if f1003:
        supplier = session.get(Supplier, f1003.supplier_id)
        check = check_invoice(session, f1003, actor="homepage-demo")

        col1, col2 = st.columns([2, 1])
        with col1:
            with st.container(border=True):
                if check.verdict.value == "SAMSVAR":
                    st.success("✅ SAMSVAR", icon="✓")
                elif check.verdict.value == "TIL_VURDERING":
                    st.warning("🟡 TIL VURDERING — 12 000 kr over avtalt", icon="⚠")
                else:
                    st.error(f"🔴 AVVIK — {nok(check.verdi_funnet)}", icon="✗")

                st.markdown("**Prisskandal.**")
                if check.findings:
                    f = check.findings[0]
                    story = "Systemet fant at " + (
                        "prisen avvek fra rammeavtalen — fant e-postavtalen fra 12. juni (J. Hansen). Krever formalisering."
                        if f.code.value == "PRICE_ABOVE_AGREED"
                        else f.message.lower()
                    )
                    st.markdown(story)

                if st.button("Se hele analysen →", type="primary", use_container_width=True):
                    st.session_state.preselect_invoice = f1003.id
                    st.switch_page("app/pages/1_Fakturakontroll.py")

        with col2:
            total_verdi = sum(float(inv.total_ex_vat) for inv in invoices)
            st.metric("Verdi funnet", nok(check.verdi_funnet) if check.verdi_funnet else "0 kr")

    st.markdown("---")

    st.caption(
        "**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer er generert. "
        "Ingen reelle data inngår."
    )

    st.markdown("---")

    st.subheader("Moduler")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**🧾 Fakturakontroll**")
            st.markdown("Three-way match og kontroll mot hele forpliktelsesbildet.")

    with col2:
        with st.container(border=True):
            st.markdown("**📋 Avtaler og forpliktelser**")
            st.markdown("Rammeavtaler og e-postavtaler i ett register.")

    col3, col4 = st.columns(2)
    with col3:
        with st.container(border=True):
            st.markdown("**⚖️ Terskelsjekk**")
            st.markdown("Regime, terskel og prosedyre med paragrafhenvisning.")

    with col4:
        with st.container(border=True):
            st.markdown("**📊 Styringsinformasjon**")
            st.markdown("Verdi funnet og kontrollstatus for hele porteføljen.")

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i logistikk og innkjøp · asliwa1986@gmail.com · Syntetiske data")
