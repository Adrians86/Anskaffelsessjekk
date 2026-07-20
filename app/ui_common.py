"""Shared small UI components. Keeps the BRAND.md verdict colors in ONE place."""

# Verdict pill — BRAND.md semantic colors (non-negotiable).
_VERDICT = {
    "AVVIK": ("🔴 AVVIK", "#C62828"),
    "TIL_VURDERING": ("🟡 TIL VURDERING", "#B58900"),
    "SAMSVAR": ("✓ SAMSVAR", "#2E7D32"),
}


def verdict_pill(verdict_value: str) -> str:
    """Return an inline HTML span for a verdict. Render with unsafe_allow_html=True."""
    label, color = _VERDICT.get(verdict_value, (verdict_value, "#6B7280"))
    return f'<span style="color:{color};font-weight:600">{label}</span>'
