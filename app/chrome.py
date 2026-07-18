"""Shared page chrome — navy header band and consistent footer.

UI-only helper (app/ layer). Keeps every page's top band and footer identical
so the demo reads as one product. Verdict semantic colors live in the pages and
must stay exactly as BRAND.md (#2E7D32 / #B58900 / #C62828).
"""
import streamlit as st

NAVY = "#1F3A5F"

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
    """Render the navy product header band. Call once, right after set_page_config."""
    st.markdown(_HEADER_HTML, unsafe_allow_html=True)


def footer() -> None:
    """Render the consistent footer. Call once at the end of the page."""
    st.markdown("---")
    st.caption(FOOTER_TEXT)
