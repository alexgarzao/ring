# Agent Design Reference

This document contains agent output schema archetypes and standards compliance requirements for Ring agents.

---

## Agent Output Schema Archetypes

Agents use standard output schema patterns based on their purpose:

### Implementation Schema

**For agents that write code/configs:**

```yaml
output_schema:
  format: "markdown"
  required_sections:
    - name: "Summary"
      pattern: "^## Summary"
      required: true
    - name: "Implementation"
      pattern: "^## Implementation"
      required: true
    - name: "Files Changed"
      pattern: "^## Files Changed"
      required: true
    - name: "Testing"
      pattern: "^## Testing"
      required: true
    - name: "Next Steps"
      pattern: "^## Next Steps"
      required: true
```

**Used by:** `ring:backend-engineer-golang`, `ring:backend-engineer-typescript`, `frontend-bff-engineer-typescript`, `ring:devops-engineer`, `ring:qa-analyst`, `ring:sre`, `finops-automation`

---

### Analysis Schema

**For agents that analyze and recommend:**

```yaml
output_schema:
  format: "markdown"
  required_sections:
    - name: "Analysis"
      pattern: "^## Analysis"
      required: true
    - name: "Findings"
      pattern: "^## Findings"
      required: true
    - name: "Recommendations"
      pattern: "^## Recommendations"
      required: true
    - name: "Next Steps"
      pattern: "^## Next Steps"
      required: true
```

**Used by:** `ring:frontend-designer`, `finops-analyzer`

---

### Reviewer Schema

**For code review agents:**

```yaml
output_schema:
  format: "markdown"
  required_sections:
    - name: "VERDICT"
      pattern: "^## VERDICT: (PASS|FAIL|NEEDS_DISCUSSION)$"
      required: true
    - name: "Summary"
      pattern: "^## Summary"
      required: true
    - name: "Issues Found"
      pattern: "^## Issues Found"
      required: true
    - name: "Categorized Issues"
      pattern: "^### (Critical|High|Medium|Low)"
      required: false
    - name: "What Was Done Well"
      pattern: "^## What Was Done Well"
      required: true
    - name: "Next Steps"
      pattern: "^## Next Steps"
      required: true
```

**Used by:** `ring:code-reviewer`, `ring:business-logic-reviewer`, `ring:security-reviewer`, `ring:dead-code-reviewer`

**Note:** `ring:business-logic-reviewer` and `ring:security-reviewer` extend the base Reviewer Schema with additional domain-specific required sections:
- `ring:business-logic-reviewer` adds: "Mental Execution Analysis", "Business Requirements Coverage", "Edge Cases Analysis"
- `ring:security-reviewer` adds: "OWASP Top 10 Coverage", "Compliance Status"

---

### Exploration Schema

**For deep codebase analysis:**

```yaml
output_schema:
  format: "markdown"
  required_sections:
    - name: "EXPLORATION SUMMARY"
      pattern: "^## EXPLORATION SUMMARY$"
      required: true
    - name: "KEY FINDINGS"
      pattern: "^## KEY FINDINGS$"
      required: true
    - name: "ARCHITECTURE INSIGHTS"
      pattern: "^## ARCHITECTURE INSIGHTS$"
      required: true
    - name: "RELEVANT FILES"
      pattern: "^## RELEVANT FILES$"
      required: true
    - name: "RECOMMENDATIONS"
      pattern: "^## RECOMMENDATIONS$"
      required: true
```

**Used by:** `ring:codebase-explorer`

---

### Planning Schema

**For implementation planning:**

```yaml
output_schema:
  format: "markdown"
  required_sections:
    - name: "Goal"
      pattern: "^\\*\\*Goal:\\*\\*"
      required: true
    - name: "Architecture"
      pattern: "^\\*\\*Architecture:\\*\\*"
      required: true
    - name: "Tech Stack"
      pattern: "^\\*\\*Tech Stack:\\*\\*"
      required: true
    - name: "Global Prerequisites"
      pattern: "^\\*\\*Global Prerequisites:\\*\\*"
      required: true
    - name: "Task"
      pattern: "^### Task \\d+:"
      required: true
```

**Used by:** `ring:write-plan`

---

## Standards Compliance (Conditional Output Section)

The `ring-dev-team` agents include a **Standards Compliance** output section that is conditionally required based on invocation context.

### Schema Definition

All ring-dev-team agents include this in their `output_schema`:

```yaml
- name: "Standards Compliance"
  pattern: "^## Standards Compliance"
  required: false  # In schema, but MANDATORY when invoked from ring:dev-refactor
  description: "Comparison of codebase against Lerian/Ring standards. MANDATORY when invoked from ring:dev-refactor skill."
```

### Conditional Requirement: `invoked_from_dev_refactor`

| Context | Standards Compliance Required | Enforcement |
|---------|------------------------------|-------------|
| Direct agent invocation | Optional | Agent may include if relevant |
| Via `ring:dev-cycle` | Optional | Agent may include if relevant |
| Via `ring:dev-refactor` | **MANDATORY** | Prompt includes `MODE: ANALYSIS ONLY` |

**How It's Triggered:**
1. User invokes `/ring:dev-refactor` command
2. The skill dispatches agents with prompts starting with `**MODE: ANALYSIS ONLY**`
3. This prompt pattern signals to agents that Standards Compliance output is MANDATORY
4. Agents load Ring standards via WebFetch and produce comparison tables

**Detection in Agent Prompts:**
```text
If prompt contains "**MODE: ANALYSIS ONLY**":
  → Standards Compliance section is MANDATORY
  → Agent MUST load Ring standards via WebFetch
  → Agent MUST produce comparison tables

If prompt does NOT contain "**MODE: ANALYSIS ONLY**":
  → Standards Compliance section is optional
  → Agent focuses on implementation/other tasks
```

### Affected Agents

All ring-dev-team agents support Standards Compliance:

| Agent | Standards Source | Categories Checked |
|-------|------------------|-------------------|
| `ring:backend-engineer-golang` | `golang.md` | lib-commons, Error Handling, Logging, Config |
| `ring:backend-engineer-typescript` | `typescript.md` | Type Safety, Error Handling, Validation |
| `ring:devops-engineer` | `devops.md` | Dockerfile, docker-compose, CI/CD |
| `frontend-bff-engineer-typescript` | `frontend.md` | Component patterns, State management |
| `ring:frontend-designer` | `frontend.md` | Accessibility, Design patterns |
| `ring:qa-analyst` | `qa.md` | Test coverage, Test patterns |
| `ring:sre` | `sre.md` | Health endpoints, Logging, Tracing |

### Output Format Examples

**When ALL categories are compliant:**
```markdown
## Standards Compliance

Fully Compliant - Codebase follows all Lerian/Ring Standards.

No migration actions required.
```

**When ANY category is non-compliant:**
```markdown
## Standards Compliance

### Lerian/Ring Standards Comparison

| Category | Current Pattern | Expected Pattern | Status | File/Location |
|----------|----------------|------------------|--------|---------------|
| Error Handling | Using panic() | Return error | Non-Compliant | handler.go:45 |
| Logging | Uses fmt.Println | lib-commons/zap | Non-Compliant | service/*.go |
| Config | os.Getenv direct | SetConfigFromEnvVars() | Non-Compliant | config.go:15 |

### Compliance Summary
- **Total Violations:** 3
- **Critical:** 0
- **High:** 1
- **Medium:** 2
- **Low:** 0

### Required Changes for Compliance

1. **Error Handling Migration**
   - Replace: `panic("error message")`
   - With: `return fmt.Errorf("context: %w", err)`
   - Files affected: handler.go, service.go

2. **Logging Migration**
   - Replace: `fmt.Println("debug info")`
   - With: `logger.Info("debug info", zap.String("key", "value"))`
   - Import: `import "github.com/LerianStudio/lib-commons/zap"`
   - Files affected: internal/service/*.go
```

### Cross-References

| Document | Location | What It Contains |
|----------|----------|-----------------|
| **Skill Definition** | `dev-team/skills/dev-refactor/SKILL.md` | HARD GATES requiring Standards Compliance |
| **Standards Source** | `dev-team/docs/standards/*.md` | Source of truth for compliance checks |
| **Agent Definitions** | `dev-team/agents/*.md` | output_schema includes Standards Compliance |
| **Session Hook** | `dev-team/hooks/session-start.sh` | Injects Standards Compliance guidance |

---

## Related Documents

- [CLAUDE.md](../CLAUDE.md) - Main project instructions (references this document)
- [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) - Language patterns for agent prompts
- [WORKFLOWS.md](WORKFLOWS.md) - How to add/modify agents

---

## Positive Example Blocks (Replaces Anti-Rationalization Tables)

**Anti-rationalization tables are no longer mandatory.** Based on Anthropic's research, positive `<example>` blocks showing correct behavior outperform prohibition-based tables.

**Why the pattern changed:**
Positive examples outperform prohibitions in prompt design. Telling a model what to do correctly — with a concrete example — is more effective than enumerating what it must not rationalize. Long anti-rationalization tables also increase prompt length without proportional benefit, and can inadvertently prime models to consider the wrong patterns.

**The new `<example>` pattern:**

Instead of a "Rationalization / Why It's WRONG / Required Action" table, agents should include a positive example block that demonstrates the correct behavior:

```markdown
<example>
Scenario: You are asked to implement an endpoint but the task lacks acceptance criteria.

Correct behavior:
1. STOP before writing any code
2. Report to orchestrator: "Blocker: Missing acceptance criteria for [endpoint]. Cannot proceed."
3. Wait for clarification — do not guess or assume

Incorrect behavior:
- Inferring acceptance criteria from context and proceeding
- Writing "placeholder" code "just to get started"
- Asking the user directly instead of reporting to orchestrator
</example>
```

**Mandatory Sections Every Agent MUST Have:**

| Section              | Purpose                        | Language Requirements                      |
| -------------------- | ------------------------------ | ------------------------------------------ |
| **Blocker Criteria** | Define when to STOP and report | Use "STOP", "CANNOT proceed", "HARD BLOCK" |
| **`<example>` block** | Show correct behavior          | Positive scenario with correct vs wrong    |

See [docs/PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) for language guidelines (Lexical Salience, enforcement word positioning).

---

## Agent Modification Verification (MANDATORY)

**HARD GATE: Before creating or modifying any agent file, MUST verify compliance with this checklist.**

**Step 1: Verify Agent Has All Required Sections**

| Required Section                              | Pattern to Check                 | If Missing                                                        |
| --------------------------------------------- | -------------------------------- | ----------------------------------------------------------------- |
| **Standards Loading (MANDATORY)**             | `## Standards Loading`           | MUST add with `_index.md` + selective module loading instructions |
| **Blocker Criteria - STOP and Report**        | `## Blocker Criteria`            | MUST add with decision type table                                 |
| **Positive `<example>` block**                | `<example>`                      | MUST add at least one block showing correct vs incorrect behavior |
| **Standards Compliance Report** (dev-team)    | `## Standards Compliance Report` | MUST add for dev-team agents                                      |

**Step 2: Pre-Completion Checklist**

```text
CHECKLIST (all must be YES):
[ ] Does agent have Standards Loading section referencing _index.md?
[ ] Does agent have Blocker Criteria table?
[ ] Does agent have at least one positive <example> block?
[ ] Does agent define when to STOP and report?
[ ] Is agent within line budget: ≤300 lines (implementation) or ≤200 lines (reviewer)?

If any checkbox is no → Agent is INCOMPLETE. Add missing sections.
```

**This verification is not optional. This is a HARD GATE for all agent modifications.**
