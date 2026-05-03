---
name: ring:portfolio-planning
description: |
  Strategic portfolio planning for multi-project coordination, capacity assessment,
  and portfolio optimization.

trigger: |
  - Assess portfolio health and composition
  - Plan quarterly/annual portfolio
  - Evaluate new project against existing portfolio
  - Rebalance priorities and resources

skip_when: |
  - Single feature planning → use ring:pre-dev-feature
  - Status reports only → use ring:executive-summary
  - Resource planning alone → use ring:resource-allocation

related:
  similar: [ring:pre-dev-feature]
  complementary: [resource-allocation, risk-management]
---

# Portfolio Planning

Systematic portfolio assessment and optimization across multiple projects.

## Purpose

Assess portfolio health, evaluate strategic alignment, optimize resource allocation, and balance risk across all active projects.

## The 5 Gates

### Gate 1: Portfolio Inventory
List all active projects, current status (Green/Yellow/Red), resource allocations, and dependencies.
**Output:** `docs/pmo/{date}/portfolio-inventory.md`

### Gate 2: Strategic Alignment
Map projects to strategic objectives and score alignment 1-5 (5=directly enables, 1=no clear value).
**Output:** `docs/pmo/{date}/strategic-alignment.md`

### Gate 3: Capacity Assessment
Aggregate resource demand across projects, identify over/under allocation, and document skill gaps.
**Dispatch:** `ring:resource-planner` for detailed analysis.
**Output:** `docs/pmo/{date}/capacity-assessment.md`

### Gate 4: Risk Portfolio View
Aggregate project risks, identify correlations, and assess portfolio-level exposure.
**Dispatch:** `ring:risk-analyst` for detailed analysis.
**Output:** `docs/pmo/{date}/portfolio-risks.md`

### Gate 5: Portfolio Optimization
Recommend prioritization, resource reallocation, and portfolio composition changes based on strategic value, resource efficiency, risk balance, dependencies, and timeline.
**Output:** `docs/pmo/{date}/portfolio-recommendations.md`

## Blockers — STOP and Report

Pause immediately if:
- Portfolio capacity exceeded by >20%
- Strategic objectives unclear
- Resource data unavailable
- Multiple high-risk projects correlated

Report blocker with context. Do NOT proceed with incomplete data.

## Output Format

```markdown
# Portfolio Status Summary - [Date]

## Overview
| Metric | Value | Status |
|--------|-------|--------|
| Active Projects | N | - |
| Capacity Utilization | X% | Green/Yellow/Red |
| Portfolio Risk | X/10 | Green/Yellow/Red |

## Strategic Alignment
| Objective | Projects | Coverage |
|-----------|----------|----------|
| Obj 1 | [list] | X% |

## Health
| Status | Count | Projects |
|--------|-------|----------|
| Green | N | [list] |
| Yellow | N | [list] |
| Red | N | [list] |

## Recommendations
1. [Recommendation with rationale]
2. [Recommendation with rationale]

## Decisions Needed
1. [Decision with options]
```

## Example Workflow

**Scenario:** Quarterly portfolio planning with 8 active projects, 2 new intake requests, resource constraints.

1. **Gate 1:** Inventory all 10 projects (8 current + 2 proposed), capture status and allocations
2. **Gate 2:** Score alignment against Q3 objectives (growth, stability, risk reduction)
3. **Gate 3:** Dispatch resource-planner to assess capacity across teams
4. **Gate 4:** Aggregate risks from RAID logs, identify correlated failures
5. **Gate 5:** Recommend prioritization: accept 1 new project, defer 1, rebalance existing

**Output:** Portfolio-recommendations.md with prioritized project list and resource reallocation plan.
