# Brief — Funksjon 3.5: OCR A–Z (O1–O7)

> **Merk om denne filen:** partnerens brief-tekst kom ikke gjennom i meldingen — bare kjernen
> (sedno). O1–O7 under er utledet av den kjernen av implementasjonsagenten og skal leses som et
> forslag partneren kan korrigere. Kjernen selv er gjengitt ordrett og er ufravikelig.

## Kjernen (ordrett fra partneren) — kritisk for produktsikkerheten

> OCR czyta → pokazuje co odczytał → Ty potwierdzasz/poprawiasz → DOPIERO potem weryfikacja.
> Skan nigdy nie idzie prosto do kontroli. To chroni przed halucynacją OCR w pieniądzach
> (11 800 odczytane jako 1 180 dałoby zły werdykt). Ekran potwierdzenia (O3) to serce tej
> funkcji — pokazuje „tak to odczytałem", Ty poprawiasz liczby, zatwierdzasz, i wtedy leci
> kontrola przez ten sam łańcuch co EHF/CSV.

Oversatt til prosjektets språk: **et skannet dokument er ALDRI et kontrollgrunnlag i seg selv.**
OCR er en LESEHJELP, ikke en kilde til sannhet. Uttrekket er et FORSLAG (som e-postuttrekket i
Funksjon 4) og deltar først i kontroll etter at et menneske har bekreftet tallene — samme
human-in-the-loop-port som hard rule #3.

## Stegene

**O1 — OCR-motor (adapter).** `core/extraction/ocr.py`: dokument (bytes) → råtekst.
- PDF med tekstlag → `pypdf` (ren Python, ingen systembinær; virker på Streamlit Cloud).
- Bilde (JPG/PNG) / skannet PDF → `pytesseract` KUN når tesseract-binæren finnes.
- Mangler motoren: ÆRLIG degradering med en tydelig melding — aldri gjetting, aldri krasj.
- Nye avhengigheter i BÅDE `pyproject.toml` og `requirements.txt` (+ `packages.txt` for Cloud).

**O2 — Feltuttrekk med konfidens.** `parse_scanned_invoice(text)` → `ProposedInvoice`:
fakturanr, dato, org.nr, beløp, linjer — hvert felt med **konfidens** (HØY/LAV) og **kildelinjen**
verdien ble lest fra. Helt ren funksjon (ingen binær) → fullt enhetstestbar.

**O3 — Bekreftelsesskjermen (HJERTET).** «Slik leste vi fakturaen»:
- hvert felt redigerbart, lav konfidens merket tydelig,
- **summekontroll**: Σ(antall × pris) mot avlest totalbeløp — fanger nettopp 11 800 → 1 180,
- råtekst tilgjengelig for kontroll mot originalen,
- ingenting går videre uten et eksplisitt «Bekreft og kontroller».

**O4 — Samme kjede etter bekreftelse.** Bekreftede felt → `intake_invoice` → `prisliste.verify`
→ verdikt m/ HVORFOR → beslutning → protokoll. INGEN ny verifikasjonsvei (ADDITIV, reconciliation
22 310 kr urørt).

**O5 — Sporbarhet.** Import fra skann skriver en AuditLog-rad som sier at kilden var OCR, hvilken
motor som leste, og at et menneske bekreftet — inkl. hvilke felt mennesket RETTET (hard rule #7).

**O6 — Ærlige grenser.** Syntetisk eksempel-PDF, fast disclaimer («OCR er en lesehjelp — kontroller
alltid beløpene mot originalen»), tydelig melding når bildemotoren ikke er tilgjengelig.

**O7 — Wrap-up.** Tester (uttrekk + konfidens + summekontroll + «skann når aldri kontroll uten
bekreftelse»), versjonsbump + rebuild-marker, CI package-guard, CLAUDE.md + STATUS, DoD, push.

## Rammer (uendret)
- Hard rules gjelder (core/ importerer ingen UI; menneske bekrefter — hard rule #3; audit
  append-only; html.escape() på all unsafe_allow_html; full-tool A→Z hard rule #12).
- Reconciliation **22 310 kr** skal være uendret.
- Tester må være grønne UTEN systembinærer (CI har ikke tesseract) → uttrekkslaget er rent.
