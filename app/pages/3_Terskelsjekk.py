from datetime import date
from decimal import Decimal

import streamlit as st

from core.rules.engine import Facts, RulesEngine

st.set_page_config(page_title="Terskelsjekk", page_icon="⚖️", layout="wide")
st.title("Terskelsjekk")
st.caption("Første steg er alltid valg av regime — beløpet avgjør aldri regimet. "
           "Reglene er versjonerte data med gyldighetsdatoer (per juli 2026).")

_REGIMES = {
    "FOA": "Klassisk sektor (anskaffelsesloven + FOA)",
    "FOSA": "Forsvars- og sikkerhetsanskaffelser (FOSA)",
    "ART123": "EØS art. 123 — vesentlige sikkerhetsinteresser (unntak)",
}

col1, col2, col3 = st.columns(3)
regime = col1.selectbox("Regime", options=list(_REGIMES), format_func=_REGIMES.get)
value = col2.number_input("Anslått verdi (NOK ekskl. mva)", min_value=0, value=750000, step=50000)
on = col3.date_input("Vurderingsdato", value=date(2026, 7, 8))

if regime == "FOSA":
    st.info("Merk: innslagspunktet på 500 000 kr gjelder IKKE for FOSA. "
            "Protokollplikt fra 100 000 kr.", icon="ℹ️")

if st.button("Vurder", type="primary"):
    hits = RulesEngine().evaluate(
        Facts(regime=regime, estimated_value=Decimal(value), assessment_date=on)
    )

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown(f"**1. Regime**\n{_REGIMES[regime]}")
    with c2:
        st.markdown("→", help="Beløp avgjør aldri regime")
    with c3:
        with st.container(border=True):
            threshold = "✓ Vilkår oppfylt" if value > 500000 else "✓ Under terskel"
            st.markdown(f"**2. Terskel**\n{threshold}")

    if not hits:
        st.warning("Ingen regler slo til for denne kombinasjonen — sjekk regime og dato.")
    else:
        st.markdown("---")
        for h in hits:
            st.markdown(f"### **3. Konsekvens: {h.consequence.replace('_', ' ')}**")
            with st.expander("Hjemmel og begrunnelse", expanded=True):
                st.markdown(f"**Hjemmel:** {h.citation}")
                if h.citation_url:
                    st.markdown(f"[Les kilden]({h.citation_url})")
                st.caption(f"Regel-ID: {h.rule_id} · Regime: {h.regime}")

    st.caption("**Regimet vurderes ALLTID før beløpet — beløp avgjør aldri regime.**")
    st.caption("Veiledende vurdering basert på registrerte regler — "
               "beslutningsstøtte, ikke juridisk rådgivning.")

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Syntetiske data")
