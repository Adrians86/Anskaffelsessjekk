import streamlit as st
from chrome import footer, header, page_header
from db import dato, get_session, nok
from sqlmodel import select
from ui_forpliktelser import (
    gyldighet_legend,
    render_email_commitment,
)
from ui_kontrakt import (
    render_kontrakt_actions,
    render_kontrakt_header,
    render_linked_invoices,
    render_ny_avtale_form,
    render_prisliste,
    show_kontrakt_flash,
    type_label,
)

from core.models import (
    Commitment,
    Contract,
    ContractLine,
    Supplier,
)
from core.registry import get_contract, list_contracts, list_suppliers

st.set_page_config(page_title="Avtaler og forpliktelser", page_icon="📋", layout="wide")
header()
page_header(
    "Forpliktelser", "Avtaler og forpliktelser",
    "Alle avtalte betingelser i ett register — formelle kontrakter OG bekreftede "
    "e-postavtaler. Dette er kontrollgrunnlaget for fakturakontrollen.",
)

show_kontrakt_flash()

tab_avtaler, tab_register = st.tabs(["Avtaler", "Forpliktelsesregister"])

# --- Tab: Avtaler (kontrakter + prisliste) — Funksjon 2 ------------------------
with tab_avtaler:
    csearch_col, cnew_col = st.columns([3, 1])
    csearch = csearch_col.text_input(
        "Søk avtale", placeholder="🔎 Søk tittel / avtalenr / leverandør",
        label_visibility="collapsed")
    with get_session() as session:
        suppliers = list_suppliers(session)
        sup_by_id = {s.id: s.name for s in suppliers}
        with cnew_col.popover("＋ Ny avtale", use_container_width=True):
            render_ny_avtale_form(session, suppliers, key_prefix="avt")

        contracts = list_contracts(session)
        if csearch:
            q = csearch.strip().lower()
            contracts = [c for c in contracts
                         if q in c.title.lower() or q in c.reference.lower()
                         or q in sup_by_id.get(c.supplier_id, "").lower()]

        if not contracts:
            st.info("Ingen treff for søket." if csearch
                    else "Ingen avtaler ennå — opprett den første med «＋ Ny avtale».")
        else:
            st.dataframe(
                [{"Tittel": c.title, "Avtalenr": c.reference,
                  "Leverandør": sup_by_id.get(c.supplier_id, "—"),
                  "Type": type_label(c.contract_type),
                  "Periode": f"{dato(c.valid_from)} → {dato(c.valid_to)}",
                  "Ramme": nok(c.total_value) if c.total_value is not None else "—",
                  "Status": c.status} for c in contracts],
                hide_index=True, use_container_width=True,
            )
            st.divider()
            labels = {c.id: f"{c.reference} — {c.title}" for c in contracts}
            preselect = st.session_state.pop("preselect_contract", None)
            default_idx = list(labels).index(preselect) if preselect in labels else 0
            chosen_id = st.selectbox("Åpne avtale", list(labels), format_func=labels.get,
                                     index=default_idx)
            contract = get_contract(session, chosen_id)
            if contract:
                render_kontrakt_header(contract, sup_by_id)
                render_kontrakt_actions(session, contract)
                st.divider()
                render_prisliste(session, contract)
                st.divider()
                render_linked_invoices(session, contract)

# --- Tab 1: the register (e-postavtaler + kontrakter) --------------------------
with tab_register:
    with get_session() as session:
        email_commitments = session.exec(
            select(Commitment).where(Commitment.source_type == "EMAIL")
        ).all()

        st.subheader("📧 E-postavtaler i kontrollgrunnlaget")
        st.caption("En e-postavtale kontrolleres alltid mot avtalen og regelverket — "
                   "den er aldri et selvstendig bevis. Nye forpliktelser legges til på "
                   "leverandørkortet (Leverandører → fanen «Avtaler, forpliktelser og fakturaer»).")
        st.markdown("**Gyldighetsvurdering — mulige utfall:**")
        gyldighet_legend()

        if email_commitments:
            for c in email_commitments:
                sup = session.get(Supplier, c.supplier_id)
                st.markdown(f"*{sup.name}*")
                render_email_commitment(c)
        else:
            st.info("Ingen e-postavtaler i kontrollgrunnlaget ennå.")

        st.divider()

        st.subheader("Kontrakter")
        for contract in session.exec(select(Contract)).all():
            sup = session.get(Supplier, contract.supplier_id)
            with st.container(border=True):
                st.markdown(f"**{contract.title}**")
                st.caption(f"{contract.reference} · {sup.name} · "
                           f"{dato(contract.valid_from)} → {dato(contract.valid_to)} · "
                           f"ramme {nok(contract.total_value)}")
                lines = session.exec(
                    select(ContractLine).where(ContractLine.contract_id == contract.id)
                ).all()
                st.dataframe(
                    [{"Artikkel": line.item_ref, "Beskrivelse": line.description,
                      "Avtalt pris": nok(line.unit_price), "Enhet": line.unit,
                      "Maks mengde": str(line.max_quantity) if line.max_quantity else "—"}
                     for line in lines],
                    hide_index=True, use_container_width=True,
                )

footer()
