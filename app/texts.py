"""UI text constants and mappings — Norwegian (bokmål)."""
from importlib.metadata import PackageNotFoundError, version

RECOMMENDED_ACTIONS = {
    "PRICE_ABOVE_AGREED": "Krev kreditnota eller avklar prisgrunnlag med leverandør",
    "QTY_ABOVE_MAX": "Avklar mermengde mot avrop",
    "INFORMAL_BASIS": "Formaliser e-postavtalen med tillegg/anneks",
    "MISSING_RECEIPT": "Bekreft mottak før betaling",
    "MISSING_ORDER": "Knytt faktura til bestilling/avrop",
    "NO_AGREED_BASIS": "Etabler avtalegrunnlag eller vurder enkeltkjøp",
    "CURRENCY_MISMATCH": "Fastsett valutakurs (Norges Bank) på fakturadato og vurder mot "
                         "avtalt NOK-pris.",
}

try:
    VERSION = version("anskaffelsessjekk")   # single source of truth: pyproject.toml
except PackageNotFoundError:
    VERSION = "0.0.0"
