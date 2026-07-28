"""Leverandør (supplier) + kontaktperson CRUD service.

Pure core: every function takes a Session and returns domain objects; NO UI import (hard rule #1).
Every mutation appends an append-only AuditLog row (hard rule #7) so who/when/what is always
traceable. Deletion of a supplier is SOFT (is_deleted) — the row and its trail are kept; the system
records, it never erases (hard rule #3/#7).
"""
from __future__ import annotations

from sqlmodel import Session, select

from core.models import AuditLog, ContactPerson, Supplier


class RegistryError(ValueError):
    """Raised on invalid registry input (missing required field, duplicate org.nr, unknown id)."""


def _audit(session: Session, actor: str, action: str, entity: str, detail: str) -> None:
    session.add(AuditLog(actor=actor or "demo-bruker", action=action, entity=entity, detail=detail))


# --- Suppliers ----------------------------------------------------------------
def list_suppliers(session: Session, *, include_deleted: bool = False) -> list[Supplier]:
    """All suppliers, ordered by name. Soft-deleted are excluded unless include_deleted."""
    stmt = select(Supplier)
    if not include_deleted:
        stmt = stmt.where(Supplier.is_deleted == False)  # noqa: E712 (SQLModel needs ==)
    return list(session.exec(stmt.order_by(Supplier.name)).all())


def get_supplier(session: Session, supplier_id: int) -> Supplier | None:
    return session.get(Supplier, supplier_id)


def create_supplier(
    session: Session,
    *,
    org_number: str,
    name: str,
    categories: str | None = None,
    notes: str | None = None,
    iso_certified: bool = False,
    security_cleared: bool = False,
    actor: str = "demo-bruker",
) -> Supplier:
    """Create a supplier from scratch. org.nr and name are required; org.nr must be unique."""
    org_number = (org_number or "").strip()
    name = (name or "").strip()
    if not org_number:
        raise RegistryError("Organisasjonsnummer er påkrevd.")
    if not name:
        raise RegistryError("Navn er påkrevd.")
    existing = session.exec(select(Supplier).where(Supplier.org_number == org_number)).first()
    if existing is not None:
        raise RegistryError(f"Organisasjonsnummer {org_number} finnes allerede.")

    sup = Supplier(
        org_number=org_number, name=name,
        categories=(categories or None), notes=(notes or None),
        iso_certified=iso_certified, security_cleared=security_cleared,
    )
    session.add(sup)
    session.commit()
    session.refresh(sup)
    _audit(session, actor, "supplier.created", f"supplier:{sup.id}",
           f"leverandør opprettet: {sup.name} (org.nr {sup.org_number})")
    session.commit()
    return sup


def update_supplier(
    session: Session,
    supplier_id: int,
    *,
    name: str | None = None,
    org_number: str | None = None,
    categories: str | None = None,
    notes: str | None = None,
    iso_certified: bool | None = None,
    security_cleared: bool | None = None,
    actor: str = "demo-bruker",
) -> Supplier:
    """Update supplier fields. Only provided (non-None) fields change. org.nr stays unique.

    categories/notes are set to whatever is passed (pass "" to clear to NULL); the other fields
    are left untouched when None."""
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")

    changed: list[str] = []
    if name is not None and name.strip() and name.strip() != sup.name:
        sup.name = name.strip()
        changed.append("navn")
    if org_number is not None and org_number.strip() and org_number.strip() != sup.org_number:
        new_org = org_number.strip()
        clash = session.exec(
            select(Supplier).where(Supplier.org_number == new_org, Supplier.id != supplier_id)
        ).first()
        if clash is not None:
            raise RegistryError(f"Organisasjonsnummer {new_org} finnes allerede.")
        sup.org_number = new_org
        changed.append("org.nr")
    if categories is not None:
        new_cat = categories.strip() or None
        if new_cat != sup.categories:
            sup.categories = new_cat
            changed.append("kategorier")
    if notes is not None:
        new_notes = notes.strip() or None
        if new_notes != sup.notes:
            sup.notes = new_notes
            changed.append("notat")
    if iso_certified is not None and iso_certified != sup.iso_certified:
        sup.iso_certified = iso_certified
        changed.append("ISO")
    if security_cleared is not None and security_cleared != sup.security_cleared:
        sup.security_cleared = security_cleared
        changed.append("sikkerhetsklarering")

    session.add(sup)
    session.commit()
    session.refresh(sup)
    detail = ("endret: " + ", ".join(changed)) if changed else "lagret uten endringer"
    _audit(session, actor, "supplier.updated", f"supplier:{sup.id}",
           f"leverandør {detail} ({sup.name})")
    session.commit()
    return sup


def soft_delete_supplier(session: Session, supplier_id: int, *, actor: str = "demo-bruker") -> Supplier:
    """Mark a supplier deleted. The row and audit trail are KEPT (soft delete)."""
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    if not sup.is_deleted:
        sup.is_deleted = True
        session.add(sup)
        session.commit()
        _audit(session, actor, "supplier.deleted", f"supplier:{sup.id}",
               f"leverandør slettet (mykt, spor beholdt): {sup.name}")
        session.commit()
    session.refresh(sup)
    return sup


def restore_supplier(session: Session, supplier_id: int, *, actor: str = "demo-bruker") -> Supplier:
    """Undo a soft delete."""
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    if sup.is_deleted:
        sup.is_deleted = False
        session.add(sup)
        session.commit()
        _audit(session, actor, "supplier.restored", f"supplier:{sup.id}",
               f"leverandør gjenopprettet: {sup.name}")
        session.commit()
    session.refresh(sup)
    return sup


# --- Contact persons ----------------------------------------------------------
def list_contacts(session: Session, supplier_id: int) -> list[ContactPerson]:
    return list(session.exec(
        select(ContactPerson).where(ContactPerson.supplier_id == supplier_id)
        .order_by(ContactPerson.name)
    ).all())


def add_contact(
    session: Session,
    supplier_id: int,
    *,
    name: str,
    role: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    actor: str = "demo-bruker",
) -> ContactPerson:
    """Add a contact person to a supplier. Name is required."""
    if session.get(Supplier, supplier_id) is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    name = (name or "").strip()
    if not name:
        raise RegistryError("Navn på kontaktperson er påkrevd.")
    contact = ContactPerson(
        supplier_id=supplier_id, name=name,
        role=(role or None), email=(email or None), phone=(phone or None),
    )
    session.add(contact)
    session.commit()
    session.refresh(contact)
    _audit(session, actor, "contact.created", f"contact:{contact.id}",
           f"kontaktperson lagt til: {contact.name} (leverandør {supplier_id})")
    session.commit()
    return contact


def update_contact(
    session: Session,
    contact_id: int,
    *,
    name: str | None = None,
    role: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    actor: str = "demo-bruker",
) -> ContactPerson:
    """Update a contact person. name (when provided) must be non-empty; role/email/phone
    accept "" to clear to NULL."""
    contact = session.get(ContactPerson, contact_id)
    if contact is None:
        raise RegistryError(f"Ukjent kontaktperson: {contact_id}")
    if name is not None:
        if not name.strip():
            raise RegistryError("Navn på kontaktperson er påkrevd.")
        contact.name = name.strip()
    if role is not None:
        contact.role = role.strip() or None
    if email is not None:
        contact.email = email.strip() or None
    if phone is not None:
        contact.phone = phone.strip() or None
    session.add(contact)
    session.commit()
    session.refresh(contact)
    _audit(session, actor, "contact.updated", f"contact:{contact.id}",
           f"kontaktperson endret: {contact.name}")
    session.commit()
    return contact


def delete_contact(session: Session, contact_id: int, *, actor: str = "demo-bruker") -> None:
    """Delete a contact person. The removal is recorded in the append-only audit trail."""
    contact = session.get(ContactPerson, contact_id)
    if contact is None:
        raise RegistryError(f"Ukjent kontaktperson: {contact_id}")
    name, supplier_id = contact.name, contact.supplier_id
    session.delete(contact)
    session.commit()
    _audit(session, actor, "contact.deleted", f"contact:{contact_id}",
           f"kontaktperson slettet: {name} (leverandør {supplier_id})")
    session.commit()
