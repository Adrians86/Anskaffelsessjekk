"""Synthetic supplier profiles for the Leverandørkort: categories + qualifications.

ALL DATA IS SYNTHETIC. "What may this supplier deliver, and is the qualification still valid" —
NOT a qualification ranking, NOT an asset/machine register (see BRIEF_LEVERANDORKORT_V2 OUT of
scope). Pure data + helpers, no UI imports.
"""
from __future__ import annotations

from datetime import date

# Fixed reference "today" for the demo so expiry rendering is deterministic.
DEMO_TODAY = date(2026, 7, 20)

SUPPLIER_PROFILES: dict[str, dict] = {
    "998877665": {  # Hydraulikk Nord AS (SYNTETISK)
        "kategorier": ["Hydrauliske komponenter", "Vedlikehold og reservedeler"],
        "kvalifikasjoner": [
            {"navn": "ISO 9001 — kvalitetsstyring", "gyldig_til": date(2027, 12, 31)},
            {"navn": "Sikkerhetsklarering — leverandør", "gyldig_til": date(2026, 3, 31)},
        ],
    },
    "987654321": {  # Konsulenthuset Øst AS (SYNTETISK)
        "kategorier": ["Konsulenttjenester", "IKT og rådgivning"],
        "kvalifikasjoner": [
            {"navn": "Rammeavtale konsulent — kvalifisert", "gyldig_til": date(2027, 12, 31)},
            {"navn": "Databehandleravtale (GDPR)", "gyldig_til": date(2028, 6, 30)},
        ],
    },
    "DE811234567": {  # Hydraulik Süd GmbH (SYNTETISK) — foreign parts supplier (EUR)
        "kategorier": ["Hydrauliske komponenter (import)"],
        "kvalifikasjoner": [
            {"navn": "CE-samsvar (EU)", "gyldig_til": date(2027, 12, 31)},
        ],
    },
}


def profile_for(org_number: str) -> dict | None:
    """Synthetic profile for a supplier by org number, or None if unknown (e.g. uploaded)."""
    return SUPPLIER_PROFILES.get(org_number)


def is_expired(gyldig_til: date, on: date = DEMO_TODAY) -> bool:
    """True when a qualification's validity has passed (rendered in red)."""
    return gyldig_til < on


def avtale_status(item_ref: str, contract_item_refs: set[str]) -> str:
    """Classify an invoiced item as on/off contract (context only — not a machine register)."""
    return "på avtale" if item_ref in contract_item_refs else "utenfor avtale"
