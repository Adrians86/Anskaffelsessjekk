# Anskaffelsessjekk — Technical Architecture (v1.0)

**AS North Advisory · 2026-07-07 · lives in the repo as `docs/ARCHITECTURE.md`**

Language convention: code, comments and technical docs in **English**; user-facing UI, reports and README in **Norwegian (bokmål)**; Norwegian domain terms (`rammeavtale`, `avrop`, `mottak`, `terskel`) are kept untranslated in code — the code speaks the language of the domain.

---

## 1. Technology decisions (and why)

| Layer | MVP (now) | Phase 2+ (commercial) | Rationale |
|---|---|---|---|
| Language | **Python 3.11+** | Python (core unchanged) | Maintainer's DS curriculum language; fastest path to demo; data ecosystem |
| UI | **Streamlit** | FastAPI + Next.js 14 + shadcn/ui | Streamlit = demo in days; swapping the UI never touches the core |
| Database | **SQLite + SQLModel (ORM)** | PostgreSQL (Supabase) + multi-tenant RLS | Migration is a connection-string change, not a rewrite; pattern proven in SpareParts AI |
| Rules | **YAML as data** (versioned, validity dates) | same + rule editor | Regulations changed three times this year — rules must NOT be code |
| Parsing | lxml (EHF/UBL XML), pdfplumber (text PDF) | + OCR (PaddleOCR) for scans | EHF is XML — OCR is unnecessary in MVP |
| LLM | Claude API (commitment extraction from e-mails, justifications) | self-hosted Llama for defence clients | Data sovereignty is a hard requirement in the forsvar segment |
| Deploy MVP | Streamlit Community Cloud / local | Docker container (on-prem-ready by design) | The on-prem variant is an architectural decision, not an add-on |

**Prime directive:** the `core` package imports nothing from any UI. Streamlit, FastAPI, CLI — all are replaceable "heads" on the same engine.

---

## 2. Repository layout

```
anskaffelsessjekk/
├── core/                        # THE HEART — zero UI dependencies
│   ├── models/                  # SQLModel: domain entities
│   │   ├── supplier.py
│   │   ├── contract.py          # contracts + lines (prices, rates, periods)
│   │   ├── commitment.py        # COMMITMENT — see §3
│   │   ├── order.py             # requisition / order / avrop
│   │   ├── receipt.py           # mottak (goods/service receipt confirmation)
│   │   ├── invoice.py           # invoice + lines
│   │   └── audit.py             # audit trail (append-only)
│   ├── rules/                   # rules engine
│   │   ├── engine.py            # evaluator: facts → rules → verdict + citations
│   │   └── data/                # rules AS DATA
│   │       ├── regimes.yaml     # regime tree FOA / FOSA / art.123→RAF
│   │       ├── thresholds_2026.yaml  # terskelverdier with validity dates
│   │       ├── raf_2026.yaml    # RAF rules (Del II ≥ 300k etc.)
│   │       └── profiles/        # forsvar.yaml / kommune.yaml / helse.yaml
│   ├── matching/
│   │   ├── three_way.py         # order ↔ mottak ↔ invoice
│   │   └── commitments.py       # invoice ↔ commitments repository
│   ├── extraction/
│   │   ├── ehf.py               # EHF parser (UBL XML)
│   │   ├── pdf_invoice.py       # pdfplumber → invoice lines
│   │   └── email_commitments.py # LLM: e-mail → structured commitments
│   ├── reporting/
│   │   ├── classify.py          # SAMSVAR / TIL VURDERING / AVVIK
│   │   └── report.py            # report + verdi_funnet + protokoll draft
│   └── synth/                   # synthetic data generator
│       ├── scenario_deler.py    # spare parts / vedlikehold
│       └── scenario_konsulent.py# consultant hire (hours × rates)
├── app/                         # Streamlit (REPLACEABLE) — UI text in Norwegian
│   ├── Hjem.py
│   └── pages/
│       ├── 1_Fakturakontroll.py
│       ├── 2_Avtaler_og_forpliktelser.py
│       ├── 3_Terskelsjekk.py
│       └── 4_Styringsinformasjon.py   # controlling dashboard
├── tests/                       # pytest — see §7
├── docs/ARCHITECTURE.md         # this file
├── pyproject.toml
└── README.md                    # Norwegian — portfolio-facing
```

---

## 3. Data model — the commitments repository (the core)

The key entity of the project. A commitment is **any source of a commercial condition**, formal or informal.

```python
class Commitment(SQLModel, table=True):
    id: int
    supplier_id: int                  # FK → Supplier
    contract_id: int | None           # FK → Contract (None = standalone agreement)
    source_type: SourceType           # CONTRACT | EMAIL | MEETING_NOTE | OTHER
    source_ref: str                   # e.g. "e-mail 2026-06-12, J. Hansen"
    source_file: str | None           # path to attached evidence (.eml / .pdf)
    condition_type: ConditionType     # PRICE | DISCOUNT | QUANTITY | DEADLINE | SCOPE | RATE
    item_ref: str | None              # article number / service category
    value: Decimal | None             # condition value (price, rate, %)
    unit: str | None                  # NOK, NOK/h, %, pcs
    valid_from: date
    valid_to: date | None
    formalization: Formalization      # FORMALIZED | PENDING_ANNEX | INFORMAL
    extracted_by: str                 # "manual" | "llm:claude-sonnet-4-6"
    confirmed_by_user: bool           # human-in-the-loop: LLM proposes, a human approves
    created_at: datetime
```

Remaining entities (summary — full definitions in `core/models/`):

- **Contract**: supplier, type (rammeavtale / enkeltkjøp), value, period, `ContractLine[]` (item, price/rate, max quantity)
- **Order**: requisition / avrop — `requested_by` (requester field, gap G5), estimated value, `regime_assessment_id` (terskelsjekk verdict at order time)
- **Receipt**: `order_id`, `confirmed_by`, `confirmed_at`, notes — the **mottak bekreftet** field (gap G1)
- **Invoice / InvoiceLine**: header + lines (item, quantity, price, total) with raw source retained (EHF XML / PDF)
- **CheckResult**: verdict per invoice/line + `rule_hits[]` (rule id, citation of the regulation/contract/e-mail) + `deviation_amount` → sum = **verdi_funnet** (gap G2)
- **AuditLog**: append-only; who, when, what, on which rules version — internkontroll / AI Act requirement

**Phase 2 migration:** the same SQLModel models run on Postgres; add a `tenant_id` column + RLS (pattern rehearsed in SpareParts AI).

---

## 4. Rules engine — rules as data

A rule lives in YAML, never in code:

```yaml
# thresholds_2026.yaml (excerpt)
- id: LOA_INNSLAGSPUNKT_2026
  regime: FOA                        # a branch of the regime tree, not an amount!
  valid_from: 2026-07-01
  valid_to: null
  condition: "order.estimated_value < 500000"
  consequence: UTENFOR_LOVEN
  citation: "Anskaffelsesloven §2, endret ved lov vedtatt 05.02.2026"
  citation_url: "https://lovdata.no/..."
- id: FOSA_PROTOKOLLPLIKT
  regime: FOSA
  valid_from: 2014-01-01
  condition: "order.estimated_value >= 100000"
  consequence: PROTOKOLLPLIKT
  citation: "FOSA §5-1, vedlegg 3/4"
```

**Evaluation (engine.py):**
1. Input: facts (order/invoice) + client profile (`forsvar.yaml` etc.) + date → select the rule set in force on that date
2. **Step 1: the regime tree** (FOA / FOSA / art. 123 → RAF Del III) — ALWAYS before any amounts
3. Step 2: threshold and procedural rules within the selected regime
4. Output: `RuleHit[]` — every hit carries a citation and link = the **"Hvorfor?"** button in the UI

Rule tests are plain table-driven pytest cases — a change in the law means a new YAML file plus tests, never touching the engine.

---

## 5. Invoice control pipeline

```
ingest (EHF / PDF / e-mail) → parse → normalize
  → three-way match   (Order ↔ Receipt ↔ Invoice)
  → commitments check (invoice lines ↔ Commitments: price/rate/quantity/deadline)
  → regime & threshold check (rules engine)
  → classify: SAMSVAR / TIL VURDERING / AVVIK   ← a recommendation, NOT a decision
  → report (verdi_funnet, rule_hits, protokoll draft) → AuditLog
```

Hard principles:
- **Human-in-the-loop:** the system never blocks a payment; the verdict is a justified recommendation
- **E-mail extraction:** the LLM proposes a `Commitment`, a human approves it (`confirmed_by_user`) — only then does it participate in control
- **Explainability:** no verdict without `rule_hits` — a result without a citation is a bug, not a feature

---

## 6. Synthetic data (core/synth/)

Two scenarios; each generates the full chain: supplier → contract → commitments (including 2–3 e-mail-based!) → orders → mottak → invoices, with **deliberately injected deviations** (price +7%, quantity above the avrop, consultant rate off-contract, invoice without mottak, order just under a threshold — split-purchase detection):

1. **scenario_deler** — spare parts / vedlikehold: line-item invoices vs rammeavtale (Adrian's home turf: SAP MM, verksted)
2. **scenario_konsulent** — consultant hire: hours × rates vs contract (validated by a dedicated FTE at Miljødirektoratet)

Every generated dataset ships a `manifest.json` listing the injected deviations → **ground truth for end-to-end tests** (did the matcher find them all? precision/recall — a ready-made DS portfolio metric).

## 7. Testing and quality

- `pytest` + `pytest-cov`; target: core ≥ 80% coverage (no requirement on UI)
- Rule tests: table-driven (input → expected verdict + citation) — one table per YAML file
- Matcher tests: on synthetic data with the manifest (precision/recall reported in CI)
- GitHub Actions: lint (ruff) + tests on push
- Typing: full (mypy strict on core/)

## 8. Security and compliance (from the MVP on)

- Zero real data — synthetic only, clearly labelled in the UI
- Append-only AuditLog from the first commit
- Configuration via environment variables (`.env` outside the repo); the LLM API key never in code
- Containerizable architecture → on-prem variant (forsvar) without a redesign
- Disclaimer in the UI and in reports: *beslutningsstøtte, ikke juridisk rådgivning*

## 9. Phase map

| | MVP (until ~21 Jul) | Phase 2 (after the gate) | Phase 3 |
|---|---|---|---|
| UI | Streamlit | FastAPI + Next.js | multi-tenant SaaS |
| Database | SQLite | Supabase/Postgres + RLS | + backup/DR |
| Modules | matcher, terskelsjekk, dashboard, report | bestiller view, cost estimator, RAG chatbot, regulation monitor | supplier registry with scoring, SAP/Visma integrations, warehouse module (SpareParts) |
| LLM | Claude API (synthetic data) | + self-hosted for forsvar | fine-tuning |

**MVP definition of done:** a 10-minute demo — upload an invoice → the system finds a price deviation → finds the 12 June e-mail changing the price → verdict "SAMSVAR (grunnlag: e-postavtale, krever formalisering)" → protokoll draft → dashboard shows verdi funnet. Every step with a working "Hvorfor?" button.
