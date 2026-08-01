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

import shutil
from dataclasses import dataclass, field

ENGINE_PDF_TEXT = "PDF-tekstlag"
ENGINE_TESSERACT = "Bilde-OCR (tesseract)"

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
