from html import escape

import pandas as pd
import streamlit as st
from chrome import footer, header
from db import get_session, money, nok
from sqlmodel import select
from ui_common import verdict_pill
from ui_forpliktelser import render_email_commitment

from core.models import (
    AuditLog,
    Commitment,
    Contract,
    ContractLine,
    Invoice,
    InvoiceLine,
    Supplier,
)
from core.reporting import evaluate_invoice
from core.synth.leverandor_profiler import avtale_status, is_expired, profile_for

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
                result = evaluate_invoice(session, inv)
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


@st.cache_data
def supplier_invoice_rows(supplier_id: int):
    """Per-supplier invoice evaluations (cached, read-only). evaluate_invoice never writes."""
    with get_session() as session:
        invoices = session.exec(
            select(Invoice).where(Invoice.supplier_id == supplier_id)
            .order_by(Invoice.invoice_number)
        ).all()
        out = []
        for inv in invoices:
            r = evaluate_invoice(session, inv)
            out.append({
                "id": inv.id, "number": inv.invoice_number,
                "date": str(inv.invoice_date), "amount": money(inv.total_ex_vat, inv.currency),
                "verdict": r.verdict.value,
                "verdi_display": nok(r.verdi_funnet) if r.verdi_funnet else "—",
                "verdi_num": float(r.verdi_funnet), "has_findings": bool(r.findings),
            })
        return out


@st.cache_data
def supplier_invoiced_objects(supplier_id: int):
    """What we actually paid a supplier for (invoice lines), each flagged på/utenfor avtale.
    Context only — NOT a machine register. Cached, read-only."""
    with get_session() as session:
        contract_refs: set[str] = set()
        for c in session.exec(select(Contract).where(Contract.supplier_id == supplier_id)).all():
            for cl in session.exec(
                select(ContractLine).where(ContractLine.contract_id == c.id)
            ).all():
                if cl.item_ref:
                    contract_refs.add(cl.item_ref)

        agg: dict[str, dict] = {}
        for inv in session.exec(select(Invoice).where(Invoice.supplier_id == supplier_id)).all():
            for ln in session.exec(
                select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id)
            ).all():
                key = ln.item_ref or "(uten artikkel)"
                a = agg.setdefault(key, {"item_ref": key, "description": ln.description,
                                         "antall": 0, "sum": 0.0, "currency": inv.currency})
                a["antall"] += 1
                a["sum"] += float(ln.line_total)
        out = []
        for key, a in agg.items():
            a["status"] = avtale_status(key, contract_refs)
            a["sum_display"] = money(a["sum"], a["currency"])
            out.append(a)
        out.sort(key=lambda x: x["sum"], reverse=True)
        return out


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

    # --- V6: Leverandørkort drill-down ----------------------------------------
    st.divider()
    st.subheader("Leverandørkort")
    chosen_name = st.selectbox("Åpne leverandørkort", options=[r["Navn"] for r in rows])

    with get_session() as session:
        sup = session.exec(select(Supplier).where(Supplier.name == chosen_name)).first()

        # (a) header
        st.markdown(
            f'### {escape(sup.name)} '
            '<span style="background:#F1F3F5;color:#6B7280;font-size:11px;font-weight:600;'
            'padding:2px 10px;border-radius:10px;vertical-align:middle">SYNTETISK</span>',
            unsafe_allow_html=True,
        )
        st.caption(f"Org.nr {escape(sup.org_number)}")

        # (L1) Kategorier + kvalifikasjoner (what the supplier may deliver; expired in red)
        st.markdown("**Kategorier og kvalifikasjoner**")
        profile = profile_for(sup.org_number)
        if profile:
            st.markdown("Kategorier: " + ", ".join(escape(k) for k in profile["kategorier"]))
            for q in profile["kvalifikasjoner"]:
                expired = is_expired(q["gyldig_til"])
                color = "#C62828" if expired else "#2E7D32"
                status = "UTLØPT" if expired else "Gyldig"
                st.markdown(
                    f'<span style="color:{color};font-weight:600">●</span> '
                    f'{escape(q["navn"])} — <span style="color:{color}">{status}</span> '
                    f'<span style="color:#8A94A0;font-size:12px">(t.o.m. {q["gyldig_til"]})</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Ingen registrerte kategorier/kvalifikasjoner (syntetisk profil mangler).")

        # (b) Avtaler
        st.markdown("**Avtaler**")
        contracts = session.exec(
            select(Contract).where(Contract.supplier_id == sup.id)
        ).all()
        if contracts:
            for c in contracts:
                n_lines = len(session.exec(
                    select(ContractLine).where(ContractLine.contract_id == c.id)
                ).all())
                st.markdown(f"- **{c.reference}** · {c.title} · {c.valid_from} → {c.valid_to} · "
                            f"ramme {nok(c.total_value)} · {n_lines} linjer")
        else:
            st.caption("Ingen kontrakter registrert.")

        # (c) Forpliktelser (reuse V1 rendering for e-mail commitments)
        st.markdown("**Forpliktelser**")
        commitments = session.exec(
            select(Commitment).where(Commitment.supplier_id == sup.id)
        ).all()
        if commitments:
            for cm in commitments:
                if cm.source_type.value == "EMAIL":
                    render_email_commitment(cm)
                else:
                    st.info(f"{cm.item_ref}: {cm.condition_type.value} = "
                            f"{nok(cm.value) if cm.value is not None else '—'} · Kilde: {cm.source_ref}")
        else:
            st.caption("Ingen registrerte tilleggsforpliktelser.")

        # (d) Fakturaer (cached, read-only)
        st.markdown("**Fakturaer**")
        inv_rows = supplier_invoice_rows(sup.id)
        sup_verdi = sum(r["verdi_num"] for r in inv_rows)
        n_with_findings = sum(1 for r in inv_rows if r["has_findings"])
        for r in inv_rows:
            col1, col2, col3, col4, col5, col6 = st.columns([1.4, 1.4, 1.5, 2, 1.5, 1])
            col1.text(r["number"])
            col2.text(r["date"])
            col3.text(r["amount"])
            col4.markdown(verdict_pill(r["verdict"]), unsafe_allow_html=True)
            col5.text(r["verdi_display"])
            if col6.button("Åpne →", key=f"levopen_{r['id']}"):
                st.session_state.preselect_invoice = r["id"]
                st.switch_page("pages/1_Fakturakontroll.py")

        # (e) Nøkkeltall — transactional facts
        st.markdown("**Nøkkeltall**")
        n_inv = len(inv_rows)
        andel = (n_with_findings / n_inv * 100) if n_inv else 0.0
        ftr = (1 - n_with_findings / n_inv) * 100 if n_inv else 100.0
        k1, k2 = st.columns(2)
        k1.metric("Fakturaer", n_inv)
        k2.metric("Verdi funnet", nok(sup_verdi))

        # (L2) Kvalitetsvurdering fra våre kontrolldata — insight, NOT a ranking (KOFA)
        st.markdown("**Kvalitetsvurdering**")
        st.info("Dette er innsikt i samarbeidet, **ikke en kvalifikasjonsrangering**. Tallene "
                "beskriver historikk i vår egen fakturakontroll og skal ikke brukes som "
                "kvalifikasjons- eller tildelingskriterium.")
        q1, q2 = st.columns(2)
        q1.metric("Andel m/ funn", f"{andel:.0f} %")
        q2.metric("First Time Right", f"{ftr:.0f} %")
        # Kvalitetsprofil: share of verdicts (not a time trend — demo has one kontrollperiode).
        vc = {"AVVIK": 0, "TIL_VURDERING": 0, "SAMSVAR": 0}
        for r in inv_rows:
            vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
        if n_inv:
            pe, pw, po = (vc["AVVIK"] / n_inv * 100, vc["TIL_VURDERING"] / n_inv * 100,
                         vc["SAMSVAR"] / n_inv * 100)
            st.markdown(
                '<div style="display:flex;height:10px;border-radius:5px;overflow:hidden;margin:4px 0">'
                f'<div style="width:{pe}%;background:#C62828"></div>'
                f'<div style="width:{pw}%;background:#B58900"></div>'
                f'<div style="width:{po}%;background:#2E7D32"></div></div>',
                unsafe_allow_html=True,
            )
            st.caption(f"● {vc['AVVIK']} avvik · {vc['TIL_VURDERING']} til vurdering · "
                       f"{vc['SAMSVAR']} samsvar. Trend over tid vises når flere "
                       "kontrollperioder foreligger.")

        # (L3) Fakturerte objekter — what we paid for, flagged på/utenfor avtale (context only)
        st.markdown("**Fakturerte objekter**")
        st.caption("Hva vi faktisk har betalt for — kontekst, ikke et maskinregister.")
        objs = supplier_invoiced_objects(sup.id)
        if objs:
            for o in objs:
                on = o["status"] == "på avtale"
                flag_color = "#2E7D32" if on else "#B58900"
                o1, o2, o3, o4 = st.columns([1.6, 3, 1.6, 1.6])
                o1.text(o["item_ref"])
                o2.text(o["description"])
                o3.text(o["sum_display"])
                o4.markdown(f'<span style="color:{flag_color};font-weight:600">{o["status"]}</span>',
                            unsafe_allow_html=True)
        else:
            st.caption("Ingen fakturerte objekter registrert.")

        # (L4) Leveranseoppfølging — honestly marked as a future module, not a quarter-product
        st.markdown("**Leveranseoppfølging** "
                    '<span style="background:#F1F3F5;color:#6B7280;font-size:11px;font-weight:600;'
                    'padding:2px 10px;border-radius:10px">Roadmap</span>',
                    unsafe_allow_html=True)
        st.caption("Planlagt område: oppfølging av leveranser og frister mot avtale. Ikke en del "
                   "av demoen ennå — vist her for å vise retningen, ikke som halvferdig funksjon.")

        # (f) Siste hendelser for this supplier (live — reflects real controls)
        st.markdown("**Siste hendelser**")
        inv_entities = {f"invoice:{r['id']}" for r in inv_rows}
        events = [e for e in session.exec(
            select(AuditLog).order_by(AuditLog.created_at.desc())
        ).all() if e.entity in inv_entities][:8]
        if events:
            for e in events:
                st.caption(f"**{e.created_at.strftime('%H:%M')}** — {e.actor}: {e.action} "
                           f"({e.entity}) · {e.detail}")
        else:
            st.caption("Ingen hendelser for denne leverandøren ennå.")

footer()
