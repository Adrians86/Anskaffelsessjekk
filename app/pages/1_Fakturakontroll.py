from html import escape

import streamlit as st
from chrome import footer, header, page_header
from db import dato, get_session, money, nok
from sqlmodel import select
from texts import RECOMMENDED_ACTIONS
from ui_faktura import (
    faktura_flash,
    linkage_banner,
    render_batch_results,
    render_decision,
    render_ocr_confirmation,
    render_single_result,
)

from core.extraction import (
    build_sample_ehf,
    build_sample_pdf,
    image_ocr_available,
    parse_ehf,
    parse_scanned_invoice,
    read_document,
)
from core.extraction.csv_faktura import CSVParseError, parse_csv
from core.extraction.ehf import EHFParseError
from core.extraction.ocr import OcrReadError, OcrUnavailable
from core.matching.currency import is_foreign
from core.matching.findings import Severity
from core.models import Invoice, InvoiceSource, Order, Supplier
from core.registry import intake_invoice
from core.reporting import build_protokoll, check_invoice
from core.rules.engine import Facts, ReglementEngine, RulesEngine

st.set_page_config(page_title="Fakturakontroll", page_icon="🧾", layout="wide")
header()
page_header(
    "Kontroll", "Fakturakontroll",
    "Kontroller en faktura mot bestilling, mottak og alle registrerte forpliktelser "
    "— i to retninger: leverandørens pris og egen prosedyre.",
)

_SEV_ICON = {Severity.DEVIATION: "🔴", Severity.WARN: "🟡", Severity.INFO: "ℹ️"}

# Source chips — the three control sources, visually distinguishable.
_CHIP_FORPLIKTELSER = "#B08D2E"   # gold
_CHIP_REGELVERK = "#2E7D32"       # green
_CHIP_INTERNT = "#1F3A5F"         # navy


def _source_chip(label: str, color: str) -> str:
    return (f'<span style="border:1px solid {color};color:{color};font-size:10px;'
            f'font-weight:600;padding:1px 8px;border-radius:10px;margin-left:6px;'
            f'white-space:nowrap">{label}</span>')


def render_audit_card(session, inv) -> None:
    """Render verdict block + finding cards + protokoll/booking CTAs for one invoice."""
    result = check_invoice(session, inv, actor="demo-bruker")
    order = session.get(Order, inv.order_id) if inv.order_id else None

    # Foreign-currency banner: amounts shown in the invoice currency, never converted to NOK.
    if is_foreign(inv):
        st.markdown(
            f'{_source_chip(inv.currency.upper(), _CHIP_INTERNT)} '
            f'<strong>Faktura i utenlandsk valuta ({escape(inv.currency.upper())})</strong> — '
            f'fakturabeløp {escape(money(inv.total_ex_vat, inv.currency))}. '
            'Beløp sammenlignes ikke automatisk mot NOK-priser.',
            unsafe_allow_html=True,
        )

    # U4 — verdict big on top: one clear editorial block, colored by outcome.
    _V = {
        "SAMSVAR": ("SAMSVAR", "#2E7D32", "#EAF4EC"),
        "TIL_VURDERING": ("TIL VURDERING", "#B58900", "#FBF7EC"),
        "AVVIK": ("AVVIK", "#C62828", "#FBEAEA"),
    }
    vlabel, vcolor, vbg = _V[result.verdict.value]
    if result.verdict.value == "SAMSVAR":
        vsub = "Fakturaen samsvarer med avtalt grunnlag."
    elif result.verdict.value == "TIL_VURDERING":
        vsub = (f"{nok(result.verdi_funnet)} til vurdering."
                if result.verdi_funnet else "Krever manuell vurdering.")
    else:
        vsub = f"{nok(result.verdi_funnet)} over avtalt."
    st.markdown(
        f'<div style="background:{vbg};border-left:6px solid {vcolor};border-radius:8px;'
        f'padding:14px 18px;margin:6px 0">'
        f"<div style=\"font-family:Georgia,'Times New Roman',serif;font-size:26px;"
        f'font-weight:700;color:{vcolor};line-height:1.1">{vlabel}</div>'
        f'<div style="font-size:13px;color:#5A6673;margin-top:2px">{escape(vsub)}</div></div>',
        unsafe_allow_html=True,
    )

    if not result.findings:
        st.success("Ingen funn. Fakturaen samsvarer med bestilling, mottak og "
                   "alle registrerte forpliktelser.")

    # U4 — findings as readable rows; the "why" (grunnlag + anbefalt handling) in an expander.
    for f in result.findings:
        is_email = f.code.value == "INFORMAL_BASIS"
        anbefalt = RECOMMENDED_ACTIONS.get(f.code.value, "Vurder med saksbehandler")
        if is_email:
            st.markdown(
                '<div style="border-left:4px solid #B58900;background:#FBF7EC;'
                'padding:10px 14px;border-radius:4px;margin:6px 0">'
                f'<strong>📧 E-postavtale:</strong> {escape(f.message)}'
                f'{_source_chip("Forpliktelser", _CHIP_FORPLIKTELSER)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="padding:6px 0">{_SEV_ICON[f.severity]} '
                f'<strong>{escape(f.message)}</strong>'
                f'{_source_chip("Forpliktelser", _CHIP_FORPLIKTELSER)}</div>',
                unsafe_allow_html=True,
            )
        with st.expander("Hvorfor — grunnlag og anbefalt handling"):
            st.markdown(f"**Grunnlag:** {f.citation}")
            st.markdown(f"**Anbefalt handling:** {anbefalt}")
            if f.expected is not None:
                st.markdown(f"**Avtalt:** {f.expected} · **Fakturert:** {f.actual}")
            if not is_email and f.deviation_amount:
                st.markdown(f"**Avvik:** {nok(f.deviation_amount)}")

    # V3 — Internt reglement: the THIRD source (organization's own rules, data-driven).
    reglement_hits = ReglementEngine().evaluate({
        "invoice_total": inv.total_ex_vat,
        "estimated_value": order.estimated_value if order else inv.total_ex_vat,
        "has_contract": 1 if (order and order.contract_id) else 0,
    })
    for h in reglement_hits:
        with st.container(border=True):
            st.markdown(f"🏛 **{escape(h.message)}**"
                        f"{_source_chip('Internt reglement', _CHIP_INTERNT)}",
                        unsafe_allow_html=True)
            st.markdown(f"**Grunnlag:** {escape(h.citation)}")

    # V2 — Regelverkssjekk: the SECOND direction (own procedure, not the supplier's price).
    st.markdown(f"#### Regelverkssjekk{_source_chip('Regelverk', _CHIP_REGELVERK)}",
                unsafe_allow_html=True)
    st.caption("Egenkontroll: prosedyre og terskel for denne anskaffelsen")
    if order is None:
        st.info("Ingen bestilling/avrop knyttet til fakturaen — terskel- og prosedyrekontroll "
                "krever et avrop å vurdere.")
    else:
        hits = RulesEngine().evaluate(Facts(
            regime=order.regime.value,
            estimated_value=order.estimated_value,
            assessment_date=order.order_date,
        ))
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.markdown(f"**Regime**\n\n{order.regime.value}")
        with c2:
            with st.container(border=True):
                st.markdown(f"**Terskel**\n\nAnslått {nok(order.estimated_value)}")
        with c3:
            with st.container(border=True):
                consequence = hits[0].consequence.replace("_", " ") if hits else "Ingen regel slo til"
                st.markdown(f"**Konsekvens (§)**\n\n{consequence}")
        for h in hits:
            with st.expander(f"Hjemmel — {h.consequence.replace('_', ' ')}"):
                st.markdown(f"**Hjemmel:** {h.citation}")
                if h.citation_url:
                    st.markdown(f"[Les kilden]({h.citation_url})")
                st.caption(f"Regel-ID: {h.rule_id} · Regime: {h.regime}")
    st.caption("Kontroll i to retninger — leverandørens faktura og egen prosedyre.")

    st.markdown("---")

    pdf_bytes = build_protokoll(session, inv)
    col_pdf, col_email = st.columns(2)
    with col_pdf:
        st.download_button(
            label="Last ned protokoll (PDF)",
            data=pdf_bytes,
            file_name=f"Anskaffelsesprotokoll_{inv.invoice_number}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            key=f"pdf_{inv.id}",
        )
    with col_email:
        st.link_button(
            "Book 20-min gjennomgang",
            "mailto:asliwa1986@gmail.com?subject=Anskaffelsessjekk%20gjennomgang",
            use_container_width=True,
        )

    st.caption("Anbefaling — beslutningen tas av saksbehandler. "
               "Kontrollen er logget i revisjonssporet.")


faktura_flash()

_SAMPLE_CSV = (
    "fakturanr;dato;orgnr;artikkelnr;beskrivelse;antall;pris\n"
    "B-1001;2026-07-10;998877665;HYD-1001;Hydraulikkpumpe;2;13000\n"
    "B-1001;2026-07-10;998877665;HYD-2002;Ventil;1;8300\n"
    "B-1002;2026-07-11;987654321;KONS-SENIOR;Seniorkonsulent;12;1600\n"
)
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB — invoices are a few kB; cap abuse/DoS.

tab_check, tab_intake = st.tabs(["Kontroller faktura", "Inntak (EHF / batch)"])

# --- Tab 1: control an existing (demo) invoice ---------------------------------
with tab_check:
    with get_session() as session:
        invoices = session.exec(select(Invoice).order_by(Invoice.invoice_number)).all()
        labels = {}
        for inv in invoices:
            sup = session.get(Supplier, inv.supplier_id)
            labels[inv.id] = (f"{inv.invoice_number} — {sup.name} — "
                              f"{money(inv.total_ex_vat, inv.currency)}")

        preselect_id = st.session_state.get("preselect_invoice")
        default_idx = list(labels.keys()).index(preselect_id) if preselect_id in labels else 0
        chosen = st.selectbox("Velg faktura", options=list(labels),
                              format_func=labels.get, index=default_idx)

        auto_run = preselect_id is not None
        button_clicked = st.button("Kontroller faktura", type="primary") or auto_run

        if button_clicked:
            if "preselect_invoice" in st.session_state:
                del st.session_state.preselect_invoice
            inv = session.get(Invoice, chosen)
            linkage_banner(session, inv)
            render_audit_card(session, inv)
            st.divider()
            render_decision(session, inv)

# --- Tab 2: intake (EHF single / batch CSV / batch EHF; PDF/JPG = Kommer OCR) --
with tab_intake:
    st.markdown("Inntak av fakturaer — enkeltvis (EHF) eller i partia (CSV / flere filer). "
                "Hver faktura knyttes til leverandør på org.nr og kontrolleres mot avtalt prisliste.")
    mode = st.radio("Kilde", ["EHF (én fil)", "Batch (CSV)", "Batch (flere EHF)", "PDF / JPG"],
                    horizontal=True)

    if mode == "EHF (én fil)":
        st.download_button("Last ned eksempel-EHF", data=build_sample_ehf(),
                           file_name="eksempel-EHF-F-1003.xml", mime="application/xml")
        up = st.file_uploader("EHF-fil (.xml)", type=["xml"], key="ehf_single")
        if up is not None and up.size > _MAX_UPLOAD_BYTES:
            st.error("Filen er for stor (maks 5 MB).")
            up = None
        if up is not None:
            try:
                parsed = parse_ehf(up.getvalue())
            except EHFParseError as exc:
                st.error(f"Kunne ikke tolke EHF: {exc}")
                parsed = None
            if parsed is not None:
                with get_session() as session:
                    inv = intake_invoice(session, parsed, source=InvoiceSource.EHF)
                    st.caption(f"Importert: **{inv.invoice_number}** · {dato(inv.invoice_date)} · "
                               f"{len(parsed.lines)} linje(r).")
                    st.divider()
                    render_single_result(session, inv)

    elif mode == "Batch (CSV)":
        st.download_button("Last ned eksempel-CSV", data=_SAMPLE_CSV,
                           file_name="eksempel-fakturaer.csv", mime="text/csv",
                           help="Syntetisk parti med to fakturaer — last ned, last opp igjen.")
        up = st.file_uploader("CSV-fil (.csv)", type=["csv"], key="csv_batch")
        if up is not None and up.size > _MAX_UPLOAD_BYTES:
            st.error("Filen er for stor (maks 5 MB).")
            up = None
        if up is not None:
            try:
                parsed_list = parse_csv(up.getvalue())
            except CSVParseError as exc:
                st.error(f"Kunne ikke tolke CSV: {exc}")
                parsed_list = None
            if parsed_list:
                with get_session() as session:
                    imported = [intake_invoice(session, p, source=InvoiceSource.MANUAL)
                                for p in parsed_list]
                    st.success(f"{len(imported)} faktura(er) importert fra CSV.")
                    st.divider()
                    render_batch_results(session, imported)

    elif mode == "Batch (flere EHF)":
        ups = st.file_uploader("EHF-filer (.xml)", type=["xml"], accept_multiple_files=True,
                               key="ehf_multi")
        valid = [u for u in (ups or []) if u.size <= _MAX_UPLOAD_BYTES]
        if valid:
            with get_session() as session:
                imported = []
                for u in valid:
                    try:
                        imported.append(intake_invoice(session, parse_ehf(u.getvalue()),
                                                        source=InvoiceSource.EHF))
                    except EHFParseError as exc:
                        st.error(f"{u.name}: {exc}")
                if imported:
                    st.success(f"{len(imported)} faktura(er) importert.")
                    st.divider()
                    render_batch_results(session, imported)

    else:  # PDF / JPG — OCR (Funksjon 3.5): les → bekreft → DERETTER kontroll
        st.caption("Et skannet dokument er en lesehjelp, ikke et kontrollgrunnlag. Vi viser hva vi "
                   "leste, du retter og bekrefter — først da kontrolleres fakturaen, gjennom "
                   "nøyaktig samme kjede som EHF og CSV.")
        img_ok, img_reason = image_ocr_available()
        if not img_ok:
            st.info(f"PDF med tekstlag leses her og nå. {img_reason}")

        st.download_button("Last ned eksempel-PDF (syntetisk)", data=build_sample_pdf(),
                           file_name="eksempel-faktura-F-2026-77.pdf", mime="application/pdf")
        up = st.file_uploader("PDF / JPG", type=["pdf", "jpg", "jpeg", "png"], key="ocr_upload")
        if up is not None and up.size > _MAX_UPLOAD_BYTES:
            st.error("Filen er for stor (maks 5 MB).")
            up = None

        confirmed_id = st.session_state.get("ocr_confirmed_invoice")
        if confirmed_id is not None:
            # O4 — after confirmation the invoice runs the SAME chain as EHF/CSV.
            with get_session() as session:
                inv = session.get(Invoice, confirmed_id)
                if inv is not None:
                    st.divider()
                    render_single_result(session, inv)
            if st.button("Les et nytt dokument"):
                del st.session_state["ocr_confirmed_invoice"]
                st.rerun()
        elif up is not None:
            try:
                reading = read_document(up.getvalue(), up.name)
            except OcrUnavailable as exc:
                st.warning(str(exc))          # honest degrade — never a guess
                reading = None
            except OcrReadError as exc:
                st.error(str(exc))
                reading = None
            if reading is not None:
                proposal = parse_scanned_invoice(reading)
                with get_session() as session:
                    render_ocr_confirmation(session, proposal)

footer()
