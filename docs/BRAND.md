# AS North Design Tokens

Brand colors and design system for Anskaffelsessjekk — consistent across all surfaces.

## Primary palette

| Token | Color | Hex | Usage |
|-------|-------|-----|-------|
| **Navy** (primary) | ![#1F3A5F](https://via.placeholder.com/24/1F3A5F/1F3A5F) | `#1F3A5F` | Text, headers, primary UI elements |
| **Gold** (accent) | ![#B08D2E](https://via.placeholder.com/24/B08D2E/B08D2E) | `#B08D2E` | Dividers, accents, emphasis |
| **Background** | ![#FAFBFC](https://via.placeholder.com/24/FAFBFC/FAFBFC) | `#FAFBFC` | Page background |
| **Secondary BG** | ![#EEF2F6](https://via.placeholder.com/24/EEF2F6/EEF2F6) | `#EEF2F6` | Cards, containers |
| **Text** | ![#1A1D21](https://via.placeholder.com/24/1A1D21/1A1D21) | `#1A1D21` | Body text, default |

## Verdict indicators (semantic colors)

Used in charts, badges, and status blocks to indicate control outcomes.

| Verdict | Color | Hex | Usage |
|---------|-------|-----|-------|
| **SAMSVAR** (compliant) | ![#2E7D32](https://via.placeholder.com/24/2E7D32/2E7D32) | `#2E7D32` | Green — no deviations |
| **TIL_VURDERING** (review needed) | ![#B58900](https://via.placeholder.com/24/B58900/B58900) | `#B58900` | Amber — warnings present |
| **AVVIK** (deviation) | ![#C62828](https://via.placeholder.com/24/C62828/C62828) | `#C62828` | Red — deviations found |

## Implementation

### Streamlit (`app/.streamlit/config.toml`)
- `primaryColor`: `#1F3A5F` (navy)
- `backgroundColor`: `#FAFBFC`
- `secondaryBackgroundColor`: `#EEF2F6`
- `textColor`: `#1A1D21`

### UI accents
- Title underline (Hjem): `3px solid #B08D2E`
- Verdict chart (Styringsinformasjon): SAMSVAR `#2E7D32`, TIL_VURDERING `#B58900`, AVVIK `#C62828`

## Notes

- Colors are final and locked for MVP (until 2026-07-21).
- Semantic colors (verdicts) are brand-agnostic but tested for WCAG AA contrast.
- Never hardcode colors in code — always reference design tokens from this file.
