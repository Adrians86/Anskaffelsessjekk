"""Kontrakt (avtale) + kontraktslinje (prisliste) CRUD service.

Pure core: every function takes a Session and returns domain objects; NO UI import (hard rule #1).
Every mutation appends an append-only AuditLog row (hard rule #7). Deleting a contract is SOFT
(is_deleted) — the row and its price list are kept so the audit trail stays intact.

The price list (kontraktslinjer) is verification basis #2: fakturalinjer are checked against these
lines. This module only manages the data; the matcher lives in core/matching.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from core.models import (
    CHANGE_CLAUSES,
    CONTRACT_REGIMES,
    CONTRACT_STATUSES,
    Contract,
    ContractLine,
    ContractType,
    Supplier,
)
from core.registry.leverandor import RegistryError, _audit


def _clause_label(clause: str) -> str:
    return {
        "kun_skriftlig_tillegg": "Kun skriftlig tillegg",
        "mindre_justering_epost": "Mindre justering (e-post)",
        "kpi_regulering": "KPI-regulering",
        "annet": "Annet",
    }.get(clause, clause)


# --- Contracts ----------------------------------------------------------------
def list_contracts(
    session: Session, *, supplier_id: int | None = None, include_deleted: bool = False,
) -> list[Contract]:
    """Contracts ordered by reference. Optionally scoped to one supplier; soft-deleted excluded."""
    stmt = select(Contract)
    if supplier_id is not None:
        stmt = stmt.where(Contract.supplier_id == supplier_id)
    if not include_deleted:
        stmt = stmt.where(Contract.is_deleted == False)  # noqa: E712
    return list(session.exec(stmt.order_by(Contract.reference)).all())


def get_contract(session: Session, contract_id: int) -> Contract | None:
    return session.get(Contract, contract_id)


def create_contract(
    session: Session,
    *,
    supplier_id: int,
    title: str,
    reference: str,
    contract_type: ContractType = ContractType.RAMMEAVTALE,
    regime: str = "FOA",
    valid_from: date,
    valid_to: date | None = None,
    total_value: Decimal | None = None,
    change_clause: str = "kun_skriftlig_tillegg",
    status: str = "aktiv",
    actor: str = "demo-bruker",
) -> Contract:
    """Create a contract for a supplier. Title, reference and valid_from are required."""
    if session.get(Supplier, supplier_id) is None:
        raise RegistryError(f"Ukjent leverandør: {supplier_id}")
    title = (title or "").strip()
    reference = (reference or "").strip()
    if not title:
        raise RegistryError("Tittel er påkrevd.")
    if not reference:
        raise RegistryError("Avtalenummer er påkrevd.")
    if valid_from is None:
        raise RegistryError("Periode fra-dato er påkrevd.")
    if change_clause not in CHANGE_CLAUSES:
        raise RegistryError(f"Ugyldig endringsklausul: {change_clause}")
    if status not in CONTRACT_STATUSES:
        raise RegistryError(f"Ugyldig status: {status}")
    if regime not in CONTRACT_REGIMES:
        raise RegistryError(f"Ugyldig regime: {regime}")

    contract = Contract(
        supplier_id=supplier_id, title=title, reference=reference,
        contract_type=contract_type, regime=regime, valid_from=valid_from, valid_to=valid_to,
        total_value=total_value, change_clause=change_clause, status=status,
    )
    session.add(contract)
    session.commit()
    session.refresh(contract)
    _audit(session, actor, "contract.created", f"contract:{contract.id}",
           f"avtale opprettet: {contract.title} ({contract.reference})")
    session.commit()
    return contract


def update_contract(
    session: Session,
    contract_id: int,
    *,
    title: str | None = None,
    reference: str | None = None,
    contract_type: ContractType | None = None,
    regime: str | None = None,
    valid_from: date | None = None,
    valid_to: date | None = None,
    update_valid_to: bool = False,
    total_value: Decimal | None = None,
    update_total_value: bool = False,
    change_clause: str | None = None,
    status: str | None = None,
    actor: str = "demo-bruker",
) -> Contract:
    """Update a contract. Only provided fields change. Pass update_valid_to / update_total_value
    to set those nullable fields (to a value or None)."""
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise RegistryError(f"Ukjent avtale: {contract_id}")

    changed: list[str] = []
    if title is not None and title.strip() and title.strip() != contract.title:
        contract.title = title.strip()
        changed.append("tittel")
    if reference is not None and reference.strip() and reference.strip() != contract.reference:
        contract.reference = reference.strip()
        changed.append("avtalenr")
    if contract_type is not None and contract_type != contract.contract_type:
        contract.contract_type = contract_type
        changed.append("type")
    if regime is not None and regime != contract.regime:
        if regime not in CONTRACT_REGIMES:
            raise RegistryError(f"Ugyldig regime: {regime}")
        contract.regime = regime
        changed.append("regime")
    if valid_from is not None and valid_from != contract.valid_from:
        contract.valid_from = valid_from
        changed.append("periode fra")
    if update_valid_to and valid_to != contract.valid_to:
        contract.valid_to = valid_to
        changed.append("periode til")
    if update_total_value and total_value != contract.total_value:
        contract.total_value = total_value
        changed.append("ramme")
    if change_clause is not None and change_clause != contract.change_clause:
        if change_clause not in CHANGE_CLAUSES:
            raise RegistryError(f"Ugyldig endringsklausul: {change_clause}")
        contract.change_clause = change_clause
        changed.append("endringsklausul")
    if status is not None and status != contract.status:
        if status not in CONTRACT_STATUSES:
            raise RegistryError(f"Ugyldig status: {status}")
        contract.status = status
        changed.append("status")

    session.add(contract)
    session.commit()
    session.refresh(contract)
    detail = ("endret: " + ", ".join(changed)) if changed else "lagret uten endringer"
    _audit(session, actor, "contract.updated", f"contract:{contract.id}",
           f"avtale {detail} ({contract.reference})")
    session.commit()
    return contract


def soft_delete_contract(session: Session, contract_id: int, *, actor: str = "demo-bruker") -> Contract:
    """Mark a contract deleted. The row and its price list are KEPT (soft delete)."""
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise RegistryError(f"Ukjent avtale: {contract_id}")
    if not contract.is_deleted:
        contract.is_deleted = True
        session.add(contract)
        session.commit()
        _audit(session, actor, "contract.deleted", f"contract:{contract.id}",
               f"avtale slettet (mykt, spor beholdt): {contract.reference}")
        session.commit()
    session.refresh(contract)
    return contract


def restore_contract(session: Session, contract_id: int, *, actor: str = "demo-bruker") -> Contract:
    """Undo a soft delete."""
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise RegistryError(f"Ukjent avtale: {contract_id}")
    if contract.is_deleted:
        contract.is_deleted = False
        session.add(contract)
        session.commit()
        _audit(session, actor, "contract.restored", f"contract:{contract.id}",
               f"avtale gjenopprettet: {contract.reference}")
        session.commit()
    session.refresh(contract)
    return contract


# --- Contract lines (prisliste) — verification basis #2 -----------------------
def list_lines(session: Session, contract_id: int) -> list[ContractLine]:
    return list(session.exec(
        select(ContractLine).where(ContractLine.contract_id == contract_id)
        .order_by(ContractLine.item_ref)
    ).all())


def add_line(
    session: Session,
    contract_id: int,
    *,
    item_ref: str,
    description: str = "",
    unit: str = "stk",
    unit_price: Decimal,
    max_quantity: Decimal | None = None,
    currency: str = "NOK",
    actor: str = "demo-bruker",
) -> ContractLine:
    """Add a price-list line. item_ref and unit_price are required."""
    if session.get(Contract, contract_id) is None:
        raise RegistryError(f"Ukjent avtale: {contract_id}")
    item_ref = (item_ref or "").strip()
    if not item_ref:
        raise RegistryError("Artikkelnr er påkrevd.")
    if unit_price is None:
        raise RegistryError("Pris er påkrevd.")
    line = ContractLine(
        contract_id=contract_id, item_ref=item_ref, description=(description or "").strip(),
        unit=(unit or "stk").strip() or "stk", unit_price=unit_price,
        max_quantity=max_quantity, currency=(currency or "NOK").strip() or "NOK",
    )
    session.add(line)
    session.commit()
    session.refresh(line)
    _audit(session, actor, "contract_line.created", f"contract_line:{line.id}",
           f"prislinje lagt til: {line.item_ref} @ {line.unit_price} (avtale {contract_id})")
    session.commit()
    return line


def update_line(
    session: Session,
    line_id: int,
    *,
    item_ref: str | None = None,
    description: str | None = None,
    unit: str | None = None,
    unit_price: Decimal | None = None,
    max_quantity: Decimal | None = None,
    update_max_quantity: bool = False,
    currency: str | None = None,
    actor: str = "demo-bruker",
) -> ContractLine:
    """Update a price-list line. Pass update_max_quantity to set that nullable field."""
    line = session.get(ContractLine, line_id)
    if line is None:
        raise RegistryError(f"Ukjent prislinje: {line_id}")
    if item_ref is not None:
        if not item_ref.strip():
            raise RegistryError("Artikkelnr er påkrevd.")
        line.item_ref = item_ref.strip()
    if description is not None:
        line.description = description.strip()
    if unit is not None:
        line.unit = unit.strip() or "stk"
    if unit_price is not None:
        line.unit_price = unit_price
    if update_max_quantity:
        line.max_quantity = max_quantity
    if currency is not None:
        line.currency = currency.strip() or "NOK"
    session.add(line)
    session.commit()
    session.refresh(line)
    _audit(session, actor, "contract_line.updated", f"contract_line:{line.id}",
           f"prislinje endret: {line.item_ref}")
    session.commit()
    return line


def delete_line(session: Session, line_id: int, *, actor: str = "demo-bruker") -> None:
    """Delete a price-list line. The removal is recorded in the append-only audit trail."""
    line = session.get(ContractLine, line_id)
    if line is None:
        raise RegistryError(f"Ukjent prislinje: {line_id}")
    item_ref, contract_id = line.item_ref, line.contract_id
    session.delete(line)
    session.commit()
    _audit(session, actor, "contract_line.deleted", f"contract_line:{line_id}",
           f"prislinje slettet: {item_ref} (avtale {contract_id})")
    session.commit()


# --- Read-only helper for the engine (M4): the change clause is available to F4 logic ---------
def change_clause_of(session: Session, contract_id: int) -> str | None:
    """Return the contract's endringsklausul (read-only). Verification logic (F4) will judge an
    e-mail price change AGAINST this. Reads never write (H1)."""
    contract = session.get(Contract, contract_id)
    return contract.change_clause if contract else None
