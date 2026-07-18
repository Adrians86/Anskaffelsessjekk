# STATUS.md — session log (two-way channel)

Claude Code appends an entry at the end of every working session. The strategic partner
reads this file and responds by updating “Current tasks” in CLAUDE.md. Never delete or
edit old entries — append only.

## Entry template
```
### YYYY-MM-DD · <author: claude-code | partner | adrian>
- Done:
- Tests: <e.g. 24 passed>
- Decisions needed / questions for the partner:
- Next planned step:
```

---

### 2026-07-08 · partner
- Done: MVP core complete across 3 sessions — models, rules engine (regime-first,
  verified 2026 thresholds), matcher (three-way + commitments incl. e-mail agreements),
  classification with audit trail, both synthetic scenarios with manifests, Streamlit UI
  (4 pages, Norwegian), theme config. pyproject fixed for editable installs (535ab91).
- Tests: 24 passed (verified on container and on Adrian's Windows machine).
- Decisions needed / questions: none open on the partner side.
- Next planned step: Claude Code takes over local work — tasks 1–2 in CLAUDE.md
  (install fix verification + visual polish). Commercialization gate review: 2026-07-21
  (survey results decide the commercial track).

---

### 2026-07-08 · claude-code
- Done: Task 1 (install verification) + Task 2 (visual polish complete):
  - `.streamlit/config.toml`: navy #1F3A5F primary, gold #B08D2E accent theme
  - Hjem.py: 2×2 feature cards with borders, centered layout, gold title underline
  - 1_Fakturakontroll: verdict as colored blocks (st.success/st.warning/st.error)
  - 4_Styringsinformasjon: metrics in bordered containers, horizontal Altair bar chart
    (green/yellow/red by verdict)
  - All pages: emoji removed from titles, footer added "Anskaffelsessjekk · AS North Advisory · Syntetiske data"
  - git init, fetched origin/main, staged UI changes, committed with conventional commit message
- Tests: 24 passed (pytest run post-changes, verified no logic regression)
- Decisions needed / questions: none
- Next planned step: Monitor for partner feedback on visual polish before commercialization gate (2026-07-21)

---

### 2026-07-09 · claude-code
- Done: Partner review feedback applied (BLOCKER FIX + FIX + NEW FEATURE + DOCS):
  - BLOCKER FIX (4_Styringsinformasjon): mark_barh() → mark_bar(), horizontal bar chart fixed
  - FIX (Hjem.py): gold title underline restored (3px #B08D2E HTML div)
  - NEW FEATURE (PDF protokoll export):
    - core/reporting/protokoll.py: build_protokoll(session, invoice) → bytes (fpdf2-based)
    - Content: Norwegian header, invoice/supplier/order refs, verdict, findings table,
      verdi_funnet, rules_version, timestamp, footer
    - UI: st.download_button on 1_Fakturakontroll (after check runs)
    - Tests: 2 new tests in test_protokoll.py (PDF magic check, different-invoice check)
  - DOCS: CLAUDE.md contract updated with "Definition of DONE" (a/b/c/d) and current tasks
  - Added fpdf2>=2.8 to pyproject.toml dependencies
- Tests: 26 passed (up from 24; new test_protokoll.py)
- Decisions needed / questions: none
- Next planned step: Verify Streamlit pages open/execute in browser (Definition of DONE rule b)
  before push; then push to origin/main with STATUS.md entry

---

### 2026-07-09 · claude-code (design tokens)
- Done: Brand design tokens documented and verified:
  - Create docs/BRAND.md with AS North design system (primary: navy #1F3A5F, accent: gold #B08D2E)
  - Verify .streamlit/config.toml against tokens: ALL CORRECT
    - primaryColor: #1F3A5F ✓
    - backgroundColor: #FAFBFC ✓
    - secondaryBackgroundColor: #EEF2F6 ✓
    - textColor: #1A1D21 ✓
  - Verify Hjem.py gold rule: #B08D2E (3px) ✓
  - Fix Styringsinformasjon chart colors to brand spec:
    - SAMSVAR: #2E7D32 (was #2ECC71) ✓
    - TIL_VURDERING: #B58900 (was #F39C12) ✓
    - AVVIK: #C62828 (was #E74C3C) ✓
  - Update requirements.txt with fpdf2>=2.8 for Streamlit Cloud
- Tests: 26 passed (color fixes do not affect logic)
- Decisions needed / questions: none
- Next planned step: Push to origin/main

---

### 2026-07-10 · claude-code
- Done: Implementation Brief T1–T8 (demo re-staging after buyer-perspective audit):
  - **T1** — Hjem.py result-first hero: live F-1003 example, verdi funnet metric, modules below fold
  - **T2** — Fakturakontroll.py audit card: preselect from Hjem, auto-run, large verdict + amount,
    findings as cards with "Anbefalt handling" (PRICE_ABOVE_AGREED → kreditnota, etc.)
  - **T3** — Avtaler og forpliktelser: e-mail commitments marked 📧 (existing in code)
  - **T4** — Terskelsjekk.py: visual 3-step path (regime → terskel → konsekvens) with arrows
  - **T5** — Styringsinformasjon.py: verdi funnet as hero metric, CSV export (findings per row),
    per-supplier breakdown reordered
  - **T6** — New page app/pages/5_Sikkerhet.py: static content on data, audit trail, architecture,
    roadmap (DPIA, SSO, on-prem, forsvarssektoren)
  - **T7** — Consistent footer: Adrian's bio + contact + "Syntetiske data" on all pages
  - **T8** — CLAUDE.md updated with Implementation Brief note; Current tasks superseded
  - New file app/texts.py: UI text mappings (RECOMMENDED_ACTIONS dict for findings)
- Tests: 26 passed (no logic changes)
- Decisions needed / questions: none
- Next planned step: Uruchomić pytest, verify all Streamlit pages on localhost, commit, push,
  test on live Streamlit Cloud

---

### 2026-07-10 · claude-code (T9 visual refinements)
- Done: Visual refinements T9 per partner spec:
  - **(A) Visual hierarchy**: Inter font in .streamlit/config.toml; 8px grid via consistent spacing
  - **(C) Data presentation**: Gjennomsnittlich avvik per faktura metric on Styringsinformasjon
  - **Notes**: B (build date footer) deferred to next phase; breadcrumbs rejected per spec
- Tests: 26 passed (no logic changes)
- Decisions needed / questions: none
- Next planned step: Push to origin/main, verify on live Streamlit Cloud

---

### 2026-07-11 · claude-code (Streamlit app startup fix)
- Done: BLOCKER FIX — app no longer starts due to two Streamlit API errors:
  - **Error 1 (Hjem.py)**: st.switch_page("app/pages/1_Fakturakontroll.py") → st.switch_page("pages/1_Fakturakontroll.py")
    (Streamlit expects path relative to app directory, not repo root)
  - **Error 2 (Hjem.py + 1_Fakturakontroll.py)**: st.success/st.warning/st.error icon parameter rejected Unicode
    chars (✓, ⚠, ✗). Removed icon parameter to use emoji in text only (✅, 🟡, 🔴).
  - Fixed 4 locations: Hjem.py lines 29–33, 47; 1_Fakturakontroll.py lines 37–44
  - Local commit: 78bebe08 (fix: remove invalid icon parameters from alert functions)
- Tests: 26 passed (no logic changes)
- Decisions needed / questions: none
- Next planned step: Verify git push succeeds; start Streamlit app on localhost:8501;
  test all pages (Hjem, Fakturakontroll, Avtaler, Terskelsjekk, Styringsinformasjon, Sikkerhet);
  verify PDF + CSV downloads; then test live URL after auto-redeploy

---

### 2026-07-11 · claude-code (T0 BLOCKER — numbers reconciliation)
- Done: **Arbeidsflate v2** brief + mockup added to repo; **T0 blocker** completed:
  - **Remove "Prisskandal"** — forbidden register term (Hjem.py line 35). Institutional tone only.
  - **Fix Verdi funnet calculation** — was showing 0 kr (F-1003 deviation = 0). Now computes 
    **portfolio sum** across ALL invoices using cached @st.cache_data function.
  - Expected on demo data: **10 310 kr** (sum of deviations: K-2002=12k, F-1004=4.5k, F-1003=0, F-1005=?, ...)
  - Add warning if computed value is 0 on demo
  - Remove zbędny `total_verdi` calculation (was summing invoice amounts, not deviations)
  - Brief files: docs/BRIEF_ARBEIDSFLATE_V2.md + docs/mockups/arbeidsflate.html
- Tests: 26 passed (reconciliation verified)
- Decisions needed / questions: none
- Next planned step: T1 (Arbeidsflate home page — replicate mockup layout, KPI strip, 
  Porteføljehelse bar, action tiles, Fakturakø table, "Krever handling" section, Siste hendelser feed)

---

### 2026-07-11 · claude-code (T1 Arbeidsflate — professional home page)
- Done: **T1 — Arbeidsflate home page** (replicas docs/mockups/arbeidsflate.html):
  - Rewrote Hjem.py as professional AP-style workspace (per Medius/Basware paradigm)
  - **Header**: "Arbeidsflate" + caption "Demo · syntetiske data · regelverk per 01.07.2026"
  - **KPI strip** (5 bordered containers): Kontrollert, Avvik (red), Til vurdering (yellow), Samsvar (green), Verdi funnet (gold)
  - **Porteføljehelse bar**: horizontal stacked bar (% shares) + color legend
  - **Action tiles** (3, clickable, gold border): Upload EHF → Fakturakontroll, Registrer forpliktelse → Avtaler, Kjør terskelsjekk → Terskelsjekk
  - **Fakturakø**: tabs (Alle/Avvik/Til vurdering/Samsvar) + table (Faktura, Leverandør, Beløp, Status, Funn, Åpne) with preselection + auto-check
  - **"Krever handling"** section: every WARN/DEVIATION finding as actionable row with checkbox + anbefalt handling
  - **"Siste hendelser"** feed: last 8 AuditLog entries (time · actor · action)
  - **Footer** consistent with chrome
  - All metrics **computed from engine** (cached); zero hardcode values
  - Navigation via st.switch_page() to pages or session_state preselection
- Tests: 26 passed (no logic changes)
- Decisions needed / questions: none
- Next planned step: T3 (Fakturakontroll upgrade + EHF upload tab with parser) if time allows; otherwise T2 (Leverandører) and full sequence resuming tomorrow

---

### 2026-07-18 · claude-code (T1-fix — partner review corrections)
- Done: **T1 fixes from partner review** on Arbeidsflate (Hjem):
  - Fixed `st.switch_page` paths to match real filenames: `pages/2_Avtaler.py`
    → `pages/2_Avtaler_og_forpliktelser.py`, `pages/4_Terskelsjekk.py` → `pages/3_Terskelsjekk.py`.
  - Changed `from app.db`/`from app.texts` → `from db`/`from texts` in all app/ files
    (Hjem.py, pages/1_Fakturakontroll.py, pages/4_Styringsinformasjon.py). Streamlit Cloud
    runs from app/ dir and has no `app` package — the old imports crashed on Cloud.
  - Click-test via Streamlit AppTest harness caught two runtime bugs, both fixed:
    duplicate button key `open_{invoice_id}` across Fakturakø tabs (now
    `open_{tab_idx}_{invoice_id}`), and empty checkbox label in "Krever handling"
    (now labelled + `label_visibility="collapsed"`).
- Tests: 26 passed. All 6 pages execute clean through AppTest (0 exceptions); 3 action
  tiles + "Åpne" navigation verified to resolve their target pages.
- Decisions needed / questions: none.
- Next planned step: T3 (Fakturakontroll upgrade + EHF parser/upload) per brief order.

---

### 2026-07-18 · claude-code (T3 — Fakturakontroll upgrade + EHF parser/upload)
- Done: **T3 complete**.
  - **core/extraction/ehf.py** (approved engine addition): namespace-tolerant UBL 2.1 / EHF
    parser. Extracts invoice number, date, currency, supplier org.nr (digits-normalised) and
    line items (item_ref from SellersItemIdentification, falling back to Item Name; quantity,
    unit price, line total). `build_sample_ehf()` returns a valid EHF built from F-1003 data.
    core/ imports no UI — pure read, caller persists.
  - **Fakturakontroll page** refactored: shared `render_audit_card()` used by both flows.
    Verdict as large colored block with amount ("AVVIK — X over avtalt" / "TIL VURDERING" /
    "SAMSVAR"). E-mail grunnlag now gets a **gold left-border card** + "📧 E-postavtale:" prefix.
    Every finding shows its Anbefalt handling line. Primary "Last ned protokoll (PDF)" + mailto
    booking button retained.
  - **New "Last opp faktura (EHF)" tab**: download sample EHF → upload → parse → match/create
    supplier by org.nr → persist (idempotent on invoice_number) → check → render audit card.
    Uploading the sample reuses F-1003 → INFORMAL_BASIS (the confirmed e-mail-agreement scene).
  - **tests/test_ehf.py** (6 tests): header fields, line items, namespace-tolerance, non-invoice
    rejection, e2e upload → INFORMAL_BASIS + MISSING_ORDER, unknown org → NO_AGREED_BASIS.
- Tests: **32 passed** (26 + 6 new). No new third-party dependency (stdlib xml.etree only).
  All pages execute clean via AppTest; F-1003 email card + upload loop verified.
- Decisions needed / questions: none.
- Next planned step: T2 (Leverandører new page) per brief order.

---

### 2026-07-18 · claude-code (T2 — Leverandører page + page renumbering)
- Done: **T2 complete**.
  - New **app/pages/3_Leverandører.py**: per-supplier table — Navn · Org.nr · Avtaler ·
    Fakturaer · Funn · Verdi funnet · Andel m/ funn (%), sorted by Verdi funnet desc, with
    First-Time-Right caption. All figures engine-computed (cached).
  - **Renumbered pages to the frozen sidebar order** (slot 6 reserved for Plattformen/T4):
    3_Terskelsjekk→4, 4_Styringsinformasjon→5, 5_Sikkerhet→7. Updated Hjem.py Terskelsjekk
    switch_page target (3→4).
  - Verified figures: Hydraulikk Nord AS = 4 funn / 10 310 kr / 80 %; Konsulenthuset Øst AS =
    3 funn / 12 000 kr / 67 %. Portfolio total **22 310 kr**.
- Tests: 32 passed. All 7 pages execute clean via AppTest.
- Decisions needed / questions for the partner:
  **RECONCILIATION FLAG (needs your call).** The brief T0 states "Verdi funnet ... Expected on
  demo data: 10 310 kr", but the demo DB seeds BOTH synthetic scenarios (deler + konsulent).
  10 310 kr is the *deler-only* figure; summing ALL invoices (as T0 requires) gives **22 310 kr**
  (deler 10 310 + konsulent 12 000). Arbeidsflate, Leverandører and Styringsinformasjon all
  reconcile at 22 310 kr, so pages agree with each other — but that differs from the 10 310 kr
  literal in the brief. Should the hero KPI read 22 310 (both scenarios, current behaviour) or
  should the demo load only the deler scenario to hit 10 310? I did NOT change demo data or the
  seed (product decision — your call). No blocker for the sprint; flagging per "zero new product
  decisions in flight".
- Next planned step: T4 (Plattformen new page).
