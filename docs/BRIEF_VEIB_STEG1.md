# Brief — Droga B Steg 1: Pionowy plasterek Next.js + FastAPI

**Strategia:** Jeden pionowy plasterek przez cały stos — landing + lista dostawców + karta
werdyktu, ciągnące prawdziwe dane z silnika Python przez API. Gdy to zadziała, wiemy że
architektura stoi, i przepisujemy resztę ekran po ekranie z pewnością.

**Kluczowa zasada:** Streamlit zostaje żywy i niezmieniony. Python engine (core/) niezmieniony —
„prime directive" się spłaca. To jest ADDYTYWNE, nie destrukcyjne.

## Steg

### B1 — FastAPI wrapper wokół silnika Python
- `api/main.py` — FastAPI app opakowujący core/ (evaluate_invoice, suppliers, contracts, invoices).
- Endpointy: `/api/stats` (KPI + porteføljehelse), `/api/invoices` (lista z verdikt/status),
  `/api/invoices/{id}` (szczegóły + findings z WHY), `/api/suppliers` (lista),
  `/api/suppliers/{id}` (karta).
- core/ NIE zmieniony — FastAPI to cienka warstwa HTTP nad istniejącymi funkcjami.
- Dodanie `fastapi` + `uvicorn` do pyproject.toml (optional dep `[api]`).

### B2 — Szkielet Next.js na Netlify
- `web/` — Next.js app z design systemem (navy #20364F, miedź/złoto #A8842A, serif Georgia).
- Tailwind CSS z tokenami projektu. Responsywny od startu.
- `netlify.toml` w root + `web/netlify.toml`.
- Layout shell (header, nav, footer) w designie „Presisjon × Fiori".

### B3 — Landing page z prawdziwymi danymi
- Nøkkeltall (KPI strip) z selektorem okresu: Måned / Kvartal / År.
- Porteføljehelse bar.
- Top 5 presserende (avvik først).
- Dane z `/api/stats` i `/api/invoices`.

### B4 — Lista dostawców + kartoteka (odczyt)
- Strona `/leverandorer` — kompaktowa lista z szukajką.
- Karta dostawcy z podstawowymi danymi (firma, kontakty, avtaler, fakturaer).
- Dane z `/api/suppliers` i `/api/suppliers/{id}`.

### B6 — Pełny łańcuch odczytu
- Landing → KPI za okres → worklist → faktura → werdykt z DLACZEGO.
- Każdy krok ciągnie dane z API, prezentuje w nowym designie.

### B7 — Testy + wrap-up
- API: pytest testy endpointów FastAPI (httpx TestClient).
- Web: build check (next build).
- STATUS.md + CLAUDE.md.
