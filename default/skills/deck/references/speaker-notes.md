# Speaker Notes

Speaker notes are embedded in the deck HTML as a single JSON block and surfaced to the presenter view via a regex extraction. This document specifies the schema, the embedding pattern, and the writing voice.

## JSON Schema

The speaker-notes block is a **flat array of strings**. Each array element is the full speaker copy for one slide. Array index corresponds to slide order: `notes[0]` is the cover slide, `notes[1]` is slide 2, and so on.

```json
[
  "<speaker copy for slide 1>",
  "<speaker copy for slide 2>",
  "<speaker copy for slide 3>"
]
```

**Array length MUST exactly match `<section>` count inside `<deck-stage>`.** The dev-server logs a warning on mismatch (`[deck-stage] Speaker-notes length N != slide count M`), but treat any mismatch as a production blocker: the presenter view will show wrong notes or `(no notes)`. The runtime does not throw — missing indices render as `(no notes)` and the deck keeps working — so the gate is yours to enforce. Being one-off during authoring is fine; shipping one-off is not.

### Embedded Entry Shape

- **Type:** string (not object).
- **Delimiter within a string:** `\n\n` for paragraph breaks. Single `\n` breaks render as spaces in presenter view.
- **Content:** plain prose. No Markdown. No HTML. No bullets.
- **Escape:** standard JSON string escaping (`\"`, `\\`, `\n`).
- **FORBIDDEN substring:** `</script>` anywhere inside a note string. The presenter extraction uses a regex that terminates on the first `</script>` — an embedded occurrence closes the inline JSON block prematurely and corrupts every note after it. `presenter-view.js` strips HTML comments before `JSON.parse`, but the `</script>` boundary is unforgeable. If you must reference the tag in speaker copy, break it: `"</scr" + "ipt>"` in source, or just write "script tag" in prose.

## Embedding Pattern

The block lives in `<head>` of `deck.html`:

```html
<head>
  <meta charset="utf-8" />
  <title>… deck title …</title>
  …

  <script type="application/json" id="speaker-notes">
  [
    "Welcome everyone. This is our first formal board meeting. …",
    "Quick map of where we're going. Five acts. …",
    …
  ]
  </script>

  …
</head>
```

**REQUIRED attributes on the `<script>` tag:**

| Attribute | Value | Why |
| --- | --- | --- |
| `type` | `"application/json"` | Prevents the browser from executing the block as script |
| `id` | `"speaker-notes"` | Stable selector for the presenter-view fetch |

## Presenter View Extraction

Presenter view (opened on the second screen) fetches `/deck.html` and regex-extracts the JSON block — it does NOT iframe the deck, because that would run the deck's own WebSocket client and double-subscribe.

```javascript
// In presenter.html runtime:
async function loadNotes() {
  const res = await fetch('/deck.html');
  const html = await res.text();
  const match = html.match(
    /<script type="application\/json" id="speaker-notes">([\s\S]*?)<\/script>/
  );
  if (!match) throw new Error('speaker-notes block not found in /deck.html');
  return JSON.parse(match[1]);
}
```

**Why regex, not DOMParser:** parsing 1920×1080 deck HTML in a second tab wastes memory and re-executes inline scripts. The regex is deterministic because the block has fixed attributes.

## Writing Voice

Speaker notes are **the script the presenter reads**, not a slide summary. Presenter voice — direct, concrete, ready to speak aloud.

### Guidance

| Guidance | Why |
| --- | --- |
| Speaking voice, not bullets | The presenter reads this aloud. Fragments break cadence. |
| One paragraph per slide; `\n\n` separators between paragraphs if more than one | Presenter scans paragraph-by-paragraph during delivery. |
| Concrete data ahead of abstraction (one technique that lands well) | "ARR is $4.2M" before "growth is strong" — the audience gets the fact before the gloss. |
| Target ~90–120 words per slide (a time budget, ~30 seconds of speech) | See "Word Budget" below. |
| Second-person for the audience; first-person for the speaker | "You'll see…" / "I want to flag…". Third-person ("the presenter walks through") reads wrong. |
| No self-reference to the slide | "Let me show you…" beats "On this slide…". The slide is the prop, not the subject. |

### Word Budget — Why 90–120 Is the Target

This is a time budget, not a style rule. ~30 seconds of speech per slide at conference pace.

- Public-speaking cadence ≈ 130–150 words/minute.
- Slide-bound delivery ≈ 100–120 words/minute (pauses, gestures).
- 30 seconds per slide × 3 words/second ≈ 90 words as the lower floor.
- Above 120 words, the presenter reads instead of presents — and the audience would rather have the deck.

Shorter works for discussion openers and factual beats; longer belongs in the appendix, not the live notes. The 90–120 target is a presenter constraint, not deck aesthetic.

## Gold-Standard Examples

Three illustrative entries — one for each typical slide role (portfolio/catalog, factual/numbers, discussion opener) — with commentary on why they work.

### Example 1 — Catalog slide (index 2)

```text
Let me show you what's actually shipping. Six products in production — name
them one by one, left to right as the audience scans — that's the full stack
we went to market with. A seventh is fully specified, build underway in the
repo today; that closes the loop for the last workflow. Plus a handful of
companion modules live today. The pipeline is the regulated work that takes
real time. The point of this slide: the "you don't have product X" objection
is dead. We have the portfolio.
```

**Why it works:**
- Opens with "Let me show you" — presenter voice, active verb.
- Names every product concretely before stating the thesis (in a real deck, substitute the literal product names).
- Ends with the takeaway ("the objection is dead") — the thing the audience should remember.
- 96 words — inside the target band.

### Example 2 — Quarterly P&L (index 7)

```text
Q1 P&L. The number that will raise eyebrows is the line item on the right —
three hundred fifteen to four hundred forty thousand a month. That is
deliberate. It's the bet behind discussion number three. Runway is twenty
months at gross burn, thirty-two months net of revenue — comfortably long
either way. One nuance worth knowing: the revenue line in this view is cash
collected, not recognised — if you prefer the accounting view it's in the
appendix.
```

**Why it works:**
- Names the concrete number ("three hundred fifteen to four hundred forty thousand") before the abstraction ("deliberate").
- Cross-references the strategic discussion ("discussion number three") — gives the presenter a natural hand-off.
- Numbers are written out as words — a good default for anything said aloud, since digits interrupt reading flow.
- 76 words — short but complete. Factual slides don't need to hit 120.

### Example 3 — Discussion opener (index 12)

```text
Discussion one. We've been calling it the platform play. Clients deploy our
products plus their own apps on shared infrastructure — three tiers, managed
to self-serve. A clear majority of new logos want this already. The question
isn't whether. It's timing, positioning, and whether we should reframe the
company around it. Where are we wrong?
```

**Why it works:**
- Immediately names the framing ("the platform play") before unpacking it.
- Ends with the board-facing question ("Where are we wrong?") — invites the debate the slide is built for.
- 59 words — low end of the range. A discussion-opener slide is a prompt, not a monologue; the actual content is the board response.

## Authoring Checklist

```
Before committing speaker-notes JSON:

Engineering (hard):
[ ] 1. Array length matches <section> count inside <deck-stage>? (Soft gate — mismatch warns but doesn't throw; match for production.)
[ ] 2. Zero literal `</script>` substrings anywhere in any note (breaks inline-JSON extraction)?
[ ] 3. JSON parses cleanly (test with JSON.parse in browser console)?

Craft (guidance):
[ ] 4. Every string reads as speaking voice (presenter script, not slide summary)?
[ ] 5. Numbers expected to be spoken aloud are written as words rather than digits?
[ ] 6. Word count per slide is in the 60–120 time budget (shorter for discussion openers; longer belongs in the appendix)?
[ ] 7. Zero "on this slide…" / "in this diagram…" self-references?

Speaker notes ship once; redoing live is expensive.
```
