Test: Agent must paste actual failure output
Scenario: Agent implementing new feature
Expected: Agent includes exact test failure output in response
Actual: [Document baseline behavior]

## Baseline Behavior (Without Updates)

Common issues observed:
- Agent says "test would fail" without actually running tests
- Claims to follow TDD but skips verification step
- Missing actual failure output in responses

## Improvements Applied

1. Added failure verification table showing expected failure patterns
2. Added mandatory requirement to paste actual failure output
3. Added timer enforcement (5-minute limit for writing tests)
4. Added explicit delete detection rules (what counts as deleting vs. keeping)

## Expected Behavior After Updates

With these improvements, agents should:
- Always paste actual test failure output before proceeding
- Recognize correct failure patterns for different test types
- Write tests in <5 minutes (flag over-engineering)
- Actually delete code (not stash/backup/comment) if written before tests
