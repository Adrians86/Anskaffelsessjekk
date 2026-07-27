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

# The gyldighetsvurdering is an INDICATION for the saksbehandler, never a legal conclusion
# (jurist red-team, BRIEF_INDIKASJON). The wording points toward a need for legal assessment.
INDIKASJON_CAPTION = ("Gyldighetsvurderingen er en indikasjon som støtte for saksbehandler — "
                      "ikke en juridisk konklusjon.")

# Long (on its own line) and short (chip) labels per status, plus indication text.
_GYLDIGHET_LABEL = {
    "GYLDIG": ("✓ SANNSYNLIGVIS GYLDIG", "✓ SANNSYNLIGVIS GYLDIG", "#2E7D32"),
    "KREVER_FORMALISERING": ("⚠ KREVER FORMALISERING", "⚠ KREVER FORMALISERING", "#B58900"),
    "UGYLDIG": ("✗ MULIG UGYLDIG — krever juridisk vurdering", "✗ MULIG UGYLDIG", "#C62828"),
}

_GYLDIGHET_NOTE = {
    "GYLDIG": "Ser ut til å være i samsvar med avtalens endringsbestemmelser. "
             "Bekreftes av saksbehandler.",
    "KREVER_FORMALISERING": "Avtalen ser ut til å kreve skriftlig tillegg — e-posten er varsel, "
                            "ikke dokumentasjon.",
    "UGYLDIG": "Kan innebære en vesentlig endring (jf. FOA §28-1). Vesentlig endring er en juridisk "
               "skjønnsvurdering som krever ny konkurranse — vurder med jurist før du bekrefter.",
}

# Formalization -> gyldighet status (the demo heuristic for older/manual commitments).
_FORM_TO_STATUS = {
    "FORMALIZED": "GYLDIG",
    "PENDING_ANNEX": "KREVER_FORMALISERING",
    "INFORMAL": "KREVER_FORMALISERING",
}


def _chip(label: str, fg: str, bg: str) -> str:
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;'
            f'padding:2px 10px;border-radius:10px;white-space:nowrap">{label}</span>')


def gyldighet_badge_html(status: str) -> str:
    """Inline colored badge (long label) for a gyldighet status — an indication, not a verdict."""
    long_label, _short, color = _GYLDIGHET_LABEL.get(status, (status, status, "#6B7280"))
    return f'<span style="color:{color};font-weight:700">{long_label}</span>'


def gyldighet_disclaimer() -> None:
    """The fixed grey disclaimer shown under any gyldighetsvurdering."""
    st.caption(INDIKASJON_CAPTION)


def formalization_chip_html(formalization_value: str) -> str:
    label, fg, bg = _FORM_CHIP.get(formalization_value, (formalization_value, "#6B7280", "#F1F3F5"))
    return _chip(label, fg, bg)


def gyldighet_legend() -> None:
    """Render the three-state gyldighet legend (short chip labels) + the indication disclaimer."""
    bg = {"GYLDIG": "#EAF4EC", "KREVER_FORMALISERING": "#FBF7EC", "UGYLDIG": "#FBEAEA"}
    chips = " &nbsp; ".join(
        _chip(_GYLDIGHET_LABEL[s][1], _GYLDIGHET_LABEL[s][2], bg[s])
        for s in ("GYLDIG", "KREVER_FORMALISERING", "UGYLDIG")
    )
    st.markdown(chips, unsafe_allow_html=True)
    gyldighet_disclaimer()


def render_email_commitment(c) -> None:
    """Render one EMAIL-source commitment as a gold-border card with source quote,
    formalization chip and gyldighetsvurdering."""
    form_value = c.formalization.value
    # Prefer a gyldighet recorded at confirm time (e.g. a MULIG UGYLDIG the human registered anyway);
    # fall back to the formalization-derived heuristic for older/manual commitments.
    status = getattr(c, "gyldighet", None) or _FORM_TO_STATUS.get(form_value, "KREVER_FORMALISERING")
    gyld_label, _short, gyld_color = _GYLDIGHET_LABEL.get(status, (status, status, "#6B7280"))
    gyld_note = _GYLDIGHET_NOTE.get(status, "")
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
    gyldighet_disclaimer()
    if not c.confirmed_by_user and c.extracted_by != "manual":
        st.caption("⚠ Ikke bekreftet av saksbehandler — deltar ikke i kontroll.")
