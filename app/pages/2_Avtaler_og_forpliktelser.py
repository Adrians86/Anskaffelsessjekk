import streamlit as st
from chrome import footer, header
from db import get_session, nok
from sqlmodel import select
from ui_forpliktelser import gyldighet_legend, render_email_commitment

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
            [{"Artikkel": line.item_ref, "Beskrivelse": line.description,
              "Avtalt pris": nok(line.unit_price), "Enhet": line.unit,
              "Maks mengde": str(line.max_quantity) if line.max_quantity else "—"}
             for line in lines],
            hide_index=True, use_container_width=True,
        )
        st.divider()

footer()
