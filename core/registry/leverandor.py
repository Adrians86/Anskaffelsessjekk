"""Leverandør (supplier) + kontaktperson CRUD service.

Pure core: every function takes a Session and returns domain objects; NO UI import (hard rule #1).
Every mutation appends an append-only AuditLog row (hard rule #7) so who/when/what is always
traceable. Deletion of a supplier is SOFT (is_deleted) — the row and its trail are kept; the system
records, it never erases (hard rule #3/#7).
"""
from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from core.models import (
    SIDE_SUPPLIER,
    AuditLog,
    ContactPerson,
    Qualification,
    Supplier,
    SupplierService,
)

# Supplier status values (v2).
SUPPLIER_STATUSES = ("Aktiv", "Inaktiv", "Sperret")


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
    address: str | None = None,
    postal_code: str | None = None,
    city: str | None = None,
    website: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    status: str | None = None,
    cooperation_rating: str | None = None,
    actor: str = "demo-bruker",
) -> Supplier:
    """Update supplier fields. Only provided (non-None) fields change. org.nr stays unique.

    Free-text fields accept "" to clear to NULL; the flag fields are left untouched when None."""
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    if status is not None and status not in SUPPLIER_STATUSES:
        raise RegistryError(f"Ugyldig status: {status}")

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
    # v2 free-text firmakort fields ("" clears to NULL).
    for value, attr, label in (
        (address, "address", "adresse"),
        (postal_code, "postal_code", "postnr"),
        (city, "city", "sted"),
        (website, "website", "nettside"),
        (email, "email", "e-post"),
        (phone, "phone", "telefon"),
        (cooperation_rating, "cooperation_rating", "samarbeidsvurdering"),
    ):
        if value is not None:
            new_val = value.strip() or None
            if new_val != getattr(sup, attr):
                setattr(sup, attr, new_val)
                changed.append(label)
    if status is not None and status != sup.status:
        sup.status = status
        changed.append("status")

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
def list_contacts(
    session: Session, supplier_id: int, *, side: str | None = None,
) -> list[ContactPerson]:
    """Contacts for a supplier, optionally filtered to one side (SUPPLIER / INTERNAL)."""
    stmt = select(ContactPerson).where(ContactPerson.supplier_id == supplier_id)
    if side is not None:
        stmt = stmt.where(ContactPerson.side == side)
    return list(session.exec(stmt.order_by(ContactPerson.name)).all())


def add_contact(
    session: Session,
    supplier_id: int,
    *,
    name: str,
    role: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    side: str = SIDE_SUPPLIER,
    actor: str = "demo-bruker",
) -> ContactPerson:
    """Add a contact person to a supplier. Name is required. `side` groups it (leverandør / intern)."""
    if session.get(Supplier, supplier_id) is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    name = (name or "").strip()
    if not name:
        raise RegistryError("Navn på kontaktperson er påkrevd.")
    contact = ContactPerson(
        supplier_id=supplier_id, name=name, side=side,
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


# --- Categories (tags: what the supplier delivers) ----------------------------
def _split_categories(raw: str | None) -> list[str]:
    return [c.strip() for c in (raw or "").split(",") if c.strip()]


def list_categories(session: Session, supplier_id: int) -> list[str]:
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    return _split_categories(sup.categories)


def add_category(session: Session, supplier_id: int, category: str,
                 *, actor: str = "demo-bruker") -> Supplier:
    """Add one category tag (case-insensitive duplicate guard)."""
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    category = (category or "").strip()
    if not category:
        raise RegistryError("Kategori er påkrevd.")
    cats = _split_categories(sup.categories)
    if category.lower() in {c.lower() for c in cats}:
        raise RegistryError(f"Kategorien «{category}» finnes allerede.")
    cats.append(category)
    sup.categories = ", ".join(cats)
    session.add(sup)
    session.commit()
    _audit(session, actor, "supplier.category_added", f"supplier:{supplier_id}",
           f"kategori lagt til: {category}")
    session.commit()
    session.refresh(sup)
    return sup


def remove_category(session: Session, supplier_id: int, category: str,
                    *, actor: str = "demo-bruker") -> Supplier:
    """Remove one category tag (case-insensitive match)."""
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    cats = _split_categories(sup.categories)
    kept = [c for c in cats if c.lower() != (category or "").strip().lower()]
    if len(kept) == len(cats):
        raise RegistryError(f"Kategorien «{category}» finnes ikke.")
    sup.categories = ", ".join(kept) or None
    session.add(sup)
    session.commit()
    _audit(session, actor, "supplier.category_removed", f"supplier:{supplier_id}",
           f"kategori fjernet: {category}")
    session.commit()
    session.refresh(sup)
    return sup


# --- Services / products ------------------------------------------------------
def list_services(session: Session, supplier_id: int) -> list[SupplierService]:
    return list(session.exec(
        select(SupplierService).where(SupplierService.supplier_id == supplier_id)
        .order_by(SupplierService.name)
    ).all())


def add_service(
    session: Session,
    supplier_id: int,
    *,
    name: str,
    description: str | None = None,
    unit: str | None = None,
    unit_price=None,
    actor: str = "demo-bruker",
) -> SupplierService:
    """Add a service/product to a supplier's catalog. Name is required."""
    if session.get(Supplier, supplier_id) is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    name = (name or "").strip()
    if not name:
        raise RegistryError("Navn på tjeneste/produkt er påkrevd.")
    svc = SupplierService(
        supplier_id=supplier_id, name=name,
        description=(description or None), unit=(unit or None), unit_price=unit_price,
    )
    session.add(svc)
    session.commit()
    session.refresh(svc)
    _audit(session, actor, "service.created", f"service:{svc.id}",
           f"tjeneste/produkt lagt til: {svc.name} (leverandør {supplier_id})")
    session.commit()
    return svc


def update_service(
    session: Session,
    service_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    unit: str | None = None,
    unit_price=None,
    update_price: bool = False,
    actor: str = "demo-bruker",
) -> SupplierService:
    """Update a service. name (when given) must be non-empty; description/unit accept "" to clear.
    Pass update_price=True to set unit_price (to a value or None)."""
    svc = session.get(SupplierService, service_id)
    if svc is None:
        raise RegistryError(f"Ukjent tjeneste/produkt: {service_id}")
    if name is not None:
        if not name.strip():
            raise RegistryError("Navn på tjeneste/produkt er påkrevd.")
        svc.name = name.strip()
    if description is not None:
        svc.description = description.strip() or None
    if unit is not None:
        svc.unit = unit.strip() or None
    if update_price:
        svc.unit_price = unit_price
    session.add(svc)
    session.commit()
    session.refresh(svc)
    _audit(session, actor, "service.updated", f"service:{svc.id}",
           f"tjeneste/produkt endret: {svc.name}")
    session.commit()
    return svc


def delete_service(session: Session, service_id: int, *, actor: str = "demo-bruker") -> None:
    svc = session.get(SupplierService, service_id)
    if svc is None:
        raise RegistryError(f"Ukjent tjeneste/produkt: {service_id}")
    name, supplier_id = svc.name, svc.supplier_id
    session.delete(svc)
    session.commit()
    _audit(session, actor, "service.deleted", f"service:{service_id}",
           f"tjeneste/produkt slettet: {name} (leverandør {supplier_id})")
    session.commit()


# --- Qualifications -----------------------------------------------------------
def list_qualifications(session: Session, supplier_id: int) -> list[Qualification]:
    return list(session.exec(
        select(Qualification).where(Qualification.supplier_id == supplier_id)
        .order_by(Qualification.name)
    ).all())


def add_qualification(
    session: Session,
    supplier_id: int,
    *,
    name: str,
    valid_to: date | None = None,
    actor: str = "demo-bruker",
) -> Qualification:
    """Add a qualification. Name is required; valid_to is optional (None = just a held check)."""
    if session.get(Supplier, supplier_id) is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    name = (name or "").strip()
    if not name:
        raise RegistryError("Navn på kvalifikasjon er påkrevd.")
    qual = Qualification(supplier_id=supplier_id, name=name, valid_to=valid_to)
    session.add(qual)
    session.commit()
    session.refresh(qual)
    _audit(session, actor, "qualification.created", f"qualification:{qual.id}",
           f"kvalifikasjon lagt til: {qual.name} (leverandør {supplier_id})")
    session.commit()
    return qual


def update_qualification(
    session: Session,
    qualification_id: int,
    *,
    name: str | None = None,
    valid_to: date | None = None,
    update_valid_to: bool = False,
    actor: str = "demo-bruker",
) -> Qualification:
    """Update a qualification. Pass update_valid_to=True to set/clear the validity date."""
    qual = session.get(Qualification, qualification_id)
    if qual is None:
        raise RegistryError(f"Ukjent kvalifikasjon: {qualification_id}")
    if name is not None:
        if not name.strip():
            raise RegistryError("Navn på kvalifikasjon er påkrevd.")
        qual.name = name.strip()
    if update_valid_to:
        qual.valid_to = valid_to
    session.add(qual)
    session.commit()
    session.refresh(qual)
    _audit(session, actor, "qualification.updated", f"qualification:{qual.id}",
           f"kvalifikasjon endret: {qual.name}")
    session.commit()
    return qual


def delete_qualification(session: Session, qualification_id: int,
                         *, actor: str = "demo-bruker") -> None:
    qual = session.get(Qualification, qualification_id)
    if qual is None:
        raise RegistryError(f"Ukjent kvalifikasjon: {qualification_id}")
    name, supplier_id = qual.name, qual.supplier_id
    session.delete(qual)
    session.commit()
    _audit(session, actor, "qualification.deleted", f"qualification:{qualification_id}",
           f"kvalifikasjon slettet: {name} (leverandør {supplier_id})")
    session.commit()
