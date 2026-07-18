import streamlit as st
from sqlmodel import select
import pandas as pd

from db import get_session, nok
from chrome import header, footer
from core.models import Contract, Invoice, Supplier
from core.reporting import check_invoice

st.set_page_config(page_title="Leverandører", page_icon="🏢", layout="wide")
header()
st.title("Leverandører")
st.caption("Hvilke leverandører genererer flest avvik — ta det opp med kilden, "
           "ikke bare symptomene. (First Time Right)")


@st.cache_data
def supplier_stats():
    rows = []
    with get_session() as session:
        suppliers = session.exec(select(Supplier)).all()
        for sup in suppliers:
            contracts = session.exec(
                select(Contract).where(Contract.supplier_id == sup.id)
            ).all()
            invoices = session.exec(
                select(Invoice).where(Invoice.supplier_id == sup.id)
            ).all()

            n_findings = 0
            verdi = 0.0
            invoices_with_findings = 0
            for inv in invoices:
                result = check_invoice(session, inv, actor="leverandoroversikt")
                if result.findings:
                    invoices_with_findings += 1
                n_findings += len(result.findings)
                verdi += float(result.verdi_funnet)

            andel = (invoices_with_findings / len(invoices) * 100) if invoices else 0.0
            rows.append({
                "Navn": sup.name,
                "Org.nr": sup.org_number,
                "Avtaler": len(contracts),
                "Fakturaer": len(invoices),
                "Funn": n_findings,
                "_verdi": verdi,
                "Verdi funnet": nok(verdi),
                "Andel m/ funn": f"{andel:.0f} %",
            })
    rows.sort(key=lambda r: r["_verdi"], reverse=True)
    return rows


rows = supplier_stats()

if not rows:
    st.info("Ingen leverandører registrert.")
else:
    df = pd.DataFrame(rows)[
        ["Navn", "Org.nr", "Avtaler", "Fakturaer", "Funn", "Verdi funnet", "Andel m/ funn"]
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)

    total_verdi = sum(r["_verdi"] for r in rows)
    st.caption(f"Total verdi funnet på tvers av leverandører: **{nok(total_verdi)}**")

footer()
