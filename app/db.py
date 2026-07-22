"""Shared demo database for the Streamlit UI.

One in-memory engine per server process, seeded once with BOTH synthetic
scenarios. ALL DATA IS SYNTHETIC — this is a demo, not a production store.
StaticPool pins every thread to the single in-memory connection —
required on Streamlit Cloud, where pages run in separate threads.
"""
from __future__ import annotations

import streamlit as st
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from core.synth import scenario_deler, scenario_konsulent


@st.cache_resource
def get_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        scenario_deler.generate(s)
        scenario_konsulent.generate(s)
    return engine


def get_session() -> Session:
    return Session(get_engine())


def nok(amount) -> str:
    """Format an amount as Norwegian kroner for the UI.

    Formats the value directly (Decimal stays exact — no float round-trip); also accepts
    float/int for already-aggregated display values.
    """
    return f"{amount:,.2f} kr".replace(",", " ").replace(".", ",")


def money(amount, currency: str | None = "NOK") -> str:
    """Format an amount with its invoice currency — 'kr' for NOK, the code otherwise (EUR, USD…).

    Never converts: a foreign-currency amount is shown in its own currency, never as NOK.
    """
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    code = (currency or "NOK").upper()
    return f"{formatted} kr" if code == "NOK" else f"{formatted} {code}"
