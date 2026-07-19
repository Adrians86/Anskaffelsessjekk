"""Smoke test: the full domain chain persists and reads back on SQLite."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlmodel import Session, SQLModel, create_engine, select

from core.models import (
    Commitment,
    ConditionType,
    Contract,
    ContractLine,
    ContractType,
    Formalization,
    Invoice,
    InvoiceLine,
    InvoiceSource,
    Order,
    Receipt,
    Regime,
    SourceType,
    Supplier,
)


def test_full_chain_roundtrip():
    engine = create_engine("sqlite://")  # in-memory
    SQLModel.metadata.create_all(engine)

    with Session(engine) as s:
        sup = Supplier(org_number="912345678", name="Hydraulikk Nord AS")
        s.add(sup)
        s.commit()
        s.refresh(sup)

        c = Contract(
            supplier_id=sup.id, contract_type=ContractType.RAMMEAVTALE,
            reference="RA-2026-001", title="Rammeavtale hydrauliske deler",
            total_value=Decimal("2400000"),
            valid_from=date(2026, 1, 1), valid_to=date(2027, 12, 31),
        )
        s.add(c)
        s.commit()
        s.refresh(c)
        s.add(ContractLine(
            contract_id=c.id, item_ref="HYD-1001",
            description="Hydraulikkpumpe A4VG", unit_price=Decimal("12500"),
        ))

        # The differentiator: an e-mail agreement changing the price,
        # proposed by the LLM and confirmed by a human.
        cm = Commitment(
            supplier_id=sup.id, contract_id=c.id,
            source_type=SourceType.EMAIL, source_ref="e-mail 2026-06-12, J. Hansen",
            condition_type=ConditionType.PRICE, item_ref="HYD-1001",
            value=Decimal("11800"), unit="NOK",
            valid_from=date(2026, 6, 12),
            formalization=Formalization.PENDING_ANNEX,
            extracted_by="llm:claude-sonnet-4-6", confirmed_by_user=True,
        )
        s.add(cm)

        o = Order(
            supplier_id=sup.id, contract_id=c.id, reference="AVROP-2026-042",
            requested_by="a.sliwa", estimated_value=Decimal("118000"),
            regime=Regime.FOSA, order_date=date(2026, 7, 1),
        )
        s.add(o)
        s.commit()
        s.refresh(o)
        s.add(Receipt(order_id=o.id, confirmed_by="verksted",
                      confirmed_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC)))

        inv = Invoice(
            supplier_id=sup.id, order_id=o.id, invoice_number="F-88991",
            invoice_date=date(2026, 7, 7), total_ex_vat=Decimal("118000"),
            source=InvoiceSource.EHF,
        )
        s.add(inv)
        s.commit()
        s.refresh(inv)
        s.add(InvoiceLine(
            invoice_id=inv.id, item_ref="HYD-1001",
            description="Hydraulikkpumpe A4VG", quantity=Decimal("10"),
            unit_price=Decimal("11800"), line_total=Decimal("118000"),
        ))
        s.commit()

        got = s.exec(select(Commitment).where(Commitment.item_ref == "HYD-1001")).one()
        assert got.is_active_on(date(2026, 7, 7)) is True
        assert got.formalization == Formalization.PENDING_ANNEX


def test_unconfirmed_llm_commitment_is_inactive():
    """Human-in-the-loop gate: unconfirmed LLM extractions never participate."""
    cm = Commitment(
        supplier_id=1, source_type=SourceType.EMAIL, source_ref="e-mail",
        condition_type=ConditionType.PRICE, valid_from=date(2026, 1, 1),
        extracted_by="llm:claude-sonnet-4-6", confirmed_by_user=False,
    )
    assert cm.is_active_on(date(2026, 6, 1)) is False
