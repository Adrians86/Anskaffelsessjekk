# Grafikk-revisjon — hardkodede verdier per side

**AS North HQ · 2026-08-09 · G0 audit FØR G1–G8-endringer**

Kartlegger alle hardkodede farger, fonter og størrelser som skal flyttes til
`app/theme.py`-tokens. Fargene er gruppert i to kategorier:

- **BRAND.md (exempt)**: `#2E7D32 / #B58900 / #C62828` — vedtaksemantikk, ikke-forhandlingsbar.
- **Chrome-farger (token-kandidater)**: navy, gold, muted, line, bg osv.

Altair-diagram bruker literate strings (`range=[...]`) og er exempt fra CSS-variable-kravet.

---

## Tabell — hardkodede verdier

| Side | Fil + linje | Hardkodet verdi | Token / håndtering |
|---|---|---|---|
| Hjem | `Hjem.py:141-143` | `#C62828`, `#B58900`, `#2E7D32` i helse-bar | BRAND.md exempt |
| Hjem | `Hjem.py:184` | `color:#5A6673` (tomt-tilstand) | `MUTED` → `var(--as-muted)` |
| Hjem | `Hjem.py:202` | `color:#5A6673` (feed entity) | `MUTED` → `var(--as-muted)` |
| Fakturakontroll | `1_Fakturakontroll.py:46` | `_CHIP_FORPLIKTELSER = "#B08D2E"` | ✅ Allerede = `GOLD` |
| Fakturakontroll | `1_Fakturakontroll.py:47` | `_CHIP_REGELVERK = "#2E7D32"` | BRAND.md exempt |
| Fakturakontroll | `1_Fakturakontroll.py:48` | `_CHIP_INTERNT = "#1F3A5F"` | ✅ Allerede = `NAVY` |
| Fakturakontroll | `1_Fakturakontroll.py:74-76` | `"#2E7D32"`, `"#B58900"`, `"#C62828"` i verdikt | BRAND.md exempt |
| Fakturakontroll | `1_Fakturakontroll.py:89` | `font-family:Georgia,'Times New Roman',serif` | `FONT_SERIF` / `var(--font-serif)` |
| Fakturakontroll | `1_Fakturakontroll.py:91` | `color:#5A6673` | `MUTED` |
| Fakturakontroll | `1_Fakturakontroll.py:105` | `#B58900`, `#FBF7EC` | BRAND.md exempt (warn) |
| Avtaler | `2_Avtaler_og_forpliktelser.py:93` | `st.subheader(...)` | → `section_header()` |
| Avtaler | `2_Avtaler_og_forpliktelser.py:110` | `st.subheader(...)` | → `section_header()` |
| Leverandører | `3_Leverandorer.py:229` | `st.subheader(...)` | → `section_header()` |
| Leverandører | `3_Leverandorer.py:238` | `#2E7D32`, `#C62828`, `#6B7280` | BRAND.md exempt / MUTED |
| Leverandører | `3_Leverandorer.py:242,244` | `#F1F3F5`, `#6B7280` | `LINE`, `MUTED` |
| Leverandører | `3_Leverandorer.py:373-374` | `#FCFBF7`, `#E4E1D8`, `#1C2733` | BG, LINE, INK |
| Leverandører | `3_Leverandorer.py:495` | `#C62828`, `#2E7D32` | BRAND.md exempt |
| Leverandører | `3_Leverandorer.py:505` | `#8A94A0` | MUTED (variant) |
| Leverandører | `3_Leverandorer.py:608,638-640` | `#2E7D32`, `#B58900`, `#C62828` | BRAND.md exempt |
| Leverandører | `3_Leverandorer.py:651-652` | `#FCFBF7`, `#E4E1D8`, `#1C2733` | BG, LINE, INK |
| Leverandører | `3_Leverandorer.py:671` | `#F1F3F5`, `#6B7280` | LINE, MUTED |
| Terskelsjekk | `4_Terskelsjekk.py:60,78,87` | `#8A94A0` | `MUTED` |
| Terskelsjekk | `4_Terskelsjekk.py:90` | `#B58900` | BRAND.md exempt (warn) |
| Styringsinformasjon | `5_Styringsinformasjon.py:81-87` | `#E4D9B8`, `#FBF7EC`, `#8A7A3A`, `#B58900`, `#8A94A0` | LINE, WARN_BG, MUTED, BRAND |
| Styringsinformasjon | `5_Styringsinformasjon.py:133` | `["#2E7D32","#B58900","#C62828"]` Altair | BRAND exempt + Altair literal |
| Styringsinformasjon | `5_Styringsinformasjon.py:144,157` | `st.subheader(...)` | → `section_header()` |
| Plattformen | `6_Plattformen.py:14-16` | `"#2E7D32"`, `"#B58900"`, `"#6B7280"` | BRAND exempt / MUTED |
| Arbeidsliste | `8_Arbeidsliste.py:27-36` | status-farger inkl. `#5A6673`, `#FCF4DE` | MUTED, WARN_BG |
| Arbeidsliste | `8_Arbeidsliste.py:132` | `#5A6673` | MUTED |
| Arbeidsliste | `8_Arbeidsliste.py:142-163` | `#E4E1D8`, `#5A6673` | LINE, MUTED |
| ui_faktura | `ui_faktura.py:23-25` | `"#2E7D32"`, `"#B58900"`, `"#C62828"` | BRAND exempt |
| ui_faktura | `ui_faktura.py:51-52,78,161,164-165` | `#FCFBF7`, `#E4E1D8`, `#5A6673`, `#20364F` | BG, LINE, MUTED, NAVY |
| ui_forpliktelser | `ui_forpliktelser.py:13` | `GOLD = "#B08D2E"` | ✅ Allerede korrekt token |
| ui_forpliktelser | `ui_forpliktelser.py:17-31,104` | BRAND+gyldighet-farger | BRAND exempt / MUTED |
| ui_kontrakt | `ui_kontrakt.py:47,68,126,205` | `#2E7D32`, `#6B7280`, `#B58900`, `#5A6673` | BRAND exempt / MUTED |

---

## Prioritert gjøremål (G1–G5)

**Frist G1–G5:** Erstatt alle **ikke-exempt** verdier med CSS-variable-referanser
(`var(--navy)`, `var(--muted)`, osv.) eller Python-konstanter fra `theme.py`.

**Phase 2 (utenfor scope):** `ui_faktura.py`, `ui_forpliktelser.py`, `ui_kontrakt.py` —
delte hjelpere med kompleks fargelogikk. Dokumentert her; konverteres når de berøres.

---

*Generert av Claude Code — 2026-08-09*
