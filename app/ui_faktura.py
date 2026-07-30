"""Funksjon 3 UI — faktura-inntak, prisliste-verifikasjon (HVORFOR), batch-liste og beslutning.

UI-only (app/ layer). Verification/persistence live in core (matching/prisliste, registry/faktura);
this module only renders and calls them. Every dynamic value in unsafe_allow_html is html.escape()-d.
"""
from __future__ import annotations

from html import escape

import streamlit as st
from db import dato, nok
from texts import RECOMMENDED_ACTIONS

from core.matching import prisliste
from core.matching.findings import Severity
from core.models import INVOICE_DECISIONS, Supplier
from core.registry import latest_decision, list_lines, record_decision
from core.reporting import build_protokoll

_V = {
    "SAMSVAR": ("SAMSVAR", "#2E7D32", "#EAF4EC"),
    "TIL_VURDERING": ("TIL VURDERING", "#B58900", "#FBF7EC"),
    "AVVIK": ("AVVIK", "#C62828", "#FBEAEA"),
}
_SEV_ICON = {Severity.DEVIATION: "🔴", Severity.WARN: "🟡", Severity.INFO: "ℹ️"}
_DEC_LABEL = {"godkjent": ("Godkjent", "#2E7D32"), "avvist": ("Avvist", "#C62828"),
              "vent": ("På vent", "#B58900")}


def faktura_flash() -> None:
    fl = st.session_state.pop("faktura_flash", None)
    if fl:
        (st.toast if fl[0] == "ok" else st.error)(fl[1], **({"icon": "✅"} if fl[0] == "ok" else {}))


def _flash_and_rerun(kind: str, msg: str) -> None:
    st.cache_data.clear()
    st.session_state["faktura_flash"] = (kind, msg)
    st.rerun()


def linkage_banner(session, inv) -> None:
    """N3 — show explicitly which contract + price list this invoice is controlled against."""
    sup = session.get(Supplier, inv.supplier_id)
    contract = prisliste.resolve_contract(session, inv)
    if contract is not None:
        n = len(list_lines(session, contract.id))
        st.markdown(
            f'<div style="background:#FCFBF7;border:1px solid #E4E1D8;border-radius:8px;'
            f'padding:10px 14px;font-size:13px;color:#1C2733">'
            f'🔗 Denne fakturaen kontrolleres MOT avtale <strong>{escape(contract.reference)}</strong> '
            f'({escape(contract.title)}) hos <strong>{escape(sup.name)}</strong> — '
            f'prisliste {n} linje(r).</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Ingen aktiv avtale funnet for {sup.name} — fakturaen mangler prisgrunnlag. "
                   "Legg til en avtale med prisliste for å kunne kontrollere prisene.")


def render_pricelist_verdict(session, inv) -> prisliste.PriceListResult:
    """N4 — verdict WITH WHY, from the price-list verification. Returns the result."""
    r = prisliste.verify(session, inv)
    vlabel, vcolor, vbg = _V[r.verdict.value]
    if r.verdict.value == "AVVIK":
        vsub = f"{nok(r.verdi_funnet)} over avtalt prisliste."
    elif r.verdict.value == "TIL_VURDERING":
        vsub = "Krever manuell vurdering."
    else:
        vsub = "Fakturaen samsvarer med avtalt prisliste."
    st.markdown(
        f'<div style="background:{vbg};border-left:6px solid {vcolor};border-radius:8px;'
        f'padding:14px 18px;margin:6px 0">'
        f"<div style=\"font-family:Georgia,'Times New Roman',serif;font-size:26px;"
        f'font-weight:700;color:{vcolor};line-height:1.1">{vlabel}</div>'
        f'<div style="font-size:13px;color:#5A6673;margin-top:2px">{escape(vsub)}</div></div>',
        unsafe_allow_html=True,
    )
    if not r.findings:
        st.success("Ingen funn mot prislisten — alle linjer er innenfor avtalt pris.")
    for f in r.findings:
        st.markdown(
            f'<div style="padding:6px 0">{_SEV_ICON[f.severity]} '
            f'<strong>{escape(f.message)}</strong></div>',
            unsafe_allow_html=True)
        with st.expander("Hvorfor — grunnlag og anbefalt handling"):
            st.markdown(f"**Grunnlag:** {escape(f.citation)}")
            st.markdown("**Anbefalt handling:** "
                        + RECOMMENDED_ACTIONS.get(f.code.value, "Vurder med saksbehandler"))
            if f.expected is not None:
                st.markdown(f"**Avtalt:** {escape(str(f.expected))} · "
                            f"**Fakturert:** {escape(str(f.actual))}")
            if f.deviation_amount:
                st.markdown(f"**Avvik:** {nok(f.deviation_amount)}")
    return r


def render_decision(session, inv) -> None:
    """N6 — human decision (approve/reject/hold + reason). System recommends, human decides."""
    st.markdown("**Beslutning** (saksbehandler)")
    current = latest_decision(session, inv.id)
    if current is not None:
        label, color = _DEC_LABEL.get(current.decision, (current.decision, "#5A6673"))
        st.markdown(
            f'<span style="background:{color}1A;color:{color};font-size:12px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px">{escape(label)}</span> '
            f'<span style="font-size:12px;color:#5A6673">'
            f'{escape(current.actor)} · {dato(current.created_at)}'
            f'{(" · " + escape(current.reason)) if current.reason else ""}</span>',
            unsafe_allow_html=True)
    with st.form(f"decision_{inv.id}"):
        choice = st.radio("Beslutning", INVOICE_DECISIONS, horizontal=True,
                          format_func=lambda d: {"godkjent": "✓ Godkjenn", "avvist": "✗ Avvis",
                                                 "vent": "⏸ Vent"}[d])
        reason = st.text_input("Begrunnelse (valgfri, men anbefalt ved avvik)")
        saved = st.form_submit_button("Registrer beslutning", type="primary")
    if saved:
        record_decision(session, inv.id, choice, reason=reason or None, actor="demo-bruker")
        _flash_and_rerun("ok", f"Beslutning «{choice}» registrert for {inv.invoice_number}.")
    st.caption("Systemet anbefaler — mennesket bestemmer. Beslutningen blokkeres aldri, kun logget "
               "i revisjonssporet (hard rule #3).")


def render_protokoll(session, inv) -> None:
    """N7 — anskaffelsesprotokoll PDF for the invoice."""
    pdf = build_protokoll(session, inv)
    st.download_button("Last ned protokoll (PDF)", data=pdf,
                       file_name=f"Anskaffelsesprotokoll_{inv.invoice_number}.pdf",
                       mime="application/pdf", key=f"pdf_{inv.id}")


def render_single_result(session, inv) -> None:
    """Full end-to-end block for one invoice: linkage → verdict WHY → decision → protokoll."""
    linkage_banner(session, inv)
    render_pricelist_verdict(session, inv)
    st.divider()
    render_decision(session, inv)
    render_protokoll(session, inv)


def render_batch_results(session, invoices) -> None:
    """N5 — batch result list, avvik on top; each row expands to the full result + decision."""
    rows = []
    for inv in invoices:
        r = prisliste.verify(session, inv)
        sup = session.get(Supplier, inv.supplier_id)
        rows.append((inv, r, sup))
    order = {"AVVIK": 0, "TIL_VURDERING": 1, "SAMSVAR": 2}
    rows.sort(key=lambda t: (order.get(t[1].verdict.value, 3), -float(t[1].verdi_funnet)))

    from ui_common import verdict_pill
    total = sum(float(r.verdi_funnet) for _, r, _ in rows)
    st.markdown(f"**{len(rows)} faktura(er) kontrollert** · verdi funnet i partiet: "
                f"**{nok(total)}**")
    for inv, r, sup in rows:
        c1, c2, c3, c4 = st.columns([2, 2.5, 1.5, 1.4])
        c1.text(inv.invoice_number)
        c2.text(sup.name)
        c3.markdown(verdict_pill(r.verdict.value), unsafe_allow_html=True)
        c4.text(nok(r.verdi_funnet) if r.verdi_funnet else "—")
        with st.expander(f"Åpne {inv.invoice_number} — {r.verdict.value}"):
            render_single_result(session, inv)
