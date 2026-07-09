import streamlit as st
from sqlmodel import select
import pandas as pd
import altair as alt

from db import get_session, nok
from core.models import Invoice, Supplier
from core.reporting import check_invoice

st.set_page_config(page_title="Styringsinformasjon", page_icon="📊", layout="wide")
st.title("Styringsinformasjon")
st.caption("Kontrollstatus for hele fakturaporteføljen — tall til controlling, "
           "internkontroll og ledelse. Gevinstrealisering: verdi funnet.")

with get_session() as session:
    invoices = session.exec(select(Invoice)).all()
    rows, total_verdi = [], 0
    counts = {"SAMSVAR": 0, "TIL_VURDERING": 0, "AVVIK": 0}
    for inv in invoices:
        r = check_invoice(session, inv, actor="dashboard")
        counts[r.verdict.value] += 1
        total_verdi += float(r.verdi_funnet)
        sup = session.get(Supplier, inv.supplier_id)
        rows.append({"Faktura": inv.invoice_number, "Leverandør": sup.name,
                     "Beløp": nok(inv.total_ex_vat), "Vurdering": r.verdict.value,
                     "Verdi funnet": nok(r.verdi_funnet) if r.verdi_funnet else "—",
                     "Antall funn": len(r.findings)})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.metric("Kontrollerte fakturaer", len(invoices))
    with col2:
        with st.container(border=True):
            st.metric("Avvik", counts["AVVIK"])
    with col3:
        with st.container(border=True):
            st.metric("Til vurdering", counts["TIL_VURDERING"])
    with col4:
        with st.container(border=True):
            st.metric("Verdi funnet totalt", nok(total_verdi))

    st.markdown("---")

    chart_data = pd.DataFrame([
        {"Vurdering": "SAMSVAR", "Antall": counts["SAMSVAR"]},
        {"Vurdering": "TIL VURDERING", "Antall": counts["TIL_VURDERING"]},
        {"Vurdering": "AVVIK", "Antall": counts["AVVIK"]}
    ])

    color_scale = alt.Scale(domain=["SAMSVAR", "TIL VURDERING", "AVVIK"],
                            range=["#2ECC71", "#F39C12", "#E74C3C"])

    chart = alt.Chart(chart_data).mark_bar().encode(
        y=alt.Y("Vurdering:N", sort=["SAMSVAR", "TIL VURDERING", "AVVIK"]),
        x=alt.X("Antall:Q", title="Antall fakturaer"),
        color=alt.Color("Vurdering:N", scale=color_scale, legend=None)
    ).properties(height=200)

    st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
    st.subheader("Fakturaer")
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("Hver kontroll er logget i revisjonssporet med regelversjon — "
               "fullt etterprøvbart ved revisjon.")

st.markdown("---")
st.caption("🔒 Anskaffelsessjekk · AS North Advisory · Syntetiske data")
