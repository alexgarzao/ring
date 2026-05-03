---
name: ring:pre-dev-subtask-creation
description: |
  Gate 8: Zero-context implementation steps - 2-5 minute atomic subtasks with
  complete code, exact commands, TDD pattern. Large Track only.

trigger: |
  - Tasks passed Gate 7 validation
  - Need absolute implementation clarity
  - Creating work for engineers with zero codebase context
  - Large Track workflow (2+ day features)

skip_when: |
  - Small Track workflow → execute tasks directly
  - Tasks simple enough without breakdown
  - Tasks not validated → complete Gate 7 first

sequence:
  after: [ring:pre-dev-task-breakdown]
  before: [ring:execute-plan, ring:subagent-driven-development]
---

# Subtask Creation — Zero-Context Implementation Steps

Write comprehensive implementation subtasks for engineers with zero context of the codebase. Each subtask follows RED-GREEN-REFACTOR: 2-5 minute steps with complete code, exact commands, and explicit verification.

**Output path:** `docs/pre-dev/{feature}/subtasks/T-[task-id]/ST-[task-id]-[number]-[description].md`

## Step Granularity

Each step is ONE action (2-5 minutes):
- "Write the failing test" → one step
- "Run it to confirm it fails" → one step
- "Implement minimal code to pass" → one step
- "Run tests and confirm pass" → one step
- "Commit" → one step

## Subtask Document Structure

**Header:**
```markdown
# ST-[task-id]-[number]: [Subtask Name]

> **For Agents:** REQUIRED SUB-SKILL: Use ring:execute-plan

**Goal:** One sentence — what this builds.
**Prerequisites:** Verification commands with expected output.
**Files:** Create: `exact/path`, Modify: `exact/path:lines`, Test: `tests/path`
```

**TDD Cycle Steps:**

| Step | Content |
|------|---------|
| Step 1: Write failing test | Complete test file with all imports |
| Step 2: Run test → confirm fail | Command + expected failure output |
| Step 3: Write minimal implementation | Complete implementation file |
| Step 4: Run test → confirm pass | Command + expected success output |
| Step 5: Update exports (if needed) | Exact modification to index/route files |
| Step 6: Verify type checking | Command + expected output |
| Step 7: Commit | Exact git commands with commit message |
| Rollback | Exact commands to undo if issues |

## Rules

### Include in Subtasks
- Exact file paths (absolute or from repo root)
- Complete file contents (if creating) or complete code snippets (if modifying)
- All imports and dependencies
- All step numbering (TDD cycle)
- Verification commands (copy-pasteable)
- Expected output (exact strings)
- Rollback procedure (exact commands)
- Prerequisites with verification commands

### Never Include
- Placeholders: `...`, `TODO`, `implement here`
- Vague instructions: "update the service", "add validation"
- Assumptions: "assuming setup is done"
- Context requirements: "you need to understand X first"
- Incomplete code: "add the rest yourself"
- Missing imports: "import necessary packages"
- Undefined success: "make sure it works"
- No verification: "test it manually"

## Multi-Module Subtasks

If topology is monorepo or multi-repo, each subtask must specify:
- `Target:` backend | frontend | shared
- `Working Directory:` absolute path from topology config
- `Agent:` ring:backend-engineer-* or ring:frontend-*-engineer-*

## Example Subtask Fragment

```markdown
# ST-T001-01: Write failing test for Account repository

**Goal:** Create failing test for AccountRepository.Create that verifies it persists an account.
**Prerequisites:**
  - `ls internal/repositories/` shows existing repo files
  - `go build ./...` passes without errors
**Files:**
  - Create: `internal/repositories/account_test.go`
  - Modify: None (test file is new)

---

### Step 1: Write the failing test

Create `internal/repositories/account_test.go`:

\`\`\`go
package repositories_test

import (
    "context"
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/LerianStudio/myservice/internal/repositories"
)

func TestAccountRepository_Create(t *testing.T) {
    repo := repositories.NewAccountRepository(testDB)
    account := &model.Account{Name: "Test Account", Status: "ACTIVE"}

    err := repo.Create(context.Background(), account)

    assert.NoError(t, err)
    assert.NotEmpty(t, account.ID)
}
\`\`\`

### Step 2: Run to confirm it fails

\`\`\`bash
go test ./internal/repositories/... -run TestAccountRepository_Create -v
\`\`\`

Expected output:
\`\`\`
--- FAIL: TestAccountRepository_Create
    account_test.go:15: undefined: repositories.NewAccountRepository
FAIL
\`\`\`

### Step 7: Commit

\`\`\`bash
git add internal/repositories/account_test.go
git commit -m "test(account): add failing test for AccountRepository.Create"
\`\`\`

### Rollback

\`\`\`bash
git reset HEAD~1
rm internal/repositories/account_test.go
\`\`\`
```

## Gate 8 Validation Checklist

| Category | Requirements |
|----------|--------------|
| **Coverage** | All tasks from Gate 7 have subtasks; every task's scope items have at least one subtask |
| **Completeness** | Every subtask has complete code (no placeholders); exact commands; expected output |
| **TDD Compliance** | Every subtask follows RED-GREEN-REFACTOR cycle |
| **Zero Context** | Subtask is completable without reading any other file or asking questions |
| **Verifiability** | Every step has a verification command with expected output |

**Gate Result:** ✅ PASS → Delivery Planning | ⚠️ CONDITIONAL (incomplete subtasks) | ❌ FAIL (placeholders or missing TDD cycle)
