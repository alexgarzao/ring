---
name: query-artifacts
description: Search the Artifact Index for relevant historical context
argument-hint: "<search-terms> [--type TYPE] [--outcome OUTCOME]"
---

Search the Artifact Index for relevant handoffs, plans, and continuity ledgers using FTS5 full-text search with BM25 ranking.

## Usage

```
/query-artifacts <search-terms> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `search-terms` | Yes | Keywords to search for (e.g., "authentication OAuth", "error handling") |
| `--mode` | No | Query mode: `search` (default) or `planning` (structured precedent) |
| `--type` | No | Filter by type: `handoffs`, `plans`, `continuity`, `all` (default: all) |
| `--outcome` | No | Filter handoffs: `SUCCEEDED`, `PARTIAL_PLUS`, `PARTIAL_MINUS`, `FAILED` |
| `--limit` | No | Maximum results per category (1-100, default: 5) |

## Examples

### Search for Authentication Work

```
/query-artifacts authentication OAuth JWT
```

Returns handoffs, plans, and continuity ledgers related to authentication.

### Find Successful Implementations

```
/query-artifacts API design --outcome SUCCEEDED
```

Returns only handoffs that were marked as successful.

### Search Plans Only

```
/query-artifacts context management --type plans
```

Returns only matching plan documents.

### Limit Results

```
/query-artifacts testing --limit 3
```

Returns at most 3 results per category.

### Planning Mode (Structured Precedent)

```
/query-artifacts api rate limiting --mode planning
```

Returns structured precedent for creating implementation plans:
- **Successful Implementations** - What worked (reference these)
- **Failed Implementations** - What failed (AVOID these patterns)
- **Relevant Past Plans** - Similar approaches

This mode is used automatically by `/write-plan` to inform new plans with historical context.

## Output

Results are displayed in markdown format:

```markdown
## Relevant Handoffs
### [OK] session-name/task-01
**Summary:** Implemented OAuth2 authentication...
**What worked:** Token refresh mechanism...
**What failed:** Initial PKCE implementation...
**File:** `/path/to/handoff.md`

## Relevant Plans
### OAuth2 Integration Plan
**Overview:** Implement OAuth2 with PKCE flow...
**File:** `/path/to/plan.md`

## Related Sessions
### Session: auth-implementation
**Goal:** Add authentication to the API...
**Key learnings:** Use refresh tokens...
**File:** `/path/to/ledger.md`
```

## Index Management

### Check Index Statistics

```
/query-artifacts --stats
```

Shows counts of indexed artifacts.

### Initialize/Rebuild Index

If the index is empty or out of date:

```bash
python3 default/lib/artifact-index/artifact_index.py --all
```

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `/write-plan` | Query before planning to inform decisions |
| `/create-handoff` | Creates handoffs that get indexed |
| `artifact-query` | The underlying skill |
| `writing-plans` | Uses query results for RAG-enhanced planning |

## Troubleshooting

### "Database not found"

The artifact index hasn't been initialized. Run:

```bash
python3 default/lib/artifact-index/artifact_index.py --all
```

### "No results found"

1. Check that artifacts exist: `ls docs/handoffs/ docs/plans/`
2. Re-index: `python3 default/lib/artifact-index/artifact_index.py --all`
3. Try broader search terms

### Slow queries

Queries should complete in < 100ms. If slow:

1. Check database size: `ls -la .ring/cache/artifact-index/`
2. Rebuild indexes: `python3 default/lib/artifact-index/artifact_index.py --all`
