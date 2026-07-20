"""Synthetic example e-mails for the "Registrer fra e-post" demo.

ALL DATA IS SYNTHETIC. Each example exercises one gyldighet outcome of parse_email:
KREVER FORMALISERING, GYLDIG, UGYLDIG.
"""
from __future__ import annotations

EXAMPLE_EMAILS: list[dict[str, str]] = [
    {
        "label": "Prisreduksjon — krever formalisering",
        "avsender": "J. Hansen, Hydraulikk Nord AS",
        "body": ("Hei. Vi bekrefter redusert pris kr 11 800 per stk for HYD-1001, "
                 "gjeldende fra 12. juni. Formelt tillegg ettersendes. "
                 "Mvh J. Hansen, Hydraulikk Nord AS"),
    },
    {
        "label": "Mindre justering — gyldig",
        "avsender": "K. Berg, Renhold Øst AS",
        "body": ("Hei. Som avtalt justerer vi timepris renhold fra kr 520 til kr 495 fra "
                 "neste måned, iht. rammeavtalens punkt om mindre justeringer. "
                 "Mvh K. Berg, Renhold Øst AS"),
    },
    {
        "label": "Utvidelse av omfang — ugyldig",
        "avsender": "T. Olsen, leverandør",
        "body": ("Hei. Vi utvider leveransen med tre nye maskintyper og øker rammen med 45%, "
                 "gjeldende umiddelbart. Mvh T. Olsen, leverandør"),
    },
]
