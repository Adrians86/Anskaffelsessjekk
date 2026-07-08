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
8. `pytest` must be green (currently 24 passed) before every commit. Run it before and after changes.
9. Conventional commit messages (feat/fix/test/docs/style/build).

## Scope freeze — until the commercialization gate (2026-07-21)
ALLOWED: visual polish of the Streamlit app, PDF protokoll export, bugfixes,
Streamlit Community Cloud deploy preparation, test coverage improvements.
FORBIDDEN without partner approval (ask via STATUS.md): Next.js or any UI framework
change, authentication, new modules/features, database migration (SQLite stays),
external integrations, changes to core data model.

## Current tasks (updated by the strategic partner)
1. **Fix local install if still broken**: `pip install -e ".[ui]"` must succeed in `.venv`
   and `python -m streamlit run app/Hjem.py` must start. pyproject has explicit package
   discovery since commit 535ab91.
2. **Visual polish of the Streamlit app** (no logic changes, no core/ changes):
   - palette from `.streamlit/config.toml`: navy #1F3A5F primary, gold #B08D2E accent only
   - Hjem.py: four feature cards with `st.container(border=True)`; header with product
     name and a thin gold rule under the title; `layout="centered"` on Hjem, wide elsewhere
   - 1_Fakturakontroll: verdict as a colored block (st.success/st.warning/st.error), large text
   - 4_Styringsinformasjon: metrics in bordered containers; replace bar_chart with a
     horizontal bar (plotly or altair) colored green/yellow/red per verdict
   - remove emoji from page titles (keep in sidebar); footer on every page:
     “Anskaffelsessjekk · AS North Advisory · Syntetiske data”
3. After each task: run pytest (24 passed), commit, append a STATUS.md entry.
