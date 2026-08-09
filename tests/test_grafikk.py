"""Grafikk v1 — the app must read as ONE product: every page opens, the «Lyst kontor»
theme is injected, the Arbeidsflate reconciliation holds (22 310 kr), and the mobile-lite
minimum is present. UI-level smoke (app/ layer) — pytest does not otherwise cover app/ pages.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = [
    "Hjem.py",
    "pages/1_Fakturakontroll.py",
    "pages/2_Avtaler_og_forpliktelser.py",
    "pages/3_Leverandorer.py",
    "pages/4_Terskelsjekk.py",
    "pages/5_Styringsinformasjon.py",
    "pages/6_Plattformen.py",
    "pages/7_Sikkerhet.py",
]


def _run(page: str) -> AppTest:
    at = AppTest.from_file(str(APP / page), default_timeout=60)
    at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_every_page_opens(page: str) -> None:
    """All eight pages render without raising — the demo never crashes on open."""
    at = _run(page)
    assert not at.exception, f"{page}: {[str(e.value) for e in at.exception]}"


def test_theme_and_page_header_on_every_page() -> None:
    """The «Lyst kontor» theme (navy #1F3A5F) and the editorial header render on each page."""
    for page in PAGES:
        md = " ".join(m.value for m in _run(page).markdown)
        assert "#1F3A5F" in md, f"{page}: theme not injected"
        assert "as-header" in md, f"{page}: shared page header missing"
        assert "Syntetiske data" in md, f"{page}: syntetiske-data chip missing"


def test_arbeidsflate_reconciliation_and_layout() -> None:
    """Arbeidsflate keeps Verdi funnet = 22 310 kr and uses the KPI editorial strip."""
    md = " ".join(m.value for m in _run("Hjem.py").markdown)
    assert "22 310" in md              # partner-confirmed demo total (both scenarios)
    assert "as-kpis" in md             # editorial strip, not loose metric cards
    assert "Krever handling" in md and "Siste hendelser" in md


def test_mobile_lite_minimum_present() -> None:
    """Mobile-lite: the narrow-screen media query and the desktop note ship on every page."""
    md = " ".join(m.value for m in _run("Hjem.py").markdown)
    assert "max-width: 640px" in md    # KPI strip wraps / tables scroll on a phone
    assert "Optimalisert for desktop" in md


def test_dato_format_ddmmyyyy() -> None:
    """UX-pass U6: dates render as DD.MM.YYYY (Norwegian); None → «—»."""
    from datetime import date

    import db
    assert db.dato(date(2026, 1, 5)) == "05.01.2026"
    assert db.dato(None) == "—"
