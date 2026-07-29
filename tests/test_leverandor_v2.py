"""Leverandør v2 — full kartotek: firma fields, categories, services, qualifications, contact
groups, cooperation rating. Pure core (no UI). Asserts hard rule #7 (every save → audit row).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import SIDE_INTERNAL, SIDE_SUPPLIER, AuditLog
from core.registry import (
    RegistryError,
    add_category,
    add_contact,
    add_qualification,
    add_service,
    create_supplier,
    delete_qualification,
    delete_service,
    list_categories,
    list_contacts,
    list_qualifications,
    list_services,
    remove_category,
    update_qualification,
    update_service,
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


def _audits(session, action: str):
    return list(session.exec(select(AuditLog).where(AuditLog.action == action)).all())


# --- Firma fields (K1) --------------------------------------------------------
def test_update_supplier_full_firma_fields(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    update_supplier(session, sup.id, address="Gata 1", postal_code="0001", city="Oslo",
                    website="a.example", email="a@a.example", phone="+47 1", status="Inaktiv")
    session.refresh(sup)
    assert (sup.address, sup.postal_code, sup.city) == ("Gata 1", "0001", "Oslo")
    assert (sup.website, sup.email, sup.phone, sup.status) == (
        "a.example", "a@a.example", "+47 1", "Inaktiv")


def test_update_supplier_rejects_bad_status(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    with pytest.raises(RegistryError):
        update_supplier(session, sup.id, status="Tulle")


def test_cooperation_rating_is_editable(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    update_supplier(session, sup.id, cooperation_rating="God dialog, følg pris.")
    session.refresh(sup)
    assert sup.cooperation_rating == "God dialog, følg pris."
    update_supplier(session, sup.id, cooperation_rating="")
    session.refresh(sup)
    assert sup.cooperation_rating is None


# --- Categories (K2) ----------------------------------------------------------
def test_category_add_remove_with_dup_guard_and_audit(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    add_category(session, sup.id, "Deler")
    add_category(session, sup.id, "IT")
    assert list_categories(session, sup.id) == ["Deler", "IT"]
    with pytest.raises(RegistryError):
        add_category(session, sup.id, "deler")            # case-insensitive dup
    remove_category(session, sup.id, "IT")
    assert list_categories(session, sup.id) == ["Deler"]
    with pytest.raises(RegistryError):
        remove_category(session, sup.id, "finnesikke")
    assert len(_audits(session, "supplier.category_added")) == 2
    assert len(_audits(session, "supplier.category_removed")) == 1


# --- Services (K3) ------------------------------------------------------------
def test_service_full_crud_with_audit(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    svc = add_service(session, sup.id, name="Pumpe", unit="stk", unit_price=Decimal("1200"))
    assert len(_audits(session, "service.created")) == 1

    update_service(session, svc.id, description="oppdatert", unit_price=Decimal("1300"),
                   update_price=True)
    session.refresh(svc)
    assert svc.description == "oppdatert"
    assert svc.unit_price == Decimal("1300")

    # Clearing the price to NULL is explicit (update_price=True, unit_price=None).
    update_service(session, svc.id, unit_price=None, update_price=True)
    session.refresh(svc)
    assert svc.unit_price is None

    delete_service(session, svc.id)
    assert list_services(session, sup.id) == []
    assert len(_audits(session, "service.deleted")) == 1


def test_add_service_requires_name(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    with pytest.raises(RegistryError):
        add_service(session, sup.id, name="  ")


# --- Qualifications (K4) ------------------------------------------------------
def test_qualification_optional_validity_and_expiry(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    q_open = add_qualification(session, sup.id, name="Startbank", valid_to=None)
    q_valid = add_qualification(session, sup.id, name="ISO 9001", valid_to=date(2999, 1, 1))
    q_exp = add_qualification(session, sup.id, name="Gammel", valid_to=date(2000, 1, 1))
    assert q_open.is_expired() is False          # no date → never expired
    assert q_valid.is_expired() is False
    assert q_exp.is_expired() is True
    assert len(list_qualifications(session, sup.id)) == 3
    assert len(_audits(session, "qualification.created")) == 3


def test_qualification_update_and_delete(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    q = add_qualification(session, sup.id, name="ISO", valid_to=None)
    update_qualification(session, q.id, valid_to=date(2000, 1, 1), update_valid_to=True)
    session.refresh(q)
    assert q.is_expired() is True
    assert len(_audits(session, "qualification.updated")) == 1
    delete_qualification(session, q.id)
    assert list_qualifications(session, sup.id) == []
    assert len(_audits(session, "qualification.deleted")) == 1


# --- Contact groups (K5) ------------------------------------------------------
def test_contacts_split_into_two_sides(session):
    sup = create_supplier(session, org_number="111", name="A AS")
    add_contact(session, sup.id, name="Leverandørkontakt", side=SIDE_SUPPLIER)
    add_contact(session, sup.id, name="Vår ansvarlig", side=SIDE_INTERNAL)
    supplier_side = list_contacts(session, sup.id, side=SIDE_SUPPLIER)
    internal_side = list_contacts(session, sup.id, side=SIDE_INTERNAL)
    assert [c.name for c in supplier_side] == ["Leverandørkontakt"]
    assert [c.name for c in internal_side] == ["Vår ansvarlig"]
    assert len(list_contacts(session, sup.id)) == 2      # no side filter → both


def test_every_new_entity_save_writes_one_audit_row(session):
    """Category add + service add + qualification add + internal contact add = 4 new rows
    on top of the 1 create."""
    sup = create_supplier(session, org_number="111", name="A AS")
    add_category(session, sup.id, "Deler")
    add_service(session, sup.id, name="Pumpe")
    add_qualification(session, sup.id, name="ISO")
    add_contact(session, sup.id, name="Intern", side=SIDE_INTERNAL)
    assert len(list(session.exec(select(AuditLog)).all())) == 5
