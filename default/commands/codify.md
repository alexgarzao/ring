---
name: codify
description: Document a solved problem to build searchable knowledge base
argument-hint: "[optional-description]"
---

Capture the current problem solution as structured documentation in `docs/solutions/{category}/`. Use this after confirming a fix worked to build institutional knowledge that helps future debugging.

## Usage

```
/ring-default:codify [optional description of the problem]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `description` | No | Brief description of the problem (helps pre-fill template) |

## Examples

### Document After Debugging
```
/ring-default:codify
```
Captures the solution from the current conversation context.

### Document With Description
```
/ring-default:codify JWT parsing error in auth middleware
```
Pre-fills the title and helps with context gathering.

### Document Specific Fix
```
/ring-default:codify race condition in user session cleanup
```
Documents a race condition fix with the given context.

## What It Does

1. **Gathers Context** - Extracts problem details from conversation history
2. **Checks for Duplicates** - Searches `docs/solutions/` for similar issues
3. **Validates Schema** - Ensures all required fields are present
4. **Creates Documentation** - Writes structured markdown to `docs/solutions/{category}/`
5. **Offers Next Steps** - Link issues, add patterns, continue workflow

## When to Use

- After debugging session where fix was non-trivial (> 5 min)
- When solution would help future developers or AI agents
- After investigating error that took multiple attempts to solve
- When you want to prevent re-investigating the same issue

## When NOT to Use

- Simple typo or syntax error (took < 2 min)
- Issue already documented in `docs/solutions/`
- One-off issue that won't recur
- Trivial fix obvious from error message

## Output Location

Solutions are stored in category-specific directories:

```
docs/solutions/
├── build-errors/
├── test-failures/
├── runtime-errors/
├── performance-issues/
├── database-issues/
├── security-issues/
├── ui-bugs/
├── integration-issues/
├── logic-errors/
├── dependency-issues/
├── configuration-errors/
└── workflow-issues/
```

## Required Fields

The command will gather and validate:

| Field | Description |
|-------|-------------|
| `date` | When the problem was solved |
| `problem_type` | Category (determines directory) |
| `component` | Affected module/service |
| `symptoms` | Observable errors/behaviors (1-5) |
| `root_cause` | Fundamental cause |
| `resolution_type` | Type of fix applied |
| `severity` | Impact level |

## Process Flow

```
/codify invoked
    ↓
Gather context from conversation
    ↓
Check for existing similar docs
    ↓
Validate YAML schema
    ↓
Create documentation file
    ↓
Present next steps menu
```

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `ring-default:systematic-debugging` | Run /codify AFTER debugging completes |
| `ring-default:codify-solution` | The underlying skill (invoked automatically) |
| `/ring-default:write-plan` | Plans can search documented solutions (invokes write-plan agent) |
| `/ring-pm-team:pre-dev-feature` | Pre-dev can reference prior solutions |

## The Compounding Effect

```
Session 1: Debug issue (30 min) → Document (5 min)
Session 2: Search docs (2 min) → Apply known fix (5 min)
Session 3: Quick lookup (1 min) → Instant fix

Time saved grows with each reuse.
```

## Troubleshooting

### "Missing required context"
The command needs more information. You'll be prompted for:
- Component name
- Error symptoms
- Root cause
- What was changed to fix it

### "Similar issue already documented"
A related solution exists. You'll be asked to:
1. Create new doc with cross-reference (different root cause)
2. Update existing doc (same root cause, new info)
3. Skip documentation (exact duplicate)

### "Schema validation failed"
A required field has an invalid value. Check:
- `problem_type` uses valid enum value
- `root_cause` uses valid enum value
- `symptoms` has 1-5 items
- `severity` is critical/high/medium/low

## Tips

1. **Run immediately after fix** - Context is freshest right after solving
2. **Include exact error messages** - Makes future searches work
3. **Add prevention tips** - Most valuable part of documentation
4. **Cross-reference related docs** - Build knowledge graph
5. **Use tags** - Improves discoverability
