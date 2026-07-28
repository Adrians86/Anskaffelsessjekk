# Anskaffelsessjekk — Mini-brief "Funksjon 1: Leverandør A–Z"

Partner directive · 2026-07-28. The FIRST function built as a full TOOL, not a view. Partner-
approved core-data-model change (new contact entity, notes, soft-delete) — this brief is the
approval required by the scope freeze. All UI Norwegian (bokmål).

## Bakgrunn (hvorfor)
Til nå har sider vært VISNINGER (les-only). Leverandør blir første funksjon som er komplett fra
A til Å: legg til → se → rediger → slett → bruk. Dette er første konkrete bevis på at produktet
tar et steg framover, ikke til siden. Etter denne sesjonen kan Adrian legge til en leverandør,
skrive inn en kontaktperson, føre en uavtale — og det blir stående (i kjørende demo-session).

## Ny hard regel til kontrakten (hard rule #12)
**Ingen funksjon er DONE før den er komplett fra A til Å — legg til → se → rediger → slett → bruk.**
En les-only «visning» er ikke en ferdig funksjon. Dette opphever tidligere «en visning holder» og
skal gjelde alle framtidige funksjoner.

## L1 — Leverandørliste + [＋ Ny leverandør]
Liste over leverandører, og en «＋ Ny leverandør»-form der du kan opprette en leverandør fra bunn
(org.nr unik + navn påkrevd, kategorier, notat). Lagring → leverandøren finnes i registeret.

## L2 — [Rediger] på firmadata
Rediger navn, org.nr, kategorier, ISO/sikkerhet på en eksisterende leverandør. Lagring skriver
endringen og en audit-rad.

## L3 — Kontaktpersoner (full CRUD)
Legg til / rediger / slett kontaktpersoner (navn, rolle, e-post, telefon) på en leverandør. Dette
er nettopp «hvor legger jeg inn en kontakt» — nå finnes stedet.

## L4 — Notater + redigerbare kvalifikasjoner
Fritt notatfelt (notater) og redigerbare kategorier/kvalifikasjoner på leverandøren. Nettopp
«uttalelsene/uwagi» det ble spurt om. (Den syntetiske profilen med gyldighetsdatoer/UTLØPT
beholdes som les-only demo-innsikt ved siden av.)

## L5 — Slett leverandør (myk sletting, med spor)
Myk sletting: leverandøren merkes slettet (is_deleted) — raden og sporet beholdes, audit-rad
skrives. Listen skjuler slettede som standard, med «Vis slettede» + gjenopprett.

## L6 — Kartotek (alt om leverandøren på ett sted)
Leverandørkortet samler avtaler, ustalinger/forpliktelser og fakturaer på ett sted, med «Kommer»-
knapper som markerer hvor de neste funksjonene kobles på (ærlige roadmap-markører, ingen falsk knapp).

## L7 — Tester + audit
CRUD-tester (opprett/rediger/slett leverandør + kontakt), og HVER lagring skriver en rad i det
append-only revisjonssporet (hard rule #7).

## Arkitektur (innenfor kontrakten)
- Persistens/logikk i `core/registry/leverandor.py` — ren, tar en Session, importerer INGEN UI
  (hard rule #1). UI (app/pages/3_Leverandorer.py) kaller disse funksjonene.
- Nye/endrede modeller: `Supplier.notes`, `Supplier.is_deleted`, ny `ContactPerson` — derfor
  versjonsbump (0.5.0 → 0.6.0) + requirements.txt rebuild-marker (hard rule #10).
- Data er fortsatt syntetisk og tydelig merket (hard rule #6). Alle interpolerte verdier i
  unsafe_allow_html er html.escape()-d (hard rule #11).
- SQLite in-memory beholdes (StaticPool, én motor per prosess): lagringer varer for kjørende
  demo-session. Durabel disk-persistens = utenfor scope (ingen DB-migrasjon, scope freeze).

## Utenfor scope (ikke bygget nå)
De neste funksjonene bak «Kommer»-knappene (registrer avtale/ustaling/faktura fra kartoteket).
Ingen ny UI-ramme, ingen auth.

## DoD (per steg)
pytest grønt, ruff rent, alle 8 sider åpner, hver lagring → audit-rad. Commit+push per steg
(L1→L7). Versjonsbump + requirements-marker (L1). CLAUDE.md hard rule #12 + Current tasks + STATUS.
