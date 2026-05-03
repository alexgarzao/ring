---
name: ring:using-pmo-team
description: |
  6 specialist PMO agents for portfolio management, resource planning, governance,
  risk analysis, executive reporting, and delivery reporting. Dispatch when you need portfolio-level oversight.

trigger: |
  - Need portfolio-level view across multiple projects
  - Resource capacity planning across teams
  - Project governance and gate reviews
  - Risk management at portfolio level
  - Executive reporting and dashboards

skip_when: |
  - Single feature planning → use ring-pm-team
  - Code implementation → use ring-dev-team
  - Code review → use ring-default reviewers
  - Technical writing → use ring-tw-team

related:
  similar: [ring:using-ring, ring:using-pm-team]
---

# Using Ring PMO Team

Dispatch specialist agents for portfolio-level work. See [ring:using-ring](https://raw.githubusercontent.com/LerianStudio/ring/main/default/skills/using-ring/SKILL.md) for ORCHESTRATOR principle.

## PMO vs PM

| Team | Focus | Scope |
|------|-------|-------|
| **ring-pmo-team** | Portfolio governance | Multi-project coordination, resources, reporting |
| **ring-pm-team** | Feature planning | PRD, TRD, task breakdown for ONE feature |

## The 6 PMO Specialists

| Agent | Specializations | Use When |
|-------|-----------------|----------|
| **portfolio-manager** | Multi-project coordination, strategic alignment, portfolio health, prioritization | Portfolio reviews, project prioritization, capacity assessment |
| **resource-planner** | Capacity planning, skills matrix, allocation, conflict resolution | Resource allocation, capacity planning, team assignments |
| **governance-specialist** | Gate reviews, compliance, process adherence, audit readiness | Gate approvals, process compliance, governance audits |
| **risk-analyst** | RAID logs, risk aggregation, mitigation planning, portfolio risk | Risk assessments, RAID management, mitigation strategies |
| **executive-reporter** | Portfolio status dashboards, project summaries, board packages | Portfolio/project status reports, board communications |
| **delivery-reporter** | Git analysis, squad delivery showcases, visual HTML presentations | Squad delivery reports, release summaries, client showcases |

## Dispatching

### Single Specialist
```
Task tool:
  subagent_type: "ring:portfolio-manager"
  prompt: "Need portfolio status for Q3 planning. Assess health across 12 projects, prioritize new intakes."
```

### Multiple Specialists (Parallel)
```
Task #1: ring:portfolio-manager — Portfolio health and prioritization
Task #2: ring:risk-analyst — Risk aggregation and mitigation
Task #3: ring:resource-planner — Capacity assessment
(All run in parallel)
```

## Example Workflows

**Quarterly Portfolio Review:**
1. Dispatch portfolio-manager → assess health across all projects
2. Dispatch resource-planner → validate capacity, identify constraints
3. Dispatch risk-analyst → aggregate portfolio risks
4. Combine results into executive summary

**New Project Intake:**
1. Dispatch portfolio-manager → assess impact on existing portfolio
2. Dispatch governance-specialist → check gate requirements
3. Dispatch resource-planner → confirm capacity available
4. Report: approved, conditional, or blocked with rationale

**Crisis Project Intervention:**
1. Dispatch risk-analyst → assess compound risk
2. Dispatch governance-specialist → recommend intervention gates
3. Report options to sponsor with trade-offs

## Key Principles

- **Always dispatch specialists.** You're the orchestrator, not the analyst. Specialists have frameworks you don't.
- **Evidence required.** PMO outputs must be data-driven, not opinions.
- **Gates are non-negotiable.** They prevent failures. Never skip them.
- **Blockers pause work.** When you hit a blocker (capacity exceeded, unclear strategy, missing data), STOP and report. Wait for decision.

## Report Types

| Need | Dispatch | Output |
|------|----------|--------|
| Portfolio status | portfolio-manager | `docs/pmo/{date}/portfolio-status.md` |
| Capacity plan | resource-planner | `docs/pmo/{date}/capacity-assessment.md` |
| Risk summary | risk-analyst | `docs/pmo/{date}/portfolio-risks.md` |
| Executive brief | executive-reporter | `docs/pmo/{date}/executive-summary.md` |
| Squad delivery | delivery-reporter | `docs/pmo/{date}/delivery-report.html` |

## When NOT to Use PMO Team

- Single feature planning → use ring:pm-team
- Code development → use ring:dev-team
- Just need a quick status check from one team → ask team lead directly, don't dispatch PMO
