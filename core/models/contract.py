"""Contracts (rammeavtale / enkeltkjøp) and their lines."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class ContractType(str, Enum):
    RAMMEAVTALE = "RAMMEAVTALE"
    ENKELTKJOP = "ENKELTKJOP"


# Endringsklausul (change clause) — how a change to the contract may legally be made. Read by the
# forpliktelse/verifikasjon logic later (F4): an e-mail that changes a price is judged AGAINST this.
CLAUSE_KUN_SKRIFTLIG = "kun_skriftlig_tillegg"      # → «krever formalisering»
CLAUSE_MINDRE_JUSTERING = "mindre_justering_epost"  # → kan være gyldig
CLAUSE_KPI = "kpi_regulering"
CLAUSE_ANNET = "annet"
CHANGE_CLAUSES = (CLAUSE_KUN_SKRIFTLIG, CLAUSE_MINDRE_JUSTERING, CLAUSE_KPI, CLAUSE_ANNET)

# Kontrakt-status and regime as simple strings (kept flexible, like Supplier.status).
CONTRACT_STATUSES = ("aktiv", "utløpt", "utkast")
CONTRACT_REGIMES = ("FOA", "FOSA")


class Contract(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    contract_type: ContractType = ContractType.RAMMEAVTALE
    reference: str = Field(index=True)          # internal contract reference (avtalenr)
    title: str
    regime: str = "FOA"                         # FOA | FOSA
    total_value: Decimal | None = None          # estimated total value / ramme (NOK, ex. VAT)
    valid_from: date
    valid_to: date | None = None
    change_clause: str = CLAUSE_KUN_SKRIFTLIG   # endringsklausul (see CHANGE_CLAUSES)
    status: str = "aktiv"                       # aktiv | utløpt | utkast
    is_deleted: bool = Field(default=False, index=True)   # soft delete — row + trail kept
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ContractLine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    contract_id: int = Field(foreign_key="contract.id", index=True)
    item_ref: str = Field(index=True)           # article number / service category (artikkelnr)
    description: str
    unit_price: Decimal                         # agreed price or hourly rate (ex. VAT)
    unit: str = "pcs"                           # stk, time, mnd ...
    max_quantity: Decimal | None = None         # ceiling per avrop / period, if agreed
    currency: str = "NOK"                       # price list currency (default NOK)
