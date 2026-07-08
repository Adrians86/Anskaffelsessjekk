import streamlit as st

st.set_page_config(page_title="Anskaffelsessjekk", page_icon="✅", layout="centered")

st.title("Anskaffelsessjekk")
st.markdown('<div style="border-bottom: 2px solid #B08D2E; margin: -10px 0 20px 0;"></div>', unsafe_allow_html=True)

st.subheader("KI-drevet kontroll av fakturaer, avtaler og anskaffelsesregelverk")
st.markdown("*med full sporbarhet*")

st.warning("**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer i denne demoen er "
           "generert. Ingen reelle data inngår.", icon="⚠️")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("### 🧾 Fakturakontroll")
        st.markdown("Three-way match og kontroll mot hele forpliktelsesbildet — også avtaler som kun finnes i e-post.")

with col2:
    with st.container(border=True):
        st.markdown("### 📋 Avtaler og forpliktelser")
        st.markdown("Rammeavtaler og uformelle avtaler i ett register, med status for formalisering.")

col3, col4 = st.columns(2)
with col3:
    with st.container(border=True):
        st.markdown("### ⚖️ Terskelsjekk")
        st.markdown("Riktig regime (FOA / FOSA / art. 123) og prosedyre — med paragrafhenvisning for hvert svar.")

with col4:
    with st.container(border=True):
        st.markdown("### 📊 Styringsinformasjon")
        st.markdown("Verdi funnet, avviksfordeling og kontrollstatus — tall til controlling og ledelse.")

st.markdown("---")
st.markdown(
    "Systemet gir **anbefalinger** (SAMSVAR / TIL VURDERING / AVVIK) — beslutningen tas "
    "alltid av et menneske. Hvert funn viser regelen og kilden det bygger på: ingen svart boks."
)

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Syntetiske data")
