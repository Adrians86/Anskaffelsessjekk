import streamlit as st
from sqlmodel import select

from db import get_session, nok
from chrome import header, footer
from ui_forpliktelser import render_email_commitment, gyldighet_legend
from core.models import Commitment, Contract, ContractLine, Supplier

st.set_page_config(page_title="Avtaler og forpliktelser", page_icon="📋", layout="wide")
header()
st.title("Avtaler og forpliktelser")
st.caption("Alle avtalte betingelser i ett register — formelle kontrakter OG bekreftede "
           "e-postavtaler. Dette er kontrollgrunnlaget for fakturakontrollen.")

with get_session() as session:
    # --- E-postavtaler i kontrollgrunnlaget (the differentiator) ---------------
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

    # --- Kontrakter og linjer (unchanged) -------------------------------------
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
            [{"Artikkel": l.item_ref, "Beskrivelse": l.description,
              "Avtalt pris": nok(l.unit_price), "Enhet": l.unit,
              "Maks mengde": str(l.max_quantity) if l.max_quantity else "—"}
             for l in lines],
            hide_index=True, use_container_width=True,
        )
        st.divider()

footer()
