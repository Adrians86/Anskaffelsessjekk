import streamlit as st
from sqlmodel import select

from db import get_session, nok
from core.models import Invoice, Supplier
from core.reporting import check_invoice

st.set_page_config(page_title="Styringsinformasjon", page_icon="📊", layout="wide")
st.title("📊 Styringsinformasjon")
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kontrollerte fakturaer", len(invoices))
    c2.metric("Avvik (AVVIK)", counts["AVVIK"])
    c3.metric("Til vurdering", counts["TIL_VURDERING"])
    c4.metric("💰 Verdi funnet totalt", nok(total_verdi))

    st.bar_chart(counts)
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("Hver kontroll er logget i revisjonssporet med regelversjon — "
               "fullt etterprøvbart ved revisjon.")
