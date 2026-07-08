"""Shared demo database for the Streamlit UI.

One in-memory engine per server process, seeded once with BOTH synthetic
scenarios. ALL DATA IS SYNTHETIC — this is a demo, not a production store.
"""
from __future__ import annotations

import streamlit as st
from sqlmodel import Session, SQLModel, create_engine

from core.synth import scenario_deler, scenario_konsulent


@st.cache_resource
def get_engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        scenario_deler.generate(s)
        scenario_konsulent.generate(s)
    return engine


def get_session() -> Session:
    return Session(get_engine())


def nok(amount) -> str:
    """Format a Decimal as Norwegian kroner for the UI."""
    return f"{float(amount):,.2f} kr".replace(",", " ").replace(".", ",")
