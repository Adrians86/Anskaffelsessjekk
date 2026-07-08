# Anskaffelsessjekk

**KI-drevet kontroll av fakturaer, avtaler og anskaffelsesregelverk for offentlig sektor — med full sporbarhet.**

> Status: MVP under utvikling (juli 2026) · Et AS North Advisory-prosjekt · [asnorth.no](https://asnorth.no)

## Problemet

Innkjøpere, planleggere og controllere i offentlig sektor bruker timer hver uke på manuell kontroll: stemmer fakturaen med rammeavtalen? Med det som ble avtalt på e-post i juni? Ble riktig prosedyre og terskelverdi fulgt? Er protokollen og dokumentasjonen på plass?

Fra 1. juli 2026 gjelder nytt innslagspunkt (500 000 kr), og forsvarssektoren fikk nye retningslinjer (RAF) fra 1. januar. Regelverket endrer seg — kontrollen gjøres fortsatt manuelt.

## Løsningen

Anskaffelsessjekk kontrollerer hver faktura mot **hele forpliktelsesbildet**:

- **Fakturakontroll** — three-way match (bestilling ↔ mottak ↔ faktura) og kontroll mot avtalte betingelser
- **Forpliktelsesregister** — rammeavtaler OG uformelle avtaler (e-post) i ett register, med status for formalisering
- **Terskelsjekk** — riktig regime (FOA / FOSA / RAF) og prosedyre, med paragrafhenvisning
- **Dokumentasjon som biprodukt** — protokollutkast og styringsinformasjon genereres automatisk
- **«Hvorfor?»-knappen** — hvert funn viser regelen og kilden. Ingen svart boks.

Systemet gir anbefalinger (SAMSVAR / TIL VURDERING / AVVIK) — beslutningen tas alltid av et menneske. *Beslutningsstøtte, ikke juridisk rådgivning.*

## Data

All demonstrasjon kjører på **syntetiske data** (tydelig merket). Ingen reelle fakturaer, avtaler eller persondata inngår i prosjektet.

## Teknisk

Python · SQLModel · regelverk som versjonerte YAML-data · Streamlit (MVP) · se [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Kontakt

Adrian Śliwa · AS North Advisory · [asnorth.no](https://asnorth.no)
