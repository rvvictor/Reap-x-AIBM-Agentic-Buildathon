# Bodega · DESIGN (provisional, freeze con HACK-002)

One visual direction: **papel cálido y café tostado**. Calm, trustworthy, built for an owner checking stock on a phone and a judge watching a projector at 1280×720.

## Tokens (CSS variables; every color comes from here)
| Token | Light | Use |
|---|---|---|
| `--bg` | #FAF6F0 | page background |
| `--surface` | #FFFFFF | cards |
| `--ink` | #2B1D14 | text (AA on bg and surface) |
| `--muted` | #6B5A4D | secondary text |
| `--accent` | #8A4B1F | primary actions, focus ring |
| `--up` | #1F7A4D | stock target up / savings |
| `--down` | #B3472A | stock target down / alerts |
| `--demo` | #7A5AF8 | `demo_data` badge |

Dark mode: swap `--bg` #17110D, `--surface` #231A14, `--ink` #F5ECE3, `--muted` #BBA999.

## Rules
- Font: Geist Variable (already in `web/src/index.css`). Numbers use tabular figures.
- Radius 12 px on cards, 8 px on controls. One shadow level.
- Every simulated number shows a small `demo_data` badge; every real number has a source tooltip.
- Each screen has empty, loading, error and sample-data states.
- The wow (forecast per product, then group savings) is fully visible at 1280×720 without scrolling.
- Animations respect `prefers-reduced-motion`. Visible focus ring on all controls, fully keyboard-operable.
- A global redesign after the lock needs a human `uak decision`.
