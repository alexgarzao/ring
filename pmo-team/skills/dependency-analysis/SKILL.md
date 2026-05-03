---
name: ring:dependency-analysis
description: |
  Cross-project dependency mapping and analysis skill for identifying, tracking,
  and managing dependencies across portfolio projects.

trigger: |
  - Need to map project dependencies
  - Dependency conflict identified
  - Planning new project with dependencies
  - Critical path analysis needed

skip_when: |
  - Single project internal dependencies → handle in project scope
  - Resource dependencies only → use resource-allocation
  - Risk from dependencies → use risk-management

related:
  complementary: [portfolio-planning, risk-management]
---

# Dependency Mapping

Systematic identification and management of cross-project dependencies.

## Dependency Types

### Internal (between tasks/projects)

| Type | Definition | Example |
|------|------------|---------|
| Finish-to-Start (FS) | B starts when A finishes | Development → Testing |
| Start-to-Start (SS) | B starts when A starts | Parallel workstreams |
| Finish-to-Finish (FF) | B finishes when A finishes | Code freeze → Doc freeze |

### External

| Type | Risk Level |
|------|------------|
| Vendor delivery | Medium-High |
| Regulatory approval | High |
| Infrastructure availability | Medium |
| API/integration readiness | Medium-High |
| Shared resource availability | Medium |

## Dependency Mapping Gates

### Gate 1: Dependency Identification

**Objective:** Identify all cross-portfolio dependencies.

Actions:
1. Review project schedules for cross-project links
2. Interview project managers for undocumented dependencies
3. Map integration points between projects
4. Identify external vendor/regulatory dependencies

**Output:** `docs/pmo/{date}/dependency-register.md`

```markdown
## Dependency Register
| ID | From | To | Type | Description | Risk Level | Owner |
|----|------|----|------|-------------|------------|-------|
| DEP-001 | Project A: API v2 | Project B: Integration | FS | B needs A's API before integration testing | High | {Owner} |
```

### Gate 2: Impact Analysis

For each dependency, assess:

| Dependency | If Delayed | Impact on Portfolio | Mitigation Available |
|------------|-----------|--------------------|--------------------|
| DEP-001 | Project B delayed 3 weeks | Blocks Q3 delivery | Mock API available? |

**Critical path dependencies:** Those where delay propagates to project end date with zero slack.

### Gate 3: Dependency Matrix

Build cross-project dependency matrix:

```
         | Project A | Project B | Project C | Vendor X |
---------|-----------|-----------|-----------|----------|
Project A | —         | Provides  | Provides  | Receives |
Project B | Receives  | —         | —         | —        |
Project C | Receives  | —         | —         | —        |
```

Highlight: Critical (🔴), At-Risk (🟡), Healthy (🟢)

### Gate 4: Resolution Planning

For each HIGH or CRITICAL dependency:

| Dependency | Resolution Option | Owner | Target Date | Contingency |
|------------|------------------|-------|-------------|-------------|
| DEP-001 | Accelerate Project A API | PM-A | 2026-04-01 | Mock API for testing |

### Gate 5: Tracking Setup

Create monitoring cadence:
- Weekly: review status of HIGH/CRITICAL dependencies
- Bi-weekly: full dependency register review
- Trigger: immediate review if any dependency status changes

**Output:** `docs/pmo/{date}/dependency-matrix.md` + tracking schedule

## Early Warning Indicators

| Signal | Action |
|--------|--------|
| Dependency owner not responding | Escalate to sponsor |
| Dependency delayed >1 week | Update critical path, notify impacted PMs |
| New dependency discovered late | Emergency planning session |
| External vendor behind schedule | Activate contingency |
