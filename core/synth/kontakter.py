"""Synthetic contact persons + notes for the seeded demo suppliers.

Gives the Leverandør A–Z tool something to show on first open (edit/delete are then demonstrable).
ALL DATA IS SYNTHETIC. Core module — no UI import. Idempotent: only seeds a supplier that has no
contacts yet, so re-running never duplicates.
"""
from __future__ import annotations

from sqlmodel import Session, select

from core.models import ContactPerson, Supplier

# org.nr -> (notes, [contacts]) for the two seeded synthetic suppliers.
_SEED: dict[str, dict] = {
    "998877665": {
        "notes": "Fast leverandør av hydrauliske deler. Følg opp formalisering av e-postavtalen "
                 "(HYD-1001) med skriftlig tillegg. (Syntetisk notat.)",
        "contacts": [
            {"name": "Jonas Hansen", "role": "Kundeansvarlig",
             "email": "jonas.hansen@hydraulikk-nord.example", "phone": "+47 900 00 001"},
            {"name": "Kari Nordheim", "role": "Fakturakontakt",
             "email": "faktura@hydraulikk-nord.example", "phone": "+47 900 00 002"},
        ],
    },
    "987654321": {
        "notes": "Konsulentrammeavtale. Vær oppmerksom på timepris mot avtalt sats. (Syntetisk notat.)",
        "contacts": [
            {"name": "Ola Berg", "role": "Oppdragsansvarlig",
             "email": "ola.berg@konsulenthuset-ost.example", "phone": "+47 900 00 010"},
        ],
    },
}


def seed(session: Session) -> None:
    """Attach synthetic contacts + notes to the seeded suppliers (once)."""
    for org, data in _SEED.items():
        sup = session.exec(select(Supplier).where(Supplier.org_number == org)).first()
        if sup is None:
            continue
        has_contacts = session.exec(
            select(ContactPerson).where(ContactPerson.supplier_id == sup.id)
        ).first()
        if has_contacts is not None:
            continue
        if sup.notes is None:
            sup.notes = data["notes"]
            session.add(sup)
        for c in data["contacts"]:
            session.add(ContactPerson(supplier_id=sup.id, **c))
    session.commit()
