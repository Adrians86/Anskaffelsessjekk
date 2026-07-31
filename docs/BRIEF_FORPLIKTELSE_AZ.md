# Brief — Funksjon 4: Forpliktelse A–Z (P1–P8)

Siste av serien «2, 3, 4». Forpliktelser (avtaler utenfor formell kontrakt — e-postavtaler, møter,
aneks) blir et fullt verktøy (add → view → edit → delete → use) forankret PÅ leverandøren, ikke i en
løsrevet fane. Modellen er den vi ble enige om.

## Hva Funksjon 4 gjør (ustalenia)

**P1 — Legg til forpliktelse ved leverandøren** (ikke i en løsrevet fane). Flere veier:
manuelt / **lim inn e-post som snarvei som fyller skjemaet** / møte / aneks. Innliming = bekvemmelighet,
ikke krav — fikser «fortsatt manuelt».

**P2 — Én eller flere leverandører** (standard: én, valg for flere).

**P3 — Gyldighetsvurdering som indikasjon** (SANNSYNLIGVIS GYLDIG / KREVER FORMALISERING /
MULIG UGYLDIG) med disclaimer, bruker **endringsklausulen fra avtalen**. Ikke en juridisk konklusjon
(FOA §28-1, vesentlig endring er skjønn — jf. tidligere «indikasjon, ikke konklusjon»-linje).

**P4 — Felles vilkår eller ulikt per leverandør** («ulikt bæres» — different per supplier).

**P5 — Full CRUD** (rediger / slett).

**P6 — Forpliktelse brukt i verifikasjon**: en faktura som passer et **bekreftet** e-postforpliktelse →
verdikt gjenspeiler det med sitat.

**P7 — Fjern den gamle løsrevne fanen «Registrer fra e-post»** (funksjonen bor nå på leverandøren).

**P8 — Wrap-up**: tester, versjonsbump + rebuild-marker, CLAUDE.md + STATUS, DoD, push.

## Rammer (uendret)
- Hard rules gjelder (core/ importerer ingen UI; menneske bekrefter — hard rule #3; audit append-only;
  html.escape() på all unsafe_allow_html; full-tool A→Z hard rule #12).
- Reconciliation **22 310 kr** skal være uendret.
- Ubekreftede LLM/regex-uttrekk deltar aldri i kontroll — kun etter menneskelig «Bekreft».
