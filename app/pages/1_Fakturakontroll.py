from html import escape

import streamlit as st
from chrome import footer, header
from db import get_session, money, nok
from sqlmodel import select
from texts import RECOMMENDED_ACTIONS

from core.extraction import build_sample_ehf, parse_ehf
from core.extraction.ehf import EHFParseError
from core.matching.currency import is_foreign
from core.matching.findings import Severity
from core.models import Invoice, InvoiceLine, InvoiceSource, Order, Supplier
from core.reporting import build_protokoll, check_invoice
from core.rules.engine import Facts, ReglementEngine, RulesEngine

st.set_page_config(page_title="Fakturakontroll", page_icon="🧾", layout="wide")
header()
st.title("Fakturakontroll")

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

    if result.verdict.value == "SAMSVAR":
        st.success("SAMSVAR — fakturaen samsvarer med avtalt grunnlag")
    elif result.verdict.value == "TIL_VURDERING":
        if result.verdi_funnet:
            st.warning(f"TIL VURDERING — {nok(result.verdi_funnet)}")
        else:
            st.warning("TIL VURDERING — krever manuell vurdering")
    else:
        st.error(f"AVVIK — {nok(result.verdi_funnet)} over avtalt")

    if not result.findings:
        st.success("Ingen funn. Fakturaen samsvarer med bestilling, mottak og "
                   "alle registrerte forpliktelser.")

    for f in result.findings:
        is_email = f.code.value == "INFORMAL_BASIS"
        if is_email:
            # E-mail-based grunnlag: gold left border + explicit prefix.
            st.markdown(
                '<div style="border-left:4px solid #B58900;background:#FBF7EC;'
                'padding:10px 14px;border-radius:4px;margin:6px 0">'
                f'<strong>📧 E-postavtale:</strong> {escape(f.message)}'
                f'{_source_chip("Forpliktelser", _CHIP_FORPLIKTELSER)}</div>',
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Grunnlag:** {f.citation}")
                with col2:
                    st.markdown(f"**Anbefalt handling:** "
                                f"{RECOMMENDED_ACTIONS.get(f.code.value, 'Vurder med saksbehandler')}")
                if f.expected is not None:
                    st.markdown(f"**Avtalt:** {f.expected} · **Fakturert:** {f.actual}")
            continue

        with st.container(border=True):
            st.markdown(f"{_SEV_ICON[f.severity]} **{escape(f.message)}**"
                        f"{_source_chip('Forpliktelser', _CHIP_FORPLIKTELSER)}",
                        unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Grunnlag:** {f.citation}")
            with col2:
                st.markdown(f"**Anbefalt handling:** "
                            f"{RECOMMENDED_ACTIONS.get(f.code.value, 'Vurder med saksbehandler')}")
            if f.expected is not None:
                st.markdown(f"**Avtalt:** {f.expected} · **Fakturert:** {f.actual}")
            if f.deviation_amount:
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


tab_check, tab_upload = st.tabs(["Kontroller faktura", "Last opp faktura (EHF)"])

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
            render_audit_card(session, inv)

# --- Tab 2: upload and parse an EHF invoice ------------------------------------
with tab_upload:
    st.markdown("Last opp en EHF-faktura (UBL 2.1 XML). Den blir tolket, knyttet til "
                "leverandør på organisasjonsnummer og kontrollert mot forpliktelsesbildet.")

    st.download_button(
        label="Last ned eksempel-EHF",
        data=build_sample_ehf(),
        file_name="eksempel-EHF-F-1003.xml",
        mime="application/xml",
        help="Syntetisk EHF bygget fra F-1003 — last ned, last opp igjen, og se kontrollen.",
    )

    _MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB — an EHF invoice is a few KB; cap abuse/DoS.

    uploaded = st.file_uploader("EHF-fil (.xml)", type=["xml"], key="ehf_upload")
    if uploaded is not None and uploaded.size > _MAX_UPLOAD_BYTES:
        st.error(f"Filen er for stor ({uploaded.size / 1_048_576:.1f} MB). "
                 "Maksimal størrelse er 5 MB — en EHF-faktura er normalt noen få kB.")
        uploaded = None
    if uploaded is not None:
        try:
            parsed = parse_ehf(uploaded.getvalue())
        except EHFParseError as exc:
            st.error(f"Kunne ikke tolke filen som EHF-faktura: {exc}")
            parsed = None

        if parsed is not None:
            st.caption(
                f"Tolket: **{parsed.invoice_number}** · {parsed.invoice_date} · "
                f"{parsed.supplier_name or 'ukjent leverandør'} "
                f"(org.nr {parsed.supplier_org or '—'}) · {len(parsed.lines)} linje(r) · "
                f"{money(parsed.total_ex_vat, parsed.currency)}"
            )
            with get_session() as session:
                supplier = None
                if parsed.supplier_org:
                    supplier = session.exec(
                        select(Supplier).where(Supplier.org_number == parsed.supplier_org)
                    ).first()
                if supplier is None:
                    supplier = Supplier(
                        org_number=parsed.supplier_org or f"UKJENT-{parsed.invoice_number}",
                        name=(parsed.supplier_name or "Ukjent leverandør") + " (OPPLASTET)",
                    )
                    session.add(supplier)
                    session.commit()
                    session.refresh(supplier)
                    st.info("Ukjent organisasjonsnummer — leverandør opprettet. "
                            "Fakturaen mangler avtalegrunnlag, som kontrollen vil vise.")

                # Idempotent: reuse an existing invoice with the same number for this supplier.
                inv = session.exec(
                    select(Invoice)
                    .where(Invoice.supplier_id == supplier.id)
                    .where(Invoice.invoice_number == parsed.invoice_number)
                ).first()
                if inv is None:
                    inv = Invoice(
                        supplier_id=supplier.id, order_id=None,
                        invoice_number=parsed.invoice_number, invoice_date=parsed.invoice_date,
                        total_ex_vat=parsed.total_ex_vat, currency=parsed.currency,
                        source=InvoiceSource.EHF,
                    )
                    session.add(inv)
                    session.commit()
                    session.refresh(inv)
                    for ln in parsed.lines:
                        session.add(InvoiceLine(
                            invoice_id=inv.id, item_ref=ln.item_ref, description=ln.description,
                            quantity=ln.quantity, unit_price=ln.unit_price, line_total=ln.line_total,
                        ))
                    session.commit()

                st.markdown("---")
                render_audit_card(session, inv)

footer()
