---
name: ring:visualize
description: Generate beautiful, self-contained HTML pages that visually explain systems, code changes, plans, and data. Use when the user asks for a diagram, architecture overview, diff review, plan review, project recap, comparison table, or any visual explanation of technical concepts. Also use proactively when you are about to render a complex ASCII table (4+ rows or 3+ columns) — present it as a styled HTML page instead.

trigger: |
  - User asks for a visual explanation, architecture overview, or comparison table
  - About to render a complex ASCII table (4+ rows or 3+ columns) in the terminal
  - Need a branded, self-contained HTML visualization with Lerian styling
  - User asks for diff review, plan review, project recap, or dashboard visualization

skip_when: |
  - User needs a lightweight, shareable mermaid.live URL (use ring:diagram instead)
  - Output is a simple table (fewer than 4 rows and 3 columns) that fits well in terminal
  - User explicitly requests plain text or markdown output
---

# Visual Explainer

Generate self-contained HTML files for technical diagrams, visualizations, and data tables. Always open the result in the browser. Never fall back to ASCII art when this skill is loaded.

**Proactive table rendering:** If the table has 4+ rows or 3+ columns → HTML page. Don't wait for the user to ask.

## Standard Template (MANDATORY)

**MUST Read `./templates/standard.html` before generating any HTML.** Copy verbatim:
1. Complete `<style>` block (above "DO NOT MODIFY" marker)
2. `<header class="lerian-header">` with inline Lerian logo SVG
3. `<footer class="lerian-footer">` with logo, company name, "Generated with Ring"
4. Date auto-fill `<script>`

**Fixed (cannot change):** Inter font, Lerian color palette (sunglow accent, zinc neutrals), logo, footer, dark mode.  
**Variable (customize per diagram):** Layout, secondary display font, background atmosphere, accent emphasis, animations.

## Workflow

### 1. Think (decide before writing)
- Who is looking? Developer? PM? Team?
- Diagram type? (architecture, flowchart, sequence, data table, timeline, dashboard, code diff)
- Aesthetic? (editorial, blueprint, neon dashboard, paper/ink, data-dense, gradient mesh) — vary each time

### 2. Structure (MUST read before writing)
1. Read `./templates/standard.html` (ALWAYS first)
2. Read diagram-specific template:

| Diagram Type | Template to Read | Required References |
|---|---|---|
| Architecture (text-heavy, CSS cards) | `./templates/architecture.html` | `./references/css-patterns.md` |
| Architecture/flowchart (topology) | `./templates/mermaid-flowchart.html` | `./references/libraries.md`, `./references/css-patterns.md` |
| Data tables / comparisons | `./templates/data-table.html` | `./references/css-patterns.md` |
| Code diffs / reviews | `./templates/code-diff.html` | `./references/css-patterns.md`, `./references/libraries.md`, `./references/responsive-nav.md` |
| Any page with 4+ sections | — | `./references/responsive-nav.md` |
| Any page using CDN libraries | — | `./references/libraries.md` (NEVER use CDN URLs from memory) |

### 3. Diagram Types Reference

| Type | Rendering Approach |
|---|---|
| Architecture (connections matter) | **Mermaid** `graph TD/LR` with `themeVariables` |
| Architecture (rich card content) | CSS Grid cards + flow arrows |
| Flowchart / pipeline | **Mermaid** `graph TD/LR` |
| Sequence diagram | **Mermaid** `sequenceDiagram` |
| ER / schema | **Mermaid** `erDiagram` |
| State machine | **Mermaid** `stateDiagram-v2` (simple labels) or `flowchart LR` (special chars) |
| Mind map | **Mermaid** `mindmap` |
| Data table / comparison | HTML `<table>` (semantic, accessible, copy-paste) |
| Timeline / roadmap | CSS central line + cards |
| Dashboard / metrics | CSS Grid + Chart.js (CDN from libraries.md) |
| Code diff / change review | `@pierre/diffs` (MANDATORY — no hand-rolled CSS diff panels) |

**Mermaid:** Always use `theme: 'base'` with custom `themeVariables` matching the Lerian palette. Add zoom controls (+/-/reset + Ctrl+scroll) to every `.mermaid-wrap`. Copy pattern from `./references/css-patterns.md`.

**Code diffs:** ⛔ MUST use `@pierre/diffs` from `./references/libraries.md`. HTML strings embedded in `<script>` blocks: escape `</script>` → `<\/script>`.

### 4. Style (applied on top of standard template foundation)

- Body font: ALWAYS Inter. MAY add secondary display font for headings only.
- Colors: Use standard template CSS custom properties (`--bg`, `--surface`, `--accent`, etc.). Map extended palette for diagram nodes.
- Backgrounds: Subtle gradients, faint grids, or radial glows — never flat solid color.
- Depth: 3+ distinct visual levels (hero/elevated, default surface, recessed/muted).
- Animations: `fadeUp` for cards, `fadeScale` for KPIs/badges, `countUp` for numbers. Respect `prefers-reduced-motion`.

### 5. Deliver

Output to `~/.agent/diagrams/` with descriptive filename.

```bash
# macOS
open ~/.agent/diagrams/filename.html
# Linux
xdg-open ~/.agent/diagrams/filename.html
```

Tell the user the file path.

## Quality Checks (HARD GATES)

Verify before delivering:
- [ ] Standard template foundation present: search generated HTML for exact SVG logo path, "Generated with Ring", `font-family: 'Inter'`
- [ ] No token conflicts: template-specific CSS doesn't redefine `--bg`, `--surface`, `--text`, `--accent`, etc.
- [ ] Squint test: 3 distinct visual depth levels visible
- [ ] Swap test: diagram-specific styles define at least 1 background atmosphere, 2+ semantic color aliases, and component classes
- [ ] Both themes (light + dark): look intentional, not broken
- [ ] No overflow: all grid/flex children have `min-width: 0`; `overflow-wrap: break-word` on panels
- [ ] Mermaid zoom controls present on every `.mermaid-wrap`
- [ ] CDN URLs match `./references/libraries.md` (not from memory)
- [ ] Code diffs use `@pierre/diffs` (NOT hand-rolled CSS diff panels)
- [ ] File opens cleanly: 0 console errors

## File Structure

Single self-contained `.html` file. No external assets except CDN links. Standard template foundation → diagram-specific styles below the "TEMPLATE-SPECIFIC STYLES" marker → content → optional CDN libraries.
