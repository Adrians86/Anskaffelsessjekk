# Anskaffelsessjekk — Mini-brief "Leverandørkort v2"

Partner directive · 2026-07-20. Extends the Leverandørkort drill-down (from Verifisering v1 · V6)
on the Leverandører page. Execute L1 → L5 in order, commit+push after each, full DoD (a–d).
All UI text Norwegian (bokmål). Synthetic data only, clearly labelled.

## L1 — Kategorier + kvalifikasjoner
What the supplier is *allowed to deliver*, with validity — expired qualifications shown in RED.
This is the "drukarka czy czołg" (printer or tank) made visible on screen: categories the supplier
covers + qualifications with a gyldig-til date. Data is synthetic (per supplier).

## L2 — Kvalitetsvurdering fra våre data
andel med funn · First Time Right · a simple trend, computed from OUR control data.
HARD legal annotation (KOFA risk protection): "Dette er innsikt i samarbeidet, IKKE en
kvalifikasjonsrangering." The card must not read as a qualification ranking.

## L3 — Fakturerte objekter som kontekst
What we actually paid the supplier for (from invoice lines), each flagged **på avtale** (item on a
contract line) / **utenfor avtale** (not on any contract line). Context only — NOT a machine
register, no asset tracking.

## L4 — Roadmap-marker "Leveranseoppfølging"
An honestly-labelled future area (grey "Roadmap" badge) — the delivery/realisation calendar as a
planned module, NOT a quarter-built product.

## L5 — Wrap-up
Tests (synthetic profiles load; expired qualification flagged; på/utenfor avtale classification),
pytest green, CLAUDE.md Current tasks update, STATUS + push. Live verification: open a
Leverandørkort, see categories/qualifications (expired in red), quality section with the KOFA
disclaimer, invoiced objects with på/utenfor flags, and the Leveranseoppfølging roadmap marker.

## OUT of scope (explicitly NOT built — do not expand)
- **Rejestr maszyn / asset register** — no per-machine inventory or serial tracking.
- **Leveringskalender / delivery calendar** — no scheduling UI (only the L4 roadmap marker).
- **Stjernerangering / star ranking** — no 1–5 score or league table of suppliers; quality metrics
  are cooperation insight, never a qualification ranking (see L2 legal annotation).

## Acceptance
Leverandørkort shows: (1) categories + qualifications with validity (expired red); (2) quality
metrics with the "innsikt, ikke rangering" disclaimer; (3) invoiced objects flagged på/utenfor
avtale; (4) a truthful Leveranseoppfølging roadmap marker. None of the OUT-of-scope items appear.
