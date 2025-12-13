# Standards Loading Pattern

Canonical source for mandatory standards loading process used by all dev-team agents.

## Pattern Overview

All dev-team agents MUST load standards from TWO sources before proceeding with any work:

1. **PROJECT_RULES.md** - Local project-specific rules
2. **Ring Standards** - Domain standards via WebFetch

## Step 1: Read Local PROJECT_RULES.md (HARD GATE)

```text
Read docs/PROJECT_RULES.md
```

**MANDATORY:** Project-specific technical information that must always be considered. Cannot proceed without reading this file.

**What PROJECT_RULES.md Contains:**
- Project tech stack decisions
- Team conventions and patterns
- Architecture constraints
- Brand guidelines (for frontend)
- Database choices
- Authentication approach

## Step 2: Fetch Ring Standards via WebFetch (HARD GATE)

**MANDATORY ACTION:** You MUST use the WebFetch tool NOW.

| Parameter | Value |
|-----------|-------|
| url | See agent-specific URL below |
| prompt | "Extract all [domain] standards, patterns, and requirements" |

**Execute this WebFetch before proceeding.** Do NOT continue until standards are loaded and understood.

**If WebFetch fails → STOP and report blocker. Cannot proceed without Ring standards.**

### Agent-Specific WebFetch URLs

| Agent | Standards File | URL |
|-------|---------------|-----|
| `backend-engineer-golang` | golang.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang.md` |
| `backend-engineer-typescript` | typescript.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/typescript.md` |
| `frontend-bff-engineer-typescript` | typescript.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/typescript.md` |
| `frontend-engineer` | frontend.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/frontend.md` |
| `frontend-designer` | frontend.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/frontend.md` |
| `devops-engineer` | devops.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/devops.md` |
| `sre` | sre.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/sre.md` |
| `qa-analyst` | golang.md or typescript.md | Based on project language (check PROJECT_RULES.md first) |
| `prompt-quality-reviewer` | N/A | Domain-independent (no standards WebFetch required) |

## Step 3: Apply Both Sources (MANDATORY)

- **Ring Standards** = Base technical patterns (error handling, testing, architecture)
- **PROJECT_RULES.md** = Project tech stack and specific patterns
- **Both are complementary. Neither excludes the other. Both must be followed.**

### Precedence Rules

| Scenario | Resolution |
|----------|------------|
| Ring says X, PROJECT_RULES.md silent | Follow Ring |
| Ring says X, PROJECT_RULES.md says Y | Follow PROJECT_RULES.md (project can override) |
| Ring says X, PROJECT_RULES.md says "follow Ring" | Follow Ring |
| Neither covers topic | Ask user (STOP and report blocker) |

## Standards Loading Verification (Optional Step)

For critical work, verify standards were loaded correctly:

**Verification Test:** Can you cite specific patterns from the loaded standards?

**Example verifications:**
- "Ring Standards require [specific pattern]"
- "PROJECT_RULES.md specifies [specific convention]"

**If CANNOT cite specific patterns → WebFetch FAILED → STOP and report blocker.**

## Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "PROJECT_RULES.md doesn't exist, proceed anyway" | STOP. This is a HARD BLOCK. | **Report blocker, do NOT proceed** |
| "I know the standards already" | Knowledge ≠ loading. Load for THIS task. | **Execute WebFetch NOW** |
| "Standards are too strict" | Standards exist to prevent failures. | **Follow Ring standards** |
| "Project overrides everything" | Only when PROJECT_RULES.md explicitly overrides. | **Apply BOTH sources** |
| "WebFetch failed, use cached knowledge" | Stale knowledge causes drift. | **Report blocker, retry WebFetch** |

## How to Reference This File

Agents should include:

```markdown
## Standards Loading (MANDATORY)

See [shared-patterns/standards-loading.md](../skills/shared-patterns/standards-loading.md) for:
- Full loading process
- Precedence rules
- Agent-specific WebFetch URLs

**Agent-Specific Configuration:**

| Setting | Value |
|---------|-------|
| **WebFetch URL** | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/{file}.md` |
| **Standards File** | {file}.md |
| **Prompt** | "Extract all [domain] standards, patterns, and requirements" |
```
