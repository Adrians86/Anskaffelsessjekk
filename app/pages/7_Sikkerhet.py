"""Security and data handling — Sikkerhet og databehandling."""
import streamlit as st
from chrome import footer, header

st.set_page_config(page_title="Sikkerhet og databehandling", page_icon="🔒", layout="wide")
header()
st.title("Sikkerhet og databehandling")

st.markdown("""
## Syntetiske data i demoen

**Anskaffelsessjekk** kjører utelukkende på syntetiske data. Alle leverandører, avtaler,
fakturaer og e-postavtaler i demoen er generert og tydelig merket som syntetiske. Ingen
reelle person- eller virksomhetsdata inngår.

## Append-only revisjonsspor

Hver kontroll logges i et append-only revisjonsspor. Loggen kan ikke endres eller slettes i
etterkant, og hver hendelse bærer:

- **Aktør** — hvem som kjørte kontrollen
- **Anbefaling** — SAMSVAR / TIL_VURDERING / AVVIK (avledet av funn, aldri fastsatt direkte)
- **Regelversjon** — hvilket regelsett kontrollen ble kjørt mot
- **Tidspunkt** — når kontrollen ble utført

Dette gir full etterprøvbarhet ved revisjon: enhver anbefaling kan spores tilbake til
regelgrunnlaget og dataene den bygger på.

## Hemmeligheter og konfigurasjon

- All konfigurasjon (eventuelle API-nøkler, databasetilkoblinger) styres via **miljøvariabler**.
- Hemmeligheter lagres **aldri** i kildekoden. `.env`-filer holdes utenfor versjonskontroll.
- Regelverket er data (YAML med gyldighetsdatoer og hjemler), ikke hardkodede terskler.

## Containeriserbar — on-premises mulig

Systemet er designet for **on-premises**-drift:

- Uavhengig av skyplattform — kan kjøres i Docker lokalt eller på egen infrastruktur.
- SQLite i demoen; kan migreres til PostgreSQL i produksjon.
- Kjernen (`core/`) er adskilt fra brukergrensesnittet og har ingen eksterne avhengigheter i
  kontrollflyten.

Dette er særlig relevant for **forsvarssektoren**, der datasikkerhet og datasuverenitet er
ikke-forhandlbare krav.

## Veikart fram mot produksjon

- **Datalagring i Norge/EØS** — data residency innenfor EØS.
- **DPIA** (personvernkonsekvensvurdering) gjennomføres **før** behandling av reelle e-poster.
  E-poster kan inneholde personopplysninger; prinsippet om dataminimering legges til grunn, og
  databehandleravtale inngås.
- **SSO med Entra ID** — enkel pålogging på veikartet for produksjon.
- **Utvidet revisjonslogging** tilpasset compliance og forsvarssektoren.

## Juridisk ansvar

**Anskaffelsessjekk gir beslutningsstøtte, ikke juridisk rådgivning.** Systemet støtter
saksbehandleren, men erstatter ikke faglig skjønn eller juridisk rådgivning. Alle anbefalinger
bygger på siterte regler og avtaledata, og ingen beslutning er fullautomatisert — mennesket
bekrefter alltid.
""")

footer()
