# Anskaffelsessjekk — Mini-brief "Valuta v1"

Partner directive · 2026-07-21. Handling foreign-currency invoices. Execute W1 → W3, commit+push
after each, full DoD. All UI text Norwegian (bokmål).

**Principle: DETECT + FLAG, ZERO automatic exchange-rate conversion.** An exchange rate is shaky
audit ground — we show the problem, the human decides. Aligned with hard rule #3 (we inform, we do
not decide) and the "better a flag than a silent guess" philosophy.

## W1 — Currency detection in the engine
- The EHF parser already reads DocumentCurrencyCode — ensure the currency reaches Invoice
  (`Invoice.currency` field; bump version + rebuild-marker per hard rule #10 for the core change).
- In evaluate_invoice/check_invoice: if invoice currency ≠ contract/price currency (default NOK) →
  a NEW finding code **CURRENCY_MISMATCH**, severity mapping **TIL_VURDERING** (not AVVIK — this is
  not an error, it needs attention):
  - message: "Faktura i {valuta}, avtale/regelverk i NOK. Beløp kan ikke sammenlignes direkte —
    kontroller kurs og grunnlag manuelt."
  - citation: "Terskelverdier og avtalepriser er i NOK — valutakontroll krever manuell vurdering
    av kurs."
- KEY: when currency ≠ NOK, do NOT compute deviation_amount from the raw amount difference
  (12 000 EUR ≠ 12 000 NOK) — deviation for that line = None/0 so verdi funnet does not lie. Price
  comparisons are suspended until a manual rate is set.

## W2 — UI
- Fakturakontroll: a foreign-currency invoice shows a currency chip (e.g. "EUR") by the amount +
  the CURRENCY_MISMATCH finding as TIL VURDERING with anbefalt handling: "Fastsett valutakurs
  (Norges Bank) på fakturadato og vurder mot avtalt NOK-pris." Amounts rendered with the invoice's
  currency code, not always "kr".
- Styringsinformasjon/Arbeidsflate: foreign-currency invoices do NOT enter the verdi funnet (NOK)
  sum — show them separately as "N fakturaer i utenlandsk valuta — krever manuell vurdering".
  NOK reconciliation untouched.

## W3 — Demo data + wrap-up
- Add to synth 1 EUR invoice (e.g. a foreign parts supplier) triggering CURRENCY_MISMATCH →
  TIL VURDERING.
- Tests: (a) EUR invoice → CURRENCY_MISMATCH finding; (b) deviation_amount not computed from raw
  currency difference; (c) NOK verdi funnet unchanged by the currency invoice. pytest green, ruff,
  CLAUDE.md + STATUS, push.
- STATUS note: exchange-rate conversion (Norges Bank, rate at invoice date) = Phase 2, deliberately
  out of scope.

## Acceptance
An EUR invoice is flagged TIL VURDERING with a clear "krever manuell vurdering av kurs" message;
it does not pollute the NOK verdi funnet; reconciliation holds.
