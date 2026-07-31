"""Forpliktelse A–Z (Funksjon 4) — commitment CRUD, audit, gyldighet-by-clause, multi-supplier.

Pure core (no UI). Asserts hard rule #7 (write → one audit row), H1 (reads never write), soft delete
that keeps the row + trail and removes the commitment from control, and the gyldighet INDICATION
disposed by the contract endringsklausul (P3). Reconciliation is covered by tests/test_grafikk.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import AuditLog, ConditionType, Formalization, SourceType
from core.registry import (
    RegistryError,
    assess_gyldighet,
    create_commitment,
    create_commitments_for_suppliers,
    create_contract,
    create_supplier,
    list_commitments,
    restore_commitment,
    soft_delete_commitment,
    update_commitment,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _supplier(session, *, org="998877665", name="Hydraulikk Nord AS", clause="mindre_justering_epost"):
    sup = create_supplier(session, org_number=org, name=name)
    create_contract(session, supplier_id=sup.id, title="Rammeavtale", reference=f"RA-{org}",
                    valid_from=date(2026, 1, 1), change_clause=clause)
    return sup


def _n_audits(session) -> int:
    return len(list(session.exec(select(AuditLog)).all()))


# --- Create + audit (hard rule #7) -------------------------------------------
def test_create_appends_one_audit_and_is_active(session):
    sup = _supplier(session)
    before = _n_audits(session)
    c = create_commitment(
        session, supplier_id=sup.id, condition_type=ConditionType.PRICE,
        source_type=SourceType.EMAIL, source_ref="e-post 2026-06-01, X",
        item_ref="ART-1", value=Decimal("500"), valid_from=date(2026, 6, 1))
    assert _n_audits(session) == before + 1
    assert c.confirmed_by_user is True
    assert c.is_active_on(date(2026, 7, 1)) is True


def test_create_requires_source_ref(session):
    sup = _supplier(session)
    with pytest.raises(RegistryError):
        create_commitment(session, supplier_id=sup.id, condition_type=ConditionType.PRICE,
                          source_ref="  ", valid_from=date(2026, 6, 1))


# --- Update (P5) --------------------------------------------------------------
def test_update_changes_field_and_audits(session):
    sup = _supplier(session)
    c = create_commitment(session, supplier_id=sup.id, condition_type=ConditionType.PRICE,
                          source_ref="e-post", item_ref="ART-1", value=Decimal("500"),
                          valid_from=date(2026, 6, 1))
    before = _n_audits(session)
    update_commitment(session, c.id, value=Decimal("450"), update_value=True)
    assert session.get(type(c), c.id).value == Decimal("450")
    assert _n_audits(session) == before + 1


# --- Soft delete removes from control, keeps the row + trail (P5) -------------
def test_soft_delete_hides_from_list_and_control_keeps_row(session):
    sup = _supplier(session)
    c = create_commitment(session, supplier_id=sup.id, condition_type=ConditionType.PRICE,
                          source_ref="e-post", item_ref="ART-1", value=Decimal("500"),
                          valid_from=date(2026, 6, 1))
    soft_delete_commitment(session, c.id)
    assert list_commitments(session, supplier_id=sup.id) == []
    assert len(list_commitments(session, supplier_id=sup.id, include_deleted=True)) == 1
    # No longer participates in control.
    assert session.get(type(c), c.id).is_active_on(date(2026, 7, 1)) is False
    restore_commitment(session, c.id)
    assert len(list_commitments(session, supplier_id=sup.id)) == 1


# --- Gyldighet as INDICATION disposed by the endringsklausul (P3) -------------
def test_gyldighet_uses_change_clause(session):
    lax = _supplier(session, org="111111111", name="Lax AS", clause="mindre_justering_epost")
    strict = _supplier(session, org="222222222", name="Strict AS", clause="kun_skriftlig_tillegg")
    assert assess_gyldighet(session, lax.id) == "GYLDIG"
    assert assess_gyldighet(session, strict.id) == "KREVER_FORMALISERING"
    # A scope expansion points toward MULIG UGYLDIG regardless of the clause.
    assert assess_gyldighet(session, lax.id, scope_change=True) == "UGYLDIG"
    # A large price increase (> internal trigger) also indicates possible vesentlig endring.
    assert assess_gyldighet(session, lax.id, pct_change=Decimal("30")) == "UGYLDIG"


# --- One or several suppliers (P2) -------------------------------------------
def test_create_for_several_suppliers(session):
    a = _supplier(session, org="333333333", name="A AS")
    b = _supplier(session, org="444444444", name="B AS")
    made = create_commitments_for_suppliers(
        session, [a.id, b.id], condition_type=ConditionType.PRICE,
        source_ref="felles e-post", item_ref="ART-9", value=Decimal("100"),
        valid_from=date(2026, 6, 1), formalization=Formalization.PENDING_ANNEX)
    assert len(made) == 2
    assert {m.supplier_id for m in made} == {a.id, b.id}


# --- Reads never write (H1) ---------------------------------------------------
def test_reads_never_write(session):
    sup = _supplier(session)
    create_commitment(session, supplier_id=sup.id, condition_type=ConditionType.PRICE,
                      source_ref="e-post", item_ref="ART-1", value=Decimal("500"),
                      valid_from=date(2026, 6, 1))
    before = _n_audits(session)
    list_commitments(session, supplier_id=sup.id)
    assess_gyldighet(session, sup.id)
    assert _n_audits(session) == before
