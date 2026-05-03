---
name: ring:testing-anti-patterns
description: |
  Test quality guard - prevents testing mock behavior, production pollution with
  test-only methods, and mocking without understanding dependencies.

trigger: |
  - Reviewing or modifying existing tests
  - Adding mocks to tests
  - Tempted to add test-only methods to production code
  - Tests passing but seem to test the wrong things

skip_when: |
  - Writing new tests via TDD → TDD prevents these patterns
  - Pure unit tests without mocks → check other quality concerns

related:
  complementary: [ring:test-driven-development]
---

# Testing Anti-Patterns

**Core principle: Test what the code does, not what the mocks do.**

Following strict TDD prevents all of these anti-patterns.

## The Iron Laws

1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies

## Anti-Pattern 1: Testing Mock Behavior

**BAD:** `expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument()` — testing mock existence.  
**GOOD:** `expect(screen.getByRole('navigation')).toBeInTheDocument()` — test real component or don't mock.

**Gate:** "Am I testing real behavior or mock existence?" If mock → delete assertion or unmock.

## Anti-Pattern 2: Test-Only Methods in Production

**BAD:** `session.destroy()` method only called in tests — pollutes production, dangerous if accidentally called.  
**GOOD:** `cleanupSession(session)` in `test-utils/` — keeps production clean.

**Gate:** "Is this method only used by tests?" → move to test utilities.

## Anti-Pattern 3: Mocking Without Understanding

**BAD:** Mocking `discoverAndCacheTools` breaks a config write test that depends on it — test passes for wrong reason.  
**GOOD:** Mock only the slow part (`MCPServerManager`), preserve behavior the test needs.

**Gate:** Before mocking → (1) What side effects does real method have? (2) Does test depend on them? If yes → mock at lower level.

**Red flags:** "Mock to be safe", "might be slow", mocking without understanding.

## Anti-Pattern 4: Incomplete Mocks

**BAD:** Partial mock missing `metadata` field — breaks when downstream code accesses `response.metadata.requestId`.  
**GOOD:** Complete mock mirroring real API — ALL fields the real API returns.

**Iron Rule:** Mock COMPLETE data structure, not just fields your test uses. Partial mocks fail silently.

**Gate:** Check real API response before writing mock. Include all documented fields.

## Anti-Pattern 5: Tests as Afterthought

**Fix:** TDD cycle — write test → implement → refactor → claim complete.

## When Mocks Become Too Complex

Warning signs: mock setup longer than test logic, mocking everything, mocks missing methods real components have.  
**Consider:** Integration tests with real components are often simpler than elaborate mocks.

## Quick Reference

| Anti-Pattern | Fix |
|--------------|-----|
| Assert on mock elements | Test real component or unmock it |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand deps first, mock minimally |
| Incomplete mocks | Mirror real API completely |
| Tests after implementation | TDD — tests first |
| Over-complex mocks | Consider integration tests |

## Red Flags

- Assertion checks for `*-mock` test IDs
- Methods only called in test files
- Mock setup is >50% of test
- Test fails when you remove the mock
- "Mocking to be safe"

**If TDD reveals you're testing mock behavior → you violated TDD.** Fix: test real behavior or question why you're mocking at all.
