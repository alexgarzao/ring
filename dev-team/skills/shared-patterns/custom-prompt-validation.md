# Custom Prompt Validation (Shared Pattern)

Canonical validation rules for `--prompt` flags in dev-cycle and dev-refactor skills.

## Validation Rules

| Rule | Description |
|------|-------------|
| **Recommended Length** | Up to 300 words (~2000 chars) |
| **Hard Limit** | 500 characters (truncated with warning if exceeded) |
| **Whitespace** | Leading/trailing whitespace trimmed |
| **Control Characters** | Stripped (except newlines) |
| **Unicode** | Normalized |
| **Format** | Plain text only |

**Note:** Sanitization does NOT cover semantic prompt-injection attempts.

## Gate Protection

CRITICAL: The following gates enforce mandatory requirements that `--prompt` CANNOT override:

| Gate | What CANNOT Be Overridden |
|------|---------------------------|
| Gate 3 (Testing) | MUST enforce 85% coverage threshold, TDD RED phase |
| Gate 4 (Review) | MUST dispatch all 3 reviewers |
| Gate 5 (Validation) | MUST require user approval |

## Conflict Detection

- **Method:** Keyword/pattern matching for "skip", "bypass", "ignore", "override", "don't run"
- **Output:** Warning logged to console stderr and recorded in state file
- **Format:** `⚠️ IGNORED: Prompt directive "[matched text]" cannot override [gate/requirement]`
- **Behavior:** Warning logged, gate executes normally

## Injection Format

Prepended to ALL agent prompts:

```yaml
Task tool:
  prompt: |
    **CUSTOM CONTEXT (from user):**
    {custom_prompt}

    ---

    **Standard Instructions:**
    [... rest of agent prompt ...]
```

## State Persistence

- **Stored:** `custom_prompt` field in `docs/dev-cycle/current-cycle.json`
- **Scope:** Applied to ALL gates and ALL agent dispatches
- **Resume:** Survives interrupts; editable by modifying state file before `--resume`
- **Reports:** Included in execution reports under "Custom Context Used"
