from datetime import date
from html import escape

import streamlit as st
from chrome import footer, header
from db import get_session, nok
from sqlmodel import select
from ui_forpliktelser import gyldighet_badge_html, gyldighet_legend, render_email_commitment

from core.extraction.epost import parse_email
from core.models import (
    AuditLog,
    Commitment,
    ConditionType,
    Contract,
    ContractLine,
    Formalization,
    SourceType,
    Supplier,
)
from core.synth.epost_examples import EXAMPLE_EMAILS

st.set_page_config(page_title="Avtaler og forpliktelser", page_icon="📋", layout="wide")
header()
st.title("Avtaler og forpliktelser")
st.caption("Alle avtalte betingelser i ett register — formelle kontrakter OG bekreftede "
           "e-postavtaler. Dette er kontrollgrunnlaget for fakturakontrollen.")

tab_register, tab_epost = st.tabs(["Forpliktelsesregister", "Registrer fra e-post"])

# --- Tab 1: the register (e-postavtaler + kontrakter) --------------------------
with tab_register:
    with get_session() as session:
        email_commitments = session.exec(
            select(Commitment).where(Commitment.source_type == "EMAIL")
        ).all()

        st.subheader("📧 E-postavtaler i kontrollgrunnlaget")
        st.caption("En e-postavtale kontrolleres alltid mot avtalen og regelverket — "
                   "den er aldri et selvstendig bevis.")
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
            st.markdown(f"**{contract.title}**")
            st.markdown(f"**{contract.reference}** · {sup.name} · "
                        f"{contract.valid_from} → {contract.valid_to} · "
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
            st.divider()

# --- Tab 2: register a commitment from an e-mail (human-in-the-loop) -----------
with tab_epost:
    st.caption("KI-uttrekk fra e-post er under utvikling. I demo brukes enkel tekstgjenkjenning "
               "— saksbehandler bekrefter alltid før forpliktelsen inngår i kontroll.")

    with get_session() as session:
        supplier_names = [s.name for s in session.exec(select(Supplier)).all()]

    # E2: load one of three synthetic example e-mails (the three gyldighet outcomes).
    def _load_example():
        ex = next(e for e in EXAMPLE_EMAILS if e["label"] == st.session_state.epost_ex_choice)
        st.session_state.epost_text = ex["body"]
        st.session_state.epost_avsender = ex["avsender"]
        st.session_state.epost_proposed = False

    colx1, colx2 = st.columns([3, 1])
    colx1.selectbox("Eksempelmail (syntetisk)", [e["label"] for e in EXAMPLE_EMAILS],
                    key="epost_ex_choice")
    colx2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    colx2.button("Last inn eksempel", on_click=_load_example)

    text = st.text_area("Lim inn e-postinnhold", key="epost_text", height=150,
                        placeholder="Lim inn teksten fra e-posten her …")
    c1, c2, c3 = st.columns(3)
    leverandor = c1.selectbox("Leverandør", supplier_names, key="epost_lev") if supplier_names else None
    avsender = c2.text_input("Avsender", key="epost_avsender")
    dato = c3.date_input("Dato", value=date(2026, 6, 12), key="epost_dato")

    if st.button("Foreslå forpliktelse", type="primary"):
        st.session_state.epost_proposed = True

    if st.session_state.get("epost_proposed") and text.strip():
        proposal = parse_email(text)

        st.markdown("#### Forslag til forpliktelse")
        st.caption("Forslag fra tekstgjenkjenning — ikke bekreftet. Kontrollér før du legger til.")
        with st.container(border=True):
            st.markdown(
                f"**Leverandør:** {escape(leverandor or '—')}  \n"
                f"**Artikkel (item_ref):** {escape(proposal.item_ref or '—')}  \n"
                f"**Betingelse:** {escape(proposal.condition_type)}  \n"
                f"**Verdi:** {nok(proposal.value) if proposal.value is not None else '—'}  \n"
                f"**Kilde:** e-post {escape(str(dato))} · {escape(avsender or '—')}"
            )
            st.markdown("**Sitat (fra e-posten):**")
            st.markdown(
                f'<div style="font-style:italic;color:#5A5140;background:#FFFDF6;'
                f'border-left:2px solid #B08D2E;padding:6px 10px;font-size:13px">'
                f'«{escape(text.strip())}»</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**Gyldighetsvurdering:** {gyldighet_badge_html(proposal.gyldighet)}",
                        unsafe_allow_html=True)
            st.caption(proposal.gyldighet_reason)

        can_confirm = proposal.gyldighet != "UGYLDIG"
        b1, b2 = st.columns(2)
        if b1.button("Bekreft og legg til", type="primary", disabled=not can_confirm):
            with get_session() as session:
                sup = session.exec(
                    select(Supplier).where(Supplier.name == leverandor)
                ).first()
                contract = session.exec(
                    select(Contract).where(Contract.supplier_id == sup.id)
                ).first()
                cond = (ConditionType[proposal.condition_type]
                        if proposal.condition_type in ConditionType.__members__
                        else ConditionType.PRICE)
                commitment = Commitment(
                    supplier_id=sup.id,
                    contract_id=contract.id if contract else None,
                    source_type=SourceType.EMAIL,
                    source_ref=f"e-post {dato.isoformat()}, {avsender}",
                    source_quote=text.strip()[:500],
                    condition_type=cond,
                    item_ref=proposal.item_ref,
                    value=proposal.value,
                    unit=proposal.unit,
                    valid_from=dato,
                    formalization=Formalization.PENDING_ANNEX,
                    extracted_by="regel:epost-parser-v1",
                    confirmed_by_user=True,
                )
                session.add(commitment)
                session.commit()
                session.refresh(commitment)
                # Real action → append-only audit trail (reads never write; this IS a write).
                session.add(AuditLog(
                    actor="demo-bruker", action="commitment.confirmed_from_email",
                    entity=f"commitment:{commitment.id}",
                    detail=f"forpliktelse bekreftet fra e-post ({avsender or 'ukjent avsender'})",
                ))
                session.commit()
            st.session_state.epost_proposed = False
            st.success("Forpliktelsen er bekreftet og lagt til i kontrollgrunnlaget "
                       "(logget i revisjonssporet).")
        if not can_confirm:
            b1.caption("Kan ikke bekreftes — vesentlig endring kan ikke avtales per e-post.")
        if b2.button("Avvis"):
            st.session_state.epost_proposed = False
            st.info("Forslaget er avvist. Ingenting er lagt til.")

footer()
