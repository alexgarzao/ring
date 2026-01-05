---
description: Analyze session learnings and propose new rules/skills
agent: plan
subtask: false
---

Analyze accumulated session learnings to detect recurring patterns and propose new rules, skills, or hooks. Requires user approval before creating any permanent artifacts.

## Options

| Option | Description |
|--------|-------------|
| (none) | Analyze learnings and generate new proposals |
| `--list` | List pending proposals without analyzing |
| `--approve <id>` | Approve a specific proposal |
| `--reject <id>` | Reject a specific proposal with optional reason |
| `--history` | Show history of approved/rejected proposals |

## Process

### 1. Gather (Automatic)
Read `.ring/cache/learnings/*.md` files, count total sessions available.

### 2. Analyze (Automatic)
- Extract patterns from What Worked, What Failed, Key Decisions
- Consolidate similar patterns using fuzzy matching
- Detect patterns appearing in 3+ sessions

### 3. Categorize (Automatic)
Classify patterns as rule, skill, or hook candidates. Generate preview content.

### 4. Propose (Interactive)
Present each qualifying pattern with draft content. Wait for decision.

### 5. Create (On Approval)
Create rule/skill/hook in appropriate location. Update proposal history.

## Output Example

```markdown
## Compound Learnings Analysis

**Sessions Analyzed:** 12
**Patterns Detected:** 8
**Qualifying (3+ sessions):** 3

---

### Proposal 1: Always use explicit file paths

**Signal:** 5 sessions
**Category:** Rule

**Preview:**
# Always use explicit file paths
Never use relative paths - always use absolute paths.

**Action Required:** Type `approve`, `reject`, or `modify`
```

$ARGUMENTS

Optionally provide --list, --approve <id>, --reject <id>, or --history.
