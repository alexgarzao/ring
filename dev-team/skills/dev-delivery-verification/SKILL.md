---
name: ring:dev-delivery-verification
description: |
  Delivery Verification Gate — verifies that what was requested is actually delivered
  as reachable, integrated code. Answers: "Is every requirement from the original task
  actually functioning in the running application?"

trigger: "Deprecated — use ring:dev-implementation instead (includes these checks as Gate 0 exit criteria)."

skip_when: "always — this skill is preserved but not dispatched in normal cycles."

sequence:
  after: [ring:dev-implementation]
  before: [ring:dev-devops]

related:
  complementary: [ring:dev-cycle, ring:dev-implementation, ring:codereview]
---

# Delivery Verification (Gate 0 Exit)

> **Status: Deprecated.** These checks are now embedded as Gate 0 exit criteria in ring:dev-implementation.
> This skill is preserved for reference and legacy cycles.

---

## Core Principle

Compilation ≠ delivery. Tests passing ≠ delivery. Integration means:
- Code is reachable (imported, wired, routed)
- Binaries include changed files
- Services start successfully

## Automated Checks

Run on all files changed by Gate 0:

### A. File Size Check

```bash
# Go
find . -name "*.go" ! -name "*_test.go" ! -path "*/generated/*" -exec wc -l {} + \
  | awk '$1 > 1000 {print "LARGE:", $0}'

# TypeScript
find . -name "*.ts" -o -name "*.tsx" | xargs wc -l | awk '$1 > 1000 {print "LARGE:", $0}'
```

- > 1500 lines: FAIL (mandatory decomposition)
- 1001-1500 lines: PARTIAL (cohesion justification required)
- ≤ 1000 lines: PASS

### B. License Header Check

```bash
for f in $files_changed; do
  head -10 "$f" | grep -qiE 'copyright|licensed|spdx' || echo "MISSING LICENSE: $f"
done
```

### C. Lint

```bash
# Go
golangci-lint run ./...

# TypeScript
npx eslint . --ext .ts,.tsx
```

### D. Migration Safety (if migrations changed)

Block patterns that cause downtime:
- `ADD COLUMN ... NOT NULL` without `DEFAULT`
- `DROP COLUMN`
- `CREATE INDEX` without `CONCURRENTLY`
- `ALTER COLUMN ... TYPE`
- `TRUNCATE`

## Integration Checklist

Per requirement:

| Check | Pass Condition |
|-------|----------------|
| Code compiles | `go build ./...` or `npm run build` succeeds |
| Binary includes changed packages | No orphaned packages |
| Endpoints registered | Route appears in router bootstrap |
| Service starts | `/health` returns 200 within 30s |
| Dependencies wired | No nil pointer panics in integration test |

## Traceability Matrix Template

```markdown
| Requirement | Requirement ID | Status | Files | Evidence |
|-------------|---------------|--------|-------|----------|
| {req text}  | REQ-001       | DELIVERED / NOT DELIVERED | path:line | {test or runtime proof} |
```

Every requirement must appear. NOT DELIVERED → return to Gate 0 with explicit gap.

## Verdict Criteria

- **PASS:** All requirements DELIVERED + all automated checks pass + service starts
- **PARTIAL:** Some requirements delivered → return to Gate 0 with explicit gap list
- **FAIL:** Critical requirements missing → return to Gate 0
