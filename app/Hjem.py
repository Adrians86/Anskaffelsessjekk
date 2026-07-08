import streamlit as st

st.set_page_config(page_title="Anskaffelsessjekk", page_icon="✅", layout="wide")

st.title("Anskaffelsessjekk")
st.subheader("KI-drevet kontroll av fakturaer, avtaler og anskaffelsesregelverk — med full sporbarhet")

st.warning("**SYNTETISKE DATA** — alle leverandører, avtaler og fakturaer i denne demoen er "
           "generert. Ingen reelle data inngår.", icon="⚠️")

col1, col2, col3, col4 = st.columns(4)
col1.markdown("### 🧾 Fakturakontroll\nThree-way match og kontroll mot hele "
              "forpliktelsesbildet — også avtaler som kun finnes i e-post.")
col2.markdown("### 📋 Avtaler og forpliktelser\nRammeavtaler og uformelle avtaler i ett "
              "register, med status for formalisering.")
col3.markdown("### ⚖️ Terskelsjekk\nRiktig regime (FOA / FOSA / art. 123) og prosedyre — "
              "med paragrafhenvisning for hvert svar.")
col4.markdown("### 📊 Styringsinformasjon\nVerdi funnet, avviksfordeling og kontrollstatus "
              "— tall til controlling og ledelse.")

st.divider()
st.markdown(
    "Systemet gir **anbefalinger** (SAMSVAR / TIL VURDERING / AVVIK) — beslutningen tas "
    "alltid av et menneske. Hvert funn viser regelen og kilden det bygger på: ingen svart boks."
)
st.caption("Beslutningsstøtte, ikke juridisk rådgivning · AS North Advisory · asnorth.no")
