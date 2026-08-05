# Anskaffelsessjekk — Brief "Vei B Steg 2: Komplett frontend + API"

**Partner directive · 2026-08-04. Save as docs/BRIEF_VEIB_STEG2.md. Execute in order A→Z.
Commit+push after each lettered section. Live URL: https://anskaffelsessjekk.netlify.app
API URL: https://anskaffelsessjekk.onrender.com**

## Kontekst
Steg 1 ga fungerende stack (Next.js + FastAPI) men: (1) design er ikke som godkjent makkett,
(2) API mangler alle skrive-endepunkter (POST/PUT/DELETE), (3) frontend mangler alle funksjoner
fra Streamlit. Dette briefen fikser ALT på én gang. Eier verifiserer på live URL etter hver push.

---

## SEKSJON A — Design fix (FØRST — eier ser dette umiddelbart)

**A1 — web/src/app/layout.tsx:** Importer Fraunces fra Google Fonts (next/font/google):
```tsx
import { Fraunces, Inter } from 'next/font/google'
const fraunces = Fraunces({ subsets: ['latin'], variable: '--font-fraunces' })
const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
// bruk begge i body className
```

**A2 — web/src/app/globals.css** — korrekte tokens fra godkjent design:
```css
@theme inline {
  --color-navy: #16233B;
  --color-copper: #C56B3E;
  --color-paper: #F7F5F0;
  --color-card: #FFFFFF;
  --color-line: #E8E4DB;
  --color-ink: #16233B;
  --color-muted: #8A93A3;
  --font-serif: var(--font-fraunces), Georgia, serif;
  --font-sans: var(--font-inter), system-ui, sans-serif;
  /* status */
  --color-avvik: #B23A1E; --color-avvik-bg: #F6E4DE;
  --color-vurdering: #9A7B1E; --color-vurdering-bg: #F5EDD8;
  --color-samsvar: #2F7D4F; --color-samsvar-bg: #EAF3ED;
}
body { background: var(--color-paper); font-family: var(--font-sans); }
```

**A3 — web/src/components/Header.tsx** — Fiori shell bar:
```tsx
<header className="bg-navy border-b-2 border-copper">
  <div className="max-w-7xl mx-auto px-6 h-[52px] flex items-center justify-between">
    <div className="flex items-center gap-3">
      <div className="w-[26px] h-[26px] border-2 border-copper rounded-[7px] flex items-center
                      justify-center text-copper text-xs font-bold">✓</div>
      <span className="text-white font-serif text-[17px] font-semibold">Anskaffelsessjekk</span>
    </div>
    <nav className="flex gap-1">
      {/* Oversikt / Fakturaer / Leverandører / Avtaler / Terskelsjekk — same as before */}
    </nav>
  </div>
</header>
```

**A4 — web/src/app/page.tsx** — Fiori launchpad layout:
Erstatt eksisterende innhold med:
1. Page header (eyebrow KONTROLLOVERSIKT copper, H1 font-serif Arbeidsflate, lede-tekst, chip)
2. Seksjon "HANDLINGER" (eyebrow) → ActionTiles-komponent (5 kafler, se A5)
3. Seksjon "NØKKELTALL" (eyebrow + periode-velger Måned/Kvartal/År) → KpiStrip som ett panel
   med vertikale hairlines mellom celler (ikke separate kort)
4. Porteføljehelse-bar
5. Seksjon "KREVER HANDLING" → UrgentList tabell

**A5 — web/src/components/ActionTiles.tsx** (ny):
5 kafler i grid (grid-cols-5), hver: icon-boks (34px, rounded-[10px]), tittel font-bold, desc text-muted.
Kafel 1 (Kontroller faktura): icon bg-copper. Resten: icon bg-navy.
Alle kafler: bg-white border border-line rounded-[12px] p-4 hover:border-copper transition.

---

## SEKSJON B — API: alle skrive-endepunkter

Legg til i api/main.py (bruk core/registry/ — eksisterende CRUD-funksjoner, ALDRI skriv logikk direkte i API):

**B1 — Leverandør CRUD:**
```python
POST   /api/suppliers              # opprett (navn, org_nr, adresse, epost, tlf, kategorier)
PUT    /api/suppliers/{id}         # oppdater grunndata
DELETE /api/suppliers/{id}         # soft-delete (is_deleted=True)
POST   /api/suppliers/{id}/contacts      # legg til kontaktperson
PUT    /api/suppliers/{id}/contacts/{cid} # rediger kontakt
DELETE /api/suppliers/{id}/contacts/{cid} # slett kontakt
POST   /api/suppliers/{id}/notes         # nytt notat
POST   /api/suppliers/{id}/services      # ny tjeneste/produkt
DELETE /api/suppliers/{id}/services/{sid}
POST   /api/suppliers/{id}/qualifications      # ny kvalifikasjon (navn, gyldig_til)
DELETE /api/suppliers/{id}/qualifications/{qid}
```

**B2 — Kontrakt CRUD:**
```python
POST   /api/contracts                    # opprett (leverandor_id, tittel, type, regime, periode, ramme, endringsklausul)
PUT    /api/contracts/{id}
DELETE /api/contracts/{id}               # soft-delete
POST   /api/contracts/{id}/lines        # legg til prislinje (artikkelnr, pris, enhet, maks_mengde)
PUT    /api/contracts/{id}/lines/{lid}
DELETE /api/contracts/{id}/lines/{lid}
GET    /api/contracts                    # liste (med leverandor_id filter)
GET    /api/contracts/{id}              # detalj med prislinjer
```

**B3 — Forpliktelse CRUD:**
```python
POST   /api/forpliktelser               # opprett (leverandor_ids[], condition_type, verdi, enhet,
                                        #          gyldig_fra, gyldig_til, kilde, source_ref,
                                        #          formalisering, avtale_id optional)
PUT    /api/forpliktelser/{id}
DELETE /api/forpliktelser/{id}
GET    /api/forpliktelser?leverandor_id=  # per leverandør
```

**B4 — Faktura mottak:**
```python
POST   /api/invoices/upload/ehf         # multipart EHF-fil → parse → returner utkast (ikke lagre)
POST   /api/invoices/upload/csv         # multipart CSV → parse → returner liste av utkast
POST   /api/invoices/confirm            # bekreft utkast → lagre + kontroller → returner verdikt
POST   /api/invoices/{id}/decision      # godkjenn/avvis/vent (action, note)
```

**B5 — Terskelsjekk:**
```python
POST   /api/terskelsjekk               # {verdi, oppdragsgiver, kontrakttype, dato} → {regime, terskel, prosedyre, citation}
```

**B6 — Stats med periode:**
```python
# Oppdater GET /api/stats til å ta ?periode=maned|kvartal|ar&fra=&til=
# Filtrer fakturaer på check_invoice dato innenfor perioden
```

---

## SEKSJON C — Frontend: alle manglende sider og funksjoner

**C1 — Leverandørkort med full CRUD** (web/src/app/leverandorer/[id]/page.tsx):
Utvid eksisterende les-visning med tabs (7 faner som i Streamlit):
- Oversikt: grunndata + nøkkeltall
- Firmadata: rediger-skjema (navn, org.nr, adresse, epost, tlf, kategorier, status)
- Kategorier og tjenester: tag-chips + tjeneste-liste med add/slett
- Kvalifikasjoner: liste + legg til (navn + valgfri gyldig_til) + utløpt rødt
- Personer: to grupper (leverandør/oss) full CRUD
- Avtaler/Forpliktelser/Fakturaer: lister med Åpne-lenker + [+ Ny]-knapper
- Vurdering og notater: auto-stats + fritekst-vurdering

Bruk `fetch` mot nye API-endepunkter fra B1.

**C2 — Ny leverandør** (web/src/app/leverandorer/ny/page.tsx):
Skjema: navn (påkrevd), org.nr (9 siffer), adresse, epost, tlf, kategorier.
POST til /api/suppliers → redirect til /leverandorer/{id}.

**C3 — Avtaler** (web/src/app/avtaler/page.tsx + [id]/page.tsx):
- Liste over alle kontrakter med leverandør, type, periode, status
- Opprett ny avtale: skjema → POST /api/contracts
- Avtaledetalj: grunndata + prisliste (add/rediger/slett linjer) + forpliktelser

**C4 — Forpliktelser ved leverandør** (del av C1 fane):
[+ Legg til forpliktelse] → modal/skjema: kilde-valg (manuell/epost/møte),
condition_type, item_ref (dropdown fra avtalens prislinjer), verdi, enhet, gyldig fra-til,
formalisering. POST /api/forpliktelser. Vises på kartoteket til alle berørte leverandører.

**C5 — Faktura mottak** (web/src/app/faktura/ny/page.tsx):
Faner: EHF (fil-upload) / CSV batch (fil-upload) / PDF (fil-upload, «OCR — bekreftelsesskjerm»).
EHF/CSV: POST til /api/invoices/upload/ehf eller /csv → vis sparsede felt →
[Bekreft og kontroller] → POST /api/invoices/confirm → redirect til /faktura/{id}.

**C6 — Fakturaworklist** (web/src/app/faktura/page.tsx — utvid):
Kompakt HTML-tabell (ikke store blokker), paginasjon 25/side, filter (verdikt/status/leverandør/søk),
sortering (avvik øverst default). «Se alle (N) →»-knapp fra landing.

**C7 — Terskelsjekk** (web/src/app/terskelsjekk/page.tsx):
Skjema: verdi (NOK), oppdragsgiver (statlig/kommune/helseforetak/forsvar), kontrakttype, dato.
POST /api/terskelsjekk → vis resultat: regime, terskel, prosedyre, citation med lenke til kilde.

---

## SEKSJON D — Navigasjon og polish

**D1** — Legg til alle sider i Header nav: Oversikt / Fakturaer / Leverandører / Avtaler / Terskelsjekk
**D2** — Alle skjemaer: navngitte lagre-knapper + toast-bekreftelse etter lagring (react-hot-toast eller lignende)
**D3** — Tomme tilstander: vennlig tekst + call-to-action på alle lister
**D4** — Responsivt: tabs wrapper på mobil, tabeller scrollable, ingen crush

---

## DoD

- Alle sider bygger uten TS-feil (`next build` clean)
- Alle API-endepunkter svarer (pytest på api/ med TestClient)
- Live på https://anskaffelsessjekk.netlify.app — eier verifiserer HVER seksjon
- Design matcher landing_hybrid.png (navy #16233B, copper #C56B3E, Fraunces serif, paper bg)
- Streamlit forblir uendret og fungerende parallelt
- CLAUDE.md + STATUS.md oppdatert, push til origin/main
