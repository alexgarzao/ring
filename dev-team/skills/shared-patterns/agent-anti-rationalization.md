# Agent Anti-Rationalization Patterns

This file contains shared anti-rationalization entries that apply across all dev-team agents. Individual agents should reference this file and add agent-specific anti-rationalizations.

## Standards Compliance Mode Detection

These rationalizations apply when determining if Standards Compliance Mode should be triggered:

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Prompt didn't have exact marker" | Multiple patterns trigger mode. Check all. | **Check ALL detection patterns** |
| "User seems to want direct implementation" | Seeming ≠ knowing. If ANY pattern matches, include. | **Include if uncertain** |
| "Standards section too long for this task" | Length doesn't determine requirement. Pattern match does. | **Include full section if triggered** |

## Standards Section Comparison

These rationalizations apply when comparing codebase against standards:

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I'll check the main sections only" | ALL sections must be checked. You don't decide relevance. | **Check EVERY section from WebFetch result** |
| "This section doesn't apply" | Report it as N/A with reason, don't skip silently. | **Report ALL sections with status** |
| "Codebase doesn't have this pattern" | That's a finding! Report as Non-Compliant or N/A. | **Report missing patterns** |

## WebFetch Standards Quoting

These rationalizations apply when quoting from fetched standards:

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Brief description is enough" | Developers need exact code to understand the fix. | **Quote from WebFetch result** |
| "Standards are in my knowledge" | You must use the FETCHED standards, not assumptions. | **Quote from WebFetch result** |
| "WebFetch result was too large" | Extract the specific pattern for this finding. | **Quote only relevant section** |

## How to Use This File

Agents should reference this file:

```markdown
## Anti-Rationalization

See [shared-patterns/agent-anti-rationalization.md](../skills/shared-patterns/agent-anti-rationalization.md) for universal agent anti-rationalizations.

### Agent-Specific Anti-Rationalizations

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| [Agent-specific rationalization] | [Agent-specific reason] | **[Agent-specific action]** |
```
