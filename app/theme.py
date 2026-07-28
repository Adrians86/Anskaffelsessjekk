"""Central visual theme — «Lyst kontor» (variant C).

Single source of truth for the app's colors and typography. UI-only (app/ layer):
`core/` never imports this. Call `inject_theme()` once per page (chrome.header() does it),
so all eight pages read as one product.

Design language:
- Navy #20364F, gold #A8842A.
- Serif in headings (Georgia — web-safe, no external font needed), sans in body.
- Hairline (1px light rule) instead of drop shadows — a calm "lyst kontor" feel.

Verdict semantic colors stay per BRAND.md (#2E7D32 / #B58900 / #C62828) — never re-tinted here.
"""
import streamlit as st

# --- Palette (variant C) ------------------------------------------------------
NAVY = "#20364F"
GOLD = "#A8842A"
INK = "#1C2733"        # body text
MUTED = "#5A6673"      # secondary / captions
HAIRLINE = "#E4E1D8"   # 1px rules instead of shadows
PAPER = "#FCFBF7"      # warm "office paper" surface
SURFACE = "#FFFFFF"    # card surface

# Verdict semantic colors (BRAND.md — non-negotiable).
GREEN = "#2E7D32"
AMBER = "#B58900"
RED = "#C62828"

SERIF = "Georgia, 'Times New Roman', serif"

# The injected stylesheet. Kept as a single string so it is trivially "one source of truth".
# Selectors lean on our own `.as-*` classes plus a few safe global niceties (headings, links,
# tabular numerals) so we do not over-couple to Streamlit's internal DOM.
_STYLE = f"""
<style>
:root {{
  --as-navy: {NAVY};
  --as-gold: {GOLD};
  --as-ink: {INK};
  --as-muted: {MUTED};
  --as-hairline: {HAIRLINE};
  --as-paper: {PAPER};
  --as-surface: {SURFACE};
  --as-ok: {GREEN};
  --as-warn: {AMBER};
  --as-err: {RED};
  --as-serif: {SERIF};
}}

/* Serif, navy headings — the editorial voice of variant C. */
.stApp h1, .stApp h2, .stApp h3, .as-serif {{
  font-family: var(--as-serif);
  color: var(--as-navy);
  letter-spacing: .1px;
}}

/* Gold links (subtle — underline only on hover). */
.stApp a, .stApp a:visited {{ color: var(--as-gold); text-decoration: none; }}
.stApp a:hover {{ text-decoration: underline; }}

/* Tabular numerals wherever numbers must line up. */
.stApp [data-testid="stMetricValue"], .as-tnum {{ font-variant-numeric: tabular-nums; }}

/* Hairline instead of shadow on bordered containers. */
.stApp [data-testid="stVerticalBlockBorderWrapper"] > div:first-child {{
  border-color: var(--as-hairline) !important;
  border-radius: 8px;
  box-shadow: none !important;
}}

/* Primary buttons in navy, secondary as hairline-outlined. */
.stApp .stButton > button[kind="primary"],
.stApp .stDownloadButton > button[kind="primary"] {{
  background: var(--as-navy);
  border-color: var(--as-navy);
}}
.stApp .stButton > button[kind="secondary"] {{
  border-color: var(--as-hairline);
  color: var(--as-navy);
}}

/* --- Page header (G2) ------------------------------------------------------ */
.as-header {{ margin: 2px 0 14px 0; }}
.as-eyebrow {{
  font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
  text-transform: uppercase; color: var(--as-gold);
}}
.as-h1 {{
  font-family: var(--as-serif); font-size: 26px; font-weight: 700;
  color: var(--as-navy); margin: 2px 0 4px 0; line-height: 1.15;
}}
.as-lede {{ font-size: 13.5px; color: var(--as-muted); max-width: 760px; }}
.as-chip {{
  display: inline-block; font-size: 10.5px; font-weight: 600; letter-spacing: .4px;
  color: var(--as-muted); background: var(--as-paper);
  border: 1px solid var(--as-hairline); border-radius: 10px;
  padding: 1px 9px; margin-top: 6px;
}}
</style>
"""


def inject_theme() -> None:
    """Inject the «Lyst kontor» stylesheet. Idempotent; call once per page."""
    st.markdown(_STYLE, unsafe_allow_html=True)
