---
description: Search the Artifact Index for relevant historical context
agent: build
subtask: false
---

Search the Artifact Index for relevant handoffs, plans, and continuity ledgers using full-text search.

## Usage

```
/query-artifacts <search-terms> [options]
```

## Options

| Option | Description |
|--------|-------------|
| `--mode` | Query mode: `search` (default) or `planning` (structured precedent) |
| `--type` | Filter: `handoffs`, `plans`, `continuity`, `all` (default) |
| `--outcome` | Filter handoffs: `SUCCEEDED`, `PARTIAL_PLUS`, `PARTIAL_MINUS`, `FAILED` |
| `--limit` | Maximum results per category (1-100, default: 5) |

## Examples

```
/query-artifacts authentication OAuth JWT
/query-artifacts API design --outcome SUCCEEDED
/query-artifacts context management --type plans
/query-artifacts api rate limiting --mode planning
```

## Output

Results displayed in markdown:

```markdown
## Relevant Handoffs
### [OK] session-name/task-01
**Summary:** Implemented OAuth2...
**What worked:** Token refresh...
**What failed:** Initial PKCE...
**File:** `/path/to/handoff.md`

## Relevant Plans
### OAuth2 Integration Plan
**Overview:** Implement OAuth2...
**File:** `/path/to/plan.md`
```

## Planning Mode

Use `--mode planning` for structured precedent when creating plans:
- **Successful Implementations** - What worked (reference these)
- **Failed Implementations** - What failed (AVOID these patterns)
- **Relevant Past Plans** - Similar approaches

$ARGUMENTS

Provide search terms and optional filters.
