# Anskaffelsessjekk — Mini-brief "UX-pass v1"

Partner directive · 2026-07-29. Whole-interface tidy (droga A — orden innenfor Streamlits rammer),
not just the supplier page. ZERO logic/threshold/rule/engine change — pure UX/layout. The 102 tests
must stay green and the reconciliation must stay 22 310 kr. All UI Norwegian (bokmål).

## U1 — Leverandørkartotek i faner (ikke én lang remse)
Kartoteket deles i faner: **Oversikt / Firmadata / Kategorier og tjenester / Kvalifikasjoner /
Personer / Avtaler, forpliktelser og fakturaer / Vurdering**. Redigering gjemmes i popover
(st.popover), henger ikke permanent på skjermen. Dette er den største komfortforbedringen.

## U2 — Leverandørliste: søk + ryddig tabell + «Ny» i popover
Et søkefelt filtrerer listen; tabellen er ryddig; «＋ Ny leverandør» ligger i en popover, ikke som
en åpen form øverst.

## U3 — Ett skjemamønster for alt
Navngitte lagre-knapper («Lagre leverandør», «Lagre tjeneste», …) og en `st.toast` etter hver
lagring. Konsistens = komfort. En liten hjelpefunksjon for lagre-flyten.

## U4 — Verdikt-kortet (produktets hjerte) ryddet
På Fakturakontroll: verdikt STORT øverst, funn i lesbare rader, «hvorfor / hjemmel» i en expander
under hvert funn. Mindre støy, tydeligere hierarki.

## U5 — Avtaler ryddet
Avtaler-siden ryddes visuelt: klarere seksjoner, samme mønster som resten.

## U6 — Globalt konsistent
Pills, ikoner (＋ ✎ 🗑 →), datoer (DD.MM.ÅÅÅÅ), beløp — samme overalt. Én dato-hjelper
(`db.dato`) og felles ikonbruk.

## U7 — Arbeidsflate: handlinger øverst, mindre «reklame»
Handlingene (last opp faktura, registrer forpliktelse, terskelsjekk) løftes til toppen; mindre
markedstekst. Full redesign kommer senere — dette er en opprydding.

## U8 — Smal skjerm + regresjon
Test på smal skjerm; ingen logikkendring; 102 tester grønne; reconciliation 22 310.

## Arkitektur / grenser
Ren UI/layout i app/. INGEN endring i core/, ingen ny modell, ingen versjonsbump (ingen core-endring).
Alle interpolerte HTML-verdier html.escape()-d (hard rule #11). Full-tool-regelen (#12) beholdes:
faner/popover endrer bare presentasjon — add/edit/delete/use finnes fortsatt for alt.

## DoD (per steg)
pytest grønt (102), ruff rent, alle 8 sider åpner, reconciliation 22 310. Commit+push per steg
(U1→U8). CLAUDE.md Current tasks + STATUS. Ingen versjonsbump.
