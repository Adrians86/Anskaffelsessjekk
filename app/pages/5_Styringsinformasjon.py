from html import escape

import altair as alt
import pandas as pd
import streamlit as st
from chrome import footer, header
from db import get_session, money, nok
from sqlmodel import select

from core.matching.currency import is_foreign
from core.models import Invoice, Supplier
from core.reporting import evaluate_invoice

st.set_page_config(page_title="Styringsinformasjon", page_icon="📊", layout="wide")
header()
st.title("Styringsinformasjon")
st.caption("Kontrollstatus for hele fakturaporteføljen — tall til controlling, "
           "internkontroll og ledelse. Gevinstrealisering: verdi funnet.")

@st.cache_data
def dashboard_data():
    """Portfolio aggregation (cached, read-only). evaluate_invoice never writes."""
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        rows, findings_rows, total_verdi = [], [], 0.0
        counts = {"SAMSVAR": 0, "TIL_VURDERING": 0, "AVVIK": 0}
        supplier_agg: dict[str, dict] = {}
        n_foreign = 0

        for inv in invoices:
            r = evaluate_invoice(session, inv)
            counts[r.verdict.value] += 1
            total_verdi += float(r.verdi_funnet)  # foreign invoices contribute 0 (no NOK deviation)
            if is_foreign(inv):
                n_foreign += 1
            sup = session.get(Supplier, inv.supplier_id)

            agg = supplier_agg.setdefault(sup.name, {"verdi": 0.0, "funn": 0, "fakturaer": 0})
            agg["verdi"] += float(r.verdi_funnet)
            agg["funn"] += len(r.findings)
            agg["fakturaer"] += 1

            rows.append({"Faktura": inv.invoice_number, "Leverandør": sup.name,
                         "Beløp": money(inv.total_ex_vat, inv.currency),
                         "Vurdering": r.verdict.value,
                         "Verdi funnet": nok(r.verdi_funnet) if r.verdi_funnet else "—",
                         "Antall funn": len(r.findings)})
            for f in r.findings:
                findings_rows.append({
                    "invoice_number": inv.invoice_number,
                    "supplier": sup.name,
                    "code": f.code.value,
                    "severity": f.severity.value,
                    "message": f.message,
                    "expected": f.expected or "",
                    "actual": f.actual or "",
                    "deviation_amount": float(f.deviation_amount),
                    "citation": f.citation,
                })
        return {"rows": rows, "findings_rows": findings_rows, "counts": counts,
                "total_verdi": total_verdi, "supplier_agg": supplier_agg,
                "n_invoices": len(invoices), "n_foreign": n_foreign}


data = dashboard_data()
rows = data["rows"]
findings_rows = data["findings_rows"]
n_foreign = data["n_foreign"]
counts = data["counts"]
total_verdi = data["total_verdi"]
supplier_agg = data["supplier_agg"]
n_invoices = data["n_invoices"]

# --- Hero: Verdi funnet (gold, largest emphasis) ------------------------------
avg_deviation = total_verdi / n_invoices if n_invoices else 0
col_hero, col_avg = st.columns([2, 1])
with col_hero:
    st.markdown(
        '<div style="border:1px solid #E4D9B8;background:#FBF7EC;border-radius:8px;'
        'padding:16px 20px">'
        '<div style="font-size:13px;color:#8A7A3A;font-weight:600;text-transform:uppercase;'
        'letter-spacing:.5px">Verdi funnet i demoporteføljen</div>'
        f'<div style="font-size:40px;font-weight:700;color:#B58900;line-height:1.1">'
        f'{escape(nok(total_verdi))}</div>'
        '<div style="font-size:12px;color:#8A94A0">Sum av alle avvik funnet av kontrollen — '
        'gevinstpotensial ved oppfølging.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with col_avg:
    with st.container(border=True):
        st.metric("Gjennomsnittlig avvik per kontrollert faktura", nok(avg_deviation))

if total_verdi == 0:
    st.warning("Verdi funnet er 0 på demodata — kontrollér at demoscenariene er lastet.")

if n_foreign:
    st.info(f"{n_foreign} faktura(er) i utenlandsk valuta inngår **ikke** i verdi funnet (NOK) — "
            "krever manuell vurdering av kurs. Se Fakturakontroll for detaljer.")

if findings_rows:
    df_findings = pd.DataFrame(findings_rows)
    st.download_button(
        "Eksporter funn (CSV)",
        data=df_findings.to_csv(index=False),
        file_name="Anskaffelsessjekk_funn.csv",
        mime="text/csv",
    )

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
for col, label, key in [
    (col1, "Kontrollerte fakturaer", None),
    (col2, "Avvik", "AVVIK"),
    (col3, "Til vurdering", "TIL_VURDERING"),
    (col4, "Samsvar", "SAMSVAR"),
]:
    with col:
        with st.container(border=True):
            st.metric(label, n_invoices if key is None else counts[key])

st.markdown("---")

chart_data = pd.DataFrame([
    {"Vurdering": "SAMSVAR", "Antall": counts["SAMSVAR"]},
    {"Vurdering": "TIL VURDERING", "Antall": counts["TIL_VURDERING"]},
    {"Vurdering": "AVVIK", "Antall": counts["AVVIK"]},
])
color_scale = alt.Scale(domain=["SAMSVAR", "TIL VURDERING", "AVVIK"],
                        range=["#2E7D32", "#B58900", "#C62828"])
chart = alt.Chart(chart_data).mark_bar().encode(
    y=alt.Y("Vurdering:N", sort=["SAMSVAR", "TIL VURDERING", "AVVIK"]),
    x=alt.X("Antall:Q", title="Antall fakturaer"),
    color=alt.Color("Vurdering:N", scale=color_scale, legend=None),
).properties(height=200)
st.altair_chart(chart, use_container_width=True)

st.markdown("---")

# --- Per-supplier deviation table ---------------------------------------------
st.subheader("Avvik per leverandør")
sup_rows = [
    {"Leverandør": name, "Fakturaer": a["fakturaer"], "Funn": a["funn"],
     "_verdi": a["verdi"], "Verdi funnet": nok(a["verdi"])}
    for name, a in supplier_agg.items()
]
sup_rows.sort(key=lambda r: r["_verdi"], reverse=True)
st.dataframe(
    pd.DataFrame(sup_rows)[["Leverandør", "Fakturaer", "Funn", "Verdi funnet"]],
    hide_index=True, use_container_width=True,
)

st.markdown("---")
st.subheader("Fakturaer")
st.dataframe(rows, hide_index=True, use_container_width=True)
st.caption("Hver kontroll er logget i revisjonssporet med regelversjon — "
           "fullt etterprøvbart ved revisjon.")

footer()
