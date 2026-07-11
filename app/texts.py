"""UI text constants and mappings — Norwegian (bokmål)."""
from datetime import datetime
import subprocess

RECOMMENDED_ACTIONS = {
    "PRICE_ABOVE_AGREED": "Krev kreditnota eller avklar prisgrunnlag med leverandør",
    "QTY_ABOVE_MAX": "Avklar mermengde mot avrop",
    "INFORMAL_BASIS": "Formaliser e-postavtalen med tillegg/anneks",
    "MISSING_RECEIPT": "Bekreft mottak før betaling",
    "MISSING_ORDER": "Knytt faktura til bestilling/avrop",
    "NO_AGREED_BASIS": "Etabler avtalegrunnlag eller vurder engeltkjøp",
}

def get_build_info() -> str:
    """Return build date from latest git commit."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split()[0]
    except Exception:
        pass
    return datetime.now().strftime("%Y-%m-%d")

FOOTER = "🔒 Anskaffelsessjekk · AS North Advisory · Adrian Śliwa — 19 år i logistikk og innkjøp · asliwa1986@gmail.com · Syntetiske data"
VERSION = "MVP 0.1.0"
BUILD_DATE = get_build_info()
