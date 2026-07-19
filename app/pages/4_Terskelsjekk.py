from datetime import date
from decimal import Decimal
from html import escape

import streamlit as st
from chrome import footer, header

from core.rules.engine import Facts, RulesEngine

st.set_page_config(page_title="Terskelsjekk", page_icon="⚖️", layout="wide")
header()
st.title("Terskelsjekk")
st.caption("Første steg er alltid valg av regime — beløpet avgjør aldri regimet. "
           "Reglene er versjonerte data med gyldighetsdatoer (per juli 2026).")

_REGIMES = {
    "FOA": "Klassisk sektor (anskaffelsesloven + FOA)",
    "FOSA": "Forsvars- og sikkerhetsanskaffelser (FOSA)",
    "ART123": "EØS art. 123 — vesentlige sikkerhetsinteresser (unntak)",
}

col1, col2, col3 = st.columns(3)
regime = col1.selectbox("Regime", options=list(_REGIMES), format_func=_REGIMES.get)
value = col2.number_input("Anslått verdi (NOK ekskl. mva)", min_value=0, value=750000, step=50000)
on = col3.date_input("Vurderingsdato", value=date(2026, 7, 8))

if regime == "FOSA":
    st.info("Merk: innslagspunktet på 500 000 kr gjelder IKKE for FOSA. "
            "Protokollplikt fra 100 000 kr.", icon="ℹ️")

def _nok(v) -> str:
    return f"{float(v):,.0f} kr".replace(",", " ")


def _step(col, title, body):
    with col:
        with st.container(border=True):
            st.markdown(f"**{title}**", unsafe_allow_html=True)
            st.markdown(body, unsafe_allow_html=True)


def _arrow(col):
    with col:
        st.markdown('<div style="text-align:center;font-size:28px;color:#8A94A0;'
                    'padding-top:24px">→</div>', unsafe_allow_html=True)


if st.button("Vurder", type="primary"):
    hits = RulesEngine().evaluate(
        Facts(regime=regime, estimated_value=Decimal(value), assessment_date=on)
    )

    st.markdown("---")
    # Three bordered step-columns with arrows: Regime -> Terskel -> Konsekvens (§).
    s1, a1, s2, a2, s3 = st.columns([3, 0.6, 3, 0.6, 3])

    _step(s1, "1. Regime", _REGIMES[regime])
    _arrow(a1)
    _step(s2, "2. Terskel",
          f"Anslått verdi <strong>{_nok(value)}</strong><br>"
          f'<span style="color:#8A94A0;font-size:12px">vurdert mot regimets '
          f"versjonerte terskelverdier (per {on.isoformat()})</span>")
    _arrow(a2)
    if hits:
        consequence = escape(hits[0].consequence.replace("_", " "))
        para = hits[0].citation.split("§")
        para_note = escape(f"§{para[1].split('(')[0].strip()}" if len(para) > 1 else "se hjemmel")
        _step(s3, "3. Konsekvens (§)",
              f"<strong>{consequence}</strong><br>"
              f'<span style="color:#8A94A0;font-size:12px">{para_note}</span>')
    else:
        _step(s3, "3. Konsekvens (§)",
              '<span style="color:#B58900">Ingen regel slo til</span>')

    if not hits:
        st.warning("Ingen regler slo til for denne kombinasjonen — sjekk regime og dato.")
    else:
        st.markdown("")
        for h in hits:
            with st.expander(f"Hjemmel og begrunnelse — {h.consequence.replace('_', ' ')}",
                             expanded=True):
                st.markdown(f"**Hjemmel:** {h.citation}")
                if h.citation_url:
                    st.markdown(f"[Les kilden]({h.citation_url})")
                st.caption(f"Regel-ID: {h.rule_id} · Regime: {h.regime}")

    st.caption("**Regimet vurderes ALLTID før beløpet — beløp avgjør aldri regime.**")
    st.caption("Veiledende vurdering basert på registrerte regler — "
               "beslutningsstøtte, ikke juridisk rådgivning.")

footer()
