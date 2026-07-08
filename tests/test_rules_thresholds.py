"""Table-driven tests for the 2026 threshold rules.

Each case: (regime, value NOK ex. VAT, assessment date, expected consequences).
The expected set is EXACT — unexpected extra hits fail the test, which is how
we catch overlapping rule bands when the law changes.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.rules.engine import Facts, RulesEngine

ENGINE = RulesEngine()

CASES = [
    # --- FOA, after 1 July 2026 (innslagspunkt 500k) ---
    ("FOA", "400000", date(2026, 8, 1), {"UTENFOR_LOVEN"}),
    ("FOA", "499999.99", date(2026, 7, 1), {"UTENFOR_LOVEN"}),
    ("FOA", "500000", date(2026, 8, 1), {"DEL_I_GRUNNLEGGENDE"}),
    ("FOA", "800000", date(2026, 8, 1), {"DEL_I_GRUNNLEGGENDE"}),
    # --- FOA, before 1 July 2026 (innslagspunkt 100k) ---
    ("FOA", "99999", date(2026, 6, 1), {"UTENFOR_LOVEN"}),
    ("FOA", "400000", date(2026, 6, 1), {"DEL_I_GRUNNLEGGENDE"}),
    # --- FOA, national threshold and EOS ---
    ("FOA", "1300000", date(2026, 8, 1), {"KUNNGJORING_DOFFIN_DEL_II"}),
    ("FOA", "1489999", date(2026, 8, 1), {"KUNNGJORING_DOFFIN_DEL_II"}),
    ("FOA", "1490000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    ("FOA", "10000000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    # --- FOSA: 500k innslagspunkt does NOT apply; protocol from 100k ---
    ("FOSA", "50000", date(2026, 8, 1), {"INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "200000", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "4999999", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "5000000", date(2026, 8, 1), {"PROTOKOLLPLIKT", "EOS_PROSEDYRE_FOSA"}),
    # --- Art. 123 exemption -> RAF Del III documentation duty, any value ---
    ("ART123", "1", date(2026, 8, 1), {"RAF_DEL_III_DOKUMENTASJONSPLIKT"}),
    ("ART123", "50000000", date(2026, 8, 1), {"RAF_DEL_III_DOKUMENTASJONSPLIKT"}),
]


@pytest.mark.parametrize("regime,value,on,expected", CASES)
def test_threshold_consequences(regime: str, value: str, on: date, expected: set[str]):
    hits = ENGINE.evaluate(Facts(regime=regime, estimated_value=Decimal(value), assessment_date=on))
    assert {h.consequence for h in hits} == expected


def test_every_hit_carries_a_citation():
    """Explainability is a hard requirement: a hit without a citation is a bug."""
    for regime, value, on in [
        ("FOA", "750000", date(2026, 8, 1)),
        ("FOSA", "6000000", date(2026, 8, 1)),
        ("ART123", "100000", date(2026, 8, 1)),
    ]:
        for hit in ENGINE.evaluate(
            Facts(regime=regime, estimated_value=Decimal(value), assessment_date=on)
        ):
            assert hit.citation.strip(), f"{hit.rule_id} has no citation"


def test_regimes_are_isolated():
    """FOA rules must never fire for FOSA facts and vice versa."""
    hits = ENGINE.evaluate(
        Facts(regime="FOSA", estimated_value=Decimal("400000"), assessment_date=date(2026, 8, 1))
    )
    assert "UTENFOR_LOVEN" not in {h.consequence for h in hits}
