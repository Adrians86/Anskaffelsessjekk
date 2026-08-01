# Brief — Funksjon 6: Worklist A–Z

**Mål:** Arbeidsflaten (landing page) skal ikke lenger rendere ALLE fakturaer — den viser
handlinger + KPI-tall + de 3–5 mest presserende (avvik først) + «→ Åpne arbeidsliste».
Dedikert arbeidsliste (ny side) håndterer 100+ fakturaer uten å mulne.

## Steg

### W1 — Landing page: kompakt oversikt, ikke portianke
- Arbeidsflaten beholder handlingsknappene (øverst) og KPI-stripen.
- Fakturakøen fjernes i sin nåværende form. Erstattes av: «Krever handling»-rader (maks 5
  av de med høyest alvorlighet, avvik først) + knapp «→ Åpne arbeidsliste».
- Porteføljehelse-baren beholdes.
- «Siste hendelser»-feeden beholdes (komprimert).

### W2 — Ny side: Arbeidsliste
- `app/pages/8_Arbeidsliste.py` — kompakt tabell (ikke store blokker), paginering 25/side.
- Filtere: verdikt (AVVIK/TIL_VURDERING/SAMSVAR), leverandør, dato (fra/til), status
  (ny/under kontroll/godkjent/avvist).
- Søkefelt (fakturanr / leverandørnavn).
- Standard sortering: avvik øverst, deretter beløp synkende.

### W3 — Åpne faktura fra arbeidslisten
- Klikk «Åpne →» setter `preselect_invoice` og navigerer til Fakturakontroll.
- Etter beslutning/tilbake bevares filter/side i session_state.

### W4 — Fakturastatus
- Utledet status: `ny` (ingen beslutning), `under_kontroll` (har avvik/vurdering, ingen
  beslutning), `godkjent` / `avvist` (fra InvoiceDecision).
- Vises som chip i arbeidslisten, filterbar.

### W6 — Ytelse + tomme tilstander
- Arbeidslisten bruker `@st.cache_data` og ren HTML-tabell (ikke N Streamlit-widgets).
- Tom tilstand: «Alt er kontrollert 🎯» — ikke reklame.

### W7 — Tester + wrap-up
- `tests/test_worklist.py`: arbeidsliste åpner, landing page åpner, status-avledning riktig,
  reconciliation 22 310 uendret.
- CI-guard, STATUS.md, CLAUDE.md oppdatert.
