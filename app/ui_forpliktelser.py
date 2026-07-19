"""Shared UI rendering for forpliktelser (commitments) — used by Avtaler and Leverandører.

UI-only helper (app/ layer). Renders an e-mail commitment as a gold-border card with source
quote, formalization chip and a UI-level gyldighetsvurdering. The gyldighet derivation is a
demo-level heuristic on existing data (no full rules pass yet) — see BRIEF_VERIFISERING_V1 V1(b).
"""
from html import escape

import streamlit as st
from db import nok

GOLD = "#B08D2E"

# Formalization chip: label + text/background colors.
_FORM_CHIP = {
    "FORMALIZED": ("FORMALISERT", "#2E7D32", "#EAF4EC"),
    "PENDING_ANNEX": ("VENTER PÅ TILLEGG", "#B58900", "#FBF7EC"),
    "INFORMAL": ("UFORMELL", "#6B7280", "#F1F3F5"),
}

# Gyldighetsvurdering (UI-level, demo): formalization -> (label, color, explanation).
_GYLDIGHET = {
    "FORMALIZED": ("✓ GYLDIG", "#2E7D32",
                   "I samsvar med avtalens endringsbestemmelser."),
    "PENDING_ANNEX": ("⚠ KREVER FORMALISERING", "#B58900",
                      "Avtalen krever skriftlig tillegg — e-posten er varsel, ikke dokumentasjon."),
    "INFORMAL": ("⚠ KREVER FORMALISERING", "#B58900",
                 "Avtalen krever skriftlig tillegg — e-posten er varsel, ikke dokumentasjon."),
}


def _chip(label: str, fg: str, bg: str) -> str:
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;'
            f'padding:2px 10px;border-radius:10px;white-space:nowrap">{label}</span>')


def formalization_chip_html(formalization_value: str) -> str:
    label, fg, bg = _FORM_CHIP.get(formalization_value, (formalization_value, "#6B7280", "#F1F3F5"))
    return _chip(label, fg, bg)


def gyldighet_legend() -> None:
    """Render the three-state gyldighet legend so the concept is always visible."""
    st.markdown(
        f'{_chip("✓ GYLDIG", "#2E7D32", "#EAF4EC")} &nbsp; '
        f'{_chip("⚠ KREVER FORMALISERING", "#B58900", "#FBF7EC")} &nbsp; '
        f'{_chip("✗ UGYLDIG", "#C62828", "#FBEAEA")}',
        unsafe_allow_html=True,
    )


def render_email_commitment(c) -> None:
    """Render one EMAIL-source commitment as a gold-border card with source quote,
    formalization chip and gyldighetsvurdering."""
    form_value = c.formalization.value
    gyld_label, gyld_color, gyld_note = _GYLDIGHET.get(
        form_value, ("⚠ KREVER FORMALISERING", "#B58900", ""))
    value_txt = escape(f"{nok(c.value)}" if c.value is not None else "—")
    unit_txt = f" {escape(c.unit)}" if c.unit else ""
    # Defensive: a stale core package on Cloud may lack source_quote — degrade, don't crash.
    quote = getattr(c, "source_quote", None)
    # XSS: every dynamic value (commitment fields originate from data / future e-mail imports)
    # is HTML-escaped before interpolation into unsafe_allow_html markup.
    item_ref = escape(c.item_ref) if c.item_ref else "—"
    condition = escape(c.condition_type.value)
    source_ref = escape(c.source_ref)
    valid_from = escape(str(c.valid_from))

    st.markdown(
        f'<div style="border-left:4px solid {GOLD};background:#FBF7EC;padding:12px 16px;'
        'border-radius:4px;margin:8px 0">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
        f'<strong>📧 {item_ref} · {condition} = {value_txt}{unit_txt}</strong>'
        f'{formalization_chip_html(form_value)}</div>'
        f'<div style="font-size:12px;color:#6B7280;margin-top:4px">'
        f'Kilde: {source_ref} · gjelder fra {valid_from}</div>'
        + (f'<div style="font-style:italic;color:#5A5140;background:#FFFDF6;'
           f'border-left:2px solid {GOLD};padding:6px 10px;margin-top:8px;font-size:13px">'
           f'«{escape(quote)}»</div>' if quote else "")
        + f'<div style="margin-top:8px;font-weight:600;color:{gyld_color}">'
          f'Gyldighetsvurdering: {gyld_label}</div>'
          f'<div style="font-size:12px;color:#6B7280">{gyld_note}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if not c.confirmed_by_user and c.extracted_by != "manual":
        st.caption("⚠ Ikke bekreftet av saksbehandler — deltar ikke i kontroll.")
