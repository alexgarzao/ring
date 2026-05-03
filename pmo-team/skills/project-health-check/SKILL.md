---
name: ring:project-health-check
description: |
  Individual project health assessment skill for evaluating project status across
  multiple dimensions. Provides early warning of troubled projects.

trigger: |
  - Need to assess single project health
  - Project showing warning signs
  - Milestone review required
  - Stakeholder escalation received

skip_when: |
  - Portfolio-level view → use portfolio-planning
  - Resource-only issue → use resource-allocation
  - Risk-only analysis → use risk-management

related:
  complementary: [portfolio-planning, risk-management]
---

# Project Health Check

Systematic assessment of individual project health across multiple dimensions.

## Prerequisites

| Prerequisite | Source |
|--------------|--------|
| Project baseline (plan) | Project manager |
| Current status data | Project manager |
| Stakeholder feedback | Stakeholders |
| Risk register | Risk analyst |

## Health Dimensions

### Dimension 1: Schedule Health

| Metric | Formula | 🟢 Green | 🟡 Yellow | 🔴 Red |
|--------|---------|---------|---------|-------|
| SPI | EV / PV | ≥0.95 | 0.85-0.94 | <0.85 |
| Schedule Variance | EV - PV | ≥0 | -5% to 0 | <-5% |
| Milestone Status | On-time % | ≥90% | 70-89% | <70% |

Questions: Is project on schedule? Are milestones met? What's on the critical path?

### Dimension 2: Cost Health

| Metric | Formula | 🟢 Green | 🟡 Yellow | 🔴 Red |
|--------|---------|---------|---------|-------|
| CPI | EV / AC | ≥0.95 | 0.85-0.94 | <0.85 |
| Cost Variance | EV - AC | ≥0 | -5% to 0 | <-5% |
| EAC vs Budget | EAC / BAC | ≤1.05 | 1.05-1.15 | >1.15 |

Questions: Within budget? What's driving overruns? What's forecast at completion?

### Dimension 3: Scope Health

| Indicator | 🟢 Green | 🟡 Yellow | 🔴 Red |
|-----------|---------|---------|-------|
| Change requests | <5% scope growth | 5-10% growth | >10% growth |
| Scope creep | Managed formally | Some informal | Uncontrolled |
| Requirements stability | Stable | Minor changes | Major changes |

### Dimension 4: Quality Health

| Indicator | 🟢 Green | 🟡 Yellow | 🔴 Red |
|-----------|---------|---------|-------|
| Defect density | Low | Medium | High |
| Test coverage | ≥85% | 70-84% | <70% |
| Technical debt | Managed | Growing | Critical |

### Dimension 5: Team Health

| Indicator | 🟢 Green | 🟡 Yellow | 🔴 Red |
|-----------|---------|---------|-------|
| Velocity trend | Stable/improving | Slight decline | Declining |
| Blockers | Few, short-lived | Some, being resolved | Many or chronic |
| Team morale | High | Medium | Low |

### Dimension 6: Stakeholder Health

| Indicator | 🟢 Green | 🟡 Yellow | 🔴 Red |
|-----------|---------|---------|-------|
| Satisfaction | High | Medium | Low/Escalating |
| Communication | Regular + effective | Gaps | Breakdown |
| Decision speed | Fast | Moderate | Blocked |

## Overall Health Score

| Score | Status | Action |
|-------|--------|--------|
| All 🟢 | Healthy | Continue, monitor normally |
| 1-2 🟡 | Watch | Increase monitoring, prepare contingency |
| 3+ 🟡 or 1 🔴 | At Risk | Escalate to sponsor, action plan required |
| 2+ 🔴 | Critical | Immediate intervention, recovery plan |

## Health Check Report

**File:** `docs/pmo/{date}/health-check-{project}.md`

```markdown
# Project Health Check: {Project Name}
**Date:** {YYYY-MM-DD}
**Assessor:** {Name}
**Overall Status:** 🟢 Healthy | 🟡 At Risk | 🔴 Critical

## Dimension Summary
| Dimension | Status | Key Indicator |
|-----------|--------|---------------|
| Schedule | 🟢/🟡/🔴 | SPI: {value} |
| Cost | 🟢/🟡/🔴 | CPI: {value} |
| Scope | 🟢/🟡/🔴 | Change requests: {N} |
| Quality | 🟢/🟡/🔴 | Test coverage: {%} |
| Team | 🟢/🟡/🔴 | Velocity: {trend} |
| Stakeholder | 🟢/🟡/🔴 | Satisfaction: {level} |

## Key Findings
[Top 3-5 findings requiring attention]

## Recommended Actions
[Specific actions with owners and due dates]

## Next Review
{Date}
```
