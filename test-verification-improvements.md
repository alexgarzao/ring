Test: Agent cannot use banned phrases
Scenario: Agent completing implementation task
Expected: No weasel words, evidence required first
Actual: [Document baseline]

## Baseline Behavior (Without Updates)

Common issues:
- Agent uses "appears to work" or "seems to work"
- Claims completion before verification
- Missing actual command output

## Improvements Applied

1. Added banned phrases list (automatic violations)
2. Added command-first rule (run → paste → claim structure)
3. Added false positive trap (checklist before claiming "all tests pass")

## Expected Behavior After Updates

With these improvements, agents should:
- Never use banned phrases like "appears to" or "should be working"
- Always run verification command BEFORE making claims
- Paste actual output in the same message as claims
- Check false positive trap before claiming test success
