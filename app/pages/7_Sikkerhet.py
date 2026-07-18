"""Security and data handling — Sikkerhet og databehandling."""
import streamlit as st

from chrome import header, footer

st.set_page_config(page_title="Sikkerhet og databehandling", page_icon="🔒", layout="wide")
header()
st.title("Sikkerhet og databehandling")

st.markdown("""
## Datakvalitet og transparens

**Anskaffelsessjekk** kjører på syntetiske data — alle leverandører, avtaler, fakturaer og
e-poster i demoen er algorithmisk generert. Ingen reelle persondata eller virksomhetsdata inngår.

## Sporbarhet

Hver kontroll logges append-only i revisjonssporet med:
- **Actor**: hvem som kjørte kontrollen
- **Verdict**: SAMSVAR / TIL_VURDERING / AVVIK
- **Rules version**: hvilken regelversjon som ble brukt
- **Timestamp**: når kontrollen ble kjørt

Dette sikrer full etterprøvbarhet ved revisjon.

## Hemmeligheter og konfigurasi

- Systemkonfigurasi (API-nøkler, database-tilkoblinger) styres via miljøvariabler.
- Hemmeligheter lagres **aldri** i koden.
- Kodebasen er kryptert i git (med `.gitignore` for `.env`-filer).

## Arkitektur — containeriserbar design

Systemet er designet for **on-premises** distribusjon:
- Uavhengig av skyplattform (Streamlit Community Cloud eller lokalt Docker)
- SQLite-database (kan migreres til PostgreSQL ved produksjon)
- **Ingen eksterne integrasjoner** som påvirkEr dataflyt (planlagt for Phase 2)

Dette er spesielt relevant for **forsvarssektoren**, hvor datasiskerhet og datasouverenitet
er ikke-forhandlingsbare.

## Veikartet fram til produksjon

- **Data residency**: Turforsikrer data lagres i Norge/EØS
- **DPIA** (Data Protection Impact Assessment): før real e-post-prosessering
  (e-poster inneholder persondata → databehandlingsavtale påkrevd)
- **SSO** (Entra ID): authentication ved produksjonsjavn
- **Audit logging**: utvidet for compliance og forsvarssektoren

## Juridisk ansvar

**Anskaffelsessjekk gir anbefalinger, ikke juridiske råd.** Systemet støtter beslutningstagere
men kan ikke erstatte menneskelig fagdømmekraft eller juridisk rådgivning.

Alle verdikter er grunnlaget i siterte regler og avtaledata; ingen beslutning er fullstendig
automatisert.

""")

footer()
