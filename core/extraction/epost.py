"""Best-effort extraction of a proposed commitment from a pasted e-mail body.

NOT an LLM (an API key is risk/cost in a public demo) — simple, transparent text recognition
(regex + keywords). The result is only a PROPOSAL: a human confirms it before it enters control
(human-in-the-loop). This module belongs to core/ and imports nothing from any UI.

The gyldighetsvurdering here is a demo-level heuristic (see BRIEF_EPOST_FLYT E2b): an e-mail is
never a self-standing proof — it is checked against the contract and the regelverk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

# Gyldighet outcomes (also used by the UI badge).
GYLDIG = "GYLDIG"
KREVER_FORMALISERING = "KREVER_FORMALISERING"
UGYLDIG = "UGYLDIG"

# Above this relative increase (or an explicit scope expansion) an e-mail cannot bind — it is a
# vesentlig endring that requires a new competition. Data, not magic: kept as a named threshold.
_VESENTLIG_PCT = Decimal("15")

_ITEM_RE = re.compile(r"\b([A-ZÆØÅ]{2,}-\d{3,})\b")
_KR_RE = re.compile(r"kr\.?\s*([\d\s.]+\d)(?:,(\d{1,2}))?", re.IGNORECASE)
_PCT_RE = re.compile(r"(\d{1,3})\s*%")

_SCOPE_WORDS = ("utvider", "utvide", "utvidet omfang", "nye maskintyper", "øker rammen",
                "utvider leveransen")
_MINDRE_WORDS = ("mindre justering",)


@dataclass(frozen=True)
class ProposedCommitment:
    """A NON-binding proposal parsed from an e-mail. Enters control only after human confirm."""
    item_ref: str | None
    condition_type: str            # PRICE | RATE | DEADLINE | SCOPE | UNKNOWN
    value: Decimal | None
    unit: str | None
    gyldighet: str                 # GYLDIG | KREVER_FORMALISERING | UGYLDIG
    gyldighet_reason: str


def _parse_amount(text: str) -> Decimal | None:
    """Extract a NOK amount. If the text says 'fra kr X til kr Y', prefer Y (the new value)."""
    matches = list(_KR_RE.finditer(text))
    if not matches:
        return None
    chosen = matches[-1] if ("til" in text.lower() and len(matches) > 1) else matches[0]
    whole = chosen.group(1).replace(" ", "").replace(".", "")
    frac = chosen.group(2)
    raw = f"{whole}.{frac}" if frac else whole
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _condition_type(text: str) -> str:
    low = text.lower()
    if "timepris" in low or "per time" in low or "/h" in low:
        return "RATE"
    if "pris" in low:
        return "PRICE"
    if "frist" in low or "leveringsdato" in low or "forfall" in low:
        return "DEADLINE"
    if any(w in low for w in _SCOPE_WORDS):
        return "SCOPE"
    return "UNKNOWN"


def _assess_gyldighet(text: str) -> tuple[str, str]:
    """Demo heuristic: vesentlig endring -> UGYLDIG; mindre justering clause -> GYLDIG;
    otherwise an informal price change -> KREVER FORMALISERING."""
    low = text.lower()
    pct = next((Decimal(m.group(1)) for m in _PCT_RE.finditer(text)), None)
    scope_expansion = any(w in low for w in _SCOPE_WORDS)
    if scope_expansion or (pct is not None and pct > _VESENTLIG_PCT):
        return (UGYLDIG,
                "Vesentlig endring (>15 % / utvidet omfang) — krever ny konkurranse, "
                "kan ikke avtales per e-post.")
    if any(w in low for w in _MINDRE_WORDS):
        return (GYLDIG, "Innenfor avtalens klausul om mindre justeringer per e-post.")
    return (KREVER_FORMALISERING,
            "Avtalen krever skriftlig tillegg — e-posten er varsel, ikke dokumentasjon.")


def parse_email(text: str) -> ProposedCommitment:
    """Parse a pasted e-mail body into a proposed (non-binding) commitment."""
    text = text or ""
    item_match = _ITEM_RE.search(text)
    gyldighet, reason = _assess_gyldighet(text)
    return ProposedCommitment(
        item_ref=item_match.group(1) if item_match else None,
        condition_type=_condition_type(text),
        value=_parse_amount(text),
        unit="NOK",
        gyldighet=gyldighet,
        gyldighet_reason=reason,
    )
