# Anskaffelsessjekk — Brief "Funksjon 2: Kontrakt + prisliste A–Z"

Basert på FUNKSJONSANALYSE + HIERARKI: kontrakt+prisliste er GRUNNLAG #2 for verifikasjon (etter
leverandør). Uten prisliste har kontrollen ingenting å sammenligne fakturapriser MOT. Full A–Z
(hard rule #12). Partner-godkjent core-datamodell-endring. All UI norsk (bokmål).

Mål: bruker kan opprette, redigere og administrere avtaler (rammeavtale/enkeltkjøp) MED prisliste,
knyttet til en leverandør. Prislisten er det verifikasjonen sjekker fakturalinjer mot. Hver skriv →
AuditLog (#7), les → ingen skriv (H1), html.escape() (#11), schema-endring → bump (#10).

## Datamodell (utvider eksisterende Contract/ContractLine)
- **Kontrakt**: id, supplier_id (FK), title (tittel), reference (avtalenr), contract_type
  (rammeavtale/enkeltkjøp), **regime (FOA/FOSA)**, valid_from/valid_to (periode), total_value (ramme,
  Decimal|None), **change_clause (endringsklausul: kun_skriftlig_tillegg / mindre_justering_epost /
  kpi_regulering / annet)**, **status (aktiv/utløpt/utkast)**, **is_deleted (soft delete)**, created_at.
- **Kontraktslinje**: id, contract_id (FK), item_ref (artikkelnr), description, unit (stk/time/mnd),
  unit_price (pris, Decimal), max_quantity (Decimal|None), **currency (default NOK)**.
- CRUD i ren `core/registry/kontrakt.py` (ingen UI-import, hard rule #1).

## M1 — Kontraktsliste + opprett
Leverandørkort fane «Avtaler»: aktiver «＋ Ny avtale» (var «Kommer») → popover-skjema. Avtaler-siden:
liste over alle kontrakter (tittel, leverandør, type, periode, ramme, status-badge) + søk + «＋ Ny
avtale». Opprett-skjema (U3-mønster): leverandør (dropdown), tittel, avtalenr, type, regime, periode
fra–til, ramme, endringsklausul. Lagre → AuditLog «avtale opprettet».

## M2 — Prisliste (kontraktslinjer) full CRUD — KJERNEN
Kontraktvisning: tabell over prislinjer. «＋ Legg til linje» → artikkelnr, beskrivelse, enhet, pris,
maks mengde, valuta. Rediger/slett hver linje. Dette ER grunnlaget verifikasjonen bruker. Tom
tilstand: «Ingen prislinjer ennå — legg til den første for å kunne kontrollere fakturaer mot denne
avtalen.»

## M3 — Kontraktvisning + rediger/slett avtale
Pen visning: grunndata + prisliste + koblede fakturaer (les, kommer i F3). «Rediger avtale» (popover,
forhåndsutfylt) / «Slett avtale» (soft-delete, bekreftelse, advarsel om koblede fakturaer). Datoer
DD.MM.ÅÅÅÅ, beløp tabular-nums.

## M4 — Endringsklausul tilgjengelig for vurdering
endringsklausul lesbart for forpliktelse-/verifikasjonslogikk senere (kun_skriftlig_tillegg →
«krever formalisering»; mindre_justering_epost → kan være gyldig). Nå: lagre + vis + gjør
tilgjengelig for motoren (les-helper). INGEN ny verifikasjonslogikk her.

## M5 — Koble til leverandørkort
Leverandørkort fane «Avtaler»: vis leverandørens avtaler som liste med «Åpne» → kontraktvisning.
Koble tellingen i kartotek-oversikten reelt.

## M6 — Seed + demo
Berik seed: hver demo-leverandør har avtaler med prislinjer (Hydraulikk: deler m/artikkelnr/pris;
Konsulenthuset: timepriser). Disse er grunnlaget de eksisterende demo-fakturaene kontrolleres mot —
reconciliation (22 310 kr) skal fortsatt stemme (fakturaene matcher EKSPLISITTE prislinjer).

## M7 — Wrap-up
Tester (tests/test_kontrakt_crud.py): opprett avtale · legg til/rediger/slett prislinje · rediger/
soft-delete avtale · hver skriv = 1 AuditLog · les = 0 · reconciliation uendret. pytest grønt, ruff
rent, CI grønn (package-guard: kontrakt-moduler i wheel). Bump 0.7.0→0.8.0 + rebuild-marker.
CLAUDE.md Current tasks + STATUS + push.

## Utenfor scope (F3/F4)
Faktura-inntak/verifikasjon = F3. Forpliktelser = F4. Her KUN kontrakt + prisliste komplett A–Z.
