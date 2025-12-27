# Session: <session-name>
Updated: <YYYY-MM-DDTHH:MM:SSZ>

## Goal
<What does "done" look like? Include measurable success criteria.>

## Constraints
<Technical requirements, patterns to follow, things to avoid>
- Constraint 1: ...
- Constraint 2: ...

## Key Decisions
<Choices made with brief rationale>
- Decision 1: Chose X over Y because...
- Decision 2: ...

## State
- Done:
  - [x] Phase 1: <completed phase description>
- Now: [->] Phase 2: <current focus - ONE thing only>
- Next:
  - [ ] Phase 3: <queued item>
  - [ ] Phase 4: <queued item>

## Open Questions
- UNCONFIRMED: <things needing verification after clear>
- UNCONFIRMED: <assumptions that should be validated>

## Working Set
- Branch: `<branch-name>`
- Key files: `<primary file or directory>`
- Test cmd: `<command to run tests>`
- Build cmd: `<command to build>`

---

## Ledger Usage Notes

**Checkbox States:**
- `[x]` = Completed
- `[->]` = In progress (current)
- `[ ]` = Pending

**When to Update:**
- After completing a phase (change `[->]` to `[x]`, move `[->]` to next)
- Before running `/clear`
- When context usage > 70%

**After Clear:**
1. Ledger loads automatically
2. Find `[->]` for current phase
3. Verify UNCONFIRMED items
4. Continue work

**To create a new ledger:**
```bash
cp .ring/templates/CONTINUITY-template.md .ring/ledgers/CONTINUITY-<session-name>.md
```
