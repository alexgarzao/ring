---
pattern_name: {{PATTERN_NAME}}
category: {{CATEGORY}}
frequency: {{high|medium|low}}
severity_when_missed: {{critical|high|medium|low}}
created: {{DATE}}
instances:
  - {{SOLUTION_DOC_1}}
---

# Critical Pattern: {{PATTERN_NAME}}

## Summary

{{One sentence description of the pattern}}

## The Pattern

{{Describe the anti-pattern or mistake that keeps recurring}}

## Why It Happens

1. {{Common reason 1}}
2. {{Common reason 2}}

## How to Recognize

**Warning Signs:**
- {{Sign 1}}
- {{Sign 2}}

**Typical Error Messages:**
```
{{Common error message}}
```

## The Fix

**Standard Solution:**

```{{LANGUAGE}}
{{Code showing the correct approach}}
```

**Checklist:**
- [ ] {{Step 1}}
- [ ] {{Step 2}}

## Prevention

### Code Review Checklist

When reviewing code in this area, check:
- [ ] {{Item to verify}}
- [ ] {{Item to verify}}

### Automated Checks

{{Suggest linting rules, tests, or CI checks that could catch this}}

## Instance History

| Date | Solution Doc | Component |
|------|--------------|-----------|
| {{DATE}} | [{{title}}]({{path}}) | {{component}} |

## Related Patterns

- {{Link to related pattern}}
