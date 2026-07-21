"""Leverandørkort v2: synthetic profiles, expiry flagging, på/utenfor avtale classification."""
from __future__ import annotations

from datetime import date

from core.synth.leverandor_profiler import (
    DEMO_TODAY,
    avtale_status,
    is_expired,
    profile_for,
)


def test_profiles_load_for_demo_suppliers():
    assert profile_for("998877665") is not None       # Hydraulikk Nord AS
    assert profile_for("987654321") is not None       # Konsulenthuset Øst AS
    assert profile_for("000000000") is None           # unknown / uploaded supplier
    assert profile_for("998877665")["kategorier"]     # categories present


def test_expired_qualification_is_flagged():
    quals = profile_for("998877665")["kvalifikasjoner"]
    expired = [q for q in quals if is_expired(q["gyldig_til"])]
    assert any("Sikkerhetsklarering" in q["navn"] for q in expired)   # one expired (red)
    # Konsulenthuset Øst has only valid qualifications.
    assert all(not is_expired(q["gyldig_til"])
               for q in profile_for("987654321")["kvalifikasjoner"])


def test_is_expired_boundary():
    assert is_expired(date(2026, 7, 19)) is True       # day before DEMO_TODAY
    assert is_expired(DEMO_TODAY) is False             # not < today
    assert is_expired(date(2027, 1, 1)) is False


def test_avtale_status_classification():
    refs = {"HYD-1001", "HYD-2002"}
    assert avtale_status("HYD-1001", refs) == "på avtale"
    assert avtale_status("UKJENT-9", refs) == "utenfor avtale"
