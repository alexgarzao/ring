# File Size Enforcement (MANDATORY)

## Standard Reference

**Source:** `golang/domain.md` → File Organization (MANDATORY)
**Rule:** Max 200-300 lines per file. If longer, split by responsibility boundaries.

This is a **HARD GATE** — not a suggestion.

---

## Thresholds

| Lines | Action |
|-------|--------|
| ≤ 300 | ✅ Compliant |
| 301-500 | ⚠️ WARNING — Must justify or split before proceeding |
| > 500 | ❌ BLOCKING — Must split before gate can pass |

**These thresholds apply to ALL source files** (`*.go`, `*.ts`, `*.tsx`). Auto-generated files (swagger, protobuf, mocks) are exempt.

---

## When to Check

| Context | Check Point |
|---------|-------------|
| **ring:dev-cycle Gate 0** | After implementation agent completes — verify no file exceeds 500 lines |
| **ring:dev-cycle Gate 0.5** | Delivery verification includes file size check |
| **ring:dev-refactor Step 4** | Agents MUST flag files > 300 lines as FINDING-XXX |
| **ring:dev-implementation** | Agent MUST NOT create files > 300 lines. If a task would make a file exceed 300 lines, agent MUST split proactively |

---

## Verification Command

```bash
# Go projects
find . -name "*.go" ! -name "*_test.go" ! -path "*/docs/*" ! -path "*/mocks*" ! -name "*.pb.go" -exec wc -l {} + | awk '$1 > 300 {print}' | sort -rn

# TypeScript projects
find . -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v dist | xargs wc -l | awk '$1 > 300 {print}' | sort -rn
```

---

## Split Strategy

When a file exceeds the threshold, split by **responsibility boundaries** (not arbitrary line counts):

| Pattern | Split Into |
|---------|-----------|
| CRUD + validation + business logic | `*_command.go`, `*_query.go`, `*_validator.go` |
| Provisioning + deprovisioning | `*_provision.go`, `*_deprovision.go` |
| Handler with settings + cache + CRUD | `*_handler.go`, `*_handler_settings.go`, `*_handler_cache.go` |
| Service with lifecycle + helpers | `*_lifecycle.go`, `*_helpers.go` |
| Large test file | Split test file to mirror source file split |

**Rules:**
1. All split files stay in the **same package** — zero breaking changes
2. All methods remain on the **same receiver** (if applicable)
3. Test files split to match: `foo.go` → `foo_test.go`
4. Run `go build ./...` and `go test ./...` after each split to verify

---

## Agent Instructions

### For ring:dev-implementation (Gate 0)

Include in ALL implementation agent prompts:

```
⛔ FILE SIZE ENFORCEMENT (MANDATORY):
- You MUST NOT create or modify files to exceed 300 lines (excluding tests)
- If implementing a feature would push a file past 300 lines, you MUST split it proactively
- Split by responsibility boundaries (not arbitrary line counts)
- Each split file stays in the same package
- Test files MUST be split to match source files
- After splitting, verify: go build ./... && go test ./...
- Files > 500 lines = HARD BLOCK. Cannot proceed.

Reference: golang/domain.md → File Organization (MANDATORY)
```

### For ring:dev-refactor (Step 4 agents)

Include in ALL analysis agent prompts:

```
⛔ FILE SIZE ENFORCEMENT (MANDATORY):
- Any source file > 300 lines MUST be flagged as FINDING-XXX
- Files 301-500 lines: severity HIGH
- Files > 500 lines: severity CRITICAL
- Files > 1000 lines: severity CRITICAL with explicit decomposition plan
- Include line count and proposed split in the finding
- Each file split = one FINDING-XXX (not grouped)
```

---

## Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "It's all one struct, can't split" | Methods on the same struct can live in different files (same package) | **Split by method responsibility** |
| "File will be split later" | Later = never. Split NOW during implementation. | **Split before gate passes** |
| "It's only 350 lines" | 350 > 300 = non-compliant. Standards are not negotiable. | **Split or justify** |
| "Splitting adds complexity" | Large files ARE complexity. Small focused files reduce cognitive load. | **Split by responsibility** |
| "Tests will break" | Split test files to match. Same package = same access. | **Split tests alongside source** |
| "Auto-generated code is large" | Auto-generated files (swagger, protobuf, mocks) are exempt. | **Check if truly auto-generated** |
| "This is a temporary file" | Temporary becomes permanent. Standards apply to all files. | **Split or delete** |
