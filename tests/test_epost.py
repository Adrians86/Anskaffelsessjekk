"""E-post-flyt: parser extraction, gyldighet outcomes, and the human-in-the-loop gate."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.extraction.epost import (
    GYLDIG,
    KREVER_FORMALISERING,
    UGYLDIG,
    confirm_audit_detail,
    parse_email,
)
from core.models import Commitment, ConditionType, SourceType
from core.synth.epost_examples import EXAMPLE_EMAILS


def test_parser_extracts_amount_and_item_from_mail1():
    p = parse_email(EXAMPLE_EMAILS[0]["body"])
    assert p.value == Decimal("11800")          # "kr 11 800" — spaces normalised
    assert p.item_ref == "HYD-1001"
    assert p.condition_type == "PRICE"
    assert p.gyldighet == KREVER_FORMALISERING


def test_parser_prefers_til_value_in_mail2():
    # "fra kr 520 til kr 495" — the NEW value (495) is the one that matters.
    p = parse_email(EXAMPLE_EMAILS[1]["body"])
    assert p.value == Decimal("495")
    assert p.condition_type == "RATE"           # "timepris"
    assert p.gyldighet == GYLDIG                 # within "mindre justeringer" clause


def test_mail3_is_ugyldig_vesentlig_endring():
    p = parse_email(EXAMPLE_EMAILS[2]["body"])
    assert p.gyldighet == UGYLDIG               # +45 % / utvidet omfang


def test_confirmed_by_user_gate():
    """An e-mail extraction participates in control ONLY after a human confirms it."""
    base = dict(
        supplier_id=1, source_type=SourceType.EMAIL, source_ref="e-post 2026-06-12",
        condition_type=ConditionType.PRICE, item_ref="HYD-1001", value=Decimal("11800"),
        valid_from=date(2026, 6, 12), extracted_by="regel:epost-parser-v1",
    )
    on = date(2026, 7, 1)
    unconfirmed = Commitment(**base, confirmed_by_user=False)
    confirmed = Commitment(**base, confirmed_by_user=True)
    assert unconfirmed.is_active_on(on) is False   # unconfirmed -> excluded from control
    assert confirmed.is_active_on(on) is True      # confirmed -> participates


def test_empty_email_is_safe():
    p = parse_email("")
    assert p.value is None
    assert p.item_ref is None
    assert p.condition_type == "UNKNOWN"


def test_ugyldig_can_be_confirmed_and_is_flagged_in_audit():
    """Hard rule #3: no auto-blocking. An UGYLDIG e-mail CAN be registered by a human, but the
    audit entry marks it explicitly, and the confirmed commitment carries the UGYLDIG status."""
    # The confirm is not blocked — it produces a distinguished audit detail.
    detail = confirm_audit_detail("T. Olsen", UGYLDIG)
    assert "TROSS UGYLDIG-vurdering" in detail
    # A normal confirm has the plain detail (no override marker).
    assert "TROSS" not in confirm_audit_detail("J. Hansen", KREVER_FORMALISERING)

    # A confirmed UGYLDIG commitment still participates in control (human took responsibility),
    # and carries the recorded gyldighet for a red status in the register.
    c = Commitment(
        supplier_id=1, source_type=SourceType.EMAIL, source_ref="e-post",
        condition_type=ConditionType.SCOPE, valid_from=date(2026, 6, 12),
        gyldighet=UGYLDIG, extracted_by="regel:epost-parser-v1", confirmed_by_user=True,
    )
    assert c.gyldighet == "UGYLDIG"
    assert c.is_active_on(date(2026, 7, 1)) is True
