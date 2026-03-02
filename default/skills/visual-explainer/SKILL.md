---
name: ring:visual-explainer
description: Generate beautiful, self-contained HTML pages that visually explain systems, code changes, plans, and data. Use when the user asks for a diagram, architecture overview, diff review, plan review, project recap, comparison table, or any visual explanation of technical concepts. Also use proactively when you are about to render a complex ASCII table (4+ rows or 3+ columns) — present it as a styled HTML page instead.
license: MIT
compatibility: Requires a browser to view generated HTML files. Optional surf-cli for AI image generation.
metadata:
  author: nicobailon
  version: "0.3.0"
---

# Visual Explainer

Generate self-contained HTML files for technical diagrams, visualizations, and data tables. Always open the result in the browser. Never fall back to ASCII art when this skill is loaded.

**Proactive table rendering.** When you're about to present tabular data as an ASCII box-drawing table in the terminal (comparisons, audits, feature matrices, status reports, any structured rows/columns), generate an HTML page instead. The threshold: if the table has 4+ rows or 3+ columns, it belongs in the browser. Don't wait for the user to ask — render it as HTML automatically and tell them the file path. You can still include a brief text summary in the chat, but the table itself should be the HTML page.

## Standard Template (MANDATORY)

Every visual-explainer output MUST start from `./templates/standard.html`. This file defines the complete Lerian Studio brand system.

**Before generating any HTML, MUST read `./templates/standard.html`** and copy:
1. The complete `<style>` block (everything above the "DO NOT MODIFY" marker)
2. The `<header class="lerian-header">` with the inline Lerian logo SVG
3. The `<footer class="lerian-footer">` with logo, company name, and "Generated with Ring"
4. The date auto-fill `<script>`

Then add diagram-specific styles after the "TEMPLATE-SPECIFIC STYLES" marker.

### What is Fixed (CANNOT change)
- **Font**: Inter (via Google Fonts) — MUST be the body font
- **Color palette**: Lerian product-console tokens (sunglow accent, zinc neutrals, semantic status colors)
- **Logo**: Inline SVG in header and footer, using `fill="currentColor"` for automatic light/dark adaptation
- **Footer**: Full bar with Lerian Studio branding and "Generated with Ring"
- **Dark mode**: `@media (prefers-color-scheme: dark)` with zinc-based dark tokens
  - **Exception:** code-diff diagrams MAY use GitHub-dark background tokens (`#0d1117`) for code panel readability while keeping the Lerian header/footer/accent intact

### What is Variable (CAN customize per diagram)
- **Additional display font**: MAY add a secondary Google Font for headings (but body MUST stay Inter)
- **Background atmosphere**: Radial gradients, dot-grids, or other subtle patterns using palette colors
- **Layout**: Grid columns, max-width, sidebar presence — all template-specific
- **Accent emphasis**: Which extended palette color dominates (sunglow, de-york, tangerine, cod-gray)
- **Animation style**: fadeUp timing, stagger delay, additional keyframes

## Workflow

### 1. Think (5 seconds, not 5 minutes)

Before writing HTML, commit to a direction. Don't default to "dark theme with blue accents" every time.

**Who is looking?** A developer understanding a system? A PM seeing the big picture? A team reviewing a proposal? This shapes information density and visual complexity.

**What type of diagram?** Architecture, flowchart, sequence, data flow, schema/ER, state machine, mind map, data table, timeline, or dashboard. Each has distinct layout needs and rendering approaches (see Diagram Types below).

**What aesthetic?** The standard template defines the brand foundation (Inter font, sunglow accent, zinc neutrals). Within that foundation, pick an atmosphere and commit:
- Editorial (generous whitespace, muted extended palette, clean lines)
- Blueprint (technical drawing feel, grid lines, precise, cod-gray emphasis)
- Neon dashboard (saturated extended palette accents on dark mode, glowing edges)
- Paper/ink (warm cream-tinted surface, hand-drawn feel, sketchy borders)
- Hand-drawn / sketch (Mermaid `handDrawn` mode, wiggly lines, informal whiteboard feel)
- Data-dense (small type, tight spacing, maximum information)
- Gradient mesh (bold gradients using extended palette, glassmorphism, modern SaaS feel)

Vary the choice each time. If the last diagram was dark and technical, make the next one light and editorial. The swap test: if you replaced your template-specific styling with nothing and the page looked generic, you haven't designed anything.

### 2. Structure

**Read the standard template FIRST**, then read the diagram-specific reference template.

MUST read templates (in order):
1. `./templates/standard.html` — brand foundation (ALWAYS read first)
2. `./templates/{diagram-type}.html` — layout reference for the specific diagram type

Diagram-specific templates:
- For text-heavy architecture overviews (card content matters more than topology): read `./templates/architecture.html`
- For flowcharts, sequence diagrams, ER, state machines, mind maps: read `./templates/mermaid-flowchart.html`
- For data tables, comparisons, audits, feature matrices: read `./templates/data-table.html`
- For code diffs, change reviews, refactoring previews: read `./templates/code-diff.html`

**For CSS/layout patterns and SVG connectors**, read `./references/css-patterns.md`.

**For pages with 4+ sections** (reviews, recaps, dashboards), also read `./references/responsive-nav.md` for section navigation with sticky sidebar TOC on desktop and horizontal scrollable bar on mobile.

**Choosing a rendering approach:**

| Diagram type | Approach | Why |
|---|---|---|
| Architecture (text-heavy) | CSS Grid cards + flow arrows | Rich card content (descriptions, code, tool lists) needs CSS control |
| Architecture (topology-focused) | **Mermaid** | Visible connections between components need automatic edge routing |
| Flowchart / pipeline | **Mermaid** | Automatic node positioning and edge routing; hand-drawn mode available |
| Sequence diagram | **Mermaid** | Lifelines, messages, and activation boxes need automatic layout |
| Data flow | **Mermaid** with edge labels | Connections and data descriptions need automatic edge routing |
| ER / schema diagram | **Mermaid** | Relationship lines between many entities need auto-routing |
| State machine | **Mermaid** | State transitions with labeled edges need automatic layout |
| Mind map | **Mermaid** | Hierarchical branching needs automatic positioning |
| Data table | HTML `<table>` | Semantic markup, accessibility, copy-paste behavior |
| Timeline | CSS (central line + cards) | Simple linear layout doesn't need a layout engine |
| Dashboard | CSS Grid + Chart.js | Card grid with embedded charts |
| Code diff / change review | HTML panels + Highlight.js | Side-by-side code with syntax highlighting needs semantic markup and fine-grained line control |

**Mermaid theming:** Always use `theme: 'base'` with custom `themeVariables` so colors match the Lerian palette. Use `look: 'handDrawn'` for sketch aesthetic or `look: 'classic'` for clean lines. Use `layout: 'elk'` for complex graphs (requires the `@mermaid-js/layout-elk` package — see `./references/libraries.md` for the CDN import). Override Mermaid's SVG classes with CSS for pixel-perfect control. See `./references/libraries.md` for full theming guide.

**Mermaid zoom controls:** Always add zoom controls (+/-/reset buttons) to every `.mermaid-wrap` container. Complex diagrams render at small sizes and need zoom to be readable. Include Ctrl/Cmd+scroll zoom on the container. See the zoom controls pattern in `./references/css-patterns.md` and the reference template at `./templates/mermaid-flowchart.html`.

**AI-generated illustrations (optional).** If [surf-cli](https://github.com/nicobailon/surf-cli) is available, you can generate images via Gemini and embed them in the page for creative, illustrative, explanatory, educational, or decorative purposes. Check availability with `which surf`. If available:

```bash
# Generate to a temp file (use --aspect-ratio for control)
surf gemini "descriptive prompt" --generate-image /tmp/ve-img.png --aspect-ratio 16:9

# Base64 encode for self-containment (macOS)
IMG=$(base64 -i /tmp/ve-img.png)
# Linux: IMG=$(base64 -w 0 /tmp/ve-img.png)

# Embed in HTML and clean up
# <img src="data:image/png;base64,${IMG}" alt="descriptive alt text">
rm /tmp/ve-img.png
```

See `./references/css-patterns.md` for image container styles (hero banners, inline illustrations, captions).

**When to use:** Hero banners that establish the page's visual tone. Conceptual illustrations for abstract systems that Mermaid can't express (physical infrastructure, user journeys, mental models). Educational diagrams that benefit from artistic or photorealistic rendering. Decorative accents that reinforce the aesthetic.

**When to skip:** Anything Mermaid or CSS handles well. Generic decoration that doesn't convey meaning. Data-heavy pages where images would distract. Always degrade gracefully — if surf isn't available, skip images without erroring. The page should stand on its own with CSS and typography alone.

**Prompt craft:** Match the image to the Lerian palette and aesthetic direction. Specify the style (3D render, technical illustration, watercolor, isometric, flat vector, etc.) and mention dominant colors from the standard template's CSS variables (sunglow yellow, zinc neutrals, de-york green, tangerine orange). Use `--aspect-ratio 16:9` for hero banners, `--aspect-ratio 1:1` for inline illustrations. Keep prompts specific — "isometric illustration of a message queue with sunglow-yellow nodes on zinc-800 background" beats "a diagram of a queue."

### 3. Style

Apply these principles to every diagram, building ON TOP of the standard template foundation:

**Typography starts with Inter.** The body font is ALWAYS Inter, loaded from the standard template. MAY add a secondary display font from Google Fonts for h1/h2 headings only — a display font with character that complements Inter. Load the secondary font via an additional `<link>` in `<head>`. Include a system font fallback in the `font-family` stack for offline resilience. The mono font is `var(--font-mono)` from the standard template.

**Color tells a story.** The standard template defines the full palette via CSS custom properties: `--bg`, `--surface`, `--border`, `--text`, `--text-secondary`, `--text-muted`, the `--accent` (sunglow), semantic status colors (`--success`, `--warning`, `--error`, `--info`), and the extended palette (`--sunglow-*`, `--de-york-*`, `--tangerine-*`, `--cod-gray-*`). Use these tokens. For diagram-specific node colors, map to the extended palette — e.g., `--node-a` could alias `--de-york-400`, `--node-b` could alias `--tangerine-500`. Name variables semantically when possible (`--pipeline-step` not `--blue-3`). Both light and dark modes are handled by the standard template.

**Surfaces whisper, they don't shout.** Build depth through subtle lightness shifts (2-4% between levels), not dramatic color changes. Borders should be low-opacity (`var(--border-subtle)` in most cases, `var(--border)` for card edges) — visible when you look, invisible when you don't.

**Backgrounds create atmosphere.** Don't use flat solid colors for the page background. Subtle gradients, faint grid patterns via CSS, or gentle radial glows behind focal areas using the Lerian palette colors. The background should feel like a space, not a void.

**Visual weight signals importance.** Not every section deserves equal visual treatment. Executive summaries and key metrics should dominate the viewport on load (larger type, more padding, subtle accent-tinted background zone). Reference sections (file maps, dependency lists, decision logs) should be compact and stay out of the way. Use `<details>/<summary>` for sections that are useful but not primary — the collapsible pattern is in `./references/css-patterns.md`.

**Surface depth creates hierarchy.** Use the standard template's `.card` and `.card-elevated` classes as the base. For hero sections, tint the background with `var(--accent-dim)`. For recessed content, use `var(--surface-muted)`. See the depth tiers in `./references/css-patterns.md`. Don't make everything elevated — when everything pops, nothing does.

**Animation earns its place.** Use the standard template's `.animate` class with `--i` stagger variable. Mix animation types by role: `fadeUp` for cards, `fadeScale` for KPIs and badges, `drawIn` for SVG connectors, `countUp` for hero numbers. Hover transitions on interactive-feeling elements make the diagram feel alive. Always respect `prefers-reduced-motion` (already handled by the standard template). CSS transitions and keyframes handle most cases. For orchestrated multi-element sequences, anime.js via CDN is available (see `./references/libraries.md`).

### 4. Deliver

**Output location:** Write to `~/.agent/diagrams/`. Use a descriptive filename based on content: `modem-architecture.html`, `pipeline-flow.html`, `schema-overview.html`. The directory persists across sessions.

**Open in browser:**
- macOS: `open ~/.agent/diagrams/filename.html`
- Linux: `xdg-open ~/.agent/diagrams/filename.html`

**Tell the user** the file path so they can re-open or share it.

## Diagram Types

### Architecture / System Diagrams
Two approaches depending on what matters more:

**Text-heavy overviews** (card content matters more than connections): CSS Grid with explicit row/column placement. Sections as rounded cards with colored borders and monospace labels. Vertical flow arrows between sections. Nested grids for subsystems. The reference template at `./templates/architecture.html` demonstrates this pattern. Use when cards need descriptions, code references, tool lists, or other rich content that Mermaid nodes can't hold.

**Topology-focused diagrams** (connections matter more than card content): **Use Mermaid.** A `graph TD` or `graph LR` with custom `themeVariables` produces proper diagrams with automatic edge routing. Use `look: 'handDrawn'` for informal feel or `look: 'classic'` for clean lines. Use when the point is showing how components connect rather than describing what each component does in detail.

### Flowcharts / Pipelines
**Use Mermaid.** Automatic node positioning and edge routing produces proper diagrams with connecting lines, decision diamonds, and parallel branches — dramatically better than CSS flexbox with arrow characters. Use `graph TD` for top-down or `graph LR` for left-right. Use `look: 'handDrawn'` for sketch aesthetic. Color-code node types with Mermaid's `classDef` or rely on `themeVariables` for automatic styling.

### Sequence Diagrams
**Use Mermaid.** Lifelines, messages, activation boxes, notes, and loops all need automatic layout. Use Mermaid's `sequenceDiagram` syntax. Style actors and messages via CSS overrides on `.actor`, `.messageText`, `.activation` classes.

### Data Flow Diagrams
**Use Mermaid.** Data flow diagrams emphasize connections over boxes — exactly what Mermaid excels at. Use `graph LR` or `graph TD` with edge labels for data descriptions. Thicker, colored edges for primary flows. Source/sink nodes styled differently from transform nodes via Mermaid's `classDef`.

### Schema / ER Diagrams
**Use Mermaid.** Relationship lines between entities need automatic routing. Use Mermaid's `erDiagram` syntax with entity attributes. Style via `themeVariables` and CSS overrides on `.er.entityBox` and `.er.relationshipLine`.

### State Machines / Decision Trees
**Use Mermaid.** Use `stateDiagram-v2` for states with labeled transitions. Supports nested states, forks, joins, and notes. Use `look: 'handDrawn'` for informal state diagrams. Decision trees can use `graph TD` with diamond decision nodes.

**`stateDiagram-v2` label caveat:** Transition labels have a strict parser — colons, parentheses, `<br/>`, HTML entities, and most special characters cause silent parse failures ("Syntax error in text"). If your labels need any of these (e.g., `cancel()`, `curate: true`, multi-line labels), use `flowchart LR` instead with rounded nodes and quoted edge labels (`|"label text"|`). Flowcharts handle all special characters and support `<br/>` for line breaks. Reserve `stateDiagram-v2` for simple single-word or plain-text labels.

### Mind Maps / Hierarchical Breakdowns
**Use Mermaid.** Use `mindmap` syntax for hierarchical branching from a root node. Mermaid handles the radial layout automatically. Style with `themeVariables` to control node colors at each depth level.

### Data Tables / Comparisons / Audits
Use a real `<table>` element — not CSS Grid pretending to be a table. Tables get accessibility, copy-paste behavior, and column alignment for free. The reference template at `./templates/data-table.html` demonstrates all patterns below.

**Use proactively.** Any time you'd render an ASCII box-drawing table in the terminal, generate an HTML table instead. This includes: requirement audits (request vs plan), feature comparisons, status reports, configuration matrices, test result summaries, dependency lists, permission tables, API endpoint inventories — any structured rows and columns.

Layout patterns:
- Sticky `<thead>` so headers stay visible when scrolling long tables
- Alternating row backgrounds via `tr:nth-child(even)` (subtle, 2-3% lightness shift)
- First column optionally sticky for wide tables with horizontal scroll
- Responsive wrapper with `overflow-x: auto` for tables wider than the viewport
- Column width hints via `<colgroup>` or `th` widths — let text-heavy columns breathe
- Row hover highlight for scanability

Status indicators (use styled `<span>` elements, never emoji):
- Match/pass/yes: colored dot or checkmark with green background
- Gap/fail/no: colored dot or cross with red background
- Partial/warning: amber indicator
- Neutral/info: dim text or muted badge

Cell content:
- Wrap long text naturally — don't truncate or force single-line
- Use `<code>` for technical references within cells
- Secondary detail text in `<small>` with dimmed color
- Keep numeric columns right-aligned with `tabular-nums`

### Timeline / Roadmap Views
Vertical or horizontal timeline with a central line (CSS pseudo-element). Phase markers as circles on the line. Content cards branching left/right (alternating) or all to one side. Date labels on the line. Color progression from past (muted) to future (vivid).

### Dashboard / Metrics Overview
Card grid layout. Hero numbers large and prominent. Sparklines via inline SVG `<polyline>`. Progress bars via CSS `linear-gradient` on a div. For real charts (bar, line, pie), use **Chart.js via CDN** (see `./references/libraries.md`). KPI cards with trend indicators (up/down arrows, percentage deltas).

### Code Diff / Change Review
Use for refactoring previews (before/after code comparison), development cycle change summaries, and any approval checkpoint that needs to show what will change. The reference template at `./templates/code-diff.html` demonstrates all patterns below.

Two modes depending on context:
- **Refactoring diffs** (before/after known): Two-column layout with the current code on the left and the Ring standard / target code on the right. Each finding gets its own diff panel with a severity badge. Group by severity (Critical first).
- **New development summaries** (planned changes): Single-column cards showing the task context, acceptance criteria, files to create/modify, and a code preview of the planned implementation approach.

Layout patterns:
- Responsive nav sidebar (read `./references/responsive-nav.md`) — one TOC entry per finding or task
- Summary KPI cards at top: Total changes, files affected, severity breakdown
- Per-finding/task collapsible `<details>` section with the diff panel inside
- Syntax highlighting via Highlight.js CDN (see `./references/libraries.md`)
- Line numbers in code blocks via CSS counter (see `./references/css-patterns.md` -> Code Diff Enhancements)
- Added lines highlighted green, removed lines highlighted red, unchanged lines dimmed
- File path + line range header above each code block (`.diff-hunk-header`)
- Severity badge (Critical/High/Medium/Low) with color-coded indicator on each section header (`.severity-badge`)
- Finding card wrapper (`.finding-card`) with header showing finding ID + severity + file path

## File Structure

Every diagram is a single self-contained `.html` file. No external assets except CDN links (fonts, optional libraries). Structure follows the standard template:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Descriptive Title</title>
  <!-- Inter font (from standard template) -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Optional: secondary display font for headings -->
  <link href="https://fonts.googleapis.com/css2?family=DisplayFont&display=swap" rel="stylesheet">
  <style>
    /* ===== LERIAN STANDARD FOUNDATION (copied from standard.html) ===== */
    /* ... all tokens, base styles, header, footer, animations ... */
    /* ===== DO NOT MODIFY ABOVE THIS LINE ===== */

    /* ===== TEMPLATE-SPECIFIC STYLES ===== */
    /* Diagram-specific layout, components, colors */
  </style>
</head>
<body>
  <div class="container">
    <!-- Lerian header with logo SVG -->
    <header class="lerian-header">...</header>

    <!-- Diagram content -->

    <!-- Lerian footer with logo, company name, "Generated with Ring" -->
    <footer class="lerian-footer">...</footer>
  </div>

  <!-- Date auto-fill script -->
  <script>
    var footerDate = document.querySelector('.footer-date');
    if (footerDate) footerDate.textContent = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  </script>
  <!-- Optional: Mermaid, Chart.js, anime.js, Highlight.js -->
</body>
</html>
```

## Quality Checks

Before delivering, verify:
- **Standard template compliance**: Does the page include the Lerian header with logo, footer with "Generated with Ring", and the full standard `<style>` block? Is Inter the body font?
- **No token conflicts:** Template-specific CSS does NOT redefine standard foundation tokens (`--bg`, `--surface`, `--text`, `--accent`, `--font-body`, `--font-mono`, `--success`, `--warning`, `--error`, `--info`, `--border`). Use NEW variable names for diagram-specific aliases (e.g., `--node-a`, `--pipeline-step`).
- **The squint test**: Blur your eyes. Can you still perceive hierarchy? Are sections visually distinct? (Verify at least 3 distinct visual depth levels: hero/elevated, default surface, recessed/muted)
- **The swap test**: Would replacing your template-specific styles with nothing make this indistinguishable from the raw standard template? If yes, push the aesthetic further. (Template-specific CSS must define at least: 1 background atmosphere, 2+ semantic color aliases, and component-specific classes)
- **Both themes**: Toggle your OS between light and dark mode. Both should look intentional, not broken. The standard template handles base dark mode, but verify diagram-specific styles also adapt.
- **Information completeness**: Does the diagram actually convey what the user asked for? Pretty but incomplete is a failure.
- **No overflow**: Resize the browser to different widths. No content should clip or escape its container. Every grid and flex child needs `min-width: 0`. Side-by-side panels need `overflow-wrap: break-word`. Never use `display: flex` on `<li>` for marker characters — it creates anonymous flex items that can't shrink, causing lines with many inline `<code>` badges to overflow. Use absolute positioning for markers instead. See the Overflow Protection section in `./references/css-patterns.md`.
- **Mermaid zoom controls**: Every `.mermaid-wrap` container must have zoom controls (+/-/reset buttons), Ctrl/Cmd+scroll zoom, and click-and-drag panning. Complex diagrams render too small without them. The cursor should change to `grab` when zoomed in and `grabbing` while dragging. See `./references/css-patterns.md` for the full pattern.
- **File opens cleanly**: No console errors, no broken font loads, no layout shifts. (Browser DevTools console shows 0 errors on load)

## Standards Loading
MANDATORY: You must load project standards if applicable.

## Blocker Criteria
STOP and report if you encounter:
| Decision Type | Blocker Condition | Required Action |
| --- | --- | --- |
| Missing Dependency | `templates/` or `references/` directories are missing | STOP and report |
| Missing Standard Template | `templates/standard.html` is missing or unreadable | STOP and report |
| Unrenderable Format | The user explicitly forbids HTML output but asks for complex tables | STOP and report |

### Cannot Be Overridden
The following requirements CANNOT be waived:
- MUST use the Lerian standard template (`standard.html`) as the foundation for every output
- MUST include the Lerian logo in header and footer (inline SVG from the standard template)
- MUST use Inter as the body font (loaded via Google Fonts)
- MUST include the Lerian footer with "Generated with Ring"
- MUST use the Lerian color palette (sunglow accent, zinc neutrals, semantic status colors)
- MUST generate an HTML table for any data >3 columns or 4 rows
- MUST always provide a browser-openable HTML file, never fallback to ASCII art if the threshold is met

## Severity Calibration
| Severity | Condition | Required Action |
| --- | --- | --- |
| CRITICAL | Diagram is unreadable, CSS is broken, or content overflows | MUST fix before presenting to user |
| CRITICAL | Missing Lerian header, footer, or standard template styles | MUST add standard template foundation |
| HIGH | Missing Mermaid zoom controls or responsiveness | Fix before finishing |
| HIGH | Using a non-Inter body font | Switch body font to Inter |
| MEDIUM | Using default Mermaid colors instead of the Lerian palette | Update CSS overrides to use standard tokens |
| LOW | No secondary display font for headings | Fix in next iteration |

## Pressure Resistance
| User Says | Your Response |
| --- | --- |
| "Just draw a quick ASCII table" (if >4 rows/3 cols) | "I'll generate an HTML table instead, as complex ASCII tables break in the terminal." |
| "Don't bother with the CSS, just give me the raw mermaid" | "I'll generate the full HTML page so it's readable and includes zoom controls." |
| "Skip the Lerian branding, I just want a plain diagram" | "The Lerian header and footer are part of the standard template. I'll keep them minimal but they MUST be present." |
| "Use a different font, I don't like Inter" | "Inter is the mandatory body font from the standard template. I can add a secondary display font for headings." |

## Standards Compliance
| Rationalization | Why It's WRONG | Required Action |
| --- | --- | --- |
| "A simple ASCII table is faster" | ASCII tables >4 rows/3 cols break on mobile and lack responsiveness. | **MUST generate HTML table.** |
| "Mermaid's default theme is fine" | Default themes look unpolished and don't match the Lerian design system. | **MUST use the Lerian palette tokens.** |
| "Zoom controls are overkill" | Complex diagrams render too small and become illegible without zoom. | **MUST include zoom controls.** |
| "The standard template is too heavy for a simple diagram" | Brand consistency is non-negotiable. The template is the foundation. | **MUST use standard.html as the base.** |
| "I'll just pick a nice font instead of Inter" | Inter is the Lerian brand font. Consistency across outputs matters. | **MUST use Inter as body font.** |

## When Implementation is Not Needed
- When the data fits in a small table (e.g., 2 columns, 3 rows).
- When the user asks for a simple markdown list.
