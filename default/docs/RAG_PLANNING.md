# RAG-Enhanced Plan Judging

Ring's plan creation workflow automatically queries historical context before generating new plans. This enables plans that learn from past successes and avoid known failure patterns.

## How It Works

```
1. User requests: "Create plan for authentication"
     │
     ▼
2. Query artifact index for "authentication" precedent
     │
     ▼
3. Results inform plan:
   - Successful patterns → Reference these
   - Failed patterns → Design to AVOID
   - Past plans → Review for approach ideas
     │
     ▼
4. Write plan with Historical Precedent section
     │
     ▼
5. Validate plan against failure patterns
     │
     ▼
6. Execute plan with confidence
```

## Components

### 1. Planning Query Mode

Query the artifact index for structured planning context:

```bash
python3 default/lib/artifact-index/artifact_query.py --mode planning "keywords" --json
```

**Returns:**
- `successful_handoffs` - Implementations that worked
- `failed_handoffs` - Implementations that failed (AVOID these)
- `relevant_plans` - Similar past plans
- `is_empty_index` - True if no historical data (normal for new projects)
- `query_time_ms` - Performance metric (target <200ms)

### 2. Historical Precedent Section

Every plan created by the ring:write-plan agent includes:

```markdown
## Historical Precedent

**Query:** "authentication oauth jwt"
**Index Status:** Populated

### Successful Patterns to Reference
- **[auth-impl/task-3]**: JWT refresh mechanism worked well
- **[api-v2/task-7]**: Token validation approach succeeded

### Failure Patterns to AVOID
- **[auth-v1/task-5]**: localStorage token storage caused XSS
- **[session-fix/task-2]**: Missing CSRF protection

### Related Past Plans
- `2024-01-15-oauth-integration.md`: Similar OAuth2 approach

---
```

### 3. Plan Validation

After creating a plan, validate it against known failures:

```bash
python3 default/lib/validate-plan-precedent.py docs/plans/YYYY-MM-DD-feature.md
```

**Interpretation:**
- `PASS` - No significant overlap with failure patterns
- `WARNING` - >30% keyword overlap with past failures (review required)

**Exit codes:**
- `0` - Plan passes validation
- `1` - Warning: overlap detected (plan may repeat failures)
- `2` - Error (invalid file, etc.)

## Usage

### Automatic (Recommended)

When using `/ring:write-plan` or the `ring:writing-plans` skill, RAG enhancement happens automatically:

1. Keywords are extracted from your planning request
2. Artifact index is queried for precedent
3. Historical Precedent section is added to plan
4. Plan is validated before execution

### Manual Query

To query precedent manually:

```bash
# Get structured planning context
python3 default/lib/artifact-index/artifact_query.py --mode planning "api rate limiting" --json

# Validate an existing plan
python3 default/lib/validate-plan-precedent.py docs/plans/my-plan.md
```

## Empty Index Handling

For new projects or empty indexes:

```json
{
  "is_empty_index": true,
  "message": "No artifact index found. This is normal for new projects."
}
```

Plans will include:
```markdown
## Historical Precedent

**Query:** "feature keywords"
**Index Status:** Empty (new project)

No historical data available. This is normal for new projects.
Proceeding with standard planning approach.
```

## Performance

| Component | Target | Measured |
|-----------|--------|----------|
| Planning query | <200ms | ~50ms |
| Plan validation | <500ms | ~100ms |
| Keyword extraction | <100ms | ~20ms |

## Overlap Detection Algorithm

The validation uses **bidirectional keyword overlap**:

1. Extract keywords from plan (Goal, Architecture, Tech Stack, Task names)
2. Extract keywords from failed handoffs (task_summary, what_failed, key_decisions)
3. Calculate overlap in both directions:
   - `plan_coverage` = intersection / plan_keywords
   - `failure_coverage` = intersection / handoff_keywords
4. Return maximum (catches both large and small plans)

**Threshold:** 30% overlap triggers warning

This bidirectional approach prevents large plans from escaping detection via keyword dilution.

## Keyword Extraction

Keywords are extracted from:

**Plans:**
- `**Goal:**` section
- `**Architecture:**` section
- `**Tech Stack:**` section
- `### Task N:` names
- `**Query:**` in Historical Precedent

**Handoffs:**
- `task_summary` field
- `what_failed` field
- `key_decisions` field

**Filtering:**
- 3+ character words only
- Stopwords removed (common English + technical generics)
- Case-insensitive matching

## Configuration

### Validation Threshold

Default: 30% overlap

```bash
# More sensitive (catches more potential issues)
python3 validate-plan-precedent.py plan.md --threshold 20

# Less sensitive (fewer warnings)
python3 validate-plan-precedent.py plan.md --threshold 50
```

### Keyword Sanitization

For security, keywords extracted from planning requests are sanitized:
- Only alphanumeric characters, hyphens, spaces allowed
- Shell metacharacters removed (`;`, `$`, `` ` ``, `|`, `&`)

## Troubleshooting

### "No historical data available"

Normal for:
- New projects
- Projects without `.ring/` initialized
- Projects where `artifact_index.py --all` hasn't been run

Solution: Run indexing once handoffs/plans exist:
```bash
python3 default/lib/artifact-index/artifact_index.py --all
```

### Query taking >200ms

Possible causes:
- Very large artifact index
- Complex query with many keywords

Solutions:
- Use more specific keywords
- Limit query scope with `--limit`

### Validation showing false positives

If validation warns about unrelated failures:
- Increase threshold: `--threshold 50`
- Review the overlapping keywords in output
- Refine plan wording to be more specific

## Tests

Run integration tests:

```bash
bash default/lib/tests/test-rag-planning.sh
```

Tests cover:
- Planning mode query functionality
- Performance (<200ms target)
- Keyword extraction quality
- Edge cases (missing files, invalid thresholds)
- Tech Stack extraction
