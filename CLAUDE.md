# CLAUDE.md — project contract for Claude Code

You are the implementation agent on **Anskaffelsessjekk** — a compliance-control tool
for Norwegian public-sector procurement (invoices vs contracts vs e-mail agreements vs
anskaffelsesregelverket). The product owner is Adrian Śliwa. Strategy, architecture and
scope are set by his strategic partner (Claude in the Claude app) and are recorded here
and in `docs/ARCHITECTURE.md`. Your job: implement within this contract.

## Team workflow — two-way channel
- **Instructions to you** live in this file (section “Current tasks” below) and in `docs/ARCHITECTURE.md`.
- **Your reports back** go to `docs/STATUS.md`: at the END of every working session, append
  an entry using the template there (date, what was done, test status, decisions needed,
  questions for the strategic partner). Commit it. The partner reads STATUS.md via GitHub
  and responds by updating the “Current tasks” section here.
- If a task requires breaking any hard rule or exceeding scope: STOP, write the question
  in STATUS.md instead of implementing.

## Hard rules (non-negotiable)
1. `core/` imports nothing from any UI. Streamlit is a replaceable head.
2. Legal rules are DATA: YAML in `core/rules/data/` with validity dates and citations.
   Never hardcode a threshold. Every rule hit must carry a citation.
3. Human-in-the-loop: the system recommends (SAMSVAR / TIL_VURDERING / AVVIK),
   never decides. No auto-blocking. Unconfirmed LLM extractions never participate in control.
4. Verdicts are derived from findings, never stated directly.
5. Language: code/comments/docs in English; user-facing UI text in Norwegian (bokmål).
   Norwegian domain terms stay untranslated in code (rammeavtale, avrop, mottak, terskel).
6. Synthetic data only — clearly labelled. Never introduce real supplier/invoice data.
7. Audit trail is append-only.
8. `pytest` must be green (currently 26 passed) before every commit. Run it before and after changes.
9. Conventional commit messages (feat/fix/test/docs/style/build).
10. Every change to `core/models` or the `core` public API REQUIRES a version bump in
    `pyproject.toml` AND a bump of the "Rebuild marker" comment in `requirements.txt` —
    Streamlit Cloud only rebuilds the pip environment when a dependency FILE changes; a
    pyproject version bump alone is invisible to Cloud, so `core` stays stale = live crash.
    Also read `source_quote`-style new fields defensively in UI (`getattr(obj, "field", None)`)
    so a page degrades gracefully instead of crashing while a stale env is still live.
11. Any dynamic value interpolated into HTML rendered with `unsafe_allow_html` MUST pass through
    `html.escape()` — user-originated content (e-mails, uploads) will flow here in future features.
12. **Full-tool rule (A→Z):** no feature is DONE until it is complete from A to Z —
    add → view → edit → delete → use. A read-only "view" is NOT a finished feature. This
    supersedes any earlier "a view is enough" and applies to every future function. CRUD/persistence
    logic lives in a pure `core/` service (takes a Session, imports no UI) and every save appends an
    audit row (hard rule #7).

## Definition of DONE (for Claude Code agents)
A task is **done** only when ALL four are true:
- (a) `pytest` green (no red)
- (b) Every touched Streamlit page actually executed/opened in browser (pytest does NOT cover app/ pages)
- (c) Committed AND pushed to `origin/main` (local commits are not done)
- (d) STATUS.md entry appended and pushed to `origin/main`
- (e) Every new dependency added to BOTH `pyproject.toml` AND `requirements.txt` in the same change
  (pyproject drives local/editable installs and tests; requirements.txt drives Streamlit Community
  Cloud deploy — a dependency missing from either surface is a runtime crash in that environment)

Reporting "done" without all five is a process violation. A missing push is not a done task.

## Scope freeze — until the commercialization gate (2026-07-21)
ALLOWED: visual polish of the Streamlit app, PDF protokoll export, bugfixes,
Streamlit Community Cloud deploy preparation, test coverage improvements.
FORBIDDEN without partner approval (ask via STATUS.md): Next.js or any UI framework
change, authentication, new modules/features, database migration (SQLite stays),
external integrations, changes to core data model.

## Current tasks

**Funksjon 3 levert — Faktura A–Z (N1–N8): inntak + verifikasjon end-to-end, første fulle kjede.**

Brief "Funksjon 3: Faktura A–Z" (docs/BRIEF_FAKTURA_AZ.md) delivered on main. Domyka kjeden
leverandør (F1) + kontrakt/prisliste (F2) → **faktura kontrolleres mot avtalt prisliste**. Partner-
approved core change. Version 0.8.0 → **0.9.0** + requirements rebuild marker.
- **N2** `core/extraction/csv_faktura.py` — batch-CSV parser (rader grupperes til fakturaer på
  fakturanr; norske header-aliaser; ; eller , ; DD.MM.ÅÅÅÅ/ISO). Gjenbruker EHF ParsedInvoice.
- **N3/N4** `core/matching/prisliste.py` (ADDITIV — rører ikke three_way/commitments, så demo-
  reconciliation 22 310 er urørt): resolve_contract (order.contract_id ellers leverandørens aktive
  avtale) + check → funn med **HVORFOR** («Pris 13000 > avtalt 12500 for HYD-1001, avtale RA-x»),
  verify() → verdikt + funn + kontrakt + antall prislinjer.
- **N6** ny `InvoiceDecision` (append-only) + `core/registry/faktura.py`: intake_invoice (delt
  EHF+CSV-persistens, idempotent, audited) + record_decision (menneske bestemmer, hard rule #3) +
  latest_decision. **N1/N5/N7** `app/ui_faktura.py`: inntaksskjerm (EHF/CSV/flere EHF/PDF-JPG
  «Kommer OCR»), koblings-banner, verdikt-m/HVORFOR, batch-liste (avvik øverst), beslutning,
  protokoll PDF. Faktura vises på avtalens koblede fakturaer + i leverandørkortet.
- **N8** `tests/test_faktura_az.py` (9 tester: CSV · prisliste-HVORFOR · beslutning=1 AuditLog · les=0
  · idempotent); CI package-guard utvidet med faktura-modulene. pytest 121 passed, ruff clean, alle
  8 sider åpner. **Reconciliation unchanged: 22 310 kr.**
- **Neste (F4):** forpliktelser (e-postavtaler) mot endringsklausul; OCR (PDF/JPG) = bølge 2.

**Funksjon 2 levert — Kontrakt + prisliste A–Z (M1–M7), grunnlag #2 for verifikasjon.**

Brief "Funksjon 2: Kontrakt + prisliste A–Z" (docs/BRIEF_KONTRAKT_AZ.md) delivered on main. Partner-
approved core-data-model change. Version 0.7.0 → **0.8.0** + requirements rebuild marker.
- **Foundation (M1)** — Contract gains regime/change_clause/status/is_deleted; ContractLine.currency.
  `core/registry/kontrakt.py` = pure CRUD (create/update/soft_delete/restore contract + add/update/
  delete line), EVERY write appends an AuditLog row; `change_clause_of` read-helper. `app/ui_kontrakt.py`
  shared «Ny avtale» form + status badge + prisliste + kontraktvisning.
- **M1** Avtaler-siden «Avtaler»-fane (liste + søk + «＋ Ny avtale»); Leverandørkort «＋ Ny avtale»
  aktivert. **M2** prisliste (kontraktslinjer) full CRUD — verifikasjonsgrunnlaget. **M3** kontrakt-
  visning + rediger (popover) + soft-delete (bekreftelse). **M4** endringsklausul som DATA for motoren
  (`clause_assessment_hint`, ingen ny verifikasjonslogikk). **M5** leverandørkort viser avtaler med
  «Åpne →» + reell telling. **M6** seed beriket (regime/klausul/status), reconciliation uendret.
- **M7** `tests/test_kontrakt_crud.py` (9 tester: CRUD + audit-per-skriv + H1 les-uten-skriv + klausul);
  CI package-guard utvidet med kontrakt-modul. pytest 112 passed, ruff clean, alle 8 sider åpner.
  **Reconciliation unchanged: 22 310 kr** (fakturaene matcher nå eksplisitte prislinjer).
- **Neste (F3/F4):** faktura-inntak/verifikasjon (F3), forpliktelser (F4).

**UX-pass v1 levert (U1–U8) — hele grensesnittet ryddet, null logikkendring.**

Mini-brief "UX-pass v1" (docs/BRIEF_UX_PASS.md) delivered on main. Pure UI/layout (droga A —
orden innenfor Streamlits rammer); NO engine/threshold/rule/core-model change, INGEN versjonsbump.
- **U1** Leverandørkartotek i 7 faner (Oversikt / Firmadata / Kategorier og tjenester /
  Kvalifikasjoner / Personer / Avtaler, forpliktelser og fakturaer / Vurdering); redigering flyttet
  til `st.popover` — skjermen holdes ryddig. Notat-redigering dobler ikke lenger som kategori-editor.
- **U2** leverandørliste: søkefelt (navn/org.nr) + ryddig tabell + «＋ Ny leverandør» i popover.
- **U3** ett skjemamønster: navngitte lagre-knapper + `st.toast` på hver lagring (feil = banner).
- **U4** verdikt-kortet (Fakturakontroll): verdikt STORT øverst (serif, farget), funn i lesbare
  rader, «Hvorfor — grunnlag og anbefalt handling» i expander per funn.
- **U5** Avtaler ryddet: kontrakter i egne bordered kort; e-post-bekreftelse → toast.
- **U6** global konsistens: ny `db.dato()` → DD.MM.ÅÅÅÅ overalt datoer vises; pills/ikoner/beløp
  ensartet. **U7** Arbeidsflate: handlinger løftet helt til topps, mindre markedstekst.
- **U8** `tests/test_grafikk.py` utvidet (dato-format + smal-skjerm/mobile-lite). pytest 103 passed,
  ruff clean, alle 8 sider åpner. **Reconciliation unchanged: 22 310 kr.**

**Leverandør v2 levert — full kartotek (K1–K8), alt redigerbart, ikke bare navn/org.nr.**

Mini-brief "Leverandør v2: full kartotek" (docs/BRIEF_LEVERANDOR_V2.md) delivered on main. Partner-
approved core-data-model change. Version 0.6.1 → **0.7.0** + requirements rebuild marker.
- **Foundation (K1)** — Supplier gains address/postal_code/city/website/email/phone/status/
  cooperation_rating; `ContactPerson.side` (SUPPLIER/INTERNAL); new `SupplierService` + `Qualification`
  models. `core/registry/leverandor.py` extended: full firma update, category add/remove, service
  CRUD, qualification CRUD, contact side — EVERY write appends an AuditLog row. Seed enriched.
- **K1** «Rediger firmadata» edits the whole firmakort (header shows status + address). **K2**
  kategorier as add/remove tags. **K3** tjenester/produkter full CRUD (optional price). **K4**
  kvalifikasjoner editable (navn + valgfri gyldig-til; utløpte i rødt). **K5** personer i to grupper
  (kontakt hos leverandøren + ansvarlig hos oss). **K6** kartotek-oversikt teller alle lister +
  «Kommer»-hooks. **K7** egen samarbeidsvurdering ved siden av auto-tall (KOFA-forbehold beholdt).
- **K8** `tests/test_leverandor_v2.py` (10 tester: firma/kategori/tjeneste/kvalifikasjon/side/audit);
  CI package-integrity guard utvidet med de nye modellfilene. pytest 102 passed, ruff clean, alle 8
  sider åpner. **Reconciliation unchanged: 22 310 kr.**

**Leverandør A–Z levert — første funksjon bygget som fullt verktøy (add→view→edit→delete→use).**

Mini-brief "Funksjon 1: Leverandør A–Z" (docs/BRIEF_LEVERANDOR_AZ.md) delivered on main. Partner-
approved core-data-model change; introduces **hard rule #12** (full-tool A→Z). Version 0.5.0 → 0.6.0.
- **Foundation** — new `ContactPerson` model; `Supplier` gains `notes` + `is_deleted` (soft delete).
  `core/registry/leverandor.py` = pure CRUD service (takes a Session, imports no UI, hard rule #1);
  EVERY write appends an AuditLog row (hard rule #7). `core/synth/kontakter.py` seeds synthetic
  contacts + notes. Version bump + requirements rebuild marker (hard rule #10).
- **L1** «＋ Ny leverandør» form (create). **L2** «✎ Rediger firmadata» (update, unique-org.nr guard).
  **L3** Kontaktpersoner full add/edit/delete. **L4** editable notat + kvalifikasjoner (categories).
  **L5** soft delete + «Vis slettede» + gjenopprett (row + trail kept). **L6** «Leverandørkartotek»
  gathers firma/kontakter/notat/avtaler/forpliktelser/fakturaer with honest «Kommer» hooks for the
  next functions. **L7** `tests/test_leverandor_crud.py` (10 tests: CRUD + one-audit-row-per-save).
- pytest 92 passed, ruff clean, all 8 pages open. **Reconciliation unchanged: 22 310 kr.** In-memory
  SQLite (StaticPool) → saves persist for the running demo-session (durable disk = out of scope).
- **Next functions (behind «Kommer»):** register avtale/forpliktelse/faktura from the kartotek.

**Grafikk v1 levert — én visuell identitet «Lyst kontor» (variant C) på alle 8 sider.**

Mini-brief "Grafikk v1" (docs/BRIEF_GRAFIKK_V1.md) delivered on main. Pure visual polish (in scope:
"visual polish of the Streamlit app") — NO engine/threshold/rule/core-model change, no version bump.
- **G1** — `app/theme.py`: single source of truth (navy #20364F, gold #A8842A, serif headings via
  Georgia, hairlines instead of shadows). `chrome.header()` injects the theme on every page.
- **G2** — `chrome.page_header(eyebrow, serif H1, lede, «Syntetiske data» chip)` replaces
  st.title()+caption on all 8 pages (every value html.escape()-d, hard rule #11).
- **G3** — Arbeidsflate variant C: KPI **editorial strip** (one connected strip w/ hairline dividers
  + semantic top-accents, not loose cards) + action tiles + «Krever handling» worklist and «Siste
  hendelser» feed **side by side**. Reconciliation unchanged: **Verdi funnet = 22 310 kr**.
- **G4** — verdict pills → rounded tinted chips (BRAND semantic colors kept); st.dataframe/HTML
  tables get hairline border, small radius, tabular-nums, paper headers; gold links global.
- **G5** — mobile-lite: @media(max-width:640px) wraps the KPI strip and scrolls wide tables,
  Streamlit stacks columns on its own; footer badge «Optimalisert for desktop». Full responsive =
  Phase 2.
- **G6** — wrap-up: `tests/test_grafikk.py` (all 8 pages open + theme/header present + reconciliation
  22 310 + mobile-lite CSS present). pytest 82 passed, ruff clean. BRAND.md updated to variant C
  (theme.py = runtime source of truth); verdict colors #2E7D32/#B58900/#C62828 untouched.

**Språk indikasjon-ikke-konklusjon levert (jurist-funn) — gyldighetsvurdering as indication, not verdict.**

Mini-brief "Språk: indikasjon, ikke konklusjon" (docs/BRIEF_INDIKASJON.md) delivered on main.
Legal red-team: a "vesentlig endring" shown as a CONCLUSION ("UGYLDIG") with a percentage is false
precision — vesentlig endring (FOA §28-1, C-454/06 Pressetext) is a legal skjønnsvurdering.
Language-only change (no engine/threshold/rule change): the three gyldighet outcomes are now
indications — "✓ SANNSYNLIGVIS GYLDIG", "⚠ KREVER FORMALISERING", "✗ MULIG UGYLDIG — krever
juridisk vurdering" (chip: "MULIG UGYLDIG", red kept). MULIG UGYLDIG text cites FOA §28-1 and
"vurder med jurist"; the % is only an internal trigger, never presented as the UI criterion. A
fixed grey disclaimer under every vurdering: "Gyldighetsvurderingen er en indikasjon som støtte for
saksbehandler — ikke en juridisk konklusjon." "Bekreft" stays active for all outcomes (hard rule
#3); audit text on confirm = "bekreftet tross indikasjon om mulig vesentlig endring". No version
bump (no schema change).

**Valuta v1 delivered — foreign-currency invoices: detect + flag, never convert.**

Mini-brief "Valuta v1" (docs/BRIEF_VALUTA_V1.md) delivered on main. Principle: DETECT + FLAG, zero
automatic exchange-rate conversion (hard rule #3; "better a flag than a silent guess").
- **W1** — new finding **CURRENCY_MISMATCH** (WARN → TIL_VURDERING) via core/matching/currency.py
  when `invoice.currency ≠ NOK`; commitments.check suspends price comparison for foreign currency so
  a raw EUR↔NOK difference never becomes a NOK deviation (deviation stays 0). Bumped core 0.3.0 → 0.4.0.
- **W2** — `db.money(amount, currency)` (kr for NOK, code otherwise; never converts). Fakturakontroll
  shows a currency banner + CURRENCY_MISMATCH anbefalt handling ("Fastsett valutakurs (Norges Bank)…").
  Arbeidsflate/Styringsinformasjon show foreign invoices separately ("N faktura(er) i utenlandsk
  valuta — krever manuell vurdering"), excluded from Verdi funnet (NOK).
- **W3** — demo EUR invoice F-EUR-1 (Hydraulik Süd GmbH, EUR) → CURRENCY_MISMATCH; tests in
  tests/test_valuta.py. **NOK reconciliation unchanged: Verdi funnet = 22 310 kr** (EUR adds 0).
- **Phase 2 (deliberately out of scope):** exchange-rate conversion (Norges Bank rate at invoice date).

**Leverandørkort v2 delivered — supplier card as a scoped, honest cooperation view.**

Mini-brief "Leverandørkort v2" (docs/BRIEF_LEVERANDORKORT_V2.md) delivered on main. The
Leverandørkort (Leverandører page) now shows, from synthetic/existing data only:
- **L1** Kategorier + kvalifikasjoner (core/synth/leverandor_profiler.py) — what the supplier may
  deliver, with validity; expired qualifications in red (UTLØPT).
- **L2** Kvalitetsvurdering (andel m/ funn, FTR, verdict-share bar) with a HARD legal annotation
  "innsikt i samarbeidet, IKKE en kvalifikasjonsrangering" (KOFA-vern); trend honestly deferred.
- **L3** Fakturerte objekter — invoice lines flagged på/utenfor avtale (context, not a machine
  register). Pure helper `avtale_status()`.
- **L4** "Leveranseoppfølging" roadmap marker (grey badge) — honest future area, no calendar built.
- **OUT of scope (deliberately NOT built):** machine/asset register, delivery calendar, star
  ranking. Tests in tests/test_leverandorkort.py.

**E-post-flyt v1 delivered — human-in-the-loop for e-mail commitment extraction.**

Mini-brief "E-post-flyt v1" (docs/BRIEF_EPOST_FLYT.md) delivered on main: a "Registrer fra e-post"
tab on Avtaler where a pasted e-mail is parsed (NO LLM — regex/keyword `core/extraction/epost.py`,
"KI-uttrekk: Under utvikling") into a NON-binding proposal; only after the human clicks "Bekreft"
does the Commitment enter the control basis (confirmed_by_user=True) with one AuditLog entry.
3 synthetic example e-mails (core/synth/epost_examples.py) showcase the three gyldighet outcomes:
KREVER FORMALISERING / GYLDIG / UGYLDIG (vesentlig endring >15 % / utvidet omfang → UGYLDIG,
"Bekreft" disabled). Pasted content is html.escape()-d (hard rule #11). Tests in tests/test_epost.py.

Also on main since Verifisering v1: **security & quality pass** (XXE via defusedxml, XSS escaping
of every unsafe_allow_html interpolation, texts.py cleanup, ruff config + CI), the **H1 core split**
(`evaluate_invoice` pure/read-only vs `check_invoice` persists — reads never write, ARCHITECTURE §5),
and a batch (EHF upload cap, verdict-pill dedup, Decimal-safe nok). CI (GitHub Actions: ruff+pytest)
runs on every push.

**Verifisering v1 delivered — demo shows full idea (3 sources, 2 directions, e-mail validity hierarchy).**

Mini-brief "Verifisering v1" (docs/BRIEF_VERIFISERING_V1.md) delivered in full on main:
- **V1** — Avtaler rebuilt as the differentiator: e-mail commitments as gold-border cards with
  source quote, formalization chips and a UI-level Gyldighetsvurdering (✓ GYLDIG / ⚠ KREVER
  FORMALISERING / ✗ UGYLDIG). Added nullable `source_quote` to Commitment.
- **V2** — Fakturakontroll shows Regelverkssjekk (the second direction: own procedure/terskel via
  the rules engine on the invoice's order), under the findings.
- **V3** — Internt reglement as the third source: core/rules/data/profiles/demo_reglement.yaml +
  ReglementEngine; findings carry a navy "Internt reglement" chip (Forpliktelser · Regelverk ·
  Internt reglement visually distinct). Procedural (deviation 0) — verdi funnet unchanged.
- **V4** — Leverandører page file renamed to ASCII (3_Leverandorer.py); title stays "Leverandører".
- **V6** — Leverandørkort drill-down (contracts, commitments, invoices with Åpne→, nøkkeltall,
  events). **V5** — this wrap-up.

Reconciliation (settled): **Verdi funnet = 22 310 kr** (both demo scenarios: deler 10 310 +
konsulent 12 000) — partner-confirmed as correct. This is the expected demo total for audits.

Engine additions to date (partner-approved): core/extraction/ehf.py (EHF/UBL parser),
core/rules ReglementEngine + profiles YAML, CSV export at UI level. `core/` still imports no UI.

Verify on the live Streamlit Cloud URL (auto-redeploy after push): all pages open, EHF upload loop
works (sample → upload → verdict), F-1003 shows all three sources, numbers reconcile at 22 310.
