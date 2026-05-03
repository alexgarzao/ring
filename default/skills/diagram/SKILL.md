---
name: ring:diagram
description: Generate Mermaid diagrams from context and open them in mermaid.live in the browser. Use when the user asks for a diagram, visualization, flowchart, sequence diagram, ER diagram, or any visual representation of code, architecture, or processes. Produces lightweight, shareable mermaid.live URLs that open in the browser for interactive editing.

trigger: |
  - User asks for a diagram, chart, flowchart, or visualization
  - User says "draw", "diagram", "visualize", "chart", "show me"
  - Need to visualize architecture, data flow, state machines, sequences, or relationships

skip_when: User needs a rich, branded, styled HTML visualization → use ring:visualize instead.
---

# Mermaid Live Diagram Generator

Generate Mermaid diagrams and open them in mermaid.live.

## Step 1: Choose Diagram Type

| Need | Type | Keyword |
|------|------|---------|
| Process flow, decisions | Flowchart | `flowchart TD` / `flowchart LR` |
| API calls, message passing | Sequence | `sequenceDiagram` |
| OOP structure | Class | `classDiagram` |
| Database schema | ER | `erDiagram` |
| State machines | State | `stateDiagram-v2` |
| Project timelines | Gantt | `gantt` |
| Git branch strategy | Git Graph | `gitGraph` |
| Brainstorming | Mindmap | `mindmap` |

## Step 2: Write Mermaid Code

**Flowchart nodes:** `A[Rectangle]` `A(Rounded)` `A{Diamond}` `A((Circle))` `A[(Database)]`  
**Edges:** `-->` (arrow), `-.->` (dotted), `==>` (thick), `|label|` for text  
**Subgraphs:** `subgraph title ... end`

**Sequence:** `->>` (solid+arrow), `-->>` (dotted+arrow). Blocks: `loop`, `alt/else`, `opt`, `par`. `autonumber` for numbering.

**ER:** `||--o{` (one-to-many), `||--||` (one-to-one), `}o--o{` (many-to-many)

**State:** `[*]` for start/end, `<<choice>>`, `<<fork>>`, `<<join>>`

⚠️ **Avoid lowercase `end` inside node labels** — reserved keyword. Use `End`, `END`, or quotes.

⚠️ **`stateDiagram-v2` label caveat:** Colons, parentheses, HTML entities cause silent parse failures. Use `flowchart LR` with quoted edge labels (`|"label text"|`) for special characters.

## Step 3: Encode and Open

```bash
cat <<'MERMAID_EOF' | python3 ~/.claude/skills/diagram/mermaid-encode.py | xargs open
<mermaid code here>
MERMAID_EOF
```

Options: `--theme dark|forest|neutral`, `--view` (view-only), `--rough` (hand-drawn style)

## Step 4: Inform the User

Tell the user: diagram type chosen and why, brief description of what it shows, that it's open in mermaid.live for editing, and the URL (for sharing).

## Design Guidelines

- **Readable labels:** Short, descriptive text. No full sentences in nodes.
- **Flow direction:** TD for hierarchies, LR for sequences/timelines.
- **Subgraphs:** Group related nodes for complex diagrams.
- **Color with purpose:** Use `classDef` to highlight key nodes (errors red, success green).
- **One idea per diagram:** Split complex systems into multiple focused diagrams.

## Notes

- Encoder uses only Python standard library — no pip install needed
- URLs are permanent — diagram state IS the URL
- Very large diagrams may exceed URL limits in some browsers
