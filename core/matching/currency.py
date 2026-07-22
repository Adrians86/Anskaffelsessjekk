"""Currency check: detect a foreign-currency invoice and FLAG it — never convert.

Principle (BRIEF_VALUTA_V1): detect + flag, zero automatic exchange-rate conversion. An exchange
rate is shaky audit ground, so we surface the problem (TIL_VURDERING) and leave the rate to a
human. When an invoice is not in NOK, price comparisons are suspended elsewhere (commitments.check)
so a raw amount difference never lies as a NOK deviation.
"""
from __future__ import annotations

from core.matching.findings import Code, Finding, Severity
from core.models import Invoice

BASE_CURRENCY = "NOK"


def is_foreign(invoice: Invoice) -> bool:
    """True when the invoice is not in the base (NOK) currency."""
    return bool(invoice.currency) and invoice.currency.upper() != BASE_CURRENCY


def check(session, invoice: Invoice) -> list[Finding]:
    if not is_foreign(invoice):
        return []
    return [Finding(
        code=Code.CURRENCY_MISMATCH, severity=Severity.WARN,
        invoice_id=invoice.id, invoice_line_id=None,
        message=(f"Faktura i {invoice.currency}, avtale/regelverk i NOK. Beløp kan ikke "
                 "sammenlignes direkte — kontroller kurs og grunnlag manuelt."),
        citation=("Terskelverdier og avtalepriser er i NOK — valutakontroll krever manuell "
                  "vurdering av kurs."),
    )]
