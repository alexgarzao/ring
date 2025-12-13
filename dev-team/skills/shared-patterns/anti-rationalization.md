# Anti-Rationalization Patterns

Canonical source for anti-rationalization patterns used by all dev-team agents and skills.

AI models naturally attempt to be "helpful" by making autonomous decisions. This is DANGEROUS in structured workflows. These tables use aggressive language intentionally to override the AI's instinct to be accommodating.

## Universal Anti-Rationalizations

These rationalizations are ALWAYS wrong, regardless of context:

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "This is prototype/throwaway code" | Prototypes become production 60% of time. Standards apply to ALL code. | **Apply full standards. No prototype exemption.** |
| "Too exhausted to do this properly" | Exhaustion doesn't waive requirements. It increases error risk. | **STOP work. Resume when able to comply fully.** |
| "Time pressure + authority says skip" | Combined pressures don't multiply exceptions. Zero exceptions × any pressure = zero exceptions. | **Follow all requirements regardless of pressure combination.** |
| "Similar task worked without this step" | Past non-compliance doesn't justify future non-compliance. | **Follow complete process every time.** |
| "User explicitly authorized skip" | User authorization doesn't override HARD GATES. | **Cannot comply. Explain non-negotiable requirement.** |

---

## Agent-Specific Anti-Rationalizations

### Standards Compliance Mode Detection

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Prompt didn't have exact marker" | Multiple patterns trigger mode. Check all. | **Check ALL detection patterns** |
| "User seems to want direct implementation" | Seeming ≠ knowing. If ANY pattern matches, include. | **Include if uncertain** |
| "Standards section too long for this task" | Length doesn't determine requirement. Pattern match does. | **Include full section if triggered** |

### Standards Section Comparison

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I'll check the main sections only" | ALL sections must be checked. You don't decide relevance. | **Check EVERY section from WebFetch result** |
| "This section doesn't apply" | Report it as N/A with reason, don't skip silently. | **Report ALL sections with status** |
| "Codebase doesn't have this pattern" | That's a finding! Report as Non-Compliant or N/A. | **Report missing patterns** |

### WebFetch Standards Quoting

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Brief description is enough" | Developers need exact code to understand the fix. | **Quote from WebFetch result** |
| "Standards are in my knowledge" | You must use the FETCHED standards, not assumptions. | **Quote from WebFetch result** |
| "WebFetch result was too large" | Extract the specific pattern for this finding. | **Quote only relevant section** |

---

## Skill-Specific Anti-Rationalizations

### Gate Execution

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Previous gate passed, this one will too" | Each gate is independent. No assumptions. | **Execute full gate requirements** |
| "Small change, skip full process" | Size doesn't determine requirements. | **Follow complete process** |
| "Already tested manually" | Manual testing ≠ gate compliance. | **Execute automated verification** |

---

## How to Reference This File

**For Agents:**
```markdown
## Anti-Rationalization

See [shared-patterns/anti-rationalization.md](../skills/shared-patterns/anti-rationalization.md) for universal and agent-specific anti-rationalizations.

### Domain-Specific Anti-Rationalizations

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| [Domain-specific rationalization] | [Domain-specific reason] | **[Domain-specific action]** |
```

**For Skills:**
```markdown
## Anti-Rationalization Table

See [shared-patterns/anti-rationalization.md](../shared-patterns/anti-rationalization.md) for universal anti-rationalizations.

### Gate-Specific Anti-Rationalizations

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| [Gate-specific rationalization] | [Gate-specific reason] | **[Gate-specific action]** |
```
