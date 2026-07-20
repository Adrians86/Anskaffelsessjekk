# Anskaffelsessjekk — Mini-brief "E-post-flyt v1"

Partner directive · 2026-07-20. Demonstrates human-in-the-loop for extraction of e-mail
commitments. Execute E1 → E2/E2b → E3, commit+push after each step, full DoD. All UI text
Norwegian (bokmål). **No LLM in production** (an API key = risk/cost in a public demo) — extraction
is a form + simple parsing, annotated "KI-uttrekk: Under utvikling".

## E1 — Tab "Registrer fra e-post" on the Avtaler og forpliktelser page
- `st.text_area` for pasting the e-mail body + fields: leverandør (selectbox of existing suppliers),
  avsender, dato.
- Button "Foreslå forpliktelse" → a simple parser extracts from the text: amount (regex on
  "kr"/numbers), item_ref (regex on patterns like HYD-XXXX), condition type (PRICE if "pris",
  DEADLINE if "frist/dato", …) — best-effort, NOT an LLM.
- Result shown as a PROPOSED Commitment (non-editable preview card) with fields for a human to
  confirm/correct.
- Two buttons: "Bekreft og legg til" (confirmed_by_user=True → persist) / "Avvis".
- Annotation under the tab: "KI-uttrekk fra e-post er under utvikling. I demo brukes enkel
  tekstgjenkjenning — saksbehandler bekrefter alltid før forpliktelsen inngår i kontroll."
- KEY: only after "Bekreft" does the commitment enter the control basis (human-in-the-loop). Persist
  via the check-path (a real action → AuditLog: "forpliktelse bekreftet fra e-post av demo-bruker").
- html.escape() on the pasted content (hard rule #11 — this is exactly the user-input we hardened
  against).

## E2 — 3 example e-mails for the demo
Button "Last inn eksempel" fills the text_area; synthetic data; add to core/synth as examples:
- Mail 1 (→ KREVER FORMALISERING, matches the contract but needs an annex):
  "Hei. Vi bekrefter redusert pris kr 11 800 per stk for HYD-1001, gjeldende fra 12. juni. Formelt
  tillegg ettersendes. Mvh J. Hansen, Hydraulikk Nord AS"
- Mail 2 (→ GYLDIG, within the "mindre justeringer per e-post" clause):
  "Hei. Som avtalt justerer vi timepris renhold fra kr 520 til kr 495 fra neste måned, iht.
  rammeavtalens punkt om mindre justeringer. Mvh K. Berg, Renhold Øst AS"
- Mail 3 (→ UGYLDIG, vesentlig endring — beyond the contract):
  "Hei. Vi utvider leveransen med tre nye maskintyper og øker rammen med 45%, gjeldende umiddelbart.
  Mvh T. Olsen, leverandør"

### E2b — gyldighetsvurdering for each (reuse V1 logic)
Mail 3 shows ✗ UGYLDIG with the reason "Vesentlig endring (>15% / utvidet omfang) — krever ny
konkurranse, kan ikke avtales per e-post" (new threshold in the logic: value/scope increase above
the threshold → UGYLDIG).

## E3 — Wrap-up
Tests (parser extracts the amount from mail 1; confirmed_by_user gate works; mail 3 → UGYLDIG),
pytest green, CLAUDE.md Current tasks update, STATUS + push. Live verification: the tab works,
"Last inn eksempel" → "Foreslå" → "Bekreft" → commitment in the register.

## Acceptance
Paste an e-mail → get a proposal → confirm → it enters control with an audit-trail entry;
mail 3 flagged UGYLDIG; an unconfirmed e-mail does NOT participate in control.
