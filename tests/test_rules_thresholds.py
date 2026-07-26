"""Table-driven tests for the 2026 threshold rules (EØS-justering fra 21.04.2026).

Each case: (regime, oppdragsgiver, kontrakttype, value NOK ex. VAT, date, expected consequences).
The expected set is EXACT — unexpected extra hits fail the test, which is how we catch overlapping
rule bands (e.g. a value matching two EØS thresholds at once).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.rules.engine import Facts, RulesEngine

ENGINE = RulesEngine()

# statlig / vare_tjeneste is the default; passed explicitly here for clarity.
CASES = [
    # --- FOA, statlig, varer/tjenester, after 1 July 2026 (innslagspunkt 500k) ---
    ("FOA", "statlig", "vare_tjeneste", "400000", date(2026, 8, 1), {"UTENFOR_LOVEN"}),
    ("FOA", "statlig", "vare_tjeneste", "499999.99", date(2026, 7, 1), {"UTENFOR_LOVEN"}),
    ("FOA", "statlig", "vare_tjeneste", "500000", date(2026, 8, 1), {"DEL_I_GRUNNLEGGENDE"}),
    ("FOA", "statlig", "vare_tjeneste", "800000", date(2026, 8, 1), {"DEL_I_GRUNNLEGGENDE"}),
    # --- FOA, before 1 July 2026 (innslagspunkt 100k) ---
    ("FOA", "statlig", "vare_tjeneste", "99999", date(2026, 6, 1), {"UTENFOR_LOVEN"}),
    ("FOA", "statlig", "vare_tjeneste", "400000", date(2026, 6, 1), {"DEL_I_GRUNNLEGGENDE"}),
    # --- FOA, statlig, national threshold and EØS (1,63 mill. fra 21.04.2026) ---
    ("FOA", "statlig", "vare_tjeneste", "1300000", date(2026, 8, 1), {"KUNNGJORING_DOFFIN_DEL_II"}),
    ("FOA", "statlig", "vare_tjeneste", "1629999", date(2026, 8, 1), {"KUNNGJORING_DOFFIN_DEL_II"}),
    ("FOA", "statlig", "vare_tjeneste", "1630000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    ("FOA", "statlig", "vare_tjeneste", "10000000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    # --- FOA, andre (kommune m.fl.), varer/tjenester, EØS 2,5 mill. ---
    ("FOA", "andre", "vare_tjeneste", "800000", date(2026, 8, 1), {"DEL_I_GRUNNLEGGENDE"}),
    ("FOA", "andre", "vare_tjeneste", "1300000", date(2026, 8, 1), {"KUNNGJORING_DOFFIN_DEL_II"}),
    ("FOA", "andre", "vare_tjeneste", "2499999", date(2026, 8, 1), {"KUNNGJORING_DOFFIN_DEL_II"}),
    ("FOA", "andre", "vare_tjeneste", "2500000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    # --- FOA, bygg/anlegg, EØS 62,9 mill. (only the EØS ceiling is modelled) ---
    ("FOA", "statlig", "bygg_anlegg", "60000000", date(2026, 8, 1), set()),
    ("FOA", "statlig", "bygg_anlegg", "62900000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    ("FOA", "andre", "bygg_anlegg", "70000000", date(2026, 8, 1), {"EOS_PROSEDYRE_DEL_III"}),
    # --- FOA, særlige/helse tjenester, EØS 8,7 mill. ---
    ("FOA", "statlig", "saerlige_tjenester", "5000000", date(2026, 8, 1), set()),
    ("FOA", "statlig", "saerlige_tjenester", "8700000", date(2026, 8, 1), {"EOS_SAERLIGE_TJENESTER"}),
    # --- FOSA, varer/tjenester: 500k innslagspunkt does NOT apply; protocol from 100k ---
    ("FOSA", "statlig", "vare_tjeneste", "50000", date(2026, 8, 1),
     {"INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "statlig", "vare_tjeneste", "200000", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "statlig", "vare_tjeneste", "4999999", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "statlig", "vare_tjeneste", "5000000", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "EOS_PROSEDYRE_FOSA"}),
    # --- FOSA, bygg/anlegg, EØS 62,9 mill. ---
    ("FOSA", "statlig", "bygg_anlegg", "200000", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "INGEN_NASJONAL_KUNNGJORINGSPLIKT"}),
    ("FOSA", "statlig", "bygg_anlegg", "62900000", date(2026, 8, 1),
     {"PROTOKOLLPLIKT", "EOS_PROSEDYRE_FOSA"}),
    # --- Art. 123 exemption -> RAF Del III documentation duty, any value ---
    ("ART123", "statlig", "vare_tjeneste", "1", date(2026, 8, 1),
     {"RAF_DEL_III_DOKUMENTASJONSPLIKT"}),
    ("ART123", "statlig", "vare_tjeneste", "50000000", date(2026, 8, 1),
     {"RAF_DEL_III_DOKUMENTASJONSPLIKT"}),
]


@pytest.mark.parametrize("regime,oppdragsgiver,kontrakttype,value,on,expected", CASES)
def test_threshold_consequences(regime, oppdragsgiver, kontrakttype, value, on, expected):
    hits = ENGINE.evaluate(Facts(
        regime=regime, estimated_value=Decimal(value), assessment_date=on,
        oppdragsgiver=oppdragsgiver, kontrakttype=kontrakttype,
    ))
    assert {h.consequence for h in hits} == expected


def test_defaults_are_statlig_vare_tjeneste():
    """Facts without discriminators = state authority, goods/services (the common case)."""
    hits = ENGINE.evaluate(Facts(regime="FOA", estimated_value=Decimal("1630000"),
                                 assessment_date=date(2026, 8, 1)))
    assert {h.consequence for h in hits} == {"EOS_PROSEDYRE_DEL_III"}


def test_every_hit_carries_a_citation():
    """Explainability is a hard requirement: a hit without a citation is a bug."""
    for regime, value in [("FOA", "750000"), ("FOSA", "6000000"), ("ART123", "100000")]:
        for hit in ENGINE.evaluate(Facts(regime=regime, estimated_value=Decimal(value),
                                         assessment_date=date(2026, 8, 1))):
            assert hit.citation.strip(), f"{hit.rule_id} has no citation"


def test_citation_amount_matches_value():
    """A citation must not state a different amount than the rule enforces (the audit blocker)."""
    hits = ENGINE.evaluate(Facts(regime="FOA", estimated_value=Decimal("1630000"),
                                 assessment_date=date(2026, 8, 1)))
    hit = next(h for h in hits if h.consequence == "EOS_PROSEDYRE_DEL_III")
    assert "1,63" in hit.citation
    assert "1,49" not in hit.citation


def test_regimes_are_isolated():
    """FOA rules must never fire for FOSA facts and vice versa."""
    hits = ENGINE.evaluate(Facts(regime="FOSA", estimated_value=Decimal("400000"),
                                 assessment_date=date(2026, 8, 1)))
    assert "UTENFOR_LOVEN" not in {h.consequence for h in hits}
