# Anskaffelsessjekk — Mini-brief "Verifisering v1" (V1–V6)

Partner directive · 2026-07-18 · main po merge Arbeidsflate v2. Execute V1→V6 in order,
commit+push after EACH V, full DoD (a–d). All UI text Norwegian (bokmål). Goal: demo shows the
FULL idea — verification against THREE sources (forpliktelser + regelverk + internt reglement),
in TWO directions (supplier deviation + own procedural error), with the e-mail validity
hierarchy. Staging of the existing engine + one small YAML — no new modules.

## V1 — Avtaler og forpliktelser: differentiator page upgrade (highest priority)
Page is the thinnest in the app while being THE differentiator. Rebuild as the showcase of the
forpliktelsesregister:
(a) Section "📧 E-postavtaler i kontrollgrunnlaget" — each EMAIL-source commitment as a card with
gold left border (#B08D2E): the condition (item, value, unit, valid_from); source line
"E-post 12.06.2026 · J. Hansen" + a short SOURCE QUOTE block (the e-mail excerpt the extraction
is based on). If synth data has no quote text, add optional nullable source_quote to Commitment +
fill in core/synth generators with a realistic Norwegian one-liner, e.g. "Vi bekrefter herved
redusert pris 118 000 kr for HYD-450 fra 15. juni."; formalization chip: FORMALISERT (green) /
VENTER PÅ TILLEGG (yellow) / UFORMELL (grey).
(b) NEW: "Gyldighetsvurdering" per e-mail commitment — three outcomes: ✓ GYLDIG · ⚠ KREVER
FORMALISERING · ✗ UGYLDIG. UI-level derivation from existing data is acceptable for demo (no full
rules pass yet): FORMALIZED → GYLDIG ("I samsvar med avtalens endringsbestemmelser");
INFORMAL/PENDING within contract scope → KREVER FORMALISERING ("Avtalen krever skriftlig tillegg
— e-posten er varsel, ikke dokumentasjon"); UGYLDIG reserved for future vesentlig-endring rule —
render the three-state legend anyway so the concept is visible. Caption: "En e-postavtale
kontrolleres alltid mot avtalen og regelverket — den er aldri et selvstendig bevis."
(c) Contract lines table stays below, unchanged.

## V2 — Fakturakontroll: one verification, two directions
On the audit card (after a check runs), add section "Regelverkssjekk" UNDER findings: fetch the
order linked to the invoice; run the existing rules engine (same call as Terskelsjekk) for that
order's estimated value + profile + date; render compact: Regime → Terskel → Konsekvens (citation
expander), prefixed "Egenkontroll: prosedyre og terskel for denne anskaffelsen". Caption:
"Kontroll i to retninger — leverandørens faktura og egen prosedyre." No core changes — UI
composition only.

## V3 — Internt reglement: the third source
(a) New core/rules/data/profiles/demo_reglement.yaml with 1–2 internal rules clearly marked as
the organization's OWN: id INTERN_ATTESTASJON_100K (invoice.total >= 100000 →
KREVER_ATTESTASJON_2_PERSONER, citation "Internt reglement §4-2 (demo-organisasjon)"); id
INTERN_TERSKEL_ENKELTKJOP (order.estimated_value >= 50000 and no contract → KREVER_INNKJOPSORDRE,
citation "Internt reglement §3-1 (demo-organisasjon)").
(b) Engine loads via existing profile mechanism; rule hits render in Fakturakontroll findings with
a distinct chip "Internt reglement" (navy outline) — three sources visually distinguishable:
Forpliktelser · Regelverk · Internt reglement.
(c) Tests: table-driven cases for both rules (mirror existing pattern).
(d) Arbeidsflate + Styringsinformasjon numbers must still reconcile after new findings; document
the new expected verdi funnet in STATUS.md.

## V4 — Rename 3_Leverandører.py → 3_Leverandorer.py
Non-ASCII filenames = classic "works locally, breaks somewhere". Page title inside stays
"Leverandører". git mv, update any switch_page references, verify sidebar order.

## V5 — Wrap-up
Click-test every page and button locally; pytest green (document new count). Update CLAUDE.md
Current tasks: "Verifisering v1 delivered — demo shows full idea (3 sources, 2 directions, e-mail
validity hierarchy)". STATUS.md entry + push. Verify live URL after auto-redeploy: all pages open,
upload flow works (sample EHF → upload → verdict), numbers reconcile.

## V6 — Leverandører: drill-down to supplier card (owner decision, added 2026-07-18)
The overview table stays; each supplier becomes openable ("Åpne →" per row, or st.selectbox above
a detail section — pick the cleaner Streamlit pattern). Detail view "Leverandørkort" shows, from
existing data only (queries by supplier_id, no core changes):
(a) header: navn, org.nr, badge SYNTETISK;
(b) Avtaler — contracts with period, value, line count;
(c) Forpliktelser — all commitments incl. 📧 e-mail ones with formalization/gyldighet chips
(reuse V1 rendering);
(d) Fakturaer — table: number · date · amount · verdict pill · verdi funnet per invoice, each
"Åpne →" jumping to Fakturakontroll (session_state preselect, same mechanism as Arbeidsflate
queue);
(e) Nøkkeltall — antall fakturaer, andel med funn (%), sum verdi funnet, First Time Right;
(f) Siste hendelser — AuditLog entries for this supplier.
Numbers must reconcile with the overview table and Arbeidsflate KPIs. Acceptance: opening
Hydraulikk Nord shows its contract, its e-mail commitment with source quote, all its invoices with
verdicts, and clicking an invoice lands on its audit card.

## Acceptance (partner will test)
1. Avtaler: e-mail commitment shows source quote + formalization chip + gyldighetsstatus + "aldri
et selvstendig bevis" caption. 2. Fakturakontroll: one card shows findings AND Regelverkssjekk.
3. At least one finding carries citation "Internt reglement §…" with its chip. 4. Numbers
reconcile across all pages (new expected total documented). 5. Supplier card drill-down works
end-to-end (V6 acceptance). 6. No page crashes on live URL; 8-second test passes.
