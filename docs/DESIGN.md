# Design direction

## Aesthetic direction

**Risograph dispatch sheet.** Wishwright looks like a maker's field report printed in midnight
ink, vermilion, and teal on warm stock. Dense labels, visible rules, and slightly offset color
layers make the request pipeline feel inspected and physical. This avoids the dark blueprint,
warm library, editorial newsprint, and stark Swiss-grid directions used by recent portfolio
projects.

## Tokens

| Token | Value | Use |
|---|---|---|
| `--bg` | `#f2ead7` | warm paper page ground |
| `--surface-1` | `#fff8e8` | primary paper panels |
| `--surface-2` | `#e3d8c2` | recessed notes and code areas |
| `--text` | `#162336` | midnight body ink |
| `--text-muted` | `#59616a` | secondary copy |
| `--accent` | `#b52f28` | vermilion mark, links, and primary CTA |
| `--support` | `#0b6965` | teal scores and status marks |
| `--success` | `#27643c` | approved state |
| `--danger` | `#9c2924` | rejected state |

- **Type:** Fraunces for the wordmark and display headings; IBM Plex Mono for UI, labels, body,
  and sample output. Each includes a matching serif or monospace system fallback.
- **Spacing:** 4px base with 8, 12, 16, 24, 32, 48, 64, and 96px steps.
- **Corners:** 4px for paper sheets and 2px for compact labels. Controls remain nearly square.
- **Depth:** hard 8px registration shadows plus a soft 24px paper lift. No glass or neon glow.
- **Motion:** 180ms ease-out for links, controls, and sheets; 120ms ease-out for pressed states.
  Reduced-motion users receive opacity and color changes without translation.

## Layout intent

At 1440 by 900, the navigation sits inside a wide ruled frame and the hero fills the remaining
viewport. The left 46 percent carries the benefit, setup command, and one primary CTA. The right
54 percent is a large ranked-output sheet with a vertical evaluation path, giving the actual CLI
result most of the visual weight. Proof and technical notes follow in an asymmetric two-column
grid rather than three interchangeable cards.

At 390 by 844, the navigation wraps without hiding either link. The headline, CTA, and sample
stack in that order, the sample keeps a horizontal scroll region for exact terminal output, and
the process becomes a vertical rail. Every control remains at least 44px tall. At 768px, the same
stack uses wider gutters and the proof sheet spans the content width.

## Signature detail

The output sheet carries a two-color registration target and a deliberately offset vermilion
shadow. Candidate scores align to a numbered print-run rail, so the page's visual flourish also
explains how a request moves from public post to reviewed brief.
