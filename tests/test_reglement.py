"""Internal reglement rules — table-driven cases (the third control source)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from core.rules.engine import ReglementEngine


@pytest.fixture(scope="module")
def engine() -> ReglementEngine:
    return ReglementEngine()


# (facts, expected consequence codes present)
_CASES = [
    # INTERN_ATTESTASJON_100K fires at/above 100 000.
    ({"invoice_total": Decimal("118000"), "estimated_value": Decimal("118000"), "has_contract": 1},
     {"KREVER_ATTESTASJON_2_PERSONER"}),
    ({"invoice_total": Decimal("100000"), "estimated_value": Decimal("0"), "has_contract": 1},
     {"KREVER_ATTESTASJON_2_PERSONER"}),
    # Below 100 000 with a contract: nothing.
    ({"invoice_total": Decimal("83000"), "estimated_value": Decimal("83000"), "has_contract": 1},
     set()),
    # INTERN_TERSKEL_ENKELTKJOP: >= 50 000 AND no contract.
    ({"invoice_total": Decimal("60000"), "estimated_value": Decimal("60000"), "has_contract": 0},
     {"KREVER_INNKJOPSORDRE"}),
    # >= 50 000 but has a contract: enkeltkjop rule does NOT fire.
    ({"invoice_total": Decimal("60000"), "estimated_value": Decimal("60000"), "has_contract": 1},
     set()),
    # < 50 000 and no contract: enkeltkjop rule does NOT fire.
    ({"invoice_total": Decimal("19600"), "estimated_value": Decimal("19600"), "has_contract": 0},
     set()),
    # Both rules fire together: >= 100 000 invoice, >= 50 000 order, no contract.
    ({"invoice_total": Decimal("120000"), "estimated_value": Decimal("120000"), "has_contract": 0},
     {"KREVER_ATTESTASJON_2_PERSONER", "KREVER_INNKJOPSORDRE"}),
]


@pytest.mark.parametrize("facts, expected", _CASES)
def test_reglement_cases(engine, facts, expected):
    hits = engine.evaluate(facts)
    assert {h.consequence for h in hits} == expected


def test_every_hit_has_internal_citation(engine):
    hits = engine.evaluate(
        {"invoice_total": Decimal("120000"), "estimated_value": Decimal("120000"), "has_contract": 0}
    )
    assert hits
    for h in hits:
        assert "Internt reglement" in h.citation
        assert h.message  # human-readable Norwegian message present
