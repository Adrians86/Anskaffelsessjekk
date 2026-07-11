# Anskaffelsessjekk — Implementation Brief "Arbeidsflate v2" (FINAL)

**Partner directive · 2026-07-11 · supersedes previous T1–T8 polish tasks · paste to Claude Code in full**

Context: buyer-perspective audit + market research (Medius/Basware work-queue paradigm) led to a
re-staging of the demo around a professional AP-style workspace. Screen architecture is FROZEN as
specified here. `core/` stays untouched except the two explicitly approved items (EHF parser —
completion of original MVP scope; CSV helper at UI level). All UI text Norwegian (bokmål).
Definition of DONE (a–e in CLAUDE.md) applies to every task. The HTML mockup
`docs/mockups/arbeidsflate.html` (add it to the repo from the file Adrian provides) is the visual
spec — replicate its layout, palette and information hierarchy in Streamlit as closely as the
framework allows.

Frozen screen architecture (sidebar order):
1. Arbeidsflate (new home) · 2. Fakturakontroll · 3. Avtaler og forpliktelser ·
4. Leverandører (new) · 5. Terskelsjekk · 6. Styringsinformasjon · 7. Plattformen (new) · 8. Sikkerhet

Work in this exact order:

---

## T0 — BLOCKER: numbers must reconcile (fix before anything else)
1. Hero/KPI metric "Verdi funnet" MUST be computed from the engine: run check_invoice for ALL
   invoices once (cache with st.cache_data on the engine session seed), sum deviation_amount.
   Expected on demo data: 10 310 kr. Add a UI-level sanity: if the computed value is 0 on demo
   data, render a warning instead of "0 kr".
2. Remove the word "Prisskandal" everywhere — forbidden register. Institutional tone only.
   Correct capitalization: "J. Hansen".
3. Every number shown on any page must come from the engine and reconcile with every other
   number on the same page. Acceptance test: manual cross-check of Arbeidsflate KPIs vs
   Styringsinformasjon vs per-invoice results.

## T1 — Arbeidsflate (new home page, replaces current Hjem content)
Replicate docs/mockups/arbeidsflate.html:
- Header row: title "Arbeidsflate", right caption "Demo · syntetiske data · regelverk per 01.07.2026".
  Sub-line: "Full oversikt over kontrollstatus — hva som krever deg, og hva som er i orden."
- KPI strip (5 bordered containers): Kontrollert · Avvik (red) · Til vurdering (yellow) ·
  Samsvar (green) · Verdi funnet (gold, largest emphasis). Colors from BRAND.md tokens.
- Porteføljehelse bar: horizontal stacked bar (red/yellow/green shares of verdicts) with legend.
  Implement with a small HTML block or Altair — same pattern as SpareParts stock health.
- Action tiles (3, gold left border): "Last opp faktura (EHF)" → jumps to Fakturakontroll upload
  tab (T5); "Registrer forpliktelse" → Avtaler page; "Kjør terskelsjekk" → Terskelsjekk page.
  Use st.switch_page.
- Fakturakø: status tabs (Alle / Avvik / Til vurdering / Samsvar) + table: Faktura · Leverandør ·
  Beløp · Status pill · Funn (one-line summary of the top finding, with 📧 prefix when the basis
  is an e-mail commitment) · "Åpne →" (sets session state, switches to Fakturakontroll with that
  invoice preselected and auto-checked).
- "Krever handling" section: list every finding whose severity is WARN or DEVIATION across the
  portfolio as an actionable row: [invoice] — [anbefalt handling text] (mapping below). A checkbox
  per row (session-state only, no persistence needed in demo) so the user experiences a worklist.
- "Siste hendelser" feed: last 8 rows from AuditLog (time · action · entity · detail).
- Footer (all pages, T7 chrome): "Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i
  logistikk og innkjøp · Beslutningsstøtte, ikke juridisk rådgivning · Syntetiske data".
- SYNTETISKE DATA notice stays but as st.caption under the header, not a warning banner.

Anbefalt handling mapping (UI layer, e.g. app/texts.py — do NOT modify core):
PRICE_ABOVE_AGREED → "Krev kreditnota eller avklar prisgrunnlag med leverandør"
QTY_ABOVE_MAX → "Avklar mermengde mot avrop"
INFORMAL_BASIS → "Formaliser e-postavtalen med tillegg/anneks"
MISSING_RECEIPT → "Bekreft mottak før betaling"
MISSING_ORDER → "Knytt faktura til bestilling/avrop"
NO_AGREED_BASIS → "Etabler avtalegrunnlag eller vurder engeltkjøp"

## T2 — Leverandører (new page)
Table of suppliers from the engine: Navn · Org.nr · Antall avtaler · Antall fakturaer ·
Antall funn · Verdi funnet (sum of deviations for that supplier) · andel fakturaer med funn (%).
Sort by verdi funnet desc. Caption explaining the "First Time Right" idea:
"Hvilke leverandører genererer flest avvik — ta det opp med kilden, ikke bare symptomene."
Clicking is not required (static table is fine for demo).

## T3 — Fakturakontroll upgrade (audit card + upload)
- When arriving via session state (from Arbeidsflate), preselect the invoice and run the check
  automatically.
- Verdict as a large colored block with amount when nonzero: e.g. st.error("AVVIK — 12 000 kr
  over avtalt") / st.warning("TIL VURDERING") / st.success("SAMSVAR").
- Findings as cards; e-mail-based grunnlag gets a gold left border and "📧 E-postavtale:" prefix.
- Each finding shows its "Anbefalt handling" line (mapping above).
- Primary CTA: "Last ned protokoll (PDF)" (type="primary"); secondary link-button
  "Book 20-min gjennomgang" → mailto:asliwa1986@gmail.com?subject=Anskaffelsessjekk%20gjennomgang
- NEW upload tab "Last opp faktura (EHF)": implement core/extraction/ehf.py — parse a UBL/EHF
  invoice XML (namespace-tolerant; extract supplier org number, invoice number, date, currency,
  line items: item_ref from SellersItemIdentification or Name, quantity, unit price, line total).
  This COMPLETES the original MVP scope (parser was in the frozen plan). On upload: parse →
  persist Invoice+InvoiceLines linked to the matching demo supplier by org number (if unknown
  org number: create supplier on the fly, invoice will yield NO_AGREED_BASIS / MISSING_ORDER
  findings — that is correct and demonstrates the control) → run check_invoice → render the
  audit card. Provide a downloadable sample EHF file ("Last ned eksempel-EHF") generated from
  the F-1003 data so a visitor can try the loop immediately. Tests: tests/test_ehf.py — parse the
  sample file, assert header fields and line count; e2e: upload-parsed invoice produces expected
  findings.

## T4 — Plattformen (new page — the honest vision map)
Grid of module cards, each with a status badge. Three badge styles:
"Tilgjengelig" (green) · "Under utvikling" (yellow) · "Roadmap" (grey).
Cards: Fakturakontroll [Tilgjengelig] · Forpliktelsesregister m/ e-postavtaler [Tilgjengelig] ·
Terskelsjekk (FOA/FOSA/RAF) [Tilgjengelig] · Styringsinformasjon m/ CSV [Tilgjengelig] ·
Protokoll (PDF) [Tilgjengelig] · Leverandøroversikt [Tilgjengelig] ·
KI-uttrekk fra e-post [Under utvikling] · ISO/revisjonsstøtte [Under utvikling] ·
Internt reglement som regelsett [Under utvikling] ·
Leverandørscoring [Roadmap] · Avtalevarsler (utløp/uttak) [Roadmap] ·
Integrasjoner (Visma/SAP) [Roadmap] · Lager & behovsplanlegging — SpareParts AI [Tilgjengelig,
external link https://spareparts-asnorth.netlify.app].
No card without a truthful badge. No fake clickable modules.
Intro line: "Én motor, ett forpliktelsesregister — modulene er visninger på samme grunnlag."

## T5 — Terskelsjekk visual path
Result rendered as three bordered step-columns with arrows:
"1. Regime" → "2. Terskel" → "3. Konsekvens (§)". Citation expanders remain below.
Caption: "Regimet vurderes ALLTID før beløpet — beløp avgjør aldri regime."

## T6 — Styringsinformasjon upgrade
Verdi funnet as hero metric (first, largest, gold). Add "Gjennomsnittlig avvik per kontrollert
faktura" secondary metric. Per-supplier deviation table. Download button "Eksporter funn (CSV)":
one row per finding across all invoices (invoice_number, supplier, code, severity, message,
expected, actual, deviation_amount, citation).

## T7 — Chrome on every page
Navy (#1F3A5F) header band with product name (thin HTML block), consistent footer (text in T1),
Inter/system font, 8px spacing rhythm where practical. No emoji in page titles (sidebar ok).
Keep verdict semantic colors EXACTLY as BRAND.md (#2E7D32/#B58900/#C62828) — non-negotiable.

## T8 — Sikkerhet page (unchanged from previous brief)
Static Norwegian content: synthetic-data-only demo; append-only audit trail with rules version;
secrets via env vars; containerizable → on-prem possible (forsvarssektoren); production plans:
data residency Norway/EEA, DPIA before processing real e-mails (personal data, minimization),
SSO (Entra ID) on roadmap.

## T9 — Contract & wrap-up
Update CLAUDE.md: replace Current tasks with "Arbeidsflate v2 delivered — awaiting partner
review"; note the two approved engine additions (ehf.py parser, CSV helper). Run FULL DoD:
pytest green (incl. new test_ehf.py), every page opened on local run AND on the live Streamlit
Cloud URL after push, commit+push verified, STATUS.md entry.

## Acceptance criteria (partner review will test exactly this)
- 8-second test: Arbeidsflate shows status, money and next action without any click.
- 2-minute test: Arbeidsflate → open F-1003 → audit card with 📧 grunnlag → PDF → dashboard → CSV,
  no guessing.
- Upload test: download sample EHF → upload it → verdict renders.
- Reconciliation test: all numbers agree across all pages.
- Honesty test: no dead tiles, no fake modules, every badge truthful.
