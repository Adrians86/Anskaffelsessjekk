"""Shared UI for kontrakter (avtaler) + prisliste — used by Avtaler-siden and Leverandørkort.

UI-only helper (app/ layer). CRUD/persistence lives in core/registry/kontrakt; this module only
renders forms/tables and calls those functions. Every dynamic value in unsafe_allow_html is
html.escape()-d (hard rule #11).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from html import escape

import streamlit as st
from db import dato, nok
from sqlmodel import select

from core.models import (
    CHANGE_CLAUSES,
    CONTRACT_REGIMES,
    CONTRACT_STATUSES,
    ContractType,
    Invoice,
)
from core.registry import (
    RegistryError,
    _clause_label,
    add_line,
    create_contract,
    delete_line,
    list_lines,
    soft_delete_contract,
    update_contract,
    update_line,
)

_TYPE_LABEL = {ContractType.RAMMEAVTALE: "Rammeavtale", ContractType.ENKELTKJOP: "Enkeltkjøp"}
_TYPE_OPTIONS = [ContractType.RAMMEAVTALE, ContractType.ENKELTKJOP]
_STATUS_COLOR = {"aktiv": "#2E7D32", "utløpt": "#6B7280", "utkast": "#B58900"}


# --- flash (toast survives the rerun after a write) ---------------------------
def kontrakt_flash_and_rerun(kind: str, msg: str) -> None:
    st.cache_data.clear()
    st.session_state["kontrakt_flash"] = (kind, msg)
    st.rerun()


def show_kontrakt_flash() -> None:
    """Emit a pending kontrakt flash. Call once near the top of any page using these helpers."""
    fl = st.session_state.pop("kontrakt_flash", None)
    if fl:
        if fl[0] == "ok":
            st.toast(fl[1], icon="✅")
        else:
            st.error(fl[1])


def status_badge(status: str) -> str:
    color = _STATUS_COLOR.get(status, "#6B7280")
    return (f'<span style="background:{color}1A;color:{color};font-size:11px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px">{escape(status)}</span>')


def type_label(contract_type) -> str:
    return _TYPE_LABEL.get(contract_type, str(contract_type))


# --- create ------------------------------------------------------------------
def render_ny_avtale_form(session, suppliers, *, default_supplier_id: int | None = None,
                          key_prefix: str = "") -> None:
    """Render the «Ny avtale» form (U3 pattern). suppliers = list of Supplier."""
    if not suppliers:
        st.caption("Registrer en leverandør først.")
        return
    names = {s.id: s.name for s in suppliers}
    ids = list(names)
    default_idx = ids.index(default_supplier_id) if default_supplier_id in ids else 0
    with st.form(f"ny_avtale_{key_prefix}", clear_on_submit=True):
        sup_id = st.selectbox("Leverandør", ids, index=default_idx,
                              format_func=lambda i: names[i],
                              disabled=default_supplier_id is not None)
        c1, c2 = st.columns(2)
        title = c1.text_input("Tittel *")
        ref = c2.text_input("Avtalenr *")
        c3, c4 = st.columns(2)
        ctype = c3.selectbox("Type", _TYPE_OPTIONS, format_func=type_label)
        regime = c4.selectbox("Regime", CONTRACT_REGIMES)
        c5, c6 = st.columns(2)
        vfrom = c5.date_input("Periode fra", value=date(2026, 1, 1))
        vto = c6.date_input("Periode til", value=date(2027, 12, 31))
        c7, c8 = st.columns(2)
        ramme = c7.number_input("Ramme (NOK)", min_value=0.0, step=10000.0, value=0.0)
        clause = c8.selectbox("Endringsklausul", CHANGE_CLAUSES, format_func=_clause_label)
        saved = st.form_submit_button("Lagre avtale", type="primary")
    if saved:
        try:
            k = create_contract(
                session, supplier_id=sup_id, title=title, reference=ref,
                contract_type=ctype, regime=regime, valid_from=vfrom, valid_to=vto,
                total_value=Decimal(str(ramme)) if ramme else None,
                change_clause=clause, actor="demo-bruker",
            )
            kontrakt_flash_and_rerun("ok", f"Avtale «{k.title}» opprettet.")
        except RegistryError as exc:
            st.error(str(exc))


# --- price list (M2) ----------------------------------------------------------
def render_prisliste(session, contract) -> None:
    """Price list (kontraktslinjer) — the verification basis. Full add/edit/delete."""
    st.markdown("**Prisliste** — grunnlaget fakturaer kontrolleres mot")
    lines = list_lines(session, contract.id)
    if lines:
        header = st.columns([1.4, 2.6, 1, 1.4, 1.2, 0.8])
        for col, h in zip(header, ["Artikkelnr", "Beskrivelse", "Enhet", "Pris", "Maks", ""],
                          strict=True):
            col.markdown(f"<span style='font-size:11px;color:#5A6673;text-transform:uppercase'>"
                         f"{escape(h)}</span>", unsafe_allow_html=True)
        for ln in lines:
            c = st.columns([1.4, 2.6, 1, 1.4, 1.2, 0.8])
            c[0].text(ln.item_ref)
            c[1].text(ln.description or "—")
            c[2].text(ln.unit or "—")
            c[3].markdown(f"<span style='font-variant-numeric:tabular-nums'>"
                          f"{escape(nok(ln.unit_price) if ln.currency == 'NOK' else f'{ln.unit_price} {ln.currency}')}"
                          f"</span>", unsafe_allow_html=True)
            c[4].text(str(ln.max_quantity) if ln.max_quantity is not None else "—")
            with c[5].popover("✎"):
                with st.form(f"edit_line_{ln.id}"):
                    e1, e2 = st.columns(2)
                    l_ref = e1.text_input("Artikkelnr", value=ln.item_ref)
                    l_unit = e2.text_input("Enhet", value=ln.unit or "")
                    l_desc = st.text_input("Beskrivelse", value=ln.description or "")
                    e3, e4, e5 = st.columns(3)
                    l_price = e3.number_input("Pris", min_value=0.0, step=100.0,
                                              value=float(ln.unit_price), key=f"lp_{ln.id}")
                    l_hasmax = e4.checkbox("Maks mengde", value=ln.max_quantity is not None,
                                           key=f"lm_{ln.id}")
                    l_max = e5.number_input("Maks", min_value=0.0, step=1.0,
                                            value=float(ln.max_quantity or 0), key=f"lmx_{ln.id}")
                    l_cur = st.text_input("Valuta", value=ln.currency or "NOK")
                    ec1, ec2 = st.columns(2)
                    l_upd = ec1.form_submit_button("Lagre linje", type="primary")
                    l_del = ec2.form_submit_button("🗑 Slett")
                if l_upd:
                    try:
                        update_line(session, ln.id, item_ref=l_ref, description=l_desc, unit=l_unit,
                                    unit_price=Decimal(str(l_price)),
                                    max_quantity=Decimal(str(l_max)) if l_hasmax else None,
                                    update_max_quantity=True, currency=l_cur, actor="demo-bruker")
                        kontrakt_flash_and_rerun("ok", f"Prislinje «{l_ref}» er lagret.")
                    except RegistryError as exc:
                        st.error(str(exc))
                if l_del:
                    delete_line(session, ln.id, actor="demo-bruker")
                    kontrakt_flash_and_rerun("ok", f"Prislinje «{ln.item_ref}» er slettet.")
    else:
        st.info("Ingen prislinjer ennå — legg til den første for å kunne kontrollere fakturaer "
                "mot denne avtalen.")

    with st.popover("＋ Legg til linje"):
        with st.form(f"add_line_{contract.id}", clear_on_submit=True):
            a1, a2 = st.columns(2)
            n_ref = a1.text_input("Artikkelnr *")
            n_unit = a2.text_input("Enhet (stk/time/mnd)", value="stk")
            n_desc = st.text_input("Beskrivelse")
            a3, a4, a5 = st.columns(3)
            n_price = a3.number_input("Pris *", min_value=0.0, step=100.0, value=0.0)
            n_hasmax = a4.checkbox("Maks mengde")
            n_max = a5.number_input("Maks", min_value=0.0, step=1.0, value=0.0)
            n_cur = st.text_input("Valuta", value="NOK")
            line_added = st.form_submit_button("Legg til linje", type="primary")
        if line_added:
            try:
                add_line(session, contract.id, item_ref=n_ref, description=n_desc, unit=n_unit,
                         unit_price=Decimal(str(n_price)),
                         max_quantity=Decimal(str(n_max)) if n_hasmax else None,
                         currency=n_cur, actor="demo-bruker")
                kontrakt_flash_and_rerun("ok", f"Prislinje «{n_ref}» er lagt til.")
            except RegistryError as exc:
                st.error(str(exc))


# --- detail view (M1 header / M3 actions + linked invoices) -------------------
def render_kontrakt_header(contract, suppliers_by_id: dict) -> None:
    """Grunndata: title + status + meta + endringsklausul (read-only)."""
    sup_name = suppliers_by_id.get(contract.supplier_id, "—")
    st.markdown(f'### {escape(contract.title)} {status_badge(contract.status)}',
                unsafe_allow_html=True)
    st.caption(
        f"{escape(contract.reference)} · {escape(sup_name)} · {type_label(contract.contract_type)} · "
        f"regime {escape(contract.regime)} · {dato(contract.valid_from)} → {dato(contract.valid_to)} · "
        f"ramme {nok(contract.total_value) if contract.total_value is not None else '—'}"
    )
    st.markdown(
        f'<div style="font-size:13px;color:#5A6673">Endringsklausul: '
        f'<strong>{escape(_clause_label(contract.change_clause))}</strong></div>',
        unsafe_allow_html=True,
    )


def render_linked_invoices(session, contract) -> None:
    """Invoices related to the contract's supplier (read-only — verification comes in F3)."""
    st.markdown("**Koblede fakturaer** (les — verifikasjon kommer i F3)")
    invs = session.exec(
        select(Invoice).where(Invoice.supplier_id == contract.supplier_id)
    ).all()
    if invs:
        for iv in invs:
            st.caption(f"{iv.invoice_number} · {dato(iv.invoice_date)}")
    else:
        st.caption("Ingen fakturaer koblet ennå.")


def render_kontrakt_actions(session, contract) -> None:
    """Rediger avtale (popover, forhåndsutfylt) + Slett avtale (soft-delete, bekreftelse)."""
    ec1, ec2, _ = st.columns([1, 1, 4])
    with ec1.popover("✎ Rediger avtale"):
        with st.form(f"edit_contract_{contract.id}"):
            r1, r2 = st.columns(2)
            t = r1.text_input("Tittel", value=contract.title)
            ref = r2.text_input("Avtalenr", value=contract.reference)
            r3, r4 = st.columns(2)
            ctype = r3.selectbox("Type", _TYPE_OPTIONS, format_func=type_label,
                                 index=_TYPE_OPTIONS.index(contract.contract_type)
                                 if contract.contract_type in _TYPE_OPTIONS else 0)
            regime = r4.selectbox("Regime", CONTRACT_REGIMES,
                                  index=CONTRACT_REGIMES.index(contract.regime)
                                  if contract.regime in CONTRACT_REGIMES else 0)
            r5, r6 = st.columns(2)
            vfrom = r5.date_input("Periode fra", value=contract.valid_from)
            vto = r6.date_input("Periode til", value=contract.valid_to or contract.valid_from)
            r7, r8 = st.columns(2)
            ramme = r7.number_input("Ramme (NOK)", min_value=0.0, step=10000.0,
                                    value=float(contract.total_value or 0))
            clause = r8.selectbox("Endringsklausul", CHANGE_CLAUSES, format_func=_clause_label,
                                  index=CHANGE_CLAUSES.index(contract.change_clause)
                                  if contract.change_clause in CHANGE_CLAUSES else 0)
            status = st.selectbox("Status", CONTRACT_STATUSES,
                                  index=CONTRACT_STATUSES.index(contract.status)
                                  if contract.status in CONTRACT_STATUSES else 0)
            saved = st.form_submit_button("Lagre avtale", type="primary")
        if saved:
            try:
                update_contract(session, contract.id, title=t, reference=ref, contract_type=ctype,
                                 regime=regime, valid_from=vfrom, valid_to=vto,
                                 update_valid_to=True,
                                 total_value=Decimal(str(ramme)) if ramme else None,
                                 update_total_value=True, change_clause=clause, status=status,
                                 actor="demo-bruker")
                kontrakt_flash_and_rerun("ok", f"Avtale «{t}» er lagret.")
            except RegistryError as exc:
                st.error(str(exc))
    with ec2.popover("🗑 Slett avtale"):
        st.caption("Myk sletting: avtalen skjules, men raden og prislisten beholdes (spor).")
        st.warning("Koblede fakturaer beholder sin historikk. Verifikasjon mot denne avtalen "
                   "(kommer i F3) vil ikke lenger bruke den.")
        confirm = st.checkbox("Jeg bekrefter sletting", key=f"cdel_{contract.id}")
        if st.button("Slett avtale", type="primary", disabled=not confirm,
                     key=f"cdelbtn_{contract.id}"):
            soft_delete_contract(session, contract.id, actor="demo-bruker")
            kontrakt_flash_and_rerun("ok", f"Avtale «{contract.reference}» er slettet (mykt).")
