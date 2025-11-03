Get suggestions for next skill based on current context.

**Usage:**
- `/ring:next-skill <current-skill> <context>` - Get next skill suggestion

**Example:**
```
User: /ring:next-skill test-driven-development "test revealed unexpected behavior"
Assistant: Analyzing workflow transition...

[Runs lib/skill-composer.sh]

Next skill suggestion: systematic-debugging

Reason: Test revealed unexpected behavior
Transition: Pause TDD, debug root cause, return to TDD after fix

Typical workflow:
1. Use systematic-debugging to find root cause
2. Fix the bug
3. Return to test-driven-development for GREEN phase
4. Continue with REFACTOR
```

**The composer suggests:**
- Next skill based on current context
- When to transition
- How to return to current skill
- Typical workflow pattern

**Helpful for:**
- Skill workflow transitions
- Avoiding getting stuck
- Following proven patterns
