---
name: ring:resource-allocation
description: |
  Resource capacity planning and allocation skill for managing people and skills
  across multiple projects. Identifies conflicts, gaps, and optimization opportunities.

trigger: |
  - Need to allocate resources to projects
  - Capacity planning for upcoming work
  - Resource conflict resolution
  - Skills gap analysis

skip_when: |
  - Single project staffing → use ring-pm-team
  - Cost analysis → use ring-finops-team
  - Project status → use project-health-check

related:
  complementary: [portfolio-planning, risk-management]
---

# Resource Allocation

Systematic resource planning across portfolio for optimal utilization.

## Prerequisites

| Prerequisite | Source |
|--------------|--------|
| Resource inventory | HR/Resource management |
| Project demands | Project managers |
| Skills matrix | HR/Training |
| Availability calendar | Team calendars |

## Resource Allocation Gates

### Gate 1: Resource Inventory

**Objective:** Establish baseline of available resources.

**Output:** `docs/pmo/{date}/resource-inventory.md`

```markdown
## Resource Inventory
| Resource | Role | Skills | Availability (FTE) | Current Allocation | Location |
|----------|------|--------|-------------------|-------------------|---------|
| [Name] | Backend Eng | Go, PostgreSQL | 1.0 | Project A (60%) | Remote |
```

Actions:
1. List all available resources
2. Document skills matrix per resource
3. Capture availability (FTE, dates, known constraints: PTO, training)
4. Note existing project allocations

### Gate 2: Demand Analysis

**Objective:** Understand resource demand across portfolio.

```markdown
## Resource Demand
| Project | Role Needed | Skills | Start | End | FTE Required |
|---------|-------------|--------|-------|-----|-------------|
| Project B | Backend Eng | Go, gRPC | 2026-04-01 | 2026-06-30 | 0.8 |
```

Actions:
1. Collect resource requests from all projects
2. Categorize by role and skill requirements
3. Map to timeline
4. Identify peak demand periods

### Gate 3: Gap Analysis

**Objective:** Identify conflicts and gaps.

```markdown
## Capacity vs Demand
| Role | Available FTE | Demanded FTE | Gap | Risk |
|------|--------------|--------------|-----|------|
| Backend Eng | 2.5 | 3.2 | -0.7 | 🔴 High |
| Frontend Eng | 1.5 | 1.2 | +0.3 | 🟢 OK |
```

**Conflict detection:** Same person over-allocated in overlapping periods.

| Resource | Project A | Project B | Total | Status |
|----------|-----------|-----------|-------|--------|
| Dev 1 | 60% (Apr-Jun) | 80% (May-Jul) | 140% May-Jun | ⚠️ Conflict |

### Gate 4: Allocation Optimization

For each conflict or gap, present options:

| Issue | Option A | Option B | Option C |
|-------|---------|---------|---------|
| Dev 1 over-allocated | Delay Project B start | Reduce Project A scope | Hire contractor |
| Backend Eng gap -0.7 FTE | Upskill Frontend Eng | Delay Project B | Hire new engineer |

User selects resolution per issue.

### Gate 5: Allocation Plan

**Output:** `docs/pmo/{date}/resource-allocation-plan.md`

```markdown
# Resource Allocation Plan — Q2 2026

## Allocation Matrix
| Resource | Apr | May | Jun | Jul |
|----------|-----|-----|-----|-----|
| Dev 1 | A(60%)+B(40%) | A(100%) | B(80%) | B(80%) |

## Unresolved Conflicts
[List any conflicts pending resolution with options presented]

## Recommendations
[Actions for leadership on hiring, training, or scope adjustments]

## Review Date
{Next review date — monthly recommended}
```

### Gate 6: Utilization Monitoring

Track actual vs planned utilization weekly:

| Resource | Planned % | Actual % | Variance | Action Needed |
|----------|-----------|---------|---------|--------------|
| Dev 1 | 80% | 95% | +15% | 🟡 Monitor |

Target utilization: 70-85% (below = underutilized, above = burnout risk)
