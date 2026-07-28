"""Shared small UI components. Keeps the BRAND.md verdict colors in ONE place."""

# Verdict pill — BRAND.md semantic colors (non-negotiable) on light tints, as a rounded chip.
# (text color, tint background)
_VERDICT = {
    "AVVIK": ("AVVIK", "#C62828", "#FBEAEA"),
    "TIL_VURDERING": ("TIL VURDERING", "#B58900", "#FCF4DE"),
    "SAMSVAR": ("SAMSVAR", "#2E7D32", "#E8F4E8"),
}


def verdict_pill(verdict_value: str) -> str:
    """Return an inline rounded chip for a verdict. Render with unsafe_allow_html=True."""
    label, fg, bg = _VERDICT.get(verdict_value, (verdict_value, "#5A6673", "#F1F3F5"))
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:700;'
            f'letter-spacing:.3px;padding:3px 10px;border-radius:10px;'
            f'white-space:nowrap">{label}</span>')
