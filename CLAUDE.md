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
