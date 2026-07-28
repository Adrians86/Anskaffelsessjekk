# AS North Design Tokens

Brand colors and design system for Anskaffelsessjekk — consistent across all surfaces.

**Runtime source of truth:** `app/theme.py` (the «Lyst kontor» / variant C theme) is the single
place the live app reads colors and typography from. This document mirrors it for reference.

## Primary palette — «Lyst kontor» (variant C)

| Token | Hex | Usage |
|-------|-----|-------|
| **Navy** (primary) | `#20364F` | Headings (serif), product band, primary UI elements |
| **Gold** (accent) | `#A8842A` | Eyebrows, links, accents, action-tile borders |
| **Ink** (body text) | `#1C2733` | Body text, default |
| **Muted** | `#5A6673` | Captions, secondary text |
| **Hairline** | `#E4E1D8` | 1px rules instead of drop shadows |
| **Paper** | `#FCFBF7` | Warm "office paper" surface accents |
| **Background** | `#FAFBFC` | Page background |

Typography: serif (Georgia — web-safe, no external font) in headings/eyebrows; sans (Inter) in body.
Hairlines replace shadows.

## Verdict indicators (semantic colors)

Used in charts, badges, and status blocks to indicate control outcomes.

| Verdict | Color | Hex | Usage |
|---------|-------|-----|-------|
| **SAMSVAR** (compliant) | ![#2E7D32](https://via.placeholder.com/24/2E7D32/2E7D32) | `#2E7D32` | Green — no deviations |
| **TIL_VURDERING** (review needed) | ![#B58900](https://via.placeholder.com/24/B58900/B58900) | `#B58900` | Amber — warnings present |
| **AVVIK** (deviation) | ![#C62828](https://via.placeholder.com/24/C62828/C62828) | `#C62828` | Red — deviations found |

## Implementation

### Streamlit (`.streamlit/config.toml`)
- `primaryColor`: `#20364F` (navy)
- `backgroundColor`: `#FAFBFC`
- `secondaryBackgroundColor`: `#F2EFE7`
- `textColor`: `#1A1D21`
- `font`: `inter` (body); headings are serif via `theme.py` CSS

### UI accents
- Editorial page header: gold eyebrow + serif navy H1 + muted lede + «Syntetiske data» chip
- Action tiles (Arbeidsflate): `4px solid #A8842A` gold left border
- Verdict chart (Styringsinformasjon): SAMSVAR `#2E7D32`, TIL_VURDERING `#B58900`, AVVIK `#C62828`

## Notes

- «Lyst kontor» (variant C) is the active identity from 2026-07-28; `app/theme.py` is authoritative.
- Semantic colors (verdicts) are brand-agnostic but tested for WCAG AA contrast — never re-tinted.
- Never hardcode colors in page code — reference `theme.py` tokens (or these design tokens).
