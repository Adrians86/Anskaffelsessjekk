"""Leverandør A–Z — the first function built as a full TOOL: add → view → edit → delete → use.

Covers the registry CRUD end to end AND asserts hard rule #7: EVERY save appends an append-only
audit row. Pure core (no UI) — a fast, deterministic guard on the persistence layer.
"""
from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import AuditLog, ContactPerson, Supplier
from core.registry import (
    RegistryError,
    add_contact,
    create_supplier,
    delete_contact,
    list_contacts,
    list_suppliers,
    restore_supplier,
    soft_delete_supplier,
    update_contact,
    update_supplier,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _audits(session, action: str) -> list[AuditLog]:
    return list(session.exec(select(AuditLog).where(AuditLog.action == action)).all())


# --- Create -------------------------------------------------------------------
def test_create_supplier_persists_and_audits(session):
    sup = create_supplier(session, org_number="111222333", name="Ny Leverandør AS",
                          categories="deler", notes="notat")
    assert sup.id is not None
    assert session.get(Supplier, sup.id).name == "Ny Leverandør AS"
    assert len(_audits(session, "supplier.created")) == 1


def test_create_supplier_requires_name_and_org(session):
    with pytest.raises(RegistryError):
        create_supplier(session, org_number="1", name="   ")
    with pytest.raises(RegistryError):
        create_supplier(session, org_number="  ", name="X AS")


def test_create_supplier_rejects_duplicate_org(session):
    create_supplier(session, org_number="111", name="A AS")
    with pytest.raises(RegistryError):
        create_supplier(session, org_number="111", name="B AS")


# --- Update -------------------------------------------------------------------
def test_update_supplier_changes_fields_and_audits(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    update_supplier(session, sup.id, name="A Renamed AS", categories="ny, kategori",
                    notes="oppdatert", iso_certified=True)
    session.refresh(sup)
    assert sup.name == "A Renamed AS"
    assert sup.categories == "ny, kategori"
    assert sup.notes == "oppdatert"
    assert sup.iso_certified is True
    assert len(_audits(session, "supplier.updated")) == 1


def test_update_supplier_can_clear_notes_to_null(session):
    sup = create_supplier(session, org_number="111", name="A AS", notes="noe")
    update_supplier(session, sup.id, notes="")
    session.refresh(sup)
    assert sup.notes is None


def test_update_supplier_rejects_org_clash_and_unknown_id(session):
    create_supplier(session, org_number="111", name="A AS")
    b = create_supplier(session, org_number="222", name="B AS")
    with pytest.raises(RegistryError):
        update_supplier(session, b.id, org_number="111")
    with pytest.raises(RegistryError):
        update_supplier(session, 9999, name="X")


# --- Soft delete / restore ----------------------------------------------------
def test_soft_delete_keeps_row_and_trail_then_restore(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    soft_delete_supplier(session, sup.id)

    # Row still exists, just flagged; excluded from the default list, visible with include_deleted.
    assert session.get(Supplier, sup.id) is not None
    assert [s.name for s in list_suppliers(session)] == []
    assert [s.name for s in list_suppliers(session, include_deleted=True)] == ["A AS"]
    assert len(_audits(session, "supplier.deleted")) == 1

    restore_supplier(session, sup.id)
    assert [s.name for s in list_suppliers(session)] == ["A AS"]
    assert len(_audits(session, "supplier.restored")) == 1


# --- Contact persons ----------------------------------------------------------
def test_contact_full_crud_with_audit(session):
    sup = create_supplier(session, org_number="111", name="A AS")

    c = add_contact(session, sup.id, name="Per Ås", role="Innkjøp", email="per@a.example")
    assert c.id is not None
    assert len(_audits(session, "contact.created")) == 1

    update_contact(session, c.id, phone="+47 123", email="")
    session.refresh(c)
    assert c.phone == "+47 123"
    assert c.email is None
    assert len(_audits(session, "contact.updated")) == 1

    assert [x.name for x in list_contacts(session, sup.id)] == ["Per Ås"]

    delete_contact(session, c.id)
    assert list_contacts(session, sup.id) == []
    assert session.get(ContactPerson, c.id) is None
    assert len(_audits(session, "contact.deleted")) == 1


def test_add_contact_requires_name_and_known_supplier(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    with pytest.raises(RegistryError):
        add_contact(session, sup.id, name="  ")
    with pytest.raises(RegistryError):
        add_contact(session, 9999, name="Per")


def test_every_save_writes_exactly_one_audit_row(session):
    """A→Z, one trail row per save: 1 create + 1 update + 1 delete(soft) + 1 contact add = 4."""
    sup = create_supplier(session, org_number="111", name="A AS")
    update_supplier(session, sup.id, name="A2 AS")
    add_contact(session, sup.id, name="Per")
    soft_delete_supplier(session, sup.id)
    assert len(list(session.exec(select(AuditLog)).all())) == 4
