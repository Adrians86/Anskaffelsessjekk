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

## Current tasks (updated by the strategic partner)

**BLOCKER FIX** — `app/pages/4_Styringsinformasjon.py`: mark_barh() does not exist in Altair;
page crashes at runtime. Use mark_bar() with axes already swapped (→ horizontal). Replace
deprecated `use_container_width=True` with responsive properties.

**FIX** — `app/Hjem.py`: gold rule under title was lost (HTML div in gold #B08D2E, 3px).

**NEW FEATURE** — PDF protokoll export (last missing MVP piece):
- New module `core/reporting/protokoll.py` with `build_protokoll(session, invoice) -> bytes`
- Use fpdf2 (add to pyproject deps)
- Content in Norwegian: header “Anskaffelsesprotokoll — utkast”, invoice/supplier/order refs,
  verdict, findings table (grunnlag/citations), verdi_funnet, rules_version, timestamp,
  footer “Beslutningsstøtte — utkast generert av Anskaffelsessjekk. Kontrolleres og
  godkjennes av saksbehandler.” No Streamlit imports in core.
- UI: `st.download_button` (“Last ned protokoll (PDF)”) on 1_Fakturakontroll after check runs
- Tests: `tests/test_protokoll.py` — returns non-empty bytes starting with %PDF and
  produces different output for different invoices

**UPDATE** — This CLAUDE.md contract:
- Add “Definition of DONE” section (a/b/c/d above)
- Replace “Current tasks” section with findings above
- Update hard rule #8: pytest target is now 26 (not 24)
