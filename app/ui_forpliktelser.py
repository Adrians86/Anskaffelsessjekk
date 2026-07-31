"""Shared UI rendering for forpliktelser (commitments) — used by Avtaler and Leverandører.

UI-only helper (app/ layer). Renders an e-mail commitment as a gold-border card with source
quote, formalization chip and a UI-level gyldighetsvurdering. The gyldighet derivation is a
demo-level heuristic on existing data (no full rules pass yet) — see BRIEF_VERIFISERING_V1 V1(b).
"""
from decimal import Decimal
from html import escape

import streamlit as st
from db import dato, nok

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
    valid_from = escape(dato(c.valid_from))

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


# =============================================================================
# Funksjon 4 — Forpliktelse A–Z: legg til (flere veier) · rediger · slett · vis
# =============================================================================
from datetime import date  # noqa: E402

from core.extraction.epost import parse_email  # noqa: E402
from core.models import ConditionType, Formalization, SourceType  # noqa: E402
from core.registry import (  # noqa: E402
    RegistryError,
    assess_gyldighet,
    create_commitment,
    list_commitments,
    soft_delete_commitment,
    update_commitment,
)

# The four registreringsveier (P1). Each preselects a source type + formalization; e-post also
# shows a paste box that fills the form (a convenience, never a requirement — «fikser fortsatt manuelt»).
_VEIER = {
    "manuelt": ("✍ Manuelt", SourceType.OTHER, Formalization.PENDING_ANNEX),
    "epost": ("📧 Lim inn e-post", SourceType.EMAIL, Formalization.PENDING_ANNEX),
    "mote": ("🤝 Møte / referat", SourceType.MEETING_NOTE, Formalization.PENDING_ANNEX),
    "aneks": ("📄 Aneks / skriftlig tillegg", SourceType.OTHER, Formalization.FORMALIZED),
}
_COND_LABEL = {
    "PRICE": "Pris", "RATE": "Timepris", "DISCOUNT": "Rabatt",
    "QUANTITY": "Mengde", "DEADLINE": "Frist", "SCOPE": "Omfang",
}
_COND_ORDER = ["PRICE", "RATE", "DISCOUNT", "QUANTITY", "DEADLINE", "SCOPE"]
_SOURCE_LABEL = {"EMAIL": "E-post", "MEETING_NOTE": "Møtereferat",
                 "CONTRACT": "Kontrakt/aneks", "OTHER": "Annet"}


def forpliktelse_flash() -> None:
    fl = st.session_state.pop("forpliktelse_flash", None)
    if fl:
        (st.toast if fl[0] == "ok" else st.error)(
            fl[1], **({"icon": "✅"} if fl[0] == "ok" else {}))


def _flash_rerun(kind: str, msg: str) -> None:
    st.cache_data.clear()
    st.session_state["forpliktelse_flash"] = (kind, msg)
    st.rerun()


def _cond_from_str(name: str) -> ConditionType:
    return ConditionType[name] if name in ConditionType.__members__ else ConditionType.PRICE


def render_ny_forpliktelse(session, suppliers, *, default_supplier_id=None, key_prefix: str) -> None:
    """P1/P2/P4 — add a forpliktelse at the supplier via several veier (manual / paste e-mail /
    meeting / annex), for one or several suppliers, with felles or per-leverandør vilkår."""
    kp = key_prefix
    vei = st.radio("Hvordan vil du registrere?", list(_VEIER),
                   format_func=lambda k: _VEIER[k][0], horizontal=True, key=f"{kp}_vei")
    _label, src_default, form_default = _VEIER[vei]

    # E-post-veien: paste box that fills the form (P1 «snarvei», not a requirement).
    if vei == "epost":
        st.text_area("Lim inn e-postinnhold", key=f"{kp}_email", height=110,
                     placeholder="Lim inn teksten fra e-posten her — vi fyller skjemaet under.")

        def _apply_email():
            p = parse_email(st.session_state.get(f"{kp}_email", ""))
            if p.item_ref:
                st.session_state[f"{kp}_item"] = p.item_ref
            if p.value is not None:
                st.session_state[f"{kp}_value"] = float(p.value)
            st.session_state[f"{kp}_cond"] = (p.condition_type
                                              if p.condition_type in _COND_LABEL else "PRICE")
            st.session_state[f"{kp}_quote"] = st.session_state.get(f"{kp}_email", "").strip()
            st.session_state[f"{kp}_scope"] = (p.gyldighet == "UGYLDIG")

        st.button("📥 Tolk e-post (fyll skjemaet)", key=f"{kp}_parse", on_click=_apply_email)
        st.caption("Tekstgjenkjenning (ikke KI) foreslår felt — kontrollér og rediger før du lagrer.")

    # P2 — én eller flere leverandører (standard: én).
    sup_by_name = {s.name: s.id for s in suppliers}
    multi = st.toggle("Gjelder flere leverandører", key=f"{kp}_multi")
    chosen_ids: list[int] = []
    per_supplier_values: dict[int, float] = {}
    felles = True
    if not multi:
        names = list(sup_by_name)
        idx = 0
        if default_supplier_id is not None:
            for i, s in enumerate(suppliers):
                if s.id == default_supplier_id:
                    idx = i
                    break
        pick = st.selectbox("Leverandør", names, index=idx, key=f"{kp}_sup")
        if pick:
            chosen_ids = [sup_by_name[pick]]
    else:
        picks = st.multiselect("Leverandører", list(sup_by_name), key=f"{kp}_sups")
        chosen_ids = [sup_by_name[n] for n in picks]
        # P4 — «ulikt bæres»: felles vilkår eller ulik verdi per leverandør.
        felles = st.radio("Vilkår", ["Felles vilkår", "Ulikt per leverandør"],
                          horizontal=True, key=f"{kp}_felles") == "Felles vilkår"

    c1, c2, c3 = st.columns(3)
    item = c1.text_input("Artikkel / tjeneste (valgfri)", key=f"{kp}_item")
    cond_name = c2.selectbox("Betingelse", _COND_ORDER, format_func=_COND_LABEL.get, key=f"{kp}_cond")
    value = c3.number_input("Avtalt verdi", min_value=0.0, step=100.0, key=f"{kp}_value")

    if multi and not felles and chosen_ids:
        st.caption("Ulik verdi per leverandør:")
        id_to_name = {v: k for k, v in sup_by_name.items()}
        vcols = st.columns(min(len(chosen_ids), 3) or 1)
        for i, sid in enumerate(chosen_ids):
            per_supplier_values[sid] = vcols[i % len(vcols)].number_input(
                id_to_name[sid], min_value=0.0, step=100.0, value=float(value),
                key=f"{kp}_val_{sid}")

    d1, d2, d3 = st.columns(3)
    kilde = d1.text_input("Kilde (avsender / referanse)", key=f"{kp}_kilde",
                          placeholder="f.eks. J. Hansen, møte 12.06")
    valid_from = d2.date_input("Gyldig fra", value=date(2026, 6, 1), key=f"{kp}_vf")
    unit = d3.text_input("Enhet", value="NOK", key=f"{kp}_unit")
    quote = st.text_area("Sitat / notat (valgfri)", key=f"{kp}_quote", height=68)

    # P3 — gyldighet as an INDICATION, using the supplier's endringsklausul. Shown live.
    scope = bool(st.session_state.get(f"{kp}_scope"))
    if len(chosen_ids) == 1:
        gyld = assess_gyldighet(session, chosen_ids[0], scope_change=scope)
        st.markdown(f"**Gyldighetsvurdering (indikasjon):** {gyldighet_badge_html(gyld)}",
                    unsafe_allow_html=True)
        gyldighet_disclaimer()
    elif len(chosen_ids) > 1:
        st.caption("Gyldighetsvurderingen beregnes per leverandør (ulik endringsklausul kan gi "
                   "ulik indikasjon).")

    if st.button("Lagre forpliktelse", type="primary", key=f"{kp}_save"):
        if not chosen_ids:
            st.error("Velg minst én leverandør.")
            return
        if not (kilde or "").strip():
            st.error("Kilde er påkrevd.")
            return
        src_ref = kilde.strip()
        extracted = "regel:epost-parser-v1" if vei == "epost" else "manual"
        try:
            for sid in chosen_ids:
                sval = per_supplier_values.get(sid, value) if (multi and not felles) else value
                create_commitment(
                    session, supplier_id=sid, condition_type=_cond_from_str(cond_name),
                    source_type=src_default, source_ref=src_ref,
                    item_ref=item or None,
                    value=(Decimal(str(sval)) if sval else None),
                    unit=unit or None, valid_from=valid_from, formalization=form_default,
                    source_quote=(quote or None),
                    gyldighet=assess_gyldighet(session, sid, scope_change=scope),
                    extracted_by=extracted, confirmed_by_user=True, actor="demo-bruker")
            n = len(chosen_ids)
            _flash_rerun("ok", f"Forpliktelse lagret for {n} leverandør{'er' if n > 1 else ''}.")
        except RegistryError as exc:
            st.error(str(exc))


def render_commitment_card(session, c, *, key_prefix: str) -> None:
    """P5 — one forpliktelse with view + edit (popover) + delete. Works for every source type."""
    if c.source_type.value == "EMAIL":
        render_email_commitment(c)
    else:
        status = getattr(c, "gyldighet", None) or "KREVER_FORMALISERING"
        with st.container(border=True):
            val = nok(c.value) if c.value is not None else "—"
            unit_txt = f" {escape(c.unit)}" if c.unit else ""
            src_label = _SOURCE_LABEL.get(c.source_type.value, c.source_type.value)
            st.markdown(
                f"**{escape(c.item_ref or '—')} · {escape(_COND_LABEL.get(c.condition_type.value, c.condition_type.value))} "
                f"= {escape(val)}{unit_txt}**  \n"
                f"<span style='font-size:12px;color:#6B7280'>{escape(src_label)}: "
                f"{escape(c.source_ref)} · gjelder fra {escape(dato(c.valid_from))}</span>",
                unsafe_allow_html=True)
            quote = getattr(c, "source_quote", None)
            if quote:
                st.markdown(
                    f'<div style="font-style:italic;color:#5A5140;background:#FFFDF6;'
                    f'border-left:2px solid {GOLD};padding:6px 10px;font-size:13px">'
                    f'«{escape(quote)}»</div>', unsafe_allow_html=True)
            st.markdown(f"Gyldighetsvurdering: {gyldighet_badge_html(status)}",
                        unsafe_allow_html=True)
            gyldighet_disclaimer()

    a1, a2 = st.columns([1, 1])
    with a1.popover("✎ Rediger"):
        _render_edit_form(session, c, key_prefix=f"{key_prefix}_edit_{c.id}")
    if a2.button("🗑 Slett", key=f"{key_prefix}_del_{c.id}"):
        soft_delete_commitment(session, c.id, actor="demo-bruker")
        _flash_rerun("ok", "Forpliktelse slettet (mykt — sporet beholdes).")


def _render_edit_form(session, c, *, key_prefix: str) -> None:
    kp = key_prefix
    cond_default = c.condition_type.value if c.condition_type.value in _COND_ORDER else "PRICE"
    e1, e2 = st.columns(2)
    item = e1.text_input("Artikkel", value=c.item_ref or "", key=f"{kp}_item")
    cond_name = e2.selectbox("Betingelse", _COND_ORDER, format_func=_COND_LABEL.get,
                             index=_COND_ORDER.index(cond_default), key=f"{kp}_cond")
    value = st.number_input("Avtalt verdi", min_value=0.0, step=100.0,
                            value=float(c.value) if c.value is not None else 0.0, key=f"{kp}_value")
    kilde = st.text_input("Kilde", value=c.source_ref, key=f"{kp}_kilde")
    if st.button("Lagre endringer", type="primary", key=f"{kp}_save"):
        try:
            update_commitment(
                session, c.id, condition_type=_cond_from_str(cond_name),
                source_ref=kilde, item_ref=(item or None), update_item_ref=True,
                value=(Decimal(str(value)) if value else None), update_value=True,
                actor="demo-bruker")
            _flash_rerun("ok", "Forpliktelse oppdatert.")
        except RegistryError as exc:
            st.error(str(exc))


def render_supplier_forpliktelser(session, suppliers, sup, *, key_prefix: str) -> None:
    """Full A–Z block used on the leverandørkort: list (view/edit/delete) + «＋ Ny forpliktelse»."""
    commitments = list_commitments(session, supplier_id=sup.id)
    if commitments:
        for cm in commitments:
            render_commitment_card(session, cm, key_prefix=key_prefix)
    else:
        st.caption("Ingen registrerte forpliktelser.")
    with st.popover("＋ Ny forpliktelse"):
        render_ny_forpliktelse(session, suppliers, default_supplier_id=sup.id,
                               key_prefix=f"{key_prefix}_ny_{sup.id}")
