"""Kontrakt + prisliste A–Z (Funksjon 2) — verification basis #2, full CRUD.

Pure core (no UI). Asserts hard rule #7 (every write → 1 audit row), H1 (reads never write), and the
endringsklausul read-path for the engine (M4). Reconciliation is covered by tests/test_grafikk.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.models import AuditLog, ContractLine, ContractType, clause_assessment_hint
from core.registry import (
    RegistryError,
    add_line,
    change_clause_of,
    create_contract,
    create_supplier,
    delete_line,
    get_contract,
    list_contracts,
    list_lines,
    restore_contract,
    soft_delete_contract,
    update_contract,
    update_line,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _sup(session):
    return create_supplier(session, org_number="111", name="A AS")


def _audits(session, action: str):
    return list(session.exec(select(AuditLog).where(AuditLog.action == action)).all())


def _n_audits(session) -> int:
    return len(list(session.exec(select(AuditLog)).all()))


def _contract(session, sup):
    return create_contract(
        session, supplier_id=sup.id, title="Rammeavtale deler", reference="RA-1",
        contract_type=ContractType.RAMMEAVTALE, regime="FOA", valid_from=date(2026, 1, 1),
        valid_to=date(2027, 12, 31), total_value=Decimal("1000000"),
        change_clause="kun_skriftlig_tillegg",
    )


# --- Contract create / validation --------------------------------------------
def test_create_contract_persists_and_audits(session):
    sup = _sup(session)
    k = _contract(session, sup)
    assert k.id is not None
    assert get_contract(session, k.id).reference == "RA-1"
    assert k.regime == "FOA"
    assert k.status == "aktiv"
    assert k.is_deleted is False
    assert len(_audits(session, "contract.created")) == 1


def test_create_contract_validation(session):
    sup = _sup(session)
    with pytest.raises(RegistryError):
        create_contract(session, supplier_id=sup.id, title="  ", reference="R",
                        valid_from=date(2026, 1, 1))
    with pytest.raises(RegistryError):
        create_contract(session, supplier_id=sup.id, title="T", reference="  ",
                        valid_from=date(2026, 1, 1))
    with pytest.raises(RegistryError):
        create_contract(session, supplier_id=sup.id, title="T", reference="R",
                        valid_from=date(2026, 1, 1), change_clause="bogus")
    with pytest.raises(RegistryError):
        create_contract(session, supplier_id=999, title="T", reference="R",
                        valid_from=date(2026, 1, 1))


# --- Price list (kontraktslinjer) full CRUD ----------------------------------
def test_line_full_crud_with_audit(session):
    sup = _sup(session)
    k = _contract(session, sup)
    ln = add_line(session, k.id, item_ref="HYD-1", description="Pumpe", unit="stk",
                  unit_price=Decimal("12500"), max_quantity=Decimal("50"))
    assert len(_audits(session, "contract_line.created")) == 1

    update_line(session, ln.id, unit_price=Decimal("12000"), max_quantity=None,
                update_max_quantity=True)
    session.refresh(ln)
    assert ln.unit_price == Decimal("12000")
    assert ln.max_quantity is None
    assert ln.currency == "NOK"
    assert len(_audits(session, "contract_line.updated")) == 1

    assert [x.item_ref for x in list_lines(session, k.id)] == ["HYD-1"]

    delete_line(session, ln.id)
    assert list_lines(session, k.id) == []
    assert session.get(ContractLine, ln.id) is None
    assert len(_audits(session, "contract_line.deleted")) == 1


def test_add_line_requires_item_ref_and_price(session):
    sup = _sup(session)
    k = _contract(session, sup)
    with pytest.raises(RegistryError):
        add_line(session, k.id, item_ref="  ", unit_price=Decimal("1"))


# --- Update / soft-delete / restore ------------------------------------------
def test_update_and_soft_delete_restore_contract(session):
    sup = _sup(session)
    k = _contract(session, sup)
    update_contract(session, k.id, status="utkast", change_clause="mindre_justering_epost")
    session.refresh(k)
    assert k.status == "utkast"
    assert k.change_clause == "mindre_justering_epost"
    assert len(_audits(session, "contract.updated")) == 1

    soft_delete_contract(session, k.id)
    assert get_contract(session, k.id) is not None            # row kept
    assert [c.reference for c in list_contracts(session)] == []
    assert [c.reference for c in list_contracts(session, include_deleted=True)] == ["RA-1"]
    assert len(_audits(session, "contract.deleted")) == 1

    restore_contract(session, k.id)
    assert [c.reference for c in list_contracts(session)] == ["RA-1"]
    assert len(_audits(session, "contract.restored")) == 1


def test_list_scoped_to_supplier(session):
    a = _sup(session)
    b = create_supplier(session, org_number="222", name="B AS")
    create_contract(session, supplier_id=a.id, title="A-avtale", reference="A-1",
                    valid_from=date(2026, 1, 1))
    create_contract(session, supplier_id=b.id, title="B-avtale", reference="B-1",
                    valid_from=date(2026, 1, 1))
    assert [c.reference for c in list_contracts(session, supplier_id=a.id)] == ["A-1"]


# --- Reads never write (H1) --------------------------------------------------
def test_reads_never_write(session):
    sup = _sup(session)
    k = _contract(session, sup)
    add_line(session, k.id, item_ref="X-1", unit_price=Decimal("100"))
    before = _n_audits(session)
    # A batch of reads.
    list_contracts(session)
    list_contracts(session, supplier_id=sup.id, include_deleted=True)
    get_contract(session, k.id)
    list_lines(session, k.id)
    change_clause_of(session, k.id)
    assert _n_audits(session) == before                       # H1: no writes on read


# --- Endringsklausul available to the engine (M4) ----------------------------
def test_change_clause_read_and_hint(session):
    sup = _sup(session)
    k = _contract(session, sup)
    assert change_clause_of(session, k.id) == "kun_skriftlig_tillegg"
    assert clause_assessment_hint("kun_skriftlig_tillegg") == "krever_formalisering"
    assert clause_assessment_hint("mindre_justering_epost") == "kan_vaere_gyldig"
    assert clause_assessment_hint("annet") == "krever_vurdering"


def test_every_write_is_one_audit_row(session):
    """1 supplier + 1 contract + 1 line add + 1 contract update + 1 soft-delete = 5 rows."""
    sup = _sup(session)
    k = _contract(session, sup)
    add_line(session, k.id, item_ref="X-1", unit_price=Decimal("100"))
    update_contract(session, k.id, status="utkast")
    soft_delete_contract(session, k.id)
    assert _n_audits(session) == 5
