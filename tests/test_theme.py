"""Tests for app/theme.py — design token integrity (G8)."""
import sys
from pathlib import Path

# Ensure app/ is on the import path (mirrors how Streamlit loads pages).
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from theme import (  # noqa: E402
    AMBER,
    BG,
    CARD,
    FONT_SERIF,
    GOLD,
    GREEN,
    HAIRLINE,
    INK,
    LINE,
    MUTED,
    NAVY,
    NAVY_DEEP,
    PAPER,
    PILL_COLORS,
    RED,
    STATUS_AVVIK_BG,
    STATUS_AVVIK_FG,
    STATUS_OK_BG,
    STATUS_OK_FG,
    STATUS_WARN_BG,
    SURFACE,
    card_close,
    card_open,
    inject_css,
    inject_theme,
    pill,
    section_header,
)


def test_primary_tokens():
    assert NAVY == "#1F3A5F"
    assert GOLD == "#B08D2E"
    assert BG == "#F4F6F9"
    assert INK == "#1A2230"
    assert MUTED == "#5C6B7F"
    assert LINE == "#E3E8EF"
    assert CARD == "#FFFFFF"
    assert NAVY_DEEP == "#152A47"


def test_brand_verdict_colors_unchanged():
    """BRAND.md colors must never change."""
    assert GREEN == "#2E7D32"
    assert AMBER == "#B58900"
    assert RED == "#C62828"


def test_status_token_alignment():
    assert STATUS_OK_FG == GREEN
    assert STATUS_AVVIK_FG == "#C0392B"  # slightly darker red for text
    assert STATUS_WARN_BG == "#FBF7EC"


def test_backward_compat_aliases():
    """Legacy aliases still resolve to the same values."""
    assert HAIRLINE == LINE
    assert PAPER == BG
    assert SURFACE == CARD


def test_inject_css_alias():
    """inject_css must be the same callable as inject_theme."""
    assert inject_css is inject_theme


def test_pill_samsvar():
    html = pill("SAMSVAR")
    assert "SAMSVAR" in html
    assert STATUS_OK_BG in html or "ok-bg" in html


def test_pill_avvik():
    html = pill("AVVIK")
    assert "AVVIK" in html
    assert STATUS_AVVIK_BG in html or "avvik-bg" in html


def test_pill_unknown_key():
    html = pill("UKJENT_KODE")
    assert "UKJENT_KODE" in html
    assert "var(--line)" in html or "var(--muted)" in html


def test_pill_colors_map_coverage():
    for key in ("SAMSVAR", "TIL_VURDERING", "AVVIK", "FORMALISERT", "UFORMELL"):
        assert key in PILL_COLORS, f"PILL_COLORS missing key: {key}"


def test_card_html_structure():
    assert "var(--card)" in card_open()
    assert "var(--line)" in card_open()
    assert card_close() == "</div>"


def test_font_serif_contains_georgia():
    assert "Georgia" in FONT_SERIF


def test_section_header_escapes_html(monkeypatch):
    """section_header must escape label — hard rule #11."""
    captured = []

    def fake_markdown(text, **kwargs):
        captured.append(text)

    import streamlit as st
    monkeypatch.setattr(st, "markdown", fake_markdown)
    section_header("<script>alert(1)</script>")
    assert captured
    assert "<script>" not in captured[0]
    assert "&lt;script&gt;" in captured[0]
