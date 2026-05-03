---
name: ring:write-plan
description: |
  Creates comprehensive implementation plans with exact file paths, complete code
  examples, and verification steps for engineers with zero codebase context.

trigger: |
  - Design phase complete (brainstorm/PRD/TRD validated)
  - Need to create executable task breakdown
  - Creating work for other engineers or AI agents

skip_when: |
  - Design not validated → use brainstorm first
  - Requirements still unclear → use ring:pre-dev-prd-creation first
  - Already have a plan → use ring:execute-plan

sequence:
  after: [brainstorm, ring:pre-dev-trd-creation]
  before: [ring:execute-plan, ring:subagent-driven-development]
---

# Writing Plans

Dispatch a specialized agent to write comprehensive implementation plans for engineers with zero codebase context.

**Announce at start:** "Using ring:write-plan skill to create the implementation plan."

## The Process

### Step 1: Dispatch Write-Plan Agent

Dispatch via `Task(subagent_type: "ring:write-plan")` with instructions to:
- Create bite-sized tasks (2-5 min each)
- Include exact file paths, complete code, verification steps
- Save to `docs/plans/YYYY-MM-DD-<feature-name>.md`

### Step 2: Validate Plan

```bash
python3 default/lib/validate-plan-precedent.py docs/plans/YYYY-MM-DD-<feature>.md
```

`PASS` → proceed. `WARNING` → review warnings, update plan, re-run until PASS.

### Step 3: Ask About Execution

Via AskUserQuestion: "Execute now?"
1. **Execute now** → `ring:subagent-driven-development`
2. **Parallel session** → user opens new session with `ring:execute-plan`
3. **Save for later** → report location and end

## Plan Requirements (Zero-Context Test)

Every task must have: exact file paths (never "somewhere in src"), complete code (never "add validation here"), verification commands with expected output, failure recovery, bite-sized steps (2-5 min).

Header: goal, architecture, tech stack. Include review checkpoints and recommended agents per task.

## Multi-Module Task Requirements

If TopologyConfig exists, each task MUST include:

```markdown
## Task N: Title

**Target:** backend | frontend | shared
**Working Directory:** packages/api
**Agent:** ring:backend-engineer-golang
```

### Agent Selection

| Task | Agent |
|------|-------|
| Go backend | `ring:backend-engineer-golang` |
| TypeScript backend | `ring:backend-engineer-typescript` |
| Frontend (direct api_pattern) | `ring:frontend-engineer` |
| Frontend BFF routes | `ring:frontend-bff-engineer-typescript` |
| Infra/CI/CD | `ring:devops-engineer` |
| Testing | `ring:qa-analyst` |
| Reliability | `ring:sre` |
| Fallback | `ring:general-purpose` |

**For frontend tasks:** read `api_pattern` from TopologyConfig. `direct` → `ring:frontend-engineer`. `bff` → BFF routes use `ring:frontend-bff-engineer-typescript`, UI components use `ring:frontend-engineer`.
