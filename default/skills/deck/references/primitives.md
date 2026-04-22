# Primitives

These are the CSS primitives available. Compose them as the narrative requires. All primitives use tokens from [`brand.md`](brand.md); don't reinvent colors, fonts, or spacing. Canvas rules (dimensions, flex, 24px floor) come from [`engineering.md`](engineering.md) — primitives do not override them.

**HARD GATE (engineering):** primitive CSS classes MUST NOT be redefined with new base styles — their class-level rules below are canon and load-bearing for visual consistency across decks. Inline `style=""` tweaks for one-off positioning (margin, width, color override) are fine.

This is an inventory of atoms, not a prescription for composition. When and where to use them is a creative choice — the "When to use" / "When NOT to use" notes below are guidance based on what has worked, not rules you must obey.

## Table of Contents

| # | Primitive | When to use |
| --- | --- | --- |
| 1 | [eyebrow](#eyebrow) | Small uppercase mono label above every h1, every section opener, every card title |
| 2 | [pill](#pill) | Rounded tag for category, status, segment, time-box on a row |
| 3 | [kpi](#kpi) | Stacked label + big Poppins number + sub — the single-metric tile |
| 4 | [ticks](#ticks) | Bulleted list with 10×10 Amarelo squares instead of dots |
| 5 | [numbered](#numbered) | Ordinal list with mono `01/02/03` gutter — steps, discussion questions |
| 6 | [table.grid](#tablegrid) | Editorial data tables — agendas, summary rows, side-by-side comps |
| 7 | [dashed-hairline](#dashed-hairline) | "Related but secondary" divider — the soft cousin of `.rule` |
| 8 | [narrative-arc](#narrative-arc) | Cross-slide threading callout — directional, names two slides by name |
| 9 | [transition-column](#transition-column) | Semantic hinge between two cards — old→new, manual→automated, legacy→modern |
| 10 | [org-node-flag](#org-node-flag) | Tab-style status badge hanging off the top edge of a card — PAIN POINT, NEW, HIRE |
| 11 | [dual-sided-argument](#dual-sided-argument) | Two-column symmetric-benefit card — same argument, two stakeholder perspectives |
| 12 | [inline-mini-legend](#inline-mini-legend) | Legend dots embedded inline inside a caption sentence — 2–3 categories |

---

## eyebrow

**Purpose:** small uppercase monospace label that sits above every h1, every card title, every chart caption. It's the editorial anchor that tells the eye "this is a new unit."

**Common uses:**
- Above a headline (`.eyebrow` → `h1`) as an anchor label
- As a section label inside a card or column ("Context", "Ownership", "Details")
- As a caption above a chart, table, or micro-data block
- Inside a meta-row (e.g., paired with a hairline: `<div class="eyebrow">Discussion 01</div> ... <div class="eyebrow">~12 min</div>`)

**Avoid:**
- As a standalone headline — it is support text, not a title
- Below the h1 (reverses the reading order)
- For body copy — use IBM Plex Serif at `--t-body` instead
- At sizes other than `--t-eyebrow` (22px) without deliberate override; 14px sub-eyebrows are used inline for deep labels

**HTML:**
```html
<div class="eyebrow">{eyebrow text}</div>
```

**CSS:**
```css
.eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--t-eyebrow);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--c-ink-3);
}
.slide.dark .eyebrow  { color: var(--c-accent); }
.slide.accent .eyebrow { color: rgba(25,26,27,0.72); }
```

**Variants:**

| Variant | How | Where observed |
| --- | --- | --- |
| Default | `<div class="eyebrow">…</div>` | Every content slide headline |
| Dark slide | auto (`.slide.dark` → Amarelo text) | Metric-summary slide, dark panels |
| Accent slide | auto (`.slide.accent` → 72%-black) | Act divider openers |
| Amarelo highlight | `style="color: var(--c-accent)"` | "Framing", "Questions for the audience", "Decision point" — signals a callout |
| Verde highlight | `style="color: var(--c-accent-2)"` | "Supporting signal" — secondary accent |
| In-card (small) | `style="font-size: 14px; color: var(--c-ink)"` | Item-tile headers ("Segment A") |

**Composition example:**
```html
<div class="eyebrow">{eyebrow text}</div>
<h1 style="margin-top: 28px; max-width: 1600px;">{headline}</h1>
```

**Timer-row pattern (paired eyebrows with hairline between):**
```html
<div style="display: flex; align-items: center; gap: 18px;">
  <div class="eyebrow">Discussion 01</div>
  <div style="height: 1px; flex: 1; background: var(--c-rule);"></div>
  <div class="eyebrow">~12 min</div>
</div>
```

The `.eyebrow` primitive is used across the example templates — `../templates/slide-content.html`, `../templates/slide-content-paper.html`, `../templates/slide-content-dark.html`, `../templates/slide-content-accent.html`, `../templates/slide-agenda.html`, `../templates/slide-appendix-intro.html`, `../templates/slide-appendix-content.html`, and `../templates/slide-cover.html`. The timer-row pattern shown above is a common composition on the same primitive.

---

## pill

**Purpose:** rounded tag for category, segment, status, or short time-box label. Sits inline next to a Poppins name or inside a row flex.

**Common uses:**
- Tagging a row with a category ("Tier A", "Tier B")
- Marking new items in a list ("New")
- Short caption tags ("Segment A", "the majority of items")
- Funnel-stage labels beside a headline ("Top of Funnel", "Cycle Mechanics")

**Avoid:**
- As the primary headline — it is chrome, not content
- As a button (deck is a projection surface; there are no clicks)
- For multi-word copy that wraps — pills are single-line
- Dense rows (beyond ~6) start reading as chips, not pills — consider splitting

**HTML:**
```html
<span class="pill">Tier A</span>
<span class="pill accent">New</span>
<span class="pill solid">Tier B</span>
```

**CSS:**
```css
.pill {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; letter-spacing: 0.04em; text-transform: uppercase;
  padding: 8px 14px; border-radius: 999px;
  border: 1px solid var(--c-rule); background: transparent; color: var(--c-ink-2);
}
.pill.solid  { background: var(--c-ink);    color: var(--c-ink-inv);    border-color: transparent; }
.pill.accent { background: var(--c-accent); color: var(--c-accent-ink); border-color: transparent; }
```

**Variants:**

| Variant | Class | Background | Text | Use |
| --- | --- | --- | --- | --- |
| Default (outline) | `.pill` | transparent | `--c-ink-2` | Neutral tag — "Tier A", "Top of Funnel" |
| Solid (dark) | `.pill.solid` | `--c-ink` | white | Emphatic tag — "Tier B", funnel stage |
| Accent (Amarelo) | `.pill.accent` | `--c-accent` | `--c-accent-ink` | "New", brand-signal tag |

**Observed inline override:** one-off pill with accent background + `white-space: nowrap` for a short stat caption. Prefer `.pill.accent` for that case going forward; the inline form is not a new variant.

**Composition example — chip row with wrapping:**
```html
<div style="margin-top: 56px; display: flex; gap: 14px; flex-wrap: wrap;">
  <span class="pill solid">{chip 1}</span>
  <span class="pill solid">{chip 2}</span>
  <span class="pill solid">{chip 3}</span>
</div>
```

**Composition example — item row (name + pills):**
```html
<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
  <span style="font-family: 'Poppins'; font-weight: 500; font-size: 26px;">{item name}</span>
  <span class="pill">{tag}</span>
  <span class="pill accent">{accent tag}</span>
</div>
```

`.pill.solid` is used in `../templates/slide-act-divider.html` — the chip row there uses a local `.act-pill` class with an inverted number chip. The outline (`.pill`) and accent (`.pill.accent`) variants are defined in the base stylesheet and available for reuse wherever an inline tag next to a Poppins name fits.

---

## kpi

**Purpose:** the single-metric tile. Stacks a mono label over a big Poppins number over a small sub-caption. Composes into 3- or 4-column KPI walls.

**Common uses:**
- KPI walls (3–4 metrics on one slide)
- Inside a left column paired with a chart on the right
- Dark-panel summary rows on statement slides

**Avoid:**
- For numbers that need to sit inline with sentence prose — use a Poppins `<span>` instead
- For ultra-hero single numbers (180–240px) — those are standalone, not tiles; see `engineering.md` Hero Numbers
- When the caption is longer than ~80 chars — kpi.sub is designed for one short line

**HTML:**
```html
<div class="kpi">
  <div class="label">Metric A</div>
  <div class="value">120</div>
  <div class="sub">Sub-metric 45 · +120% YoY · +24% MoM</div>
</div>
```

**CSS:**
```css
.kpi { display: flex; flex-direction: column; gap: 10px; }
.kpi .label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--c-ink-3);
}
.kpi .value {
  font-family: 'Poppins', sans-serif;
  font-weight: 500; font-size: 96px; line-height: 0.95; letter-spacing: -0.03em;
  color: var(--c-ink);
}
.kpi .sub { font-size: 22px; color: var(--c-ink-3); }
.slide.dark .kpi .value { color: var(--c-ink-inv); }
.slide.dark .kpi .label,
.slide.dark .kpi .sub   { color: rgba(255,255,255,0.55); }
```

**Variants:**

| Variant | How | Where observed |
| --- | --- | --- |
| Default | `<div class="kpi">` with 96px value | Metric-summary slide, generic tiles |
| Accent value | `style="color: var(--c-accent)"` on `.value` | Primary KPI on a dark slide ("120") |
| Reduced value | `style="font-size: 76px"` (or 60px) on `.value` | When three tiles stack vertically and 96px blows the column |
| Dark-slide auto | auto via `.slide.dark` | Value goes white, label/sub drop to 55% opacity |
| Inline sub-span | `<span style="font-size: 26px; font-weight: 400; color: rgba(255,255,255,0.55);">target</span>` inside `.value` | "130% target" — appendix to the hero number |

**Composition example — 4-up KPI row on a dark panel:**
```html
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 40px;">
  <div class="kpi">
    <div class="label">Stage</div>
    <div class="value" style="font-size: 76px;">Stage A</div>
  </div>
  <div class="kpi">
    <div class="label">Window</div>
    <div class="value" style="font-size: 76px;">20 – 32 mo</div>
  </div>
  <div class="kpi">
    <div class="label">Volume</div>
    <div class="value" style="font-size: 76px;">5.9 active</div>
  </div>
  <div class="kpi">
    <div class="label" style="color: var(--c-accent);">Readiness</div>
    <div class="value" style="font-size: 76px;">Inflection</div>
  </div>
</div>
```

The dark-panel variant of this primitive is used in `../templates/slide-content-dark.html` — the local `.dark-kpi` class in that template is the canonical `.slide.dark .kpi` rendering (white value, 55%-white label/sub). The light-panel `.kpi` shape composes cleanly inside any `.slide` or `.slide.paper` context when you need a metric tile or a 3-/4-up KPI row.

**HARD GATE (engineering):** when three `.kpi` tiles stack vertically inside a column, reduce `.value` to 60–76px. The 96px default assumes one row of tiles, not three stacked — keep it and the type overflows.

---

## ticks

**Purpose:** custom-bulleted list. 10×10 Amarelo square marker replaces the dot bullet — Lerian's list fingerprint.

**Common uses:**
- "Context" columns or evidence blocks under a headline
- Any 3–6 item editorial list where each item is 1–3 lines

**Avoid:**
- For step-ordered content — [`numbered`](#numbered) carries ordinal meaning; ticks don't
- Long lists (>6) dilute the square rhythm — consider splitting or trimming
- For single-line tag sequences — [`pill`](#pill) in a flex row reads better

**HTML:**
```html
<ul class="ticks">
  <li>{tick item with optional <strong>emphasis</strong>}</li>
  <li>{tick item}</li>
  <li>{tick item}</li>
</ul>
```

**CSS:**
```css
ul.ticks { list-style: none; padding: 0; margin: 0; }
ul.ticks li {
  position: relative; padding-left: 28px;
  font-size: 22px; line-height: 1.5; margin-bottom: 18px;
}
ul.ticks li::before {
  content: ""; width: 10px; height: 10px;
  background: var(--c-accent);
  display: block; border-radius: 2px;
  transform: translateY(12px);
}
```

**Variants:**
- Default is the only variant observed in the reference. No dark-slide override is defined — inherit body color from `.slide.dark p, .slide.dark li { color: rgba(255,255,255,0.78); }` in the base; the Amarelo square reads against both light and dark surfaces without a variant.
- Common inline adjustment: `style="flex: 1;"` on the `<ul>` so it stretches when the parent column is a flex container (discussion slides).

**Note on 22px font-size:** this is below the 24px body floor from `engineering.md`. The reference uses 22px intentionally for list density. Prefer 24px when shipping new slides. If staying at 22px, treat it as a chrome-density exception (documented in `engineering.md` Minimum Text Size table, row "18–22px … small labels") and MUST NOT go lower.

**Composition example — list column with eyebrow:**
```html
<div class="eyebrow" style="margin-bottom: 24px; color: var(--c-ink);">{section label}</div>
<ul class="ticks" style="flex: 1;">
  <li>{tick item}</li>
  <li>{tick item with optional <strong>emphasis</strong>}</li>
  <li>{tick item}</li>
</ul>
```

The Amarelo square reads against `.slide` (white), `.slide.paper`, and `.slide.dark` without variant overrides. See `../templates/slide-content-paper.html` for one example composition — a "Context" column of ticks on the paper surface.

---

## numbered

**Purpose:** ordinal list. Mono `01 / 02 / 03` gutter on the left, Poppins/Serif content on the right. For steps, questions, priorities where order matters.

**Common uses:**
- Step-by-step process lists
- Ranked priorities
- Discussion-question blocks (one common pattern)

**Avoid:**
- Unordered lists — [`ticks`](#ticks) carries the "no order" meaning
- When the numerals themselves need to be huge (20–150px) — use a hero-number layout, not a list gutter

**HTML (canonical form, using the `ul.numbered` class):**
```html
<ul class="numbered">
  <li>
    <span class="n">01</span>
    <div>{item one}</div>
  </li>
  <li>
    <span class="n">02</span>
    <div>{item two}</div>
  </li>
</ul>
```

**CSS:**
```css
ul.numbered {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 24px;
}
ul.numbered li {
  display: grid; grid-template-columns: 60px 1fr; gap: 28px; align-items: baseline;
  font-size: var(--t-body); line-height: 1.4;
}
ul.numbered li .n {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; letter-spacing: 0.06em;
  color: var(--c-ink-3); padding-top: 8px;
}
```

**Variants:**

| Variant | How | Where observed |
| --- | --- | --- |
| Default (light) | `ul.numbered` on `.slide` | Canonical form per CSS |
| Dark-panel, Amarelo numerals | Inline-flex blocks on dark card, `.n` in Amarelo, Poppins title + Serif sub | "Questions for the audience" blocks on discussion slides |

**Two forms shipped.** (a) `ul.numbered` — canonical list form for simple ordered lists on light slides. (b) Inline dark-panel variant — dark `<div>` card with `display: flex` rows, `<span>` numeral in `JetBrains Mono` + Amarelo, `<div>` title/sub. Both are canonical. Prefer the class form for plain ordered lists; use the inline dark variant when each item needs title + body on a dark card (e.g., "Questions for the audience").

**Composition example — dark numbered card (inline variant):**
```html
<div style="background: var(--c-ink); color: var(--c-ink-inv); padding: 40px 44px;
            border-radius: 4px; display: flex; flex-direction: column; gap: 24px;
            justify-content: space-between;">
  <div class="eyebrow" style="color: var(--c-accent);">{eyebrow text}</div>

  <div style="display: flex; gap: 14px;">
    <span style="font-family: 'JetBrains Mono'; color: var(--c-accent);
                 font-size: 16px; flex-shrink: 0; padding-top: 8px;">01</span>
    <div>
      <div style="font-family: 'Poppins'; font-size: 24px; font-weight: 500;
                  color: var(--c-ink-inv); line-height: 1.25;">{item title}</div>
      <div style="font-size: 17px; line-height: 1.5;
                  color: rgba(255,255,255,0.75); margin-top: 6px;">
        {optional sub-copy}
      </div>
    </div>
  </div>
  <!-- more items … -->
</div>
```

One example of the dark-card numbered variant (Amarelo numeral + Poppins title + Serif sub on `background: var(--c-ink)`) lives in `../templates/slide-content-paper.html`. The light-slide `ul.numbered` class form is equally valid for ranked-step lists on any light surface.

---

## table.grid

**Purpose:** the editorial data grid. Hairline rules top and bottom, generous row padding, JetBrains Mono column headers, tabular-nums for numeric cells, Amarelo highlight row for the emphatic line.

**Common uses:**
- Agenda tables
- Summary grids and numeric snapshots
- Side-by-side comparisons with ≥3 columns
- Any data set where row rhythm carries meaning

**Avoid:**
- 1-column or 2-column lists where an editorial row would read as overengineered — [`ticks`](#ticks) or a `div` row is lighter
- For layouts that need fixed column heights — `table.grid` is content-sized (see `engineering.md` Fixed-Height Cards — FORBIDDEN)
- Inside a scrollable container — the canvas is 1080px tall; rows MUST fit

**HTML:**
```html
<table class="grid" style="margin-top: 72px;">
  <thead>
    <tr>
      <th style="width: 100px;">{col 1}</th>
      <th>{col 2}</th>
      <th style="width: 160px; text-align: right;">{col 3}</th>
      <th style="width: 220px; text-align: right;">{col 4}</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="num">01</td>
      <td style="font-size: 28px; font-family: 'Poppins'; color: var(--c-ink);">{row title}</td>
      <td class="num" style="text-align: right;">{value}</td>
      <td style="text-align: right; color: var(--c-ink-3);">{aux}</td>
    </tr>
    <tr class="hl">
      <td class="num">04</td>
      <td style="font-size: 28px; font-family: 'Poppins';">{highlight row title}
        <span style="opacity: 0.62; font-weight: 400;">— {optional sub-copy}</span></td>
      <td class="num" style="text-align: right;">{value}</td>
      <td style="text-align: right; font-weight: 600;">{aux}</td>
    </tr>
  </tbody>
</table>
```

**CSS:**
```css
table.grid {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--t-small);
}
table.grid th, table.grid td {
  text-align: left; padding: 18px 20px;
  border-top: 1px solid var(--c-rule);
  color: var(--c-ink-2);
  vertical-align: top;
}
table.grid th {
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--c-ink-3); font-weight: 500;
  border-top: none;
  padding-bottom: 14px;
}
table.grid tr:last-child td        { border-bottom: 1px solid var(--c-rule); }
table.grid td.num                  { font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; color: var(--c-ink); }
table.grid tr.hl td                { background: var(--c-accent); color: var(--c-accent-ink); font-weight: 500; }
table.grid tr.hl td.num            { color: var(--c-accent-ink); }
table.grid.compact th,
table.grid.compact td              { padding: 10px 16px; }
table.grid.compact th              { font-size: 14px; padding-bottom: 8px; }
table.grid.compact.tight th,
table.grid.compact.tight td        { padding: 7px 14px; font-size: 18px; }
table.grid.compact.tight td:last-child { font-size: 17px; color: var(--c-ink-2); }
```

**Variants:**

| Variant | Class | Row padding | Font | Use |
| --- | --- | --- | --- | --- |
| Default | `table.grid` | `18px 20px` | `--t-small` (22px) | Agendas, summary grids, most editorial tables |
| Highlight row | `tr.hl` (on any density) | inherits | bg Amarelo, ink preto | The emphatic line ("Debate", "Total") |
| Numeric cell | `td.num` | inherits | JetBrains Mono, tabular-nums | Ordinal + numeric figures |
| Compact | `table.grid.compact` | `10px 16px` | 14px th / 22px td | Higher-density grids (defined; unused in reference) |
| Compact-tight | `table.grid.compact.tight` | `7px 14px` | 18px th/td, 17px last col | Dense grids with an axis-label last column (defined; unused in reference) |

**Density variants — compact and compact-tight.** `compact` (10px 16px padding, 14px/22px type) for grids where default density would overflow the canvas. `compact-tight` (7px 14px, 18px type, 17px last col) for dense grids with an axis-label last column — e.g., summary with Q1..Q4 + YoY.

**Composition example — summary grid with a highlight row:**
```html
<table class="grid">
  <thead><tr>
    <th>{row label col}</th>
    <th style="text-align: right;">{col 1}</th>
    <th style="text-align: right;">{col 2}</th>
    <th style="text-align: right;">{col 3}</th>
  </tr></thead>
  <tbody>
    <tr><td style="font-size: 22px; font-family: 'Poppins'; color: var(--c-ink);">{row 1}</td>
        <td class="num" style="text-align: right;">{n}</td>
        <td class="num" style="text-align: right;">{n}</td>
        <td class="num" style="text-align: right;">{n}</td></tr>
    <tr class="hl"><td style="font-size: 22px; font-family: 'Poppins';">{highlight row}</td>
        <td class="num" style="text-align: right;">{n}</td>
        <td class="num" style="text-align: right;">{n}</td>
        <td class="num" style="text-align: right; font-weight: 600;">{n}</td></tr>
  </tbody>
</table>
```

An example of `tr.hl` — the Amarelo highlight row — lives in `../templates/slide-agenda.html`. The variant classes (`compact`, `compact.tight`) are defined in the base stylesheet for denser grids.

**HARD GATE (engineering):** no `height`, no `min-height` on rows. Row rhythm comes from padding, not fiat. Fixed cell heights are forbidden per `engineering.md`.

---

## dashed-hairline

**Purpose:** "related but secondary" divider. A softer cousin of the solid `.rule` hairline. The dashed edge reads as a semantic pause — "the thing below is connected to the thing above, but not continuous with it."

**Common uses:**
- Above a [`narrative-arc`](#narrative-arc) callout — "related but secondary"
- Threading a tangential footnote or caption off the main argument
- Between a card's main body and a meta-row when a solid rule would feel too assertive

**Avoid:**
- For structural separation — a solid `.rule` (1px `--c-rule`) or table border reads as structural
- As generic decoration — the dash carries semantic weight; overuse flattens the signal
- On `.slide.accent` backgrounds — Amarelo eats the dash rhythm; a solid rule or no divider reads better

**HTML:**
```html
<div style="border-top: 1px dashed var(--c-rule);"></div>
```

**Inline composition — above a narrative-arc callout:**
```html
<div style="margin-top: 26px; padding-top: 18px; border-top: 1px dashed var(--c-rule);">
  <!-- narrative-arc block goes here -->
</div>
```

**Dashed vs solid — pairing table:**

| Style | CSS | Semantic role |
| --- | --- | --- |
| Solid `.rule` | `border-top: 1px solid var(--c-rule)` | Structural — "new section," column divider, footer border |
| Dashed hairline | `border-top: 1px dashed var(--c-rule)` | Semantic pause — "related but secondary," threads a callout off the main argument |

**Guidance:** don't mix dashed and solid hairlines inside a single card without a reason. Inconsistent hairlines read as sloppy, not editorial.

**Anti-pattern:** using a dashed hairline as a generic "divider with visual interest" — it flattens the signal. The callout-threading role is where it earns its weight.

Pairs with: [`narrative-arc`](#narrative-arc) (dashed hairline sits directly above the arc callout).

---

## narrative-arc

**Purpose:** cross-slide threading device. A small callout that names the current slide's relationship to another slide by name, letting the audience hold the deck's through-line across sections. One arc per slide at most.

**Common uses:**
- A slide that *depends on* or *continues from* an earlier slide — name both and the relationship
- A decision slide that *opens* a section the audience hasn't reached yet — name the forward link
- A summary slide that *closes* a loop opened earlier — name the callback

**Avoid:**
- Vague relationships ("related to X") — the arc's value is directional specificity
- As slide-summary chrome — the arc threads a *relationship*, not a recap
- Everywhere — overused, it neutralizes itself
- On `.slide.accent` or `.slide.dark` — the Amarelo pill + muted prose is tuned for light surfaces

**Relationship vocabulary — pick one:**

| Word | Direction | Example |
| --- | --- | --- |
| **hinge** | Present slide is the pivot between two sections | "Discussion 01 · Topic A is the **hinge** into Act 05 · Topic B." |
| **continues** | Present slide extends an argument from earlier | "This **continues** 04 · Topic A — the question asked there." |
| **answers** | Present slide resolves a question opened earlier | "This **answers** Discussion 02 · Topic B." |
| **opens** | Present slide sets up a section ahead | "This **opens** Act 04 · Strategic Discussions." |
| **closes** | Present slide resolves a loop opened earlier | "This **closes** the thread started at A1." |

**HTML:**
```html
<div style="margin-top: 26px; padding-top: 18px; border-top: 1px dashed var(--c-rule); display: flex; align-items: flex-start; gap: 12px;">
  <div style="font-family: 'JetBrains Mono'; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--c-accent-ink); background: var(--c-accent); padding: 3px 8px; border-radius: 2px; white-space: nowrap; font-weight: 600; flex-shrink: 0;">Narrative arc</div>
  <div style="font-size: 14px; line-height: 1.45; color: var(--c-ink-2);"><strong style="color: var(--c-ink);">{slide A}</strong> {relationship verb} <strong style="color: var(--c-ink);">{slide B}</strong>. {one-sentence consequence}.</div>
</div>
```

**Composition guidance:**

- **Pill text is the recognition pattern.** "Narrative arc" (or the translated equivalent: `Arco narrativo`, `Fil narratif`) is the label the audience learns to recognize. Changing it per slide erases the pattern.
- **Subdued prose.** Body text at `var(--c-ink-2)` (14px IBM Plex Serif); key slide names bolded in full `var(--c-ink)`. Bold is the primary emphasis — italics and underlines compete with the pill.
- **Dashed hairline above.** The dashed separator from `border-top: 1px dashed var(--c-rule)` carries the "related but secondary" read. A solid rule promotes the arc to primary content.
- **Directional statement.** Name both slides and use one of the relationship words above. A non-directional arc ("related to slide 3") loses its point.
- **One per slide typically.** Two arcs stacked on one slide overload the threading.

**Anti-patterns:**
- Vague connection — "See also Discussion 01" is a breadcrumb, not an arc
- Summary-flavored arcs — "This slide covers cloud" is a lede, not a cross-reference
- Arc above the dashed rule — the rule MUST sit above the arc to signal "threading off the main content"
- Arc pill in outline form (`.pill`) — the Amarelo fill is load-bearing; an outlined pill reads as generic chrome

Pairs with: [`dashed-hairline`](#dashed-hairline) (always sits above the arc).

---

## transition-column

**Purpose:** a named narrow column that sits *between* two cards signaling a journey. Not a card, not a gap — a semantic hinge. The reader's eye crosses it and understands "the thing on the right is what the thing on the left becomes."

**Common uses:**
- Legacy → Modern migration narratives
- Old → New architecture comparisons where the *transition* is the story
- Manual → Automated process diagrams
- Any two-card pair where the relationship word ("migrating," "upgrading," "consolidating") is load-bearing

**Avoid:**
- For `vs.` comparisons — [`2x2-matrix`](chart-primitives.md#2x2-matrix) or a two-column `table.grid` reads better; a transition column implies motion
- As a generic separator between any two cards — a `.rule` or a grid `gap` is lighter
- For three-way transitions (A → B → C) — the pattern is two-card. Three stages is a [`funnel`](chart-primitives.md#funnel).
- Inside columns narrower than ~80px — the arrow + dual-label stack collapses

**HTML:**
```html
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 14px; position: relative; min-width: 80px;">
  <div style="font-family: 'JetBrains Mono'; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--c-ink-3); text-align: center; line-height: 1.3; white-space: nowrap;">{verb/phase}</div>
  <div style="font-size: 42px; color: var(--c-ink); margin-top: 4px; line-height: 1;">→</div>
  <div style="font-family: 'JetBrains Mono'; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--c-ink-3); text-align: center; line-height: 1.3; margin-top: 4px; white-space: nowrap;">{destination}</div>
</div>
```

**Parent composition — three-cell grid with the transition column as the `auto` track:**
```html
<div style="display: grid; grid-template-columns: 1fr auto 1.15fr; gap: 0; align-items: stretch;">
  <div class="card"> <!-- left card: current state --> </div>
  <div> <!-- transition column HTML from above --> </div>
  <div class="card"> <!-- right card: target state --> </div>
</div>
```

**Composition guidance:**

- **`grid-template-columns: 1fr auto 1.15fr`.** The right card gets a slight size premium when it's the destination — the eye lands there. `1fr auto 1fr` works when both states carry equal weight.
- **Arrow glyph is `→` at 42px.** Unicode arrow, black on white. An SVG or emoji substitute reads different; the 42px mono arrow is the signature.
- **Top and bottom mono labels answer "from what, to what."** Top = verb/phase ("Migrating", "Upgrading", "Consolidating"). Bottom = destination ("to modern", "to v5", "to one pipeline"). Both in JetBrains Mono 10px, `--c-ink-3`.
- **Flanking cards share the paired-shape convention.** Left card rounds its outward corners, squares its inward; right card mirrors. Visual read: one split shape bridged by the transition column. `border-radius: 4px 0 0 4px` on left, `0 4px 4px 0` on right.

**Anti-patterns:**
- Transition column as "vs." separator — violates the directional contract
- Arrow pointing left or bidirectional — the column is one-way. For reciprocal relationships, [`dual-sided-argument`](#dual-sided-argument) reads better.
- Missing top or bottom label — the arrow alone is ambiguous
- Using `.rule` styling (solid border) between the cards instead of the column — loses the "hinge" semantics

---

## org-node-flag

**Purpose:** tab-style status badge, absolute-positioned above an org-chart (or any entity) card. Hangs off the top edge like a file-tab — drawing the eye to a single card that needs special attention inside a grid of siblings.

**Common uses:**
- Org charts: flagging a role (open to hire, at risk, critical path)
- Product matrices: flagging an area (pain point, newly shipped)
- Roadmap grids: flagging the quarter or swim-lane the slide is about
- Any uniform grid where one card needs "read me first" treatment without becoming a hero

**Avoid:**
- Multiple flags in a grid — two flags cancel each other. For two points of emphasis, flag one and bold the other.
- On hero slides — the flag is a grid-level signal; hero slides have no siblings to contrast against
- As a decorative tag — `.pill.accent` is the tag primitive; the flag is structural

**Suggested values — ALL CAPS, one or two words:**

| Value | Meaning |
| --- | --- |
| `PAIN POINT` | This card is the problem the slide is naming |
| `NEW` | This card arrived since last review |
| `AT RISK` | This card is slipping or under-resourced |
| `CRITICAL PATH` | The plan depends on this card |
| `HIRE` | Open role (org-chart use) |

**HTML (badge + parent card):**
```html
<div style="background: var(--c-ink); color: var(--c-ink-inv); padding: 18px 20px; border-radius: 4px; text-align: center; position: relative; border: 2px solid var(--c-accent);">
  <div style="position: absolute; top: -11px; left: 50%; transform: translateX(-50%); background: var(--c-accent); color: var(--c-ink); font-family: 'JetBrains Mono'; font-size: 10px; letter-spacing: 0.12em; padding: 3px 8px; border-radius: 2px; font-weight: 600; white-space: nowrap;">PAIN POINT</div>
  <!-- card content -->
</div>
```

**Composition guidance:**

- **Parent card MUST be `position: relative` (engineering).** The flag is absolute-positioned relative to its parent; non-relative parents break the layout.
- **Parent card gains `border: 2px solid var(--c-accent)`.** The Amarelo border visually binds the flag to the card. Without the accent border, the flag reads as a floating sticker.
- **Flag text is ALL CAPS JetBrains Mono 10px.** Letter-spacing `0.12em`, font-weight 600. Mixed case or larger sizes break the tab density.
- **Flag position: `top: -11px; left: 50%; transform: translateX(-50%)`.** The -11px offset hangs half the flag above the card edge — the "file-tab" signature.
- **One flag per card, typically.** Two flags stack awkwardly and dilute the signal.

**Anti-patterns:**
- Flag without Amarelo card border — the tab floats, loses its binding
- Lowercase or Title Case flag text — breaks the mono-tab aesthetic
- More than one flag per card — the signal is "read this one"; two flags contradict
- Flag on `.slide.accent` (Amarelo background) — the Amarelo flag disappears; swap the flag background to `var(--c-ink)` with white text, or pick a different primitive

---

## dual-sided-argument

**Purpose:** a two-column symmetric-benefit card. The eyebrow on top names the relationship ("Works both ways"), two columns show the same argument from two stakeholder perspectives. Use when a decision genuinely cuts the same way for both sides.

**Common uses:**
- Users + Company benefits (a change that serves both)
- Buyers + Sellers (marketplace decisions)
- Devs + Ops (platform choices)
- Present + Future (decision that compounds positively in both directions)

**Avoid:**
- Asymmetric benefits — forcing asymmetric content into symmetric columns creates false equivalence; a two-column layout with distinct eyebrows reads better
- Visual-weight mismatch (three bullets on one side, one on the other) — undermines the "both ways" claim
- Three or more stakeholders — the primitive is two-column by construction. Three groups is a [`table.grid`](#tablegrid).
- As a generic two-column comparison — this is a specific rhetorical device, not a layout primitive

**HTML:**
```html
<div style="background: var(--c-card); border: 1px solid var(--c-rule); border-radius: 4px; padding: 14px 20px;">
  <div class="eyebrow" style="margin-bottom: 6px;">{relationship label}</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
    <div>
      <div style="font-family: 'JetBrains Mono'; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--c-ink-3); margin-bottom: 3px;">{side A label}</div>
      <div style="font-size: 16px; line-height: 1.35;">{side A benefit}</div>
    </div>
    <div>
      <div style="font-family: 'JetBrains Mono'; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--c-ink-3); margin-bottom: 3px;">{side B label}</div>
      <div style="font-size: 16px; line-height: 1.35;">{side B benefit}</div>
    </div>
  </div>
</div>
```

**Composition guidance:**

- **Eyebrow text names the relationship.** "Works both ways," "Cuts both ways," "Serves both sides," "Both sides win." A generic label like "Benefits" loses the "both ways" signal.
- **Sub-eyebrows name the two sides.** Common pattern: "For users" / "For the company." Sub-eyebrows are JetBrains Mono 11px `--c-ink-3` — smaller than the top eyebrow so the hierarchy reads as "one card, two sides."
- **Columns are `1fr 1fr`.** Equal real estate. Asymmetric widths (`1fr 1.2fr`) undermine the symmetric-benefit claim.
- **Body text is 16px IBM Plex Serif.** Below the 24px body floor — deliberate, because this primitive is a supporting block inside a larger argument, not the primary content. Treat it as a chrome-density exception (see `engineering.md` Minimum Text Size).
- **Each side is one sentence or one short paragraph.** If one side needs three bullets and the other one, the primitive is being asked to do something it isn't for.

**Anti-patterns:**
- Asymmetric content forced into symmetric columns — defeats the whole point
- Three or more columns — the primitive is two-column by construction
- Wordy copy (>2 lines per side) — the card grows too tall; either trim or promote to a full-slide layout
- Stakeholder labels in Title Case ("For Users") — MUST be ALL CAPS mono to match eyebrow conventions

---

## inline-mini-legend

**Purpose:** legend dots embedded directly inside a caption sentence, using inline-block spans. Compresses a typical multi-line legend block into a single line of prose. Ideal for tiny charts (e.g., inline micro-charts in table cells) where a full legend block would outweigh the chart.

**Common uses:**
- Paired with [`inline-micro-chart` in table cells](chart-primitives.md#inline-micro-chart) — a typical pairing
- As a caption under a small `vertical-bar-chart` with 2 categories
- For 2–3 categories where a stacked legend block would dominate visual weight

**Avoid:**
- For 4+ categories — readability breaks; a stacked legend block reads better (see `chart-primitives.md` → `stacked-horizontal-bar` legend pattern)
- When the chart is the slide's main content — a full legend with numeric values is clearer
- Inside body paragraphs — this is caption chrome, not prose

**HTML:**
```html
<div style="font-size: 14px; color: var(--c-ink-2);">
  All figures in thousands ·
  Category A <span style="display: inline-block; width: 7px; height: 7px; border: 1.5px solid var(--c-ink); border-radius: 999px; margin: 0 3px -1px 3px; box-sizing: border-box;"></span>
  Category B <span style="display: inline-block; width: 7px; height: 7px; background: var(--c-ink); border-radius: 999px; margin: 0 3px -1px 3px;"></span>
</div>
```

**Composition guidance:**

- **Dots are 7×7px, `border-radius: 999px` (circles).** Square dots read as data points; circles read as legend markers.
- **Outline state: `border: 1.5px solid var(--c-ink)` with no background.** The "empty/unfilled" category in a two-state split.
- **Filled state: `background: var(--c-ink)` with no border.** The "full/filled" category. A border on the filled state visually doubles the weight.
- **Baseline alignment: `margin: 0 3px -1px 3px`.** The `-1px` bottom margin nudges the dot onto the text baseline. Without it, dots float above the line.
- **`box-sizing: border-box` on the outline state.** Without it, the 1.5px border adds to the 7px width, making outlined dots visually larger than filled ones. (Filled dots need no `box-sizing`.)
- **Category name precedes the dot.** "Category A ●" not "● Category A" — the text anchors the dot semantically.
- **Categories separated by ` · `.** Mid-dot on spaces, not commas. Matches the eyebrow and meta-row cadence.

**Anti-patterns:**
- 4+ categories inline — unreadable prose. Use a stacked legend.
- Dot before label — flips reading order
- Filled dot with border + outlined dot without `box-sizing` — size mismatch breaks the pairing
- Using for a chart where segment sizes are the message — the inline legend has no numeric anchor; add `numeric %` or use a full legend

Pairs with: [`inline-micro-chart` in table cells](chart-primitives.md#inline-micro-chart) (typical pairing — mini-chart in cells, mini-legend in the caption below).

---

## Composition Notes

These are things that have worked well — not rules. Composition is yours.

- **Eyebrows anchor headlines.** A common pattern is `.eyebrow` immediately above an `h1` — the mono label tells the eye "this is a new unit." Headlines without an eyebrow read as floating.
- **Bullet grammars.** `ul.ticks` (unordered) and `ul.numbered` (ordinal) mixed in the same column tend to conflict — the bullet shapes compete. Splitting into siblings usually reads cleaner.
- **Pills cluster; kpis breathe.** Pill rows flex-wrap tight (`gap: 10–14px`); kpi walls use `36–80px` column gaps. Pill density on kpis (or vice versa) looks off.
- **Pill and tick density.** Beyond ~6 in one row/list, pill rhythm turns into chip noise and tick rhythm dilutes. Splitting or trimming usually helps.
- **KPI value stack (engineering).** Three stacked `.kpi` tiles → reduce `.value` to 60–76px; at 96px they overflow. Four-up horizontal rows usually keep 96px.
- **table.grid rhythm (engineering).** Double borders, zebra stripes, or solid backgrounds beyond `tr.hl` break the hairline rhythm — the white space between rows is the rhythm.
- **`.slide.accent` + table.grid (engineering).** The Amarelo background eats the hairline rules — use a different slide variant or primitive.
- **Eyebrow color carries meaning.** Default ink-3 = "label." Amarelo = "callout" (works well for framing, decision, question callouts). Verde = "supporting signal." Using Amarelo for neutral labels dilutes the signal.

## Dark vs Light Pairing

| Primitive | Works on `.slide` | Works on `.slide.paper` | Works on `.slide.dark` | Works on `.slide.accent` |
| --- | --- | --- | --- | --- |
| eyebrow | yes | yes | yes (auto Amarelo) | yes (auto 72% ink) |
| pill | yes (all variants) | yes | `.pill.accent` only (outline disappears) | `.pill.solid` only (accent on accent = invisible) |
| kpi | yes | yes | yes (preferred — hero summaries) | avoid (Amarelo on Amarelo loses the value) |
| ticks | yes | yes | yes (inherits 78% white body) | yes, but the Amarelo square on Amarelo bg is invisible — swap bullet to ink inline |
| numbered | yes (class form) | yes | yes (the inline Questions-card pattern — numeral Amarelo, title white, sub 75% white) | avoid (same Amarelo-on-Amarelo problem) |
| table.grid | yes | yes | needs inverted rules (`border-color: rgba(255,255,255,0.18)`) — not in reference canon | **FORBIDDEN** — Amarelo bg eats hairlines |
| dashed-hairline | yes | yes | needs `border-color: rgba(255,255,255,0.18)` dashed | **FORBIDDEN** — Amarelo eats the dash rhythm |
| narrative-arc | yes | yes | avoid — Amarelo pill on dark loses contrast; muted prose disappears | **FORBIDDEN** — pill + muted prose collapse |
| transition-column | yes | yes | yes (labels inherit `rgba(255,255,255,0.55)`) | avoid — arrow on Amarelo reads as chrome |
| org-node-flag | yes | yes | yes (flag Amarelo on dark card — strong contrast) | **FORBIDDEN** — Amarelo flag on Amarelo bg invisible |
| dual-sided-argument | yes | yes | needs `background: rgba(255,255,255,0.06)` and inverted rule color | avoid — light card on Amarelo loses the card boundary |
| inline-mini-legend | yes | yes | swap outline dot to `rgba(255,255,255,0.75)` border, filled dot to white | avoid — black dots on Amarelo read as noise |

**HARD GATE (engineering):** "FORBIDDEN" pairings break rendering (Amarelo-on-Amarelo is invisible, not just ugly). Pick a different primitive or slide variant rather than patching with inline color overrides. "Avoid" pairings are soft — legibility-dependent.

## Related

- Brand tokens: [`brand.md`](brand.md)
- Canvas + flex engineering: [`engineering.md`](engineering.md)
- Example templates: `../templates/slide-cover.html`, `../templates/slide-agenda.html`, `../templates/slide-act-divider.html`, `../templates/slide-content.html`, `../templates/slide-content-paper.html`, `../templates/slide-content-dark.html`, `../templates/slide-content-accent.html`, `../templates/slide-appendix-intro.html`, `../templates/slide-appendix-content.html` — compositions you can borrow from; not a required menu
