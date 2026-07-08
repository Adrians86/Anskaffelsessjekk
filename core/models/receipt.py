"""Mottak — goods/service receipt confirmation (gap G1: 'mottak bekreftet')."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Receipt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    confirmed_by: str
    confirmed_at: datetime
    notes: str | None = None
