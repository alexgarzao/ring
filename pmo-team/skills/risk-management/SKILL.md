---
name: ring:risk-management
description: |
  Portfolio-level risk management skill for identifying, assessing, and mitigating
  risks across multiple projects. Maintains RAID logs and tracks risk responses.

trigger: |
  - Need portfolio risk assessment
  - Creating or updating RAID log
  - Risk response planning
  - Risk correlation analysis

skip_when: |
  - Single project risk → handle in project scope
  - Financial risk only → use ring-finops-team
  - Technical risk in code → use ring:qa-analyst

related:
  complementary: [portfolio-planning, project-health-check]
---

# Risk Management

Systematic portfolio-level risk identification, assessment, and mitigation.

## Prerequisites

| Prerequisite | Source |
|--------------|--------|
| Project risk registers | Project managers |
| Historical risk data | Previous projects |
| Stakeholder input | Key stakeholders |
| Impact criteria | PMO standards |

## Risk Categories

| Category | Examples |
|----------|---------|
| Strategic | Market changes, competition, regulation |
| Resource | Key person departure, skill shortage, capacity |
| Technical | Technology obsolescence, integration, security |
| Financial | Budget cuts, cost overruns, currency |
| Schedule | Dependencies, delays, scope creep |
| External | Vendor, regulatory, geopolitical |

## Risk Management Gates

### Gate 1: Risk Identification

**Objective:** Identify all portfolio-level risks.

Actions:
1. Collect project-level risks from PMs
2. Identify cross-project risks (risks affecting multiple projects)
3. Identify portfolio-level risks (strategy, governance, capacity)
4. Document assumptions and their risks

**Output:** `docs/pmo/{date}/risk-register.md`

### Gate 2: Risk Assessment

**Objective:** Score probability and impact.

| Score | Probability | Impact |
|-------|-------------|--------|
| 1 | Rare (<10%) | Negligible |
| 2 | Unlikely (10-30%) | Minor |
| 3 | Possible (30-50%) | Moderate |
| 4 | Likely (50-70%) | Major |
| 5 | Almost certain (>70%) | Critical |

**Risk Score = Probability × Impact**

| Score | Category | Action |
|-------|----------|--------|
| 15-25 | Critical | Immediate action, sponsor escalation |
| 8-14 | High | Mitigation plan, weekly tracking |
| 4-7 | Medium | Monitor, contingency plan |
| 1-3 | Low | Accept, periodic review |

### Gate 3: Risk Response Planning

For each Medium+ risk, define response:

| Strategy | When to Use | Example |
|----------|-------------|---------|
| Avoid | Eliminate the cause | Change project approach |
| Transfer | Share with third party | Insurance, contract terms |
| Mitigate | Reduce probability/impact | Add buffer, prototype |
| Accept | Acknowledge, monitor | Low-impact risks |

### Gate 4: Risk Correlation Analysis

Identify risks that affect multiple projects or amplify each other:

| Risk Cluster | Projects Affected | Combined Impact | Priority |
|-------------|------------------|-----------------|---------|
| Key-person dependency | A, B, C | Schedule slip across all | Critical |
| Vendor X delays | A, D | Integration delays in 2 projects | High |

### Gate 5: RAID Log

Maintain combined RAID (Risks, Assumptions, Issues, Dependencies) log:

**File:** `docs/pmo/{date}/raid-log.md`

```markdown
# RAID Log — {Portfolio} — {Date}

## Risks
| ID | Description | Category | Score | Owner | Response | Status |
|----|-------------|----------|-------|-------|----------|--------|
| R-001 | Key engineer leaving | Resource | 12 | HR | Succession plan | Active |

## Assumptions
| ID | Assumption | If Wrong | Owner | Validation Date |
|----|-----------|----------|-------|----------------|

## Issues
| ID | Description | Impact | Owner | Resolution | Target Date |
|----|-------------|--------|-------|------------|-------------|

## Dependencies
[Cross-reference with dependency-analysis output]
```

### Gate 6: Risk Tracking

- Critical/High risks: reviewed weekly
- Medium risks: reviewed bi-weekly
- Low risks: reviewed monthly
- Trigger: immediate review on any risk materialization

## Risk Escalation Criteria

| Condition | Action |
|-----------|--------|
| Risk score increases to Critical | Immediate sponsor escalation |
| Risk materializes (becomes issue) | Move to Issues, activate contingency |
| Mitigation not working | Escalate + revise response |
| New portfolio-wide risk identified | Emergency PMO session |
