# Anskaffelsessjekk — Mini-brief "Leverandør v2: full kartotek (10 elementer)"

Partner directive · 2026-07-29. Answers the honest complaint on Leverandør A–Z: "I can only edit
name and org.nr — that's a joke." v2 makes the kartotek a real, complete supplier record. Partner-
approved core-data-model change (new fields + Service/Qualification entities + contact grouping);
this brief is the approval required by the scope freeze. Full-tool rule (#12) applies to every part.
All UI Norwegian (bokmål).

## K1 — «Rediger firmadata» dekker ALT
Firma-skjemaet redigerer hele firmakortet, ikke to felt: adresse, postnr/sted, nettside, e-post,
telefon, kategorier, status (Aktiv/Inaktiv/Sperret) — pluss navn/org.nr/ISO/sikkerhet. Én lagring,
én audit-rad.

## K2 — Kategorier (hva leverandøren leverer) — legg til / fjern
Kategorier forvaltes som tagger: legg til og fjern enkeltkategorier (ikke ett fritekstfelt).

## K3 — Tjenester/produkter — full CRUD
Egen katalog av tjenester/produkter per leverandør (navn, beskrivelse, enhet, pris) med
legg til → rediger → slett.

## K4 — Kvalifikasjoner («oba»): enkel avkryssing + valgfrie gyldighetsdatoer
Kvalifikasjon = navn + valgfri «gyldig til»-dato. Uten dato: bare et hak (gjelder). Med dato:
utløpte vises i rødt (UTLØPT). Legg til / rediger / slett.

## K5 — Personer i to grupper
Kontaktpersoner deles i to: **kontakt hos leverandøren** og **ansvarlig hos oss** (intern). Samme
CRUD, gruppert visning.

## K6 — Lister: avtaler / ustalinger / fakturaer
Kartoteket samler avtaler, forpliktelser og fakturaer, med ærlige «Kommer»-knapper der de neste
funksjonene kobles på (ingen falsk knapp).

## K7 — Statistikk («oba»): auto fra fakturaer + egen samarbeidsvurdering
Auto-tall fra fakturakontrollen (andel m/funn, First Time Right) BEHOLDES, pluss et eget
fritekstfelt «samarbeidsvurdering» du kan skrive selv. HARD KOFA-annotasjon beholdes: innsikt i
samarbeidet, IKKE en kvalifikasjonsrangering.

## K8 — Tester, audit, versjon 0.7.0
CRUD-tester for de nye entitetene; HVER lagring → audit-rad (hard rule #7). Versjonsbump
0.6.1 → 0.7.0 + requirements rebuild-marker (hard rule #10).

## Arkitektur (innenfor kontrakten)
- All persistens/logikk i `core/registry/leverandor.py` — ren, tar en Session, importerer INGEN UI
  (hard rule #1). Nye modeller: `SupplierService`, `Qualification`; nye Supplier-felt (adresse,
  postnr, sted, nettside, e-post, telefon, status, samarbeidsvurdering); `ContactPerson.side`.
- Data syntetisk og tydelig merket (hard rule #6); alle interpolerte HTML-verdier html.escape()-d
  (hard rule #11). In-memory SQLite beholdes (saves varer for demo-session).

## Utenfor scope (ikke bygget nå)
Funksjonene bak «Kommer» (registrer avtale/forpliktelse/faktura). Ingen ny UI-ramme, ingen auth,
ingen durabel disk-DB.

## DoD (per steg)
pytest grønt, ruff rent, alle 8 sider åpner, hver lagring → audit-rad, reconciliation 22 310.
Commit+push per steg (K1→K8). Versjonsbump 0.7.0 + marker. CLAUDE.md Current tasks + STATUS.
