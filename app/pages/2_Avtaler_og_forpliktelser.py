import streamlit as st
from sqlmodel import select

from db import get_session, nok
from core.models import Commitment, Contract, ContractLine, Supplier

st.set_page_config(page_title="Avtaler og forpliktelser", page_icon="📋", layout="wide")
st.title("Avtaler og forpliktelser")
st.caption("Alle avtalte betingelser i ett register — formelle kontrakter OG bekreftede "
           "e-postavtaler. Dette er kontrollgrunnlaget for fakturakontrollen.")

_FORM = {"FORMALIZED": "✅ Formalisert", "PENDING_ANNEX": "🟡 Venter på tillegg",
         "INFORMAL": "🟠 Uformell"}

with get_session() as session:
    for contract in session.exec(select(Contract)).all():
        sup = session.get(Supplier, contract.supplier_id)
        st.subheader(f"{contract.title}")
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
            hide_index=True, width="stretch",
        )
        commitments = session.exec(
            select(Commitment).where(Commitment.contract_id == contract.id)
        ).all()
        if commitments:
            st.markdown("**Tilleggsforpliktelser (utenfor kontraktsdokumentet):**")
            for c in commitments:
                st.info(
                    f"**{c.item_ref}**: {c.condition_type.value} = {nok(c.value)} "
                    f"fra {c.valid_from} · Kilde: {c.source_ref} · "
                    f"{_FORM[c.formalization.value]} · "
                    f"{'Bekreftet av saksbehandler' if c.confirmed_by_user else 'IKKE bekreftet — deltar ikke i kontroll'}",
                    icon="📧" if c.source_type.value == "EMAIL" else "📄",
                )
        st.divider()

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Syntetiske data")
