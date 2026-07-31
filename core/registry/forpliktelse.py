"""Forpliktelse (commitment) CRUD service — Funksjon 4.

A forpliktelse is an agreed condition that lives OUTSIDE the formal contract: an e-mail agreement,
a meeting note, an annex. It is anchored on the leverandør. Pure core: takes a Session, imports no
UI (hard rule #1). Every write appends an append-only AuditLog row (hard rule #7). Deleting is SOFT
(is_deleted) — the row and its trail are kept. Human-in-the-loop (hard rule #3): only a saksbehandler
saving the form makes a forpliktelse participate in control; the gyldighetsvurdering is an INDICATION.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from core.models import (
    Commitment,
    ConditionType,
    Formalization,
    SourceType,
    Supplier,
)
from core.models.contract import (
    CLAUSE_HINT_FORMALISERING,
    CLAUSE_HINT_KAN_GYLDIG,
    clause_assessment_hint,
)
from core.registry.kontrakt import change_clause_of, list_contracts
from core.registry.leverandor import RegistryError, _audit

# Gyldighet indication codes (UI-level; mirror core/extraction/epost + ui_forpliktelser).
GYLDIG = "GYLDIG"
KREVER_FORMALISERING = "KREVER_FORMALISERING"
UGYLDIG = "UGYLDIG"

# Above this relative price increase (or an explicit scope expansion) an e-mail change points toward
# a possible vesentlig endring (FOA §28-1) — an internal trigger, never presented as the criterion.
_VESENTLIG_PCT = Decimal("15")


# --- Reads --------------------------------------------------------------------
def list_commitments(
    session: Session,
    *,
    supplier_id: int | None = None,
    source_type: SourceType | None = None,
    include_deleted: bool = False,
) -> list[Commitment]:
    """Commitments newest-first. Optionally scoped to a supplier / source type; soft-deleted
    excluded unless include_deleted. Reads never write (H1)."""
    stmt = select(Commitment)
    if supplier_id is not None:
        stmt = stmt.where(Commitment.supplier_id == supplier_id)
    if source_type is not None:
        stmt = stmt.where(Commitment.source_type == source_type)
    if not include_deleted:
        stmt = stmt.where(Commitment.is_deleted == False)  # noqa: E712
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda c: (c.valid_from, c.id or 0), reverse=True)
    return rows


def get_commitment(session: Session, commitment_id: int) -> Commitment | None:
    return session.get(Commitment, commitment_id)


def resolve_contract_id(session: Session, supplier_id: int) -> int | None:
    """The supplier's active (non-deleted) contract, else the first — for clause + linkage. Read-only."""
    contracts = list_contracts(session, supplier_id=supplier_id)
    for c in contracts:
        if c.status == "aktiv":
            return c.id
    return contracts[0].id if contracts else None


def assess_gyldighet(
    session: Session,
    supplier_id: int,
    *,
    scope_change: bool = False,
    pct_change: Decimal | None = None,
    contract_id: int | None = None,
) -> str:
    """Gyldighet INDICATION (never a legal conclusion — FOA §28-1 vesentlig endring is skjønn),
    disposed by the supplier's contract endringsklausul (P3). A scope expansion or a large price
    increase points toward MULIG UGYLDIG regardless of the clause. Reads never write (H1)."""
    if scope_change or (pct_change is not None and pct_change > _VESENTLIG_PCT):
        return UGYLDIG
    if contract_id is None:
        contract_id = resolve_contract_id(session, supplier_id)
    clause = change_clause_of(session, contract_id) if contract_id else None
    hint = clause_assessment_hint(clause) if clause else None
    if hint == CLAUSE_HINT_KAN_GYLDIG:
        return GYLDIG
    if hint == CLAUSE_HINT_FORMALISERING:
        return KREVER_FORMALISERING
    return KREVER_FORMALISERING


# --- Writes (each appends one audit row) --------------------------------------
def create_commitment(
    session: Session,
    *,
    supplier_id: int,
    condition_type: ConditionType,
    source_type: SourceType = SourceType.EMAIL,
    source_ref: str,
    item_ref: str | None = None,
    value: Decimal | None = None,
    unit: str | None = "NOK",
    valid_from: date,
    valid_to: date | None = None,
    formalization: Formalization = Formalization.PENDING_ANNEX,
    source_quote: str | None = None,
    gyldighet: str | None = None,
    extracted_by: str = "manual",
    confirmed_by_user: bool = True,
    contract_id: int | None = None,
    actor: str = "demo-bruker",
) -> Commitment:
    """Create a forpliktelse for a supplier. supplier_id, condition_type, source_ref and
    valid_from are required. Links to the supplier's active contract unless contract_id is given."""
    if session.get(Supplier, supplier_id) is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    source_ref = (source_ref or "").strip()
    if not source_ref:
        raise RegistryError("Kilde er påkrevd.")
    if valid_from is None:
        raise RegistryError("Gyldig fra-dato er påkrevd.")
    if contract_id is None:
        contract_id = resolve_contract_id(session, supplier_id)

    commitment = Commitment(
        supplier_id=supplier_id, contract_id=contract_id,
        source_type=source_type, source_ref=source_ref,
        source_quote=(source_quote.strip()[:500] if source_quote else None),
        gyldighet=gyldighet, condition_type=condition_type,
        item_ref=(item_ref.strip() if item_ref else None), value=value,
        unit=(unit.strip() if unit else None), valid_from=valid_from, valid_to=valid_to,
        formalization=formalization, extracted_by=extracted_by,
        confirmed_by_user=confirmed_by_user,
    )
    session.add(commitment)
    session.commit()
    session.refresh(commitment)
    _audit(session, actor, "commitment.created", f"commitment:{commitment.id}",
           f"forpliktelse opprettet: {commitment.item_ref or '—'} "
           f"{commitment.condition_type.value} fra {commitment.source_type.value} "
           f"({commitment.source_ref})")
    session.commit()
    return commitment


def create_commitments_for_suppliers(
    session: Session, supplier_ids: list[int], **kwargs
) -> list[Commitment]:
    """P2 — register the SAME forpliktelse for one or several suppliers (a shared vilkår). For
    different terms per supplier, call create_commitment per supplier instead (P4)."""
    return [create_commitment(session, supplier_id=sid, **kwargs) for sid in supplier_ids]


def update_commitment(
    session: Session,
    commitment_id: int,
    *,
    condition_type: ConditionType | None = None,
    source_type: SourceType | None = None,
    source_ref: str | None = None,
    item_ref: str | None = None,
    update_item_ref: bool = False,
    value: Decimal | None = None,
    update_value: bool = False,
    unit: str | None = None,
    valid_from: date | None = None,
    valid_to: date | None = None,
    update_valid_to: bool = False,
    formalization: Formalization | None = None,
    gyldighet: str | None = None,
    actor: str = "demo-bruker",
) -> Commitment:
    """Update a forpliktelse. Only provided fields change. Pass update_item_ref / update_value /
    update_valid_to to set those nullable fields (to a value or None)."""
    c = session.get(Commitment, commitment_id)
    if c is None:
        raise RegistryError(f"Ukjent forpliktelse: {commitment_id}")

    changed: list[str] = []
    if condition_type is not None and condition_type != c.condition_type:
        c.condition_type = condition_type
        changed.append("betingelse")
    if source_type is not None and source_type != c.source_type:
        c.source_type = source_type
        changed.append("kildetype")
    if source_ref is not None and source_ref.strip() and source_ref.strip() != c.source_ref:
        c.source_ref = source_ref.strip()
        changed.append("kilde")
    if update_item_ref:
        new_item = item_ref.strip() if item_ref else None
        if new_item != c.item_ref:
            c.item_ref = new_item
            changed.append("artikkel")
    if update_value and value != c.value:
        c.value = value
        changed.append("verdi")
    if unit is not None and (unit.strip() or None) != c.unit:
        c.unit = unit.strip() or None
        changed.append("enhet")
    if valid_from is not None and valid_from != c.valid_from:
        c.valid_from = valid_from
        changed.append("gyldig fra")
    if update_valid_to and valid_to != c.valid_to:
        c.valid_to = valid_to
        changed.append("gyldig til")
    if formalization is not None and formalization != c.formalization:
        c.formalization = formalization
        changed.append("formalisering")
    if gyldighet is not None and gyldighet != c.gyldighet:
        c.gyldighet = gyldighet
        changed.append("gyldighet")

    session.add(c)
    session.commit()
    session.refresh(c)
    detail = ("endret: " + ", ".join(changed)) if changed else "lagret uten endringer"
    _audit(session, actor, "commitment.updated", f"commitment:{c.id}",
           f"forpliktelse {detail}")
    session.commit()
    return c


def soft_delete_commitment(
    session: Session, commitment_id: int, *, actor: str = "demo-bruker"
) -> Commitment:
    """Mark a forpliktelse deleted. The row and its audit trail are KEPT (soft delete)."""
    c = session.get(Commitment, commitment_id)
    if c is None:
        raise RegistryError(f"Ukjent forpliktelse: {commitment_id}")
    if not c.is_deleted:
        c.is_deleted = True
        session.add(c)
        session.commit()
        _audit(session, actor, "commitment.deleted", f"commitment:{c.id}",
               f"forpliktelse slettet (mykt, spor beholdt): {c.item_ref or '—'} "
               f"({c.source_ref})")
        session.commit()
    session.refresh(c)
    return c


def restore_commitment(
    session: Session, commitment_id: int, *, actor: str = "demo-bruker"
) -> Commitment:
    """Undo a soft delete."""
    c = session.get(Commitment, commitment_id)
    if c is None:
        raise RegistryError(f"Ukjent forpliktelse: {commitment_id}")
    if c.is_deleted:
        c.is_deleted = False
        session.add(c)
        session.commit()
        _audit(session, actor, "commitment.restored", f"commitment:{c.id}",
               f"forpliktelse gjenopprettet: {c.item_ref or '—'} ({c.source_ref})")
        session.commit()
    session.refresh(c)
    return c
