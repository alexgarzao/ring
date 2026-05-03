---
name: ring:deck
description: Scaffold Lerian-branded HTML presentation projects with live-reload dev server, presenter view on second screen, phone-as-remote over WebSocket, auto-scaling canvas (authored at 1920×1080, fits any viewport), in-browser toolbar (tweak/presenter/PDF/PPTX/remote), feedback-to-file loop for iterating with Claude, PPTX + PDF export (Puppeteer), browser-native PDF (Cmd+P), and `npm start` one-command bootstrap. Use when the user asks for a deck, presentation, board deck, investor deck, or slide deck.
trigger: |
  - User asks to create a deck, presentation, board deck, investor deck, conference deck, all-hands deck, or any Lerian-branded slide deliverable
  - User says "make a deck", "build a deck", "new presentation", "slide deck"
skip_when: |
  - Editing an already-scaffolded deck — edit deck.html directly
  - Non-presentational document (memo, one-pager, email)
  - Single static HTML visualization with no tooling — use ring:visualize instead
prerequisites:
  - node_installed (>=18.0.0)
  - pnpm_installed OR npm_installed
---

# ring:deck — Lerian Editorial Deck Scaffolder

Scaffold a self-contained Node project for a Lerian-branded HTML presentation. Ships with live-reload dev server, presenter view (second screen), phone-as-remote over WebSocket, and Puppeteer-driven PDF export.

## Two Design Systems (HARD GATE)

`ring:deck` uses editorial tokens: Amarelo `#FEED02`, Poppins + IBM Plex Serif, JetBrains Mono.  
`ring:visualize` uses product-console tokens: sunglow `#FDCB28`, Inter.  
**MUST NOT cross-mix.** Both are canonical Lerian — keep them pure.

## Mandatory Reading (HARD GATE — read before writing any slide content)

1. `references/brand.md` — colors, typography, logo (inviolable)
2. `references/engineering.md` — canvas, flex, pagination, 24px text floor, overflow (inviolable)
3. `references/primitives.md` — CSS atoms: eyebrow, pill, kpi, ticks, numbered, table.grid, etc.
4. `references/chart-primitives.md` — stacked-horizontal-bar, vertical-bar-chart, 2x2-matrix, funnel
5. `references/speaker-notes.md` — JSON schema + presenter voice

On-demand: `references/server.md` (dev server), `references/export.md` (Puppeteer PDF).

**Skipping engineering.md and brand.md is the #1 failure mode.**

## Workflow

### Phase 1: Gather Requirements

Ask the user (skip if already answered):
1. Deck title
2. Audience (board, investors, conference, team, external)
3. Rough slide count
4. Directory name (defaults to kebab-cased title)

MUST NOT ask about tokens, fonts, layout, runtime, export — those are fixed by the skill.

### Phase 2: Read Mandatory References (refs 1-5 above)

### Phase 3: Scaffold Project

Compute substitution variables first:
- `DECK_TITLE` = user-supplied title verbatim (HTML-escape `&`, `<`, `>`, `"`, and `'` as `&amp;` `&lt;` `&gt;` `&quot;` `&#39;`)
- `DECK_NAME` = kebab-cased: `DECK_TITLE.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')`
- `YEAR` = current 4-digit year
- `COPYRIGHT_HOLDER` = "Lerian Studio" (unless user specifies otherwise)

Copy from skill's `templates/`, `assets/`, `scripts/` directories:

| Source | Destination |
|--------|-------------|
| `templates/deck.html` | `deck.html` (substitute `{{DECK_TITLE}}`) |
| `templates/presenter.html` | `presenter.html` |
| `templates/remote.html` | `remote.html` |
| `templates/package.json.tmpl` | `package.json` (substitute `{{DECK_NAME}}`) |
| `assets/*` | `assets/*` |
| `scripts/*` | `scripts/*` |
| `templates/LICENSE.tmpl` | `LICENSE` (substitute `{{YEAR}}`, `{{COPYRIGHT_HOLDER}}`) |
| `templates/README.md.tmpl` | `README.md` |
| `templates/.gitignore.tmpl` | `.gitignore` |

### Phase 4: Compose Slides

Compose from brand tokens and primitives. Use slide templates in `templates/slide-*.html` when a composition fits. No required slide menu — use what serves the narrative.

Per slide: obey `flex: 1; min-height: 0` from `engineering.md`, use only chart primitives (4 types, no Chart.js in v1), replace all placeholder content.

### Phase 5: Write Speaker Notes

Flat JSON array of strings, zero-indexed, one entry per `<section>`. Speaking voice (not written). `\n\n` for paragraph breaks.

### Phase 6: Hand Off to User

Print Handoff Message (do NOT run `pnpm install` or `pnpm dev` for the user):

```
Deck scaffolded at: ./<deck-name>/

  cd <deck-name>
  npm start    # installs, boots dev server on http://localhost:7007, auto-opens browser

During presentation:
  Main deck:   http://localhost:7007
  Presenter:   http://localhost:7007/presenter  (second screen)
  Remote:      http://<LAN-IP>:7007/remote      (phone, same Wi-Fi)

Export:
  npm run export         # PDF via bundled Chromium
  npm run export:chrome  # PDF via system Chrome (faster)
  npm run export:pptx    # PPTX (screenshots + notes)
```

## Non-Negotiables

- Lerian brand tokens: Amarelo `#FEED02`, Poppins + IBM Plex Serif, JetBrains Mono
- Apache 2.0 license on every scaffolded deck
- Dynamic pagination: `<span class="page-num">` + `<span class="page-total">`
- `flex: 1; min-height: 0` on main content grids
- Speaker-notes flat JSON array
- Only 4 chart primitives (no Chart.js in v1)

## Blocker Criteria

| Condition | Action |
|-----------|--------|
| Node < 18.0.0 not installed | STOP — user must install Node 18+ |
| Target directory exists non-empty | STOP — ask: overwrite, rename, or cancel |
| User asks editable PPTX (text+shapes) | STOP — v1 is screenshots-mode only; offer PDF or screenshots PPTX |
| Missing `references/` mandatory files | STOP — report which is missing, instruct re-clone |
