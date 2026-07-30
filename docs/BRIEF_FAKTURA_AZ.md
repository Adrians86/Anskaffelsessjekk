# Anskaffelsessjekk — Brief "Funksjon 3: Faktura A–Z (inntak + verifikasjon end-to-end)"

Domyka pierwszy pełny łańcuch: leverandør (F1) + kontrakt/prisliste (F2) → **faktura kontrolleres mot
avtalt prisliste**. Full A–Z (hard rule #12). Hver skriv → AuditLog (#7), les → ingen skriv (H1),
html.escape() (#11), schema-endring → bump (#10). Reconciliation 22 310 kr skal fortsatt stemme.

## N1 — Inntaksskjerm
Fakturakontroll får inntak: **enkeltvis (EHF)** + **partia (CSV / flere filer)**. PDF/JPG vises, men
ærlig «Kommer (OCR)» (bølge 2). EHF-enkeltopplasting beholdes.

## N2 — CSV-parser for partia
`core/extraction/csv_faktura.py`: parse en CSV med flere fakturaer (rader grupperes til fakturaer på
fakturanr). Kolonner: fakturanr, dato, orgnr, artikkelnr, beskrivelse, antall, pris. Returnerer
ParsedInvoice-objekter (samme som EHF).

## N3 — Kobling faktura → leverandør (F1) → avtale + prisliste (F2)
Vis eksplisitt: «Denne fakturaen kontrolleres MOT avtale RA-x, prisliste N linjer.» Kontrakt løses
via order.contract_id når satt, ellers via leverandørens aktive avtale.

## N4 — Verdikt med HVORFOR (nordstjernen)
Ikke bare «avvik», men «avvik FORDI pris 550 > avtalt 500 (artikkel ART-123, avtale RA-x)». Funn mot
prisliste: pris over avtalt, mengde over maks, artikkel uten prislinje. Serce produktu.

## N5 — Batch-resultatliste (worklist-frø)
Liste over resultater i partiet, **avvik øverst**, med verdikt-pille + verdi funnet.

## N6 — Menneskets beslutning (informerer, blokkerer ikke)
Godkjenn / avvis / vent med begrunnelse → `InvoiceDecision` (append-only) + AuditLog. Systemet
anbefaler, mennesket bestemmer (hard rule #3).

## N7 — Protokoll + kobling tilbake
Protokoll PDF per faktura (finnes: build_protokoll). Fakturaen vises på avtalens «koblede fakturaer»
og i leverandørkortet.

## N8 — Wrap-up
Tester (tests/test_faktura_az.py): CSV-parse · prisliste-verifikasjon HVORFOR · beslutning=1 AuditLog ·
les=0 · reconciliation uendret. pytest grønt, ruff rent, CI-guard (faktura-moduler i wheel).
Bump 0.8.0→0.9.0 + rebuild-marker. CLAUDE.md + STATUS + push.

## Arkitektur / grenser
Ny prisliste-verifikasjon `core/matching/prisliste.py` er ADDITIV — rører IKKE eksisterende
three_way/commitments-matcher, så demo-reconciliation (22 310) er urørt. Beslutning i ny modell
`InvoiceDecision`; helpere i core (ingen UI-import, #1). Utenfor scope: OCR (PDF/JPG), F4 forpliktelser.
