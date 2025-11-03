# Ring Testing Documentation

## Overview

Testing for ring infrastructure includes:
1. Integration tests (validate end-to-end workflows)
2. Pressure tests (validate skills resist rationalization)
3. Unit tests (validate individual lib scripts)

## Integration Tests

Located in `testing/test-*.md`:
- `test-review-orchestrator.md` - Sequential review automation
- `test-skill-matcher.md` - Task-to-skill mapping
- `test-lib-validators.md` - Validator scripts

**Run integration tests:**
```bash
# Manual testing - follow test procedures in each file
cat testing/test-review-orchestrator.md
# Execute test cases as documented
```

## Pressure Tests

Located in `skills/*/test-*.md`:
- Test skills under pressure (time limits, missing info)
- Validate skills resist rationalization
- Ensure mandatory steps aren't skipped

**See:** `skills/systematic-debugging/test-pressure-*.md` for examples

## Unit Tests for lib/ Scripts

**Testing compliance-validator.sh:**
```bash
# Test 1: No compliance rules
./lib/compliance-validator.sh skills/using-ring/SKILL.md
# Expected: "No compliance rules defined" (exit 0)

# Test 2: Invalid file
./lib/compliance-validator.sh nonexistent.md
# Expected: "File not found" (exit 2)
```

**Testing output-validator.sh:**
```bash
# Test 1: Valid output
echo "## VERDICT: PASS\n## Summary\nGood\n## Issues Found\nNone\n## Next Steps\nDone" > /tmp/valid.md
./lib/output-validator.sh agents/code-reviewer.md /tmp/valid.md
# Expected: "Output format validation: PASS" (exit 0)

# Test 2: Missing VERDICT
echo "## Summary\nNo verdict" > /tmp/invalid.md
./lib/output-validator.sh agents/code-reviewer.md /tmp/invalid.md
# Expected: "Missing required section: VERDICT" (exit 1)
```

**Testing skill-matcher.sh:**
```bash
# Test 1: Debugging task
./lib/skill-matcher.sh "debug authentication error"
# Expected: systematic-debugging in top results

# Test 2: Implementation task
./lib/skill-matcher.sh "implement user login"
# Expected: test-driven-development in top results

# Test 3: No matches
./lib/skill-matcher.sh "xyz unrelated abc"
# Expected: "No matching skills found"
```

**Testing metrics-tracker.sh:**
```bash
# Test 1: Track skill usage
./lib/metrics-tracker.sh skill test-skill used
cat .ring/metrics.json | jq '.skills["test-skill"].usage_count'
# Expected: 1

# Test 2: Track violation
./lib/metrics-tracker.sh skill test-skill violation "test_violation"
cat .ring/metrics.json | jq '.skills["test-skill"].violations'
# Expected: {"test_violation": {"count": 1, ...}}
```

## Adding New Tests

When adding new infrastructure features:
1. Create `testing/test-<feature>.md`
2. Document test cases with expected outputs
3. Add to this README
4. Run tests before marking feature complete

## Automated Testing (Future)

Future enhancement: Convert .md test documentation to executable test suite (bash scripts, pytest, etc.)
