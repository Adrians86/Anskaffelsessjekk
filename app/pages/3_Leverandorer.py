from datetime import date
from decimal import Decimal
from html import escape

import pandas as pd
import streamlit as st
from chrome import footer, header, page_header
from db import get_session, money, nok
from sqlmodel import select
from ui_common import verdict_pill
from ui_forpliktelser import render_email_commitment

from core.models import (
    SIDE_INTERNAL,
    SIDE_SUPPLIER,
    AuditLog,
    Commitment,
    Contract,
    ContractLine,
    Invoice,
    InvoiceLine,
    Supplier,
)
from core.registry import (
    SUPPLIER_STATUSES,
    RegistryError,
    add_category,
    add_contact,
    add_qualification,
    add_service,
    create_supplier,
    delete_contact,
    delete_qualification,
    delete_service,
    list_categories,
    list_contacts,
    list_qualifications,
    list_services,
    remove_category,
    restore_supplier,
    soft_delete_supplier,
    update_contact,
    update_qualification,
    update_service,
    update_supplier,
)
from core.reporting import evaluate_invoice
from core.synth.leverandor_profiler import avtale_status

st.set_page_config(page_title="Leverandører", page_icon="🏢", layout="wide")
header()
page_header(
    "Samarbeid", "Leverandører",
    "Hvilke leverandører genererer flest avvik — ta det opp med kilden, "
    "ikke bare symptomene. (First Time Right)",
)

# One form pattern (U3): every save shows a toast; the message survives the st.rerun() we trigger
# after a write. A save-error stays as a prominent banner (must not be missed).
_flash = st.session_state.pop("lev_flash", None)
if _flash:
    if _flash[0] == "ok":
        st.toast(_flash[1], icon="✅")
    else:
        st.error(_flash[1])


def _flash_and_rerun(kind: str, msg: str) -> None:
    """Store a flash toast, drop stale caches, and rerun so the change is visible immediately."""
    st.cache_data.clear()
    st.session_state["lev_flash"] = (kind, msg)
    st.rerun()


def _kommer(label: str, key: str) -> None:
    """Honest roadmap hook: a disabled button + «Kommer» chip marking where the next
    function will connect. Never a fake working button."""
    c1, c2 = st.columns([2, 6])
    c1.button(label, disabled=True, key=key, use_container_width=True)
    c2.markdown('<span class="as-chip">Kommer</span>', unsafe_allow_html=True)


@st.cache_data
def supplier_stats(include_deleted: bool = False):
    rows = []
    with get_session() as session:
        stmt = select(Supplier)
        if not include_deleted:
            stmt = stmt.where(Supplier.is_deleted == False)  # noqa: E712
        suppliers = session.exec(stmt).all()
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
                "Status": "Slettet" if sup.is_deleted else "Aktiv",
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


# --- Leverandørliste: søk + tabell + «Ny leverandør» i popover (U2) -----------
top_search, top_new = st.columns([3, 1])
search = top_search.text_input(
    "Søk", placeholder="🔎 Søk på navn eller org.nr …", label_visibility="collapsed")
with top_new.popover("＋ Ny leverandør", use_container_width=True):
    with st.form("ny_leverandor", clear_on_submit=True):
        n_org = st.text_input("Organisasjonsnummer *")
        n_name = st.text_input("Navn *")
        n_cat = st.text_input("Kategorier (kommaseparert)")
        n_notes = st.text_area("Notat", height=80,
                               placeholder="Fritt notat om leverandøren …")
        submitted = st.form_submit_button("Lagre leverandør", type="primary")
    if submitted:
        try:
            with get_session() as session:
                new_sup = create_supplier(
                    session, org_number=n_org, name=n_name,
                    categories=n_cat or None, notes=n_notes or None, actor="demo-bruker",
                )
                new_name = new_sup.name
            st.cache_data.clear()  # list/kort caches are now stale — refresh this run
            st.toast(f"«{new_name}» opprettet.", icon="✅")
        except RegistryError as exc:
            st.error(str(exc))

show_deleted = st.toggle("Vis slettede leverandører", value=False,
                         help="Myk sletting beholder raden og sporet — her kan de vises og gjenopprettes.")
rows = supplier_stats(show_deleted)
if search:
    _q = search.strip().lower()
    rows = [r for r in rows if _q in r["Navn"].lower() or _q in r["Org.nr"].lower()]

if not rows:
    st.info("Ingen treff for søket." if search else "Ingen leverandører registrert.")
else:
    cols = ["Navn", "Org.nr", "Avtaler", "Fakturaer", "Funn", "Verdi funnet", "Andel m/ funn"]
    if show_deleted:
        cols = ["Status", *cols]
    st.dataframe(pd.DataFrame(rows)[cols], use_container_width=True, hide_index=True)

    total_verdi = sum(r["_verdi"] for r in rows)
    st.caption(f"{len(rows)} leverandør(er) · total verdi funnet: **{nok(total_verdi)}**")

    # --- Leverandørkartotek (U1: faner + popover-redigering) -------------------
    st.divider()
    st.subheader("Leverandørkartotek")
    st.caption("Alt om leverandøren på ett sted — organisert i faner. Redigering ligger i popover, "
               "så skjermen holdes ryddig.")
    chosen_name = st.selectbox("Åpne kartotek", options=[r["Navn"] for r in rows])

    with get_session() as session:
        sup = session.exec(select(Supplier).where(Supplier.name == chosen_name)).first()

        # Firmakort header: name + SYNTETISK + status chip, then address/contact line.
        _status_color = {"Aktiv": "#2E7D32", "Inaktiv": "#6B7280", "Sperret": "#C62828"}
        _sc = _status_color.get(sup.status, "#6B7280")
        st.markdown(
            f'### {escape(sup.name)} '
            '<span style="background:#F1F3F5;color:#6B7280;font-size:11px;font-weight:600;'
            'padding:2px 10px;border-radius:10px;vertical-align:middle">SYNTETISK</span> '
            f'<span style="background:{_sc}1A;color:{_sc};font-size:11px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px;vertical-align:middle">'
            f'{escape(sup.status)}</span>',
            unsafe_allow_html=True,
        )
        _addr = ", ".join(escape(x) for x in (sup.address, f"{sup.postal_code or ''} "
                          f"{sup.city or ''}".strip()) if x and x.strip())
        _lines = [f"Org.nr {escape(sup.org_number)}"]
        if _addr:
            _lines.append(_addr)
        _contact_bits = [escape(x) for x in (sup.phone, sup.email, sup.website) if x]
        if _contact_bits:
            _lines.append(" · ".join(_contact_bits))
        st.caption("  \n".join(_lines))

        # Shared read-only data used across several tabs (cached, read-only).
        inv_rows = supplier_invoice_rows(sup.id)
        sup_verdi = sum(r["verdi_num"] for r in inv_rows)
        n_with_findings = sum(1 for r in inv_rows if r["has_findings"])
        n_inv = len(inv_rows)

        def _render_contact_group(side: str, add_label: str) -> None:
            for c in list_contacts(session, sup.id, side=side):
                with st.expander(f"{c.name} — {c.role or 'kontakt'}"):
                    st.caption(f"E-post: {escape(c.email or '—')} · "
                               f"Telefon: {escape(c.phone or '—')}")
                    with st.form(f"edit_contact_{c.id}"):
                        nm = st.text_input("Navn", value=c.name)
                        rl = st.text_input("Rolle", value=c.role or "")
                        em = st.text_input("E-post", value=c.email or "")
                        ph = st.text_input("Telefon", value=c.phone or "")
                        cs1, cs2 = st.columns(2)
                        upd = cs1.form_submit_button("Lagre person", type="primary")
                        rem = cs2.form_submit_button("🗑 Slett")
                    if upd:
                        try:
                            update_contact(session, c.id, name=nm, role=rl, email=em, phone=ph,
                                           actor="demo-bruker")
                            _flash_and_rerun("ok", f"«{nm}» er lagret.")
                        except RegistryError as exc:
                            st.error(str(exc))
                    if rem:
                        delete_contact(session, c.id, actor="demo-bruker")
                        _flash_and_rerun("ok", f"«{c.name}» er slettet.")
            with st.popover(add_label):
                with st.form(f"add_contact_{side}_{sup.id}", clear_on_submit=True):
                    a_name = st.text_input("Navn *", key=f"cn_{side}_{sup.id}")
                    a_role = st.text_input("Rolle", key=f"cr_{side}_{sup.id}")
                    a_email = st.text_input("E-post", key=f"ce_{side}_{sup.id}")
                    a_phone = st.text_input("Telefon", key=f"cp_{side}_{sup.id}")
                    add_ok = st.form_submit_button("Legg til person", type="primary")
                if add_ok:
                    try:
                        add_contact(session, sup.id, name=a_name, role=a_role, email=a_email,
                                    phone=a_phone, side=side, actor="demo-bruker")
                        _flash_and_rerun("ok", f"«{a_name}» er lagt til.")
                    except RegistryError as exc:
                        st.error(str(exc))

        (tab_over, tab_firma, tab_katj, tab_kval, tab_pers, tab_avt, tab_vurd) = st.tabs([
            "Oversikt", "Firmadata", "Kategorier og tjenester", "Kvalifikasjoner",
            "Personer", "Avtaler, forpliktelser og fakturaer", "Vurdering",
        ])

        # ---- Oversikt -------------------------------------------------------
        with tab_over:
            _n_contracts = len(session.exec(
                select(Contract).where(Contract.supplier_id == sup.id)).all())
            _n_invoices = len(session.exec(
                select(Invoice).where(Invoice.supplier_id == sup.id)).all())
            _n_commit = len(session.exec(
                select(Commitment).where(Commitment.supplier_id == sup.id)).all())
            st.caption(
                f"**Kartotek:** {len(list_categories(session, sup.id))} kategorier · "
                f"{len(list_services(session, sup.id))} tjenester · "
                f"{len(list_qualifications(session, sup.id))} kvalifikasjoner · "
                f"{len(list_contacts(session, sup.id))} personer · "
                f"{_n_contracts} avtaler · {_n_commit} forpliktelser · {_n_invoices} fakturaer"
            )
            o1, o2, o3 = st.columns(3)
            o1.metric("Fakturaer", n_inv)
            o2.metric("Verdi funnet", nok(sup_verdi))
            o3.metric("Andel m/ funn", f"{(n_with_findings / n_inv * 100) if n_inv else 0:.0f} %")
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

        # ---- Firmadata ------------------------------------------------------
        with tab_firma:
            with st.popover("✎ Rediger firmadata"):
                with st.form(f"rediger_firma_{sup.id}"):
                    e1, e2 = st.columns(2)
                    r_name = e1.text_input("Navn", value=sup.name)
                    r_org = e2.text_input("Organisasjonsnummer", value=sup.org_number)
                    r_addr = st.text_input("Adresse", value=sup.address or "")
                    p1, p2, p3 = st.columns([1, 2, 2])
                    r_post = p1.text_input("Postnr", value=sup.postal_code or "")
                    r_city = p2.text_input("Sted", value=sup.city or "")
                    r_status = p3.selectbox("Status", SUPPLIER_STATUSES,
                                            index=SUPPLIER_STATUSES.index(sup.status)
                                            if sup.status in SUPPLIER_STATUSES else 0)
                    w1, w2, w3 = st.columns(3)
                    r_web = w1.text_input("Nettside", value=sup.website or "")
                    r_email = w2.text_input("E-post", value=sup.email or "")
                    r_phone = w3.text_input("Telefon", value=sup.phone or "")
                    r_iso = st.checkbox("ISO-sertifisert", value=sup.iso_certified)
                    r_sec = st.checkbox("Sikkerhetsklarert", value=sup.security_cleared)
                    saved = st.form_submit_button("Lagre leverandør", type="primary")
                if saved:
                    try:
                        update_supplier(session, sup.id, name=r_name, org_number=r_org,
                                        address=r_addr, postal_code=r_post, city=r_city,
                                        website=r_web, email=r_email, phone=r_phone,
                                        status=r_status, iso_certified=r_iso,
                                        security_cleared=r_sec, actor="demo-bruker")
                        _flash_and_rerun("ok", f"Firmadata for «{r_name}» er lagret.")
                    except RegistryError as exc:
                        st.error(str(exc))

            st.markdown("**Notat**")
            if sup.notes:
                st.markdown(
                    '<div style="background:#FCFBF7;border:1px solid #E4E1D8;border-radius:8px;'
                    'padding:8px 12px;font-size:13px;color:#1C2733;white-space:pre-wrap">'
                    f'{escape(sup.notes)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Ingen notater ennå.")
            with st.popover("✎ Rediger notat"):
                with st.form(f"notat_{sup.id}"):
                    n4_notes = st.text_area("Notat", value=sup.notes or "", height=120,
                                            placeholder="Fritt notat om samarbeidet …")
                    saved4 = st.form_submit_button("Lagre notat", type="primary")
                if saved4:
                    update_supplier(session, sup.id, notes=n4_notes, actor="demo-bruker")
                    _flash_and_rerun("ok", "Notat er lagret.")

            st.divider()
            if sup.is_deleted:
                st.warning("Denne leverandøren er slettet (mykt). Raden og revisjonssporet "
                           "er beholdt.")
                if st.button("↩ Gjenopprett leverandør", key=f"restore_{sup.id}"):
                    restore_supplier(session, sup.id, actor="demo-bruker")
                    _flash_and_rerun("ok", f"«{sup.name}» er gjenopprettet.")
            else:
                with st.popover("🗑 Slett leverandør"):
                    st.caption("Myk sletting: leverandøren skjules fra listen, men raden og "
                               "revisjonssporet beholdes (kan gjenopprettes).")
                    confirm = st.checkbox("Jeg bekrefter sletting", key=f"confirm_del_{sup.id}")
                    if st.button("Slett leverandør", type="primary", disabled=not confirm,
                                 key=f"del_{sup.id}"):
                        soft_delete_supplier(session, sup.id, actor="demo-bruker")
                        _flash_and_rerun("ok", f"«{sup.name}» er slettet (mykt).")

        # ---- Kategorier og tjenester ---------------------------------------
        with tab_katj:
            st.markdown("**Kategorier** — hva leverandøren leverer")
            cats = list_categories(session, sup.id)
            if cats:
                ccols = st.columns(4)
                for i, cat in enumerate(cats):
                    if ccols[i % 4].button(f"✕ {cat}", key=f"delcat_{sup.id}_{i}",
                                           use_container_width=True, help="Fjern kategori"):
                        remove_category(session, sup.id, cat, actor="demo-bruker")
                        _flash_and_rerun("ok", f"Kategori «{cat}» fjernet.")
            else:
                st.caption("Ingen kategorier ennå.")
            with st.popover("＋ Ny kategori"):
                with st.form(f"addcat_{sup.id}", clear_on_submit=True):
                    new_cat = st.text_input("Kategori", key=f"nc_{sup.id}",
                                            placeholder="F.eks. «Vedlikehold»")
                    cat_added = st.form_submit_button("Legg til kategori", type="primary")
                if cat_added:
                    try:
                        add_category(session, sup.id, new_cat, actor="demo-bruker")
                        _flash_and_rerun("ok", f"Kategori «{new_cat}» lagt til.")
                    except RegistryError as exc:
                        st.error(str(exc))

            st.divider()
            st.markdown("**Tjenester og produkter**")
            services = list_services(session, sup.id)
            if services:
                for svc in services:
                    price = nok(svc.unit_price) if svc.unit_price is not None else "—"
                    unit_txt = f" / {svc.unit}" if svc.unit else ""
                    with st.expander(f"{svc.name} — {price}{unit_txt}"):
                        with st.form(f"edit_svc_{svc.id}"):
                            sv1, sv2 = st.columns(2)
                            s_name = sv1.text_input("Navn", value=svc.name)
                            s_unit = sv2.text_input("Enhet", value=svc.unit or "")
                            s_desc = st.text_input("Beskrivelse", value=svc.description or "")
                            sp1, sp2 = st.columns([1, 2])
                            s_haspris = sp1.checkbox("Angi pris", value=svc.unit_price is not None,
                                                     key=f"hp_{svc.id}")
                            s_price = sp2.number_input(
                                "Pris (NOK)", min_value=0.0, step=100.0,
                                value=float(svc.unit_price) if svc.unit_price is not None else 0.0,
                                key=f"pr_{svc.id}")
                            se1, se2 = st.columns(2)
                            s_upd = se1.form_submit_button("Lagre tjeneste", type="primary")
                            s_del = se2.form_submit_button("🗑 Slett")
                        if s_upd:
                            try:
                                update_service(
                                    session, svc.id, name=s_name, description=s_desc, unit=s_unit,
                                    unit_price=Decimal(str(s_price)) if s_haspris else None,
                                    update_price=True, actor="demo-bruker")
                                _flash_and_rerun("ok", f"«{s_name}» er lagret.")
                            except RegistryError as exc:
                                st.error(str(exc))
                        if s_del:
                            delete_service(session, svc.id, actor="demo-bruker")
                            _flash_and_rerun("ok", f"«{svc.name}» er slettet.")
            else:
                st.caption("Ingen tjenester/produkter registrert ennå.")
            with st.popover("＋ Ny tjeneste/produkt"):
                with st.form(f"add_svc_{sup.id}", clear_on_submit=True):
                    nv1, nv2 = st.columns(2)
                    a_name = nv1.text_input("Navn *")
                    a_unit = nv2.text_input("Enhet (stk/time/måned)")
                    a_desc = st.text_input("Beskrivelse ")
                    np1, np2 = st.columns([1, 2])
                    a_haspris = np1.checkbox("Angi pris", key=f"hp_new_{sup.id}")
                    a_price = np2.number_input("Pris (NOK)", min_value=0.0, step=100.0, value=0.0,
                                               key=f"pr_new_{sup.id}")
                    svc_added = st.form_submit_button("Legg til tjeneste", type="primary")
                if svc_added:
                    try:
                        add_service(session, sup.id, name=a_name, description=a_desc, unit=a_unit,
                                    unit_price=Decimal(str(a_price)) if a_haspris else None,
                                    actor="demo-bruker")
                        _flash_and_rerun("ok", f"«{a_name}» er lagt til.")
                    except RegistryError as exc:
                        st.error(str(exc))

        # ---- Kvalifikasjoner ------------------------------------------------
        with tab_kval:
            st.caption("Uten dato: bare et hak (gjelder). Med dato: utløpte vises i rødt.")
            quals = list_qualifications(session, sup.id)
            if quals:
                for q in quals:
                    expired = q.is_expired()
                    color = "#C62828" if expired else "#2E7D32"
                    if q.valid_to is None:
                        status_txt, date_txt = "Gjelder", "uten utløp"
                    else:
                        status_txt = "UTLØPT" if expired else "Gyldig"
                        date_txt = f"t.o.m. {q.valid_to}"
                    st.markdown(
                        f'<span style="color:{color};font-weight:600">●</span> '
                        f'{escape(q.name)} — <span style="color:{color};font-weight:600">'
                        f'{status_txt}</span> '
                        f'<span style="color:#8A94A0;font-size:12px">({escape(date_txt)})</span>',
                        unsafe_allow_html=True,
                    )
                    with st.expander(f"✎ {q.name}"):
                        with st.form(f"edit_qual_{q.id}"):
                            q_name = st.text_input("Navn", value=q.name)
                            qh1, qh2 = st.columns([1, 2])
                            q_has = qh1.checkbox("Har gyldighetsdato", value=q.valid_to is not None,
                                                 key=f"qh_{q.id}")
                            q_date = qh2.date_input("Gyldig til", value=q.valid_to or date.today(),
                                                    key=f"qd_{q.id}")
                            qe1, qe2 = st.columns(2)
                            q_upd = qe1.form_submit_button("Lagre kvalifikasjon", type="primary")
                            q_del = qe2.form_submit_button("🗑 Slett")
                        if q_upd:
                            try:
                                update_qualification(session, q.id, name=q_name,
                                                     valid_to=(q_date if q_has else None),
                                                     update_valid_to=True, actor="demo-bruker")
                                _flash_and_rerun("ok", f"«{q_name}» er lagret.")
                            except RegistryError as exc:
                                st.error(str(exc))
                        if q_del:
                            delete_qualification(session, q.id, actor="demo-bruker")
                            _flash_and_rerun("ok", f"«{q.name}» er slettet.")
            else:
                st.caption("Ingen kvalifikasjoner registrert ennå.")
            with st.popover("＋ Ny kvalifikasjon"):
                with st.form(f"add_qual_{sup.id}", clear_on_submit=True):
                    aq_name = st.text_input("Navn *", key=f"aqn_{sup.id}")
                    aq1, aq2 = st.columns([1, 2])
                    aq_has = aq1.checkbox("Har gyldighetsdato", key=f"aqh_{sup.id}")
                    aq_date = aq2.date_input("Gyldig til", value=date.today(), key=f"aqd_{sup.id}")
                    qual_added = st.form_submit_button("Legg til kvalifikasjon", type="primary")
                if qual_added:
                    try:
                        add_qualification(session, sup.id, name=aq_name,
                                          valid_to=(aq_date if aq_has else None),
                                          actor="demo-bruker")
                        _flash_and_rerun("ok", f"«{aq_name}» er lagt til.")
                    except RegistryError as exc:
                        st.error(str(exc))

        # ---- Personer -------------------------------------------------------
        with tab_pers:
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("*Kontakt hos leverandøren*")
                _render_contact_group(SIDE_SUPPLIER, "＋ Ny kontakt (leverandør)")
            with g2:
                st.markdown("*Ansvarlig hos oss*")
                _render_contact_group(SIDE_INTERNAL, "＋ Ny ansvarlig (intern)")

        # ---- Avtaler, forpliktelser og fakturaer ----------------------------
        with tab_avt:
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
            _kommer("＋ Registrer avtale", f"komm_avtale_{sup.id}")

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
                                f"{nok(cm.value) if cm.value is not None else '—'} · "
                                f"Kilde: {cm.source_ref}")
            else:
                st.caption("Ingen registrerte tilleggsforpliktelser.")
            _kommer("＋ Registrer forpliktelse", f"komm_forpl_{sup.id}")

            st.markdown("**Fakturaer**")
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
            if not inv_rows:
                st.caption("Ingen fakturaer registrert.")
            _kommer("＋ Registrer faktura", f"komm_faktura_{sup.id}")

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
                    o4.markdown(
                        f'<span style="color:{flag_color};font-weight:600">{o["status"]}</span>',
                        unsafe_allow_html=True)
            else:
                st.caption("Ingen fakturerte objekter registrert.")

        # ---- Vurdering ------------------------------------------------------
        with tab_vurd:
            st.info("Dette er innsikt i samarbeidet, **ikke en kvalifikasjonsrangering**. Tallene "
                    "beskriver historikk i vår egen fakturakontroll og skal ikke brukes som "
                    "kvalifikasjons- eller tildelingskriterium.")
            andel = (n_with_findings / n_inv * 100) if n_inv else 0.0
            ftr = (1 - n_with_findings / n_inv) * 100 if n_inv else 100.0
            q1, q2 = st.columns(2)
            q1.metric("Andel m/ funn", f"{andel:.0f} %")
            q2.metric("First Time Right", f"{ftr:.0f} %")
            vc = {"AVVIK": 0, "TIL_VURDERING": 0, "SAMSVAR": 0}
            for r in inv_rows:
                vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
            if n_inv:
                pe, pw, po = (vc["AVVIK"] / n_inv * 100, vc["TIL_VURDERING"] / n_inv * 100,
                             vc["SAMSVAR"] / n_inv * 100)
                st.markdown(
                    '<div style="display:flex;height:10px;border-radius:5px;overflow:hidden;'
                    'margin:4px 0">'
                    f'<div style="width:{pe}%;background:#C62828"></div>'
                    f'<div style="width:{pw}%;background:#B58900"></div>'
                    f'<div style="width:{po}%;background:#2E7D32"></div></div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"● {vc['AVVIK']} avvik · {vc['TIL_VURDERING']} til vurdering · "
                           f"{vc['SAMSVAR']} samsvar. Trend over tid vises når flere "
                           "kontrollperioder foreligger.")

            st.divider()
            st.markdown("**Egen samarbeidsvurdering**")
            if sup.cooperation_rating:
                st.markdown(
                    '<div style="background:#FCFBF7;border:1px solid #E4E1D8;border-radius:8px;'
                    'padding:8px 12px;font-size:13px;color:#1C2733;white-space:pre-wrap">'
                    f'{escape(sup.cooperation_rating)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Ingen samarbeidsvurdering skrevet ennå.")
            with st.popover("✎ Rediger samarbeidsvurdering"):
                with st.form(f"samarbeid_{sup.id}"):
                    cr = st.text_area("Samarbeidsvurdering (egen vurdering)",
                                      value=sup.cooperation_rating or "", height=100,
                                      placeholder="Din egen vurdering av samarbeidet …")
                    cr_saved = st.form_submit_button("Lagre vurdering", type="primary")
                if cr_saved:
                    update_supplier(session, sup.id, cooperation_rating=cr, actor="demo-bruker")
                    _flash_and_rerun("ok", "Samarbeidsvurdering er lagret.")
            st.caption("Egen vurdering — supplerer auto-tallene over. Samme KOFA-forbehold gjelder: "
                       "innsikt i samarbeidet, ikke en kvalifikasjonsrangering.")

            st.markdown("**Leveranseoppfølging** "
                        '<span style="background:#F1F3F5;color:#6B7280;font-size:11px;'
                        'font-weight:600;padding:2px 10px;border-radius:10px">Roadmap</span>',
                        unsafe_allow_html=True)
            st.caption("Planlagt område: oppfølging av leveranser og frister mot avtale. Ikke en "
                       "del av demoen ennå — vist her for å vise retningen, ikke som halvferdig "
                       "funksjon.")

footer()
