"""Shared page chrome — theme injection, navy product band, editorial page header, footer.

UI-only helper (app/ layer). Keeps every page's styling, top band and footer identical so the
demo reads as one product. Colors/typography come from theme.py (single source of truth).
Verdict semantic colors stay exactly as BRAND.md (#2E7D32 / #B58900 / #C62828).
"""
from html import escape

import streamlit as st
from theme import HAIRLINE, MUTED, NAVY, inject_theme

FOOTER_TEXT = (
    "Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i logistikk og "
    "innkjøp · Beslutningsstøtte, ikke juridisk rådgivning · Syntetiske data"
)

_HEADER_HTML = (
    f'<div style="background:{NAVY};color:#FFFFFF;padding:6px 14px;border-radius:6px;'
    'font-weight:600;font-size:13px;letter-spacing:.4px;margin:0 0 8px 0">'
    'Anskaffelsessjekk'
    '<span style="opacity:.7;font-weight:400"> · kontroll av offentlige anskaffelser</span>'
    '</div>'
)


def header() -> None:
    """Inject the theme, then render the navy product band. Call once, after set_page_config."""
    inject_theme()
    st.markdown(_HEADER_HTML, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, lede: str, chip: str = "Syntetiske data") -> None:
    """Render the shared editorial page header: eyebrow + serif H1 + lede + a small chip.

    Replaces per-page st.title()+caption so all eight pages share one masthead. Every value is
    HTML-escaped (hard rule #11) even though today's callers pass static strings."""
    st.markdown(
        '<div class="as-header">'
        f'<div class="as-eyebrow">{escape(eyebrow)}</div>'
        f'<div class="as-h1">{escape(title)}</div>'
        f'<div class="as-lede">{escape(lede)}</div>'
        f'<span class="as-chip">{escape(chip)}</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    """Render the consistent footer with a hairline rule."""
    st.markdown(
        f'<hr style="border:0;border-top:1px solid {HAIRLINE};margin:18px 0 8px 0">'
        f'<div style="font-size:11.5px;color:{MUTED}">{escape(FOOTER_TEXT)}</div>',
        unsafe_allow_html=True,
    )
