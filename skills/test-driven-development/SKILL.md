---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code - write the test first, watch it fail, write minimal code to pass; ensures tests actually verify behavior by requiring failure first
---

# Test-Driven Development (TDD)

**Core principle:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

If you didn't watch the test fail, you don't know if it tests the right thing.

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask your human partner):**
- Throwaway prototypes
- Generated code
- Configuration files

Thinking "skip TDD just this once"? Stop. That's rationalization.

## Red-Green-Refactor Cycle

### RED - Write Failing Test

Write one minimal test showing what should happen.

**Good example:**
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```
Clear name, tests real behavior, one thing.

**Bad example:**
```typescript
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```
Vague name, tests mock not code.

**Requirements:**
- One behavior
- Clear name
- Real code (no mocks unless unavoidable)

**Time limit:** <5 minutes. Longer = over-engineering.

If your test needs complex mocks, lots of setup, or multiple assertions → design too complex.

### Verify RED - Watch It Fail

**MANDATORY. Never skip.**

```bash
npm test path/to/test.test.ts
```

**Paste the ACTUAL failure output in your response:**
```
[PASTE EXACT OUTPUT HERE]
[NO OUTPUT = VIOLATION]
```

If you can't paste output, you didn't run the test.

**Required Failure Patterns:**

| Test Type | Must See This Failure | Wrong Failure = Wrong Test |
|-----------|----------------------|---------------------------|
| New feature | `NameError: function not defined` or `AttributeError` | Test passing = testing existing behavior |
| Bug fix | Actual wrong output/behavior | Test passing = not testing the bug |
| Refactor | Tests pass before and after | Tests fail after = broke something |

**Confirm:**
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

**Test passes?** You're testing existing behavior. Fix test.

**Test errors?** Fix error, re-run until it fails correctly.

### GREEN - Minimal Code

Write simplest code to pass the test.

**Good:**
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```
Just enough to pass.

**Bad:**
```typescript
async function retryOperation<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number) => void;
  }
): Promise<T> {
  // YAGNI - over-engineered
}
```

Don't add features, refactor other code, or "improve" beyond the test.

### Verify GREEN - Watch It Pass

**MANDATORY.**

```bash
npm test path/to/test.test.ts
```

**Confirm:**
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix code, not test.

**Other tests fail?** Fix now.

### REFACTOR - Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Don't add behavior.

### Repeat

Next failing test for next feature.

## Code Written Before Test

**If you wrote implementation before test:**

1. **Delete it:** `rm [file]` or `git reset --hard`
2. **Delete means DELETE** - no stash, no .bak, no clipboard, no "reference"
3. Write failing test first
4. Implement fresh from tests

**Not deleting = violation:**
- `git stash` → Hiding, not deleting
- `mv file.py file.py.bak` → Keeping
- Copy to clipboard → Keeping
- Comment out → Keeping

**Delete means gone forever. Implement fresh.**

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in name? Split it. | `test('validates email and domain and whitespace')` |
| **Clear** | Name describes behavior | `test('test1')` |
| **Real** | Tests actual code, not mocks | Tests mock behavior |

## Verification Checklist

Before marking work complete:

```
TDD Verification:
□ Every new function/method has a test
□ Watched each test fail before implementing
□ Each test failed for expected reason (feature missing, not typo)
□ Wrote minimal code to pass each test
□ All tests pass
□ Output pristine (no errors, warnings)
□ Tests use real code (mocks only if unavoidable)
□ Edge cases and errors covered
```

**Can't check all boxes? You skipped TDD. Start over.**

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write wished-for API. Write assertion first. Ask partner. |
| Test too complicated | Design too complicated. Simplify interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify design. |

## Red Flags

**STOP and start over if:**
- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why test failed
- "I'll test after" / "Tests after achieve same goals"
- "Already manually tested it"
- "Too simple to test"
- "Deleting X hours is wasteful" (sunk cost fallacy)
- "Keep as reference" (you'll adapt it = testing after)
- "TDD is dogmatic, being pragmatic" (TDD IS pragmatic)
- "It's about spirit not ritual" (tests-first IS the spirit)

**All of these mean: Delete code. Start over with TDD.**

## Integration

**Bug fixes:** Write failing test reproducing bug. Follow TDD cycle. Test proves fix and prevents regression.

**With systematic-debugging:** Pause TDD if test reveals unexpected behavior. Use systematic-debugging to find root cause. Return to TDD after fix.

**Never fix bugs without a test.**

## Required Patterns

This skill uses these universal patterns:
- **State Tracking:** See `skills/shared-patterns/state-tracking.md`
- **Failure Recovery:** See `skills/shared-patterns/failure-recovery.md`
- **Exit Criteria:** See `skills/shared-patterns/exit-criteria.md`
- **TodoWrite:** See `skills/shared-patterns/todowrite-integration.md`

Apply ALL patterns when using this skill.
