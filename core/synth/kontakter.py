"""Synthetic v2 kartotek data for the seeded demo suppliers.

Gives the Leverandør tool something to show on first open (edit/delete are then demonstrable):
firma fields, contacts on both sides, services/products, and qualifications (incl. one expired).
ALL DATA IS SYNTHETIC. Core module — no UI import. Idempotent: only seeds a supplier that has no
contacts yet, so re-running never duplicates.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from core.models import (
    SIDE_INTERNAL,
    SIDE_SUPPLIER,
    ContactPerson,
    Qualification,
    Supplier,
    SupplierService,
)

# org.nr -> full v2 seed for the synthetic suppliers.
_SEED: dict[str, dict] = {
    "998877665": {
        "firma": {
            "notes": "Fast leverandør av hydrauliske deler. Følg opp formalisering av e-postavtalen "
                     "(HYD-1001) med skriftlig tillegg. (Syntetisk notat.)",
            "address": "Havnegata 12", "postal_code": "8006", "city": "Bodø",
            "website": "hydraulikk-nord.example", "email": "post@hydraulikk-nord.example",
            "phone": "+47 75 00 00 00", "status": "Aktiv",
            "categories": "Hydrauliske deler, Vedlikehold, Reservedeler",
            "cooperation_rating": "God leveringspresisjon, men prisavvik må følges opp. (Syntetisk.)",
        },
        "contacts": [
            {"name": "Jonas Hansen", "role": "Kundeansvarlig", "side": SIDE_SUPPLIER,
             "email": "jonas.hansen@hydraulikk-nord.example", "phone": "+47 900 00 001"},
            {"name": "Kari Nordheim", "role": "Fakturakontakt", "side": SIDE_SUPPLIER,
             "email": "faktura@hydraulikk-nord.example", "phone": "+47 900 00 002"},
            {"name": "Per Innkjøp", "role": "Innkjøpsansvarlig (oss)", "side": SIDE_INTERNAL,
             "email": "per.innkjop@var-etat.example", "phone": "+47 400 00 001"},
        ],
        "services": [
            {"name": "Hydraulikkpumpe HYD-1001", "description": "Reservedel, rammeavtale",
             "unit": "stk", "unit_price": Decimal("12500")},
            {"name": "Vedlikeholdstime", "description": "Feltservice", "unit": "time",
             "unit_price": Decimal("950")},
        ],
        "qualifications": [
            {"name": "ISO 9001", "valid_to": date(2027, 6, 30)},
            {"name": "Startbank-registrert", "valid_to": None},
            {"name": "Sentral godkjenning (utløpt)", "valid_to": date(2025, 12, 31)},
        ],
    },
    "987654321": {
        "firma": {
            "notes": "Konsulentrammeavtale. Vær oppmerksom på timepris mot avtalt sats. (Syntetisk notat.)",
            "address": "Storgata 1", "postal_code": "0155", "city": "Oslo",
            "website": "konsulenthuset-ost.example", "email": "kontakt@konsulenthuset-ost.example",
            "phone": "+47 22 00 00 00", "status": "Aktiv",
            "categories": "Konsulenttjenester, IT-rådgivning",
            "cooperation_rating": None,
        },
        "contacts": [
            {"name": "Ola Berg", "role": "Oppdragsansvarlig", "side": SIDE_SUPPLIER,
             "email": "ola.berg@konsulenthuset-ost.example", "phone": "+47 900 00 010"},
            {"name": "Nina Kontrakt", "role": "Kontraktsansvarlig (oss)", "side": SIDE_INTERNAL,
             "email": "nina.kontrakt@var-etat.example", "phone": "+47 400 00 010"},
        ],
        "services": [
            {"name": "Seniorkonsulent", "description": "Rådgivning", "unit": "time",
             "unit_price": Decimal("1450")},
        ],
        "qualifications": [
            {"name": "ISO 27001", "valid_to": date(2027, 3, 31)},
        ],
    },
}


def seed(session: Session) -> None:
    """Attach synthetic v2 kartotek data to the seeded suppliers (once)."""
    for org, data in _SEED.items():
        sup = session.exec(select(Supplier).where(Supplier.org_number == org)).first()
        if sup is None:
            continue
        has_contacts = session.exec(
            select(ContactPerson).where(ContactPerson.supplier_id == sup.id)
        ).first()
        if has_contacts is not None:
            continue
        # Fresh supplier (no contacts yet) → populate the v2 firmakort fields.
        for attr, value in data["firma"].items():
            setattr(sup, attr, value)
        session.add(sup)
        for c in data["contacts"]:
            session.add(ContactPerson(supplier_id=sup.id, **c))
        for s in data["services"]:
            session.add(SupplierService(supplier_id=sup.id, **s))
        for q in data["qualifications"]:
            session.add(Qualification(supplier_id=sup.id, **q))
    session.commit()
