import streamlit as st
from io import StringIO
from sqlmodel import select
import pandas as pd
import altair as alt

from app.db import get_session, nok
from core.models import Invoice, Supplier
from core.reporting import check_invoice

st.set_page_config(page_title="Styringsinformasjon", page_icon="📊", layout="wide")
st.title("Styringsinformasjon")
st.caption("Kontrollstatus for hele fakturaporteføljen — tall til controlling, "
           "internkontroll og ledelse. Gevinstrealisering: verdi funnet.")

with get_session() as session:
    invoices = session.exec(select(Invoice)).all()
    rows, findings_rows, total_verdi = [], [], 0
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
        for f in r.findings:
            findings_rows.append({
                "Faktura": inv.invoice_number,
                "Leverandør": sup.name,
                "Kode": f.code.value,
                "Alvorlighet": f.severity.value,
                "Beskrivelse": f.message,
                "Avtalt": f.expected or "—",
                "Fakturert": f.actual or "—",
                "Avvik": float(f.deviation_amount),
                "Grunnlag": f.citation
            })

    col_hero_left, col_hero_right = st.columns(2)
    with col_hero_left:
        st.metric("Verdi funnet i demoporteføljen", nok(total_verdi), delta=None)
    with col_hero_right:
        avg_deviation = total_verdi / len(invoices) if invoices else 0
        st.metric("Gjennomsnittlich avvik per faktura", nok(avg_deviation), delta=None)

    col_pdf, col_csv = st.columns(2)
    with col_csv:
        if findings_rows:
            csv_buffer = StringIO()
            df_findings = pd.DataFrame(findings_rows)
            csv_data = df_findings.to_csv(index=False)
            st.download_button(
                "Eksporter funn (CSV)",
                data=csv_data,
                file_name="Anskaffelsessjekk_funn.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")

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
            st.metric("Samsvar", counts["SAMSVAR"])

    st.markdown("---")

    chart_data = pd.DataFrame([
        {"Vurdering": "SAMSVAR", "Antall": counts["SAMSVAR"]},
        {"Vurdering": "TIL VURDERING", "Antall": counts["TIL_VURDERING"]},
        {"Vurdering": "AVVIK", "Antall": counts["AVVIK"]}
    ])

    color_scale = alt.Scale(domain=["SAMSVAR", "TIL VURDERING", "AVVIK"],
                            range=["#2E7D32", "#B58900", "#C62828"])

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
