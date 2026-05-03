---
name: ring:brainstorm
description: |
  Socratic design refinement - transforms rough ideas into validated designs through
  structured questioning, alternative exploration, and incremental validation.

trigger: |
  - New feature or product idea (requirements unclear)
  - User says "plan", "design", or "architect" something
  - Multiple approaches seem possible
  - Design hasn't been validated by user

skip_when: |
  - Design already complete and validated → use ring:write-plan
  - Have detailed plan ready to execute → use ring:execute-plan
  - Just need task breakdown from existing design → use ring:write-plan

sequence:
  before: [ring:write-plan, ring:worktree]
---

# Brainstorming Ideas Into Designs

Transform rough ideas into fully-formed designs through structured questioning and alternative exploration.

**Core principle:** Research first, ask targeted questions to fill gaps, explore alternatives, validate incrementally.

**Announce at start:** "Using ring:brainstorm skill to refine your idea into a design."

## Phases

### Prep: Autonomous Recon (MANDATORY first)

**Run ALL of these and paste evidence:**
```bash
ls -la && git log --oneline -10 && (cat README.md 2>/dev/null || echo "No README") | head -50
find . -name "*test*" | wc -l
cat package.json 2>/dev/null || cat go.mod 2>/dev/null || cat requirements.txt 2>/dev/null
```

Only after pasting all evidence: form your model and share findings.

### Question Budget: max 3 per phase

Hit the limit → do research instead of asking.

### Phase 1: Understanding

Share synthesized understanding first, invite corrections. Ask only for genuine gaps you cannot close yourself.

<example>
"Based on the README and yesterday's commit, we're expanding localization to dashboard and billing emails; admin console is still untouched. Only gap I see is whether support responses need localization in this iteration. Did I miss anything?"
</example>

### Phase Lock Rules

Once in a phase, CANNOT skip ahead. Asked a question → WAIT for answer before solutions. Proposed approaches → WAIT for selection before design.

### Phase 2: Exploration

Propose 2-3 approaches. For each: core architecture, trade-offs, complexity, recommendation. Lead with your preference and explain why.

Use AskUserQuestion when you need a genuine judgment call. State your recommended option inside the question.

### Phase 3: Design Presentation

Present in ~200-300 word sections. Cover: architecture, components, data flow, error handling, testing. Check in at natural breakpoints.

**Design approval gate:** NOT approved until user explicitly says "approved", "looks good", "proceed", "let's implement that", or "yes" (in response to "shall I proceed?"). Silence, "interesting", or questions = keep refining.

### Phase 4: Design Documentation

Write to `docs/plans/YYYY-MM-DD-<topic>-design.md`. Commit before proceeding.

### Phase 5: Worktree Setup

When implementation follows design approval:
- Announce: "Using ring:worktree skill to set up isolated workspace."
- Use ring:worktree skill

### Phase 6: Planning Handoff

Ask: "Ready to create the implementation plan?" On confirmation:
- Announce: "Using ring:write-plan skill to create the implementation plan."
- Use ring:write-plan skill

## AskUserQuestion vs Open-Ended

| Use AskUserQuestion | Use Open-Ended |
|---------------------|----------------|
| Judgment call between real alternatives | Design validation ("Does this look right so far?") |
| You have a recommendation to state | When partner should describe requirements |
| Prioritization ambiguous, can't infer | When structured options would limit creative input |

**If you know the answer from repo/docs → state it as fact and proceed. No question needed.**

## When to Revisit Earlier Phases

New constraint revealed → Phase 1. Partner questions approach → Phase 2. Requirements unclear → Phase 1.

**Avoid forcing forward linearly when going backward gives better results.**
