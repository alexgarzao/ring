---
name: ring:executive-summary
description: |
  Executive communication and reporting skill for creating dashboards, status summaries,
  and board packages. Focuses on actionable insights for leadership.

trigger: |
  - Need executive status update
  - Board meeting preparation
  - Portfolio dashboard creation
  - Stakeholder escalation report

skip_when: |
  - Detailed project analysis → use project-health-check
  - Technical documentation → use ring-tw-team
  - Financial deep dive → use ring-finops-team

related:
  complementary: [portfolio-planning, project-health-check]
---

# Executive Reporting

Creating effective executive communications that drive decisions and action.

## Executive Communication Principles

### The Executive Pyramid

| Level | Content | Time |
|-------|---------|------|
| Summary | Key message in one sentence | 10 seconds |
| Overview | 3-5 key points | 1 minute |
| Detail | Supporting data and analysis | 5 minutes |
| Appendix | Full data for reference | As needed |

**What executives want:** Clear status (RAG), actionable insights, decisions required, trends and patterns, risks and mitigations.

**What executives don't want:** Ambiguous status, information dumps, problems without options, raw data, surprises.

## Report Types

### Type 1: Portfolio Status Dashboard

**Audience:** Executive team | **Frequency:** Weekly/Monthly | **Length:** 1-2 pages

```markdown
# Portfolio Status Dashboard — {Month YYYY}

## Portfolio Health (RAG)
| Project | Schedule | Cost | Scope | Overall | Key Issue |
|---------|----------|------|-------|---------|-----------|
| Project A | 🟢 | 🟡 | 🟢 | 🟡 | Cost +8% |
| Project B | 🔴 | 🟢 | 🟢 | 🔴 | 3 weeks behind |

## Portfolio Metrics
| Metric | Value | Trend |
|--------|-------|-------|
| SPI (avg) | 0.92 | ↓ |
| CPI (avg) | 0.97 | → |
| Team Utilization | 78% | ↑ |

## Exceptions Requiring Attention
1. [Project B: 3-week delay on critical path — recommend scope reduction]
2. [...]

## Upcoming Milestones (next 30 days)
| Project | Milestone | Date | Status |
|---------|-----------|------|--------|

## Decisions Needed
- [ ] Approve scope reduction for Project B
- [ ] Resource allocation for Project C Q3
```

### Type 2: Project Escalation Report

**Audience:** Sponsor/Executive | **Trigger:** Yellow/Red status | **Length:** 1 page

```markdown
# Escalation: {Project Name}

## Situation
{1-2 sentences: what happened and why it matters}

## Impact
- Schedule: {X weeks delay}
- Cost: {R$ X over budget or X% variance}
- Deliverable: {what will be late/missing}

## Options
| Option | Impact | Cost | Recommendation |
|--------|--------|------|---------------|
| A. Scope reduction | Save 2 weeks | No cost | Recommended |
| B. Add resources | Save 1 week | +R$ X | If A not acceptable |
| C. Accept delay | No cost | Stakeholder risk | Not recommended |

## Decision Needed By: {Date}
```

### Type 3: Board Package

**Audience:** Board of Directors | **Frequency:** Quarterly | **Length:** 5-10 pages

Sections:
1. Executive Summary (1 page)
2. Portfolio Health Dashboard (1 page)
3. Strategic Initiatives Status (2-3 pages)
4. Key Risks and Mitigations (1 page)
5. Decisions Required (1 page)
6. Appendix: Detailed metrics

## RAG Status Definitions

| Status | Criteria |
|--------|---------|
| 🟢 Green | On track; no significant issues; will meet commitments |
| 🟡 Yellow | Potential issue; manageable with action; may need support |
| 🔴 Red | Issue materialized; needs intervention; commitment at risk |

## Output

**File:** `docs/pmo/{date}/executive-summary.md`

Tone requirements:
- Lead with status, not with background
- Numbers over adjectives ("3 weeks behind" not "significantly delayed")
- Options not just problems
- Decisions needed are explicit and time-bound
