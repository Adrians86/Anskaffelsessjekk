"""OCR intake — read a PDF/image invoice into RAW TEXT. Never a control basis in itself.

Safety principle for this whole module (Funksjon 3.5): **a scan is a READING AID, not a source of
truth.** This layer only produces text and, in `parse_scanned_invoice`, a NON-binding proposal with
per-field confidence. Nothing here reaches the control basis — a human confirms the numbers on the
bekreftelsesskjerm first (same human-in-the-loop gate as hard rule #3). An OCR misread of money
(11 800 read as 1 180) must never be able to produce a verdict on its own.

Engines, in order of trust:
1. **PDF with a text layer** → `pypdf`. Pure Python, no system binary — works on Streamlit Cloud.
   The characters are read exactly as embedded; this is extraction, not recognition.
2. **Image (JPG/PNG)** → `pytesseract`, and ONLY when the `tesseract` binary is actually installed.
   Genuine recognition: uncertain by nature, so every field is flagged for human control.

When an engine is missing we degrade HONESTLY with a Norwegian message — never a guess, never a
crash. Pure core: no UI import (hard rule #1).
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

ENGINE_PDF_TEXT = "PDF-tekstlag"
ENGINE_TESSERACT = "Bilde-OCR (tesseract)"

# Confidence of a single read field. LAV means: a human MUST look at this before it is used.
CONF_HIGH = "HØY"
CONF_LOW = "LAV"

# Below this many characters a PDF is treated as having no usable text layer (i.e. a scan).
_MIN_PDF_TEXT_CHARS = 40

_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")


class OcrUnavailable(RuntimeError):
    """The engine needed for this file type is not installed in this environment."""


class OcrReadError(ValueError):
    """The file could not be read at all (corrupt, encrypted, unsupported)."""


@dataclass(frozen=True)
class OcrReading:
    """Raw text read from a document, plus which engine read it and what to be careful about."""
    text: str
    engine: str
    warnings: list[str] = field(default_factory=list)

    @property
    def is_recognition(self) -> bool:
        """True when the text came from image recognition (uncertain) rather than a text layer."""
        return self.engine == ENGINE_TESSERACT


def image_ocr_available() -> tuple[bool, str]:
    """(available, reason) for image OCR. Reason is a Norwegian message shown to the user when the
    engine is missing — the honest degrade instead of a guess."""
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return (False, "Bilde-OCR er ikke installert i dette miljøet (pytesseract mangler).")
    if shutil.which("tesseract") is None:
        return (False, "Bilde-OCR-motoren (tesseract) er ikke installert på serveren. "
                       "PDF med tekstlag kan leses; skannede bilder krever tesseract.")
    return (True, "")


def _read_pdf(data: bytes) -> OcrReading:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is declared in pyproject
        raise OcrUnavailable(
            "PDF-lesing er ikke tilgjengelig i dette miljøet (pypdf mangler)."
        ) from exc
    import io
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [(p.extract_text() or "") for p in reader.pages]
    except Exception as exc:
        raise OcrReadError(f"Kunne ikke lese PDF-en: {exc}") from exc

    text = "\n".join(pages).strip()
    if len(text) < _MIN_PDF_TEXT_CHARS:
        # A scanned PDF (image-only). We do NOT silently guess — rasterising needs another engine.
        raise OcrUnavailable(
            "PDF-en har ikke et lesbart tekstlag — den er sannsynligvis en skanning. "
            "Last den opp som JPG/PNG for bilde-OCR, eller bruk EHF/CSV for et sikkert inntak."
        )
    warnings: list[str] = []
    if len(reader.pages) > 1:
        warnings.append(f"Dokumentet har {len(reader.pages)} sider — kontroller at alle "
                        "fakturalinjer er med.")
    return OcrReading(text=text, engine=ENGINE_PDF_TEXT, warnings=warnings)


def _read_image(data: bytes) -> OcrReading:
    ok, reason = image_ocr_available()
    if not ok:
        raise OcrUnavailable(reason)
    import io

    import pytesseract
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as exc:
        raise OcrReadError(f"Kunne ikke åpne bildet: {exc}") from exc
    try:
        text = pytesseract.image_to_string(img, lang="nor")
    except Exception:
        # Norwegian language data may not be installed; English still reads digits fine.
        try:
            text = pytesseract.image_to_string(img)
        except Exception as exc:
            raise OcrReadError(f"Bilde-OCR feilet: {exc}") from exc
    return OcrReading(
        text=(text or "").strip(), engine=ENGINE_TESSERACT,
        warnings=["Teksten er gjenkjent fra et bilde — beløp og tall MÅ kontrolleres mot "
                  "originalen før fakturaen kontrolleres."],
    )


def read_document(data: bytes, filename: str) -> OcrReading:
    """Read a PDF/image into raw text. Raises OcrUnavailable (engine missing — honest degrade) or
    OcrReadError (unreadable file). The returned text is NEVER a control basis on its own."""
    if not data:
        raise OcrReadError("Filen er tom.")
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _read_pdf(data)
    if name.endswith(_IMAGE_SUFFIXES):
        return _read_image(data)
    raise OcrReadError(f"Filtypen støttes ikke for OCR: {filename}")


# =============================================================================
# O2 — field extraction: raw text → a NON-BINDING proposal with per-field confidence
# =============================================================================
# Pure text processing: no engine, no binary, no I/O. This is the layer that must be trustworthy
# enough to SHOW a human, and never trustworthy enough to control an invoice on its own.

@dataclass(frozen=True)
class ReadField:
    """One read value: what we think it says, how sure we are, and the line we read it from.

    `source_line` is what makes the bekreftelsesskjerm honest — the human can compare our reading
    against the original document line by line.
    """
    value: object | None
    confidence: str = CONF_LOW
    source_line: str = ""

    @property
    def found(self) -> bool:
        return self.value is not None


@dataclass(frozen=True)
class ProposedLine:
    """A proposed invoice line. Every number here is a PROPOSAL until a human confirms it."""
    item_ref: str | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    confidence: str
    source_line: str


@dataclass(frozen=True)
class SumCheck:
    """Independent cross-check: do the lines add up to the stated total?

    This is the single most valuable safeguard against an OCR digit error in money (11 800 read as
    1 180): the wrong number stops agreeing with its neighbours, and we can say so out loud.
    """
    lines_sum: Decimal
    stated_total: Decimal | None
    ok: bool
    message: str


@dataclass(frozen=True)
class ProposedInvoice:
    """A NON-binding reading of a scanned invoice. Enters control only after human confirmation."""
    invoice_number: ReadField
    invoice_date: ReadField
    supplier_org: ReadField
    supplier_name: ReadField
    currency: ReadField
    total_ex_vat: ReadField
    lines: list[ProposedLine] = field(default_factory=list)
    raw_text: str = ""
    engine: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def fields(self) -> dict[str, ReadField]:
        return {
            "invoice_number": self.invoice_number, "invoice_date": self.invoice_date,
            "supplier_org": self.supplier_org, "supplier_name": self.supplier_name,
            "currency": self.currency, "total_ex_vat": self.total_ex_vat,
        }

    @property
    def low_confidence_fields(self) -> list[str]:
        return [n for n, f in self.fields.items() if f.confidence == CONF_LOW]

    @property
    def inconsistent_lines(self) -> list[ProposedLine]:
        """Lines whose own arithmetic does not hold (antall × pris ≠ linjesum).

        This is the finer of the two money safeguards: a misread unit price (11 800 → 1 180) stops
        agreeing with its OWN line total even when the column of line totals still adds up.
        """
        return [ln for ln in self.lines
                if abs(ln.quantity * ln.unit_price - ln.line_total) > Decimal("0.5")]

    def sum_check(self) -> SumCheck:
        """Σ(line totals) vs the stated total, plus per-line arithmetic. Never blocks — it tells the
        human exactly where to look before anything is confirmed."""
        lines_sum = sum((ln.line_total for ln in self.lines), Decimal("0"))
        stated = self.total_ex_vat.value if isinstance(self.total_ex_vat.value, Decimal) else None
        if stated is None:
            return SumCheck(lines_sum, None, False,
                            "Fant ikke totalbeløp i dokumentet — kontroller summen mot originalen.")
        if not self.lines:
            return SumCheck(lines_sum, stated, False,
                            "Fant ingen fakturalinjer — legg dem inn manuelt før kontroll.")
        if (bad := self.inconsistent_lines):
            refs = ", ".join(ln.item_ref or "linje" for ln in bad)
            return SumCheck(
                lines_sum, stated, False,
                f"Antall × pris stemmer ikke med linjesummen for {refs}. Et beløp er "
                "sannsynligvis lest feil — kontroller mot originalen.")
        if abs(lines_sum - stated) <= Decimal("0.5"):
            return SumCheck(lines_sum, stated, True, "Linjene summerer til totalbeløpet.")
        return SumCheck(
            lines_sum, stated, False,
            f"Summen av linjene ({_money(lines_sum)}) stemmer IKKE med avlest totalbeløp "
            f"({_money(stated)}). Dette er ofte et tegn på at et beløp er lest feil — "
            "kontroller tallene mot originalen.")


def _money(d: Decimal) -> str:
    return f"{d:,.2f}".replace(",", " ").replace(".", ",").replace(" ", " ")


_DATE_PATTERNS = (
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), ("y", "m", "d")),
    (re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b"), ("d", "m", "y")),
)
# A space is only a thousands separator when followed by exactly three digits — otherwise one
# greedy match swallows a whole invoice row ("2 11800,00 23600,00") and every amount is lost.
_NUM_RE = re.compile(
    r"(?:"
    r"\d{1,3}(?:[\u00a0\u202f ]\d{3})+(?:[.,]\d{1,2})?"   # 23 600,00
    r"|\d+(?:[.,]\d{3})+(?:[.,]\d{1,2})?"                    # 23.600,00
    r"|\d+(?:[.,]\d{1,2})?"                                   # 11800,00 / 2
    r")(?!\d)"                                                 # a group may not run into more digits
)
_ITEM_RE = re.compile(r"\b([A-ZÆØÅ]{2,}[-‑]?\d{3,})\b")
_ORG_RE = re.compile(r"\b(\d{3}[ .]?\d{3}[ .]?\d{3})\b")
_CURRENCY_RE = re.compile(r"\b(NOK|EUR|USD|SEK|DKK|GBP)\b", re.IGNORECASE)

_LABEL_INVOICE_NO = re.compile(
    r"(?:faktura(?:nummer|nr\.?|\s*nr\.?)|invoice\s*(?:no\.?|number))\s*[:.\-]?\s*"
    r"([A-Za-z0-9][A-Za-z0-9\-/_]{1,30})", re.IGNORECASE)
_LABEL_DATE = re.compile(r"(?:faktura)?dato|invoice\s*date", re.IGNORECASE)
_LABEL_ORG = re.compile(r"org(?:anisasjons)?\.?\s*nr|foretaksregister", re.IGNORECASE)
_LABEL_TOTAL = re.compile(
    r"(?:bel(?:ø|o)p\s*eks|sum\s*eks|netto|total(?:sum|beløp|belop)?|å\s*betale|a\s*betale|sum)\b",
    re.IGNORECASE)
# Only an INCLUSIVE-VAT marker disqualifies a total line. A bare "mva" must not match, or
# "Beløp eks. mva" would be rejected as a VAT-inclusive line.
_TOTAL_INCL_VAT = re.compile(r"inkl\.?\s*mva|herav\s*mva", re.IGNORECASE)


def _num(raw: str) -> Decimal | None:
    """Parse a Norwegian/English number. '23 600,00' → 23600.00; '1.180,50' → 1180.50.

    When both separators appear the LAST one is the decimal separator; a lone comma/dot with
    exactly two trailing digits is decimal, otherwise it is a thousands separator.
    """
    s = (raw or "").strip().replace(" ", "").replace(" ", "")
    if not s:
        return None
    last_comma, last_dot = s.rfind(","), s.rfind(".")
    if last_comma >= 0 and last_dot >= 0:
        dec = max(last_comma, last_dot)
        s = s[:dec].replace(",", "").replace(".", "") + "." + s[dec + 1:]
    elif last_comma >= 0:
        s = (s[:last_comma] + "." + s[last_comma + 1:]) if len(s) - last_comma - 1 == 2 \
            else s.replace(",", "")
    elif last_dot >= 0 and len(s) - last_dot - 1 != 2:
        s = s.replace(".", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _numbers_in(line: str) -> list[Decimal]:
    out = []
    for m in _NUM_RE.finditer(line):
        v = _num(m.group(0))
        if v is not None:
            out.append(v)
    return out


def _parse_date(text: str) -> date | None:
    for pattern, order in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        parts = dict(zip(order, m.groups(), strict=True))
        try:
            return date(int(parts["y"]), int(parts["m"]), int(parts["d"]))
        except ValueError:
            continue
    return None


def _find_labelled(lines: list[str], label: re.Pattern) -> tuple[str, str] | None:
    """(matched_line, remainder_after_label) for the first line whose label matches."""
    for ln in lines:
        m = label.search(ln)
        if m:
            return (ln, ln[m.end():])
    return None


def parse_scanned_invoice(reading: OcrReading) -> ProposedInvoice:
    """Read raw OCR text into a NON-binding proposal with per-field confidence.

    Policy (the safety core of Funksjon 3.5): when the text came from image RECOGNITION, every
    money field is marked LAV confidence regardless of how clean the pattern looked — recognised
    digits are never trusted silently. The result is always shown to a human before any control.
    """
    text = reading.text or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    recognised = reading.is_recognition

    def money_conf(base: str) -> str:
        return CONF_LOW if recognised else base

    # --- invoice number ---
    inv_no = ReadField(None, CONF_LOW, "")
    for ln in lines:
        m = _LABEL_INVOICE_NO.search(ln)
        if m:
            inv_no = ReadField(m.group(1).strip(" .:-"), CONF_HIGH if not recognised else CONF_LOW, ln)
            break

    # --- invoice date ---
    inv_date = ReadField(None, CONF_LOW, "")
    hit = _find_labelled(lines, _LABEL_DATE)
    if hit and (d := _parse_date(hit[1] or hit[0])) is not None:
        inv_date = ReadField(d, CONF_HIGH if not recognised else CONF_LOW, hit[0])
    else:
        for ln in lines:                                    # fallback: any date anywhere = LAV
            if (d := _parse_date(ln)) is not None:
                inv_date = ReadField(d, CONF_LOW, ln)
                break

    # --- supplier org number ---
    org = ReadField(None, CONF_LOW, "")
    hit = _find_labelled(lines, _LABEL_ORG)
    if hit and (m := _ORG_RE.search(hit[1] or hit[0])):
        org = ReadField(re.sub(r"\D", "", m.group(1)), CONF_HIGH if not recognised else CONF_LOW,
                        hit[0])
    else:
        for ln in lines:
            if (m := _ORG_RE.search(ln)) and len(re.sub(r"\D", "", m.group(1))) == 9:
                org = ReadField(re.sub(r"\D", "", m.group(1)), CONF_LOW, ln)
                break

    # --- supplier name: first line that looks like a company, never a strong claim ---
    name = ReadField(None, CONF_LOW, "")
    for ln in lines:
        if re.search(r"\b(AS|ASA|ANS|DA|GmbH|AB|Ltd)\b", ln):
            name = ReadField(ln.strip(), CONF_LOW, ln)
            break

    # --- currency (absent = NOK by convention, flagged LAV so the human sees the assumption) ---
    cur = ReadField("NOK", CONF_LOW, "")
    for ln in lines:
        if (m := _CURRENCY_RE.search(ln)):
            cur = ReadField(m.group(1).upper(), CONF_HIGH if not recognised else CONF_LOW, ln)
            break

    # --- total ex VAT: prefer an explicitly "eks. mva"-labelled line ---
    total = ReadField(None, CONF_LOW, "")
    for ln in lines:
        if _LABEL_TOTAL.search(ln) and not _TOTAL_INCL_VAT.search(ln):
            nums = _numbers_in(ln)
            if nums:
                total = ReadField(max(nums), money_conf(CONF_HIGH), ln)
                break
    if not total.found:
        for ln in lines:
            if _LABEL_TOTAL.search(ln):
                nums = _numbers_in(ln)
                if nums:
                    total = ReadField(max(nums), CONF_LOW, ln)
                    break

    # --- lines: an article-like token plus at least three numbers (qty, unit price, line total) ---
    parsed_lines: list[ProposedLine] = []
    for ln in lines:
        m = _ITEM_RE.search(ln)
        if not m:
            continue
        # Read amounts from the line WITHOUT the article number — otherwise the digits in
        # "HYD-1001" would be taken as the quantity.
        rest = ln[:m.start()] + " " + ln[m.end():]
        if _LABEL_TOTAL.search(ln) and len(_numbers_in(rest)) < 3:
            continue
        nums = [n for n in _numbers_in(rest) if n != 0]
        if len(nums) < 3:
            continue
        qty, unit_price, line_total = nums[0], nums[1], nums[-1]
        computed = qty * unit_price
        consistent = abs(computed - line_total) <= Decimal("0.5")
        desc = ln[m.end():].strip()
        for n in nums:                                       # strip the numbers from the description
            desc = desc.replace(f"{n:f}".rstrip("0").rstrip("."), "")
        desc = re.sub(r"[\d ,. ]{2,}", " ", desc).strip(" -|") or m.group(1)
        parsed_lines.append(ProposedLine(
            item_ref=m.group(1).replace("‑", "-"), description=desc[:80],
            quantity=qty, unit_price=unit_price, line_total=line_total,
            confidence=money_conf(CONF_HIGH if consistent else CONF_LOW), source_line=ln,
        ))

    warnings = list(reading.warnings)
    if recognised:
        warnings.append("Alle beløp er markert som usikre fordi teksten er gjenkjent fra et bilde.")
    if not parsed_lines:
        warnings.append("Ingen fakturalinjer ble gjenkjent — de må legges inn manuelt.")

    return ProposedInvoice(
        invoice_number=inv_no, invoice_date=inv_date, supplier_org=org, supplier_name=name,
        currency=cur, total_ex_vat=total, lines=parsed_lines,
        raw_text=text, engine=reading.engine, warnings=warnings,
    )
