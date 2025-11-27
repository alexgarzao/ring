---
date: {{DATE}}  # Format: YYYY-MM-DD (e.g., 2025-01-27)
problem_type: {{PROBLEM_TYPE}}
component: {{COMPONENT}}
symptoms:
  - "{{SYMPTOM_1}}"
  # - "{{SYMPTOM_2}}"  # Add if applicable
  # - "{{SYMPTOM_3}}"  # Add if applicable
  # - "{{SYMPTOM_4}}"  # Add if applicable
  # - "{{SYMPTOM_5}}"  # Add if applicable (max 5 per schema)
root_cause: {{ROOT_CAUSE}}
resolution_type: {{RESOLUTION_TYPE}}
severity: {{SEVERITY}}
# Optional fields (remove if not applicable)
project: {{PROJECT|unknown}}
language: {{LANGUAGE|unknown}}
framework: {{FRAMEWORK|none}}
tags:
  - {{TAG_1|untagged}}
  # - {{TAG_2}}  # Add relevant tags for searchability
  # - {{TAG_3}}  # Maximum 8 tags per schema
related_issues: []
---

# {{TITLE}}

## Problem

{{Brief description of the problem - what was happening, what was expected}}

### Symptoms

{{List the observable symptoms - error messages, visual issues, unexpected behavior}}

```
{{Exact error message or log output if applicable}}
```

### Context

- **Component:** {{COMPONENT}}
- **Affected files:** {{List key files involved}}
- **When it occurred:** {{Under what conditions - deployment, specific input, load, etc.}}

## Investigation

### What didn't work

1. {{First thing tried and why it didn't solve it}}
2. {{Second thing tried and why it didn't solve it}}

### Root Cause

{{Technical explanation of the actual cause - be specific}}

## Solution

### The Fix

{{Describe what was changed and why}}

```{{LANGUAGE}}
// Before
{{Code that had the problem}}

// After
{{Code with the fix}}
```

### Files Changed

| File | Change |
|------|--------|
| {{file_path}} | {{Brief description of change}} |

## Prevention

### How to avoid this in the future

1. {{Preventive measure 1}}
2. {{Preventive measure 2}}

### Warning signs to watch for

- {{Early indicator that this problem might be occurring}}

## Related

- {{Link to related solution docs or external resources}}
