"""Central visual theme — «Lyst kontor» (variant C).

Single source of truth for the app's colors and typography. UI-only (app/ layer):
`core/` never imports this. Call `inject_theme()` (alias: `inject_css()`) once per page
(chrome.header() does it), so all eight pages read as one product.

Design language:
- Navy #1F3A5F, gold #B08D2E.
- Serif in headings (Georgia — web-safe, no external font needed), sans in body.
- Hairline (1px light rule) instead of drop shadows — a calm "lyst kontor" feel.

Verdict semantic colors stay per BRAND.md (#2E7D32 / #B58900 / #C62828) — never re-tinted here.
"""
from html import escape

import streamlit as st

# --- Palette (variant C) ------------------------------------------------------
NAVY      = "#1F3A5F"
NAVY_DEEP = "#152A47"
GOLD      = "#B08D2E"
GOLD_SOFT = "#D9C079"
INK       = "#1A2230"
MUTED     = "#5C6B7F"
LINE      = "#E3E8EF"   # hairlines and borders (also: HAIRLINE)
BG        = "#F4F6F9"   # page/warm background (also: PAPER)
CARD      = "#FFFFFF"   # card surface (also: SURFACE)

# Backward-compat aliases
HAIRLINE = LINE
PAPER    = BG
SURFACE  = CARD

# Verdict semantic colors (BRAND.md — non-negotiable).
GREEN = "#2E7D32"
AMBER = "#B58900"
RED   = "#C62828"

# Status backgrounds + foregrounds (maps to BRAND.md verdict colors)
STATUS_OK_BG    = "#EAF4EC"
STATUS_OK_FG    = "#2E7D32"
STATUS_WARN_BG  = "#FBF7EC"
STATUS_WARN_FG  = "#B8860B"
STATUS_AVVIK_BG = "#FBEAEA"
STATUS_AVVIK_FG = "#C0392B"

# Radii and shadows
RADIUS_CARD  = "12px"
RADIUS_SMALL = "9px"
RADIUS_PILL  = "20px"
SHADOW_CARD  = "0 1px 2px rgba(21,42,71,.06), 0 2px 8px rgba(21,42,71,.05)"

# Typography
FONT_SANS  = "-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
FONT_SERIF = "Georgia,'Times New Roman',serif"
SERIF      = FONT_SERIF   # backward-compat alias

# Pill color map keyed on verdict/status strings
PILL_COLORS: dict[str, tuple[str, str]] = {
    "SAMSVAR":        (STATUS_OK_BG,    STATUS_OK_FG),
    "TIL_VURDERING":  (STATUS_WARN_BG,  STATUS_WARN_FG),
    "AVVIK":          (STATUS_AVVIK_BG, STATUS_AVVIK_FG),
    "FORMALISERT":    (STATUS_OK_BG,    STATUS_OK_FG),
    "UFORMELL":       (STATUS_WARN_BG,  STATUS_WARN_FG),
}

# The injected stylesheet. One string = one source of truth.
# Selectors lean on our own `.as-*` classes plus a few safe global niceties.
_STYLE = f"""
<style>
:root {{
  /* Primary tokens (new naming) */
  --navy: {NAVY}; --navy-deep: {NAVY_DEEP};
  --gold: {GOLD}; --gold-soft: {GOLD_SOFT};
  --ink: {INK}; --muted: {MUTED};
  --line: {LINE}; --bg: {BG}; --card: {CARD};
  --ok-bg: {STATUS_OK_BG}; --ok-fg: {STATUS_OK_FG};
  --warn-bg: {STATUS_WARN_BG}; --warn-fg: {STATUS_WARN_FG};
  --avvik-bg: {STATUS_AVVIK_BG}; --avvik-fg: {STATUS_AVVIK_FG};
  --radius-card: {RADIUS_CARD}; --radius-sm: {RADIUS_SMALL}; --radius-pill: {RADIUS_PILL};
  --shadow-card: {SHADOW_CARD};
  --font-sans: {FONT_SANS}; --font-serif: {FONT_SERIF};

  /* Legacy aliases (--as-*) for backward compat with existing CSS classes */
  --as-navy: {NAVY}; --as-gold: {GOLD};
  --as-ink: {INK}; --as-muted: {MUTED};
  --as-hairline: {LINE}; --as-paper: {BG}; --as-surface: {CARD};
  --as-ok: {GREEN}; --as-warn: {AMBER}; --as-err: {RED};
  --as-serif: {FONT_SERIF};
}}

body, .stApp {{ background: var(--bg); font-family: var(--font-sans); color: var(--ink); }}

/* Serif, navy headings */
.stApp h1, .stApp h2, .stApp h3, .as-serif {{
  font-family: var(--font-serif);
  color: var(--navy);
  letter-spacing: .1px;
}}

/* Gold links */
.stApp a, .stApp a:visited {{ color: var(--gold); text-decoration: none; }}
.stApp a:hover {{ text-decoration: underline; }}

/* Tabular numerals */
.stApp [data-testid="stMetricValue"], .as-tnum {{ font-variant-numeric: tabular-nums; }}

/* Hairline on bordered containers */
.stApp [data-testid="stVerticalBlockBorderWrapper"] > div:first-child {{
  border-color: var(--line) !important;
  border-radius: 8px;
  box-shadow: none !important;
}}

/* Primary buttons in navy */
.stApp .stButton > button[kind="primary"],
.stApp .stDownloadButton > button[kind="primary"] {{
  background: var(--navy);
  border-color: var(--navy);
}}
.stApp .stButton > button[kind="secondary"] {{
  border-color: var(--line);
  color: var(--navy);
}}

/* --- Page header (G2) ------------------------------------------------------ */
.as-header {{ margin: 2px 0 14px 0; }}
.as-eyebrow {{
  font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
  text-transform: uppercase; color: var(--gold);
}}
.as-h1 {{
  font-family: var(--font-serif); font-size: 26px; font-weight: 700;
  color: var(--navy); margin: 2px 0 4px 0; line-height: 1.15;
}}
.as-lede {{ font-size: 13.5px; color: var(--muted); max-width: 760px; }}
.as-chip {{
  display: inline-block; font-size: 10.5px; font-weight: 600; letter-spacing: .4px;
  color: var(--muted); background: var(--bg);
  border: 1px solid var(--line); border-radius: 10px;
  padding: 1px 9px; margin-top: 6px;
}}

/* --- KPI editorial strip (G3) ---------------------------------------------- */
.as-kpis {{
  display: flex; background: var(--card);
  border: 1px solid var(--line); border-radius: 10px;
  overflow: hidden; margin: 2px 0 16px 0;
}}
.as-kpi {{
  flex: 1; padding: 12px 16px;
  border-left: 1px solid var(--line); border-top: 3px solid var(--navy);
}}
.as-kpi:first-child {{ border-left: 0; }}
.as-kpi .as-kpi-label {{
  font-size: 10.5px; letter-spacing: .8px; text-transform: uppercase; color: var(--muted);
}}
.as-kpi .as-kpi-val {{
  font-family: var(--font-serif); font-size: 25px; font-weight: 700; color: var(--navy);
  margin-top: 2px; line-height: 1.1; font-variant-numeric: tabular-nums;
}}
.as-kpi.err {{ border-top-color: {RED}; }}
.as-kpi.err .as-kpi-val {{ color: {RED}; }}
.as-kpi.warn {{ border-top-color: {AMBER}; }}
.as-kpi.warn .as-kpi-val {{ color: {AMBER}; }}
.as-kpi.ok {{ border-top-color: {GREEN}; }}
.as-kpi.ok .as-kpi-val {{ color: {GREEN}; }}
.as-kpi.gold {{ border-top-color: var(--gold); }}
.as-kpi.gold .as-kpi-val {{ color: var(--gold); }}

/* --- Panel heading + events feed (G3) -------------------------------------- */
.as-panel-title {{
  font-size: 11px; letter-spacing: .8px; text-transform: uppercase;
  color: var(--muted); font-weight: 700; margin: 4px 0 8px 0;
}}
.as-feed {{
  background: var(--card); border: 1px solid var(--line);
  border-radius: 10px; padding: 6px 14px; font-size: 12.5px; color: var(--ink);
}}
.as-feed .as-feed-row {{ padding: 7px 0; border-bottom: 1px dashed var(--line); }}
.as-feed .as-feed-row:last-child {{ border-bottom: 0; }}
.as-feed time {{ color: var(--muted); margin-right: 8px; font-variant-numeric: tabular-nums; }}

/* --- Tables unified (G4) --------------------------------------------------- */
.stApp [data-testid="stDataFrame"] {{
  border: 1px solid var(--line); border-radius: 8px; overflow: hidden;
}}
.stApp table {{
  border: 1px solid var(--line); border-radius: 8px; border-collapse: separate;
  border-spacing: 0; overflow: hidden; font-variant-numeric: tabular-nums;
}}
.stApp table th {{
  background: var(--bg); color: var(--navy);
  font-size: 11px; letter-spacing: .3px; text-transform: uppercase;
}}
.stApp table td, .stApp table th {{ border-color: var(--line) !important; }}

/* --- Section header (G3) --------------------------------------------------- */
.as-section-header {{
  display: flex; align-items: center; gap: 12px; margin: 24px 0 12px;
}}
.as-section-label {{
  font-family: var(--font-sans); font-size: 11px; letter-spacing: 2px;
  text-transform: uppercase; color: var(--navy); font-weight: 700; white-space: nowrap;
}}
.as-section-rule {{ flex: 1; height: 1px; background: var(--line); }}

/* --- Sidebar (G5): navy background, gold active indicator ------------------ */
[data-testid="stSidebar"] {{
  background: var(--navy-deep) !important;
}}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {{
  color: #B8C8D8 !important;
}}
[data-testid="stSidebarNavLink"][aria-selected="true"] {{
  background: rgba(176,141,46,0.15) !important;
  border-left: 3px solid var(--gold) !important;
  color: var(--gold) !important;
}}

/* --- Mobile-lite (G5) ------------------------------------------------------ */
@media (max-width: 640px) {{
  .as-kpis {{ flex-wrap: wrap; }}
  .as-kpi {{ flex: 1 1 45%; border-left: 0; border-bottom: 1px solid var(--line); }}
  .as-h1 {{ font-size: 22px; }}
  .as-lede {{ font-size: 12.5px; }}
  .stApp table {{ display: block; overflow-x: auto; white-space: nowrap; }}
}}
</style>
"""


def inject_theme() -> None:
    """Inject the «Lyst kontor» stylesheet. Idempotent; call once per page."""
    st.markdown(_STYLE, unsafe_allow_html=True)


# Alias — brief calls for inject_css()
inject_css = inject_theme


def section_header(label: str) -> None:
    """Render a section label with a trailing hairline rule.

    Replaces st.subheader() throughout the app for visual consistency.
    """
    st.markdown(
        f'<div class="as-section-header">'
        f'<span class="as-section-label">{escape(label)}</span>'
        f'<div class="as-section-rule"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def card_open() -> str:
    """Return opening HTML for a styled card div."""
    return (
        '<div style="background:var(--card);border:1px solid var(--line);'
        'border-radius:var(--radius-card);box-shadow:var(--shadow-card);'
        'padding:20px 24px;margin-bottom:16px">'
    )


def card_close() -> str:
    """Return closing HTML for a card div."""
    return '</div>'


def kpi_tile(label: str, value: str, color: str = "var(--gold)") -> None:
    """Render a KPI tile with a 3px left accent."""
    st.markdown(
        f'<div style="background:var(--card);border:1px solid var(--line);'
        f'border-radius:var(--radius-card);border-left:3px solid {color};'
        f'padding:16px 20px;box-shadow:var(--shadow-card)">'
        f'<div style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;'
        f'color:var(--muted);margin-bottom:6px">{escape(label)}</div>'
        f'<div style="font-family:var(--font-serif);font-size:32px;font-weight:700;'
        f'font-feature-settings:\'tnum\';color:var(--ink)">{escape(value)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def pill(label: str, key: str | None = None) -> str:
    """Return an HTML pill span for verdict/status display.

    Render the result with unsafe_allow_html=True.
    """
    k = (key or label).upper()
    bg, fg = PILL_COLORS.get(k, ("var(--line)", "var(--muted)"))
    return (
        f'<span style="display:inline-block;background:{bg};color:{fg};'
        f'border-radius:var(--radius-pill);padding:2px 9px;'
        f'font-size:11px;font-weight:700">{escape(label)}</span>'
    )
