---
name: ring:pmo-retrospective
description: |
  Portfolio retrospective skill for capturing lessons learned, process improvements,
  and organizational learning across completed projects.

trigger: |
  - Project closure requiring retrospective
  - Portfolio period review (quarterly/annual)
  - Process improvement initiative
  - Pattern of issues recurring

skip_when: |
  - Sprint retrospective → team-level, not PMO
  - Technical post-mortem → use ring-dev-team
  - Single incident analysis → handle in project scope

related:
  complementary: [portfolio-planning, project-health-check]
---

# PMO Retrospective

Systematic capture and application of lessons learned at portfolio level.

## Retrospective Types

| Type | Trigger | Scope | Participants |
|------|---------|-------|-------------|
| Project Closure | Project completion/termination | Single project | Project team, sponsor, key stakeholders |
| Portfolio Period Review | Quarterly or annual | All projects in period | PMO, PMs, executives |
| Thematic | Recurring pattern observed | Projects sharing the pattern | Affected PMs, PMO, SMEs |

## Retrospective Gates

### Gate 1: Context Setting

Define scope, participants, and gather data.

| Output | Content |
|--------|---------|
| Scope statement | Type, projects included, timeframe |
| Participant list | Names and roles |
| Data package | Health reports, metrics, timeline, cost actuals |
| Scheduled sessions | Dates, format (in-person/remote) |

### Gate 2: Data Gathering (Pre-Session)

Collect inputs before the retrospective session:
- Survey participants: "What went well? What didn't? What should we change?"
- Extract quantitative metrics: SPI, CPI, schedule variance, defect rates
- Review project artifacts: health check reports, change log, risk register
- Compile timeline of key events

### Gate 3: Analysis Session

Facilitate structured discussion:

**Retrospective Canvas:**
```
| Went Well ✅ | Challenges ❌ | Root Causes 🔍 | Improvements 💡 |
|-------------|--------------|----------------|----------------|
| [items]     | [items]      | [causes]       | [actions]      |
```

**Root Cause Analysis (for challenges):**
- 5 Whys technique for recurring issues
- Pattern identification across multiple projects
- Distinguish symptoms from root causes

### Gate 4: Action Planning

For each improvement identified:

| Action | Owner | Due Date | Success Metric | Priority |
|--------|-------|----------|---------------|----------|
| [Action] | [Name] | [Date] | [Measurable outcome] | High/Med/Low |

Only commit to actions with clear owners and deadlines.

### Gate 5: Knowledge Capture

Document findings in the PMO knowledge base:

**File:** `docs/pmo/retrospectives/{YYYY-MM}-{type}-retrospective.md`

```markdown
# PMO Retrospective: {Type} — {Period/Project}
**Date:** {YYYY-MM-DD}
**Type:** Project Closure | Portfolio Period | Thematic
**Scope:** {Projects/Period}

## Summary
{2-3 sentences on key findings}

## What Went Well
- [item with evidence]

## Key Challenges
- [challenge + root cause]

## Lessons Learned
| Lesson | Context | Recommended Change |
|--------|---------|-------------------|
| [Lesson] | [When this applies] | [Process/template/checklist change] |

## Action Items
| Action | Owner | Due | Status |
|--------|-------|-----|--------|

## Patterns Identified (if recurring)
[Cross-project patterns that indicate systemic issues]
```

### Gate 6: Organizational Learning

Apply lessons to PMO standards:
- Update process templates affected by lessons
- Update onboarding materials with new knowledge
- Schedule follow-up to verify action item completion
- Feed patterns into risk register for future projects

## Output

**Primary output:** `docs/pmo/retrospectives/{date}-retrospective.md`
**Secondary output:** Updated process templates, risk register entries, checklist improvements
