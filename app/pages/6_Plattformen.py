import streamlit as st

st.set_page_config(page_title="Plattformen", page_icon="🧩", layout="wide")
st.title("Plattformen")
st.markdown("Én motor, ett forpliktelsesregister — modulene er visninger på samme grunnlag.")

# Truthful status badges only — no card without one, no fake clickable module.
AVAILABLE = ("Tilgjengelig", "#2E7D32", "#EAF4EC")
DEVELOPING = ("Under utvikling", "#B58900", "#FBF7EC")
ROADMAP = ("Roadmap", "#6B7280", "#F1F3F5")

MODULES = [
    ("Fakturakontroll", "Tre-veis match og kontroll mot avtalt grunnlag.", AVAILABLE, None),
    ("Forpliktelsesregister m/ e-postavtaler", "Avtaler, avrop og bekreftede e-postavtaler som kontrollgrunnlag.", AVAILABLE, None),
    ("Terskelsjekk (FOA/FOSA/RAF)", "Riktig regime og prosedyre — regimet vurderes før beløpet.", AVAILABLE, None),
    ("Styringsinformasjon m/ CSV", "Porteføljetall og eksport av funn for videre analyse.", AVAILABLE, None),
    ("Protokoll (PDF)", "Anskaffelsesprotokoll per faktura for revisjonssporet.", AVAILABLE, None),
    ("Leverandøroversikt", "Hvilke leverandører genererer flest avvik.", AVAILABLE, None),
    ("KI-uttrekk fra e-post", "Automatisk forslag til forpliktelser — bekreftes alltid av menneske.", DEVELOPING, None),
    ("ISO/revisjonsstøtte", "Kontrollspor og dokumentasjon tilpasset revisjon.", DEVELOPING, None),
    ("Internt reglement som regelsett", "Virksomhetens egne innkjøpsregler som datadrevne regler.", DEVELOPING, None),
    ("Leverandørscoring", "Historisk avviksrate per leverandør over tid.", ROADMAP, None),
    ("Avtalevarsler (utløp/uttak)", "Varsler ved avtaleutløp og uttak mot ramme.", ROADMAP, None),
    ("Integrasjoner (Visma/SAP)", "Direkte innhenting av fakturaer og bestillinger.", ROADMAP, None),
    ("Lager & behovsplanlegging — SpareParts AI", "Lagerstyring og behovsplanlegging (egen tjeneste).",
     AVAILABLE, "https://spareparts-asnorth.netlify.app"),
]


def badge_html(badge):
    label, fg, bg = badge
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;'
            f'padding:2px 10px;border-radius:10px;white-space:nowrap">{label}</span>')


cols = st.columns(3)
for i, (title, desc, badge, link) in enumerate(MODULES):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                f'<strong>{title}</strong>{badge_html(badge)}</div>',
                unsafe_allow_html=True,
            )
            st.caption(desc)
            if link:
                st.link_button("Åpne SpareParts AI ↗", link, use_container_width=True)

st.markdown("---")
st.caption("Statusmerkene er sannferdige: Tilgjengelig = i drift i denne demoen · "
           "Under utvikling = påbegynt · Roadmap = planlagt. Ingen moduler uten merke.")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i logistikk og innkjøp · Beslutningsstøtte, ikke juridisk rådgivning · Syntetiske data")
