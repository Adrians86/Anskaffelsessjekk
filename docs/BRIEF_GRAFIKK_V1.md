# Anskaffelsessjekk — Mini-brief "Grafikk v1"

Partner directive · 2026-07-28. Visual polish only (within scope freeze: "visual polish of the
Streamlit app"). No engine/threshold/rule/core-model change. All UI Norwegian (bokmål).

## Bakgrunn (hvorfor)
Demoen skal lese som ÉTT produkt, ikke åtte løse Streamlit-sider. Vi låser én visuell identitet
("Lyst kontor", variant C) med ett sentralt tema (én kilde til sannhet), et felles redaksjonelt
sidehode, og en Arbeidsflate som følger variant C. Mobil får et "lite" minimum slik at telefon
ikke er ødelagt — full responsivitet er bevisst Phase 2.

## G1 — Fundament: sentralt tema "Lyst kontor" (variant C)
Ett tema, kalt på hver side (via `chrome.header()` → `theme.inject_theme()`):
- Navy `#20364F`, gull `#A8842A`.
- Serif i overskrifter (H1/eyebrow), sans i brødtekst.
- Hairline (1px lys linje) i stedet for skygger — rolig, "lyst kontor"-preg.
- `app/theme.py` er kilden til sannhet for farge/typografi. Verdikt-farger forblir per BRAND.md
  (`#2E7D32` / `#B58900` / `#C62828`) — ikke rørt.

## G2 — Felles sidehode på alle 8 sider
`chrome.page_header(eyebrow, title, lede)`:
- eyebrow (liten, gull, sperret) + serif H1 + lede (dempet undertekst) + chip "Syntetiske data".
- Erstatter `st.title(...)` + løs caption på alle 8 sider.

## G3 — Arbeidsflate iht. variant C
- KPI-stripe som redaksjonell stripe (én sammenhengende stripe med hairline-skiller), ikke løse kort.
- Handlingskafler (gull venstrekant) beholdt.
- Worklist ("Krever handling") og "Siste hendelser" side om side (feed hentet fra variant A).
- Reconciliation uendret: Verdi funnet = 22 310 kr.

## G4 — Tabeller og piller ensrettet globalt
- Liten radius, `tabular-nums` på tall, gull-lenker.
- Verdikt-piller som avrundede chips (samme semantiske farger).
- Definert globalt i `theme.py` CSS + `ui_common.verdict_pill`.

## G5 — Mobile-lite (bevisst minimum)
- KPI-stripe wrapper, paneler stables vertikalt, tabeller i horisontal scroll.
- Stopptekst "Optimalisert for desktop".
- Full responsivitet = Phase 2 (ikke bygget nå).

## G6 — Wrap-up
- Test på smal skjerm (alle sider åpner), reconciliation 22 310.
- CLAUDE.md Current tasks + STATUS.md. DoD: pytest grønt, ruff rent.

## Utenfor scope (ikke rør)
Motorlogikk / terskler / regeldata / core-datamodell — INGEN endring. Ingen ny UI-ramme, ingen
auth. Ren visuell polering.

## DoD
pytest grønt, ruff rent, alle 8 sider åpner (AppTest), reconciliation 22 310. Commit+push per steg.
Ingen versjonsbump (ingen core-endring).
