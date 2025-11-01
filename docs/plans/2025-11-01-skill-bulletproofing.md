# Skill Bulletproofing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use ring:executing-plans to implement this plan task-by-task.

**Goal:** Strengthen ring skills to be bulletproof against rationalization and ensure consistent execution

**Architecture:** Add state tracking, failure recovery, concrete exit criteria, and mandatory TodoWrite integration across all skills. Each skill gets specific counter-rationalizations and enforcement mechanisms.

**Tech Stack:** Markdown documentation, YAML frontmatter, ring skills system

---

## Task 1: Improve using-ring skill

**Files:**
- Modify: `skills/using-ring/SKILL.md`

**Step 1: Write the failing test**

Create test scenario in temporary file `test-using-ring-improvements.md`:
```markdown
Test: Agent should check for skills before ANY tool use
Scenario: Agent asked to "find all test files in the project"
Expected: Agent checks for skills before using Grep/Find
Actual: [Run without updated skill to document baseline]
```

**Step 2: Run test to verify current behavior**

Run: Dispatch test agent with current skill and document behavior
Expected: Agent uses Grep/Find without checking for skills first

**Step 3: Add counter-rationalization for context gathering**

Add after line 46 in SKILL.md:
```markdown
- "Let me gather information first" → WRONG. Skills tell you HOW to gather information. Check for skills.
- "I need context before checking skills" → WRONG. Gathering context IS a task. Check for skills first.
- "Just a quick look at files" → WRONG. Looking at files requires skills check first.
```

**Step 4: Add mandatory skill check points**

Add new section after line 51:
```markdown
## Mandatory Skill Check Points

**Before EVERY tool use**, ask yourself:
- About to use Read? → Is there a skill for reading this type of file?
- About to use Bash? → Is there a skill for this command type?
- About to use Grep? → Is there a skill for searching?
- About to use Task? → Which subagent_type matches?

**No tool use without skill check first.**
```

**Step 5: Add skill activation tracking requirement**

Add after line 61:
```markdown
## TodoWrite Requirement

When starting ANY task:
1. First todo: "Check for relevant skills"
2. Mark complete only after actual check
3. Document which skills apply/don't apply

Skipping this todo = automatic failure.
```

**Step 6: Add penalty clause**

Add after Common Rationalizations section:
```markdown
## The Cost of Skipping Skills

Every time you skip checking for skills:
- You fail your task (skills contain critical patterns)
- You waste time (rediscovering solved problems)
- You make known errors (skills prevent common mistakes)
- You lose trust (not following mandatory workflows)

**This is not optional. Check for skills or fail.**
```

**Step 7: Run test to verify improvements work**

Run: Test agent with updated skill
Expected: Agent checks for skills before tool use

**Step 8: Commit**

```bash
git add skills/using-ring/SKILL.md test-using-ring-improvements.md
git commit -m "feat: strengthen using-ring with mandatory check points and TodoWrite requirement"
```

---

## Task 2: Improve test-driven-development skill

**Files:**
- Modify: `skills/test-driven-development/SKILL.md`

**Step 1: Write the failing test**

Create `test-tdd-improvements.md`:
```markdown
Test: Agent must paste actual failure output
Scenario: Agent implementing new feature
Expected: Agent includes exact test failure output in response
Actual: [Document baseline behavior]
```

**Step 2: Run test to verify current behavior**

Run: Test with current skill
Expected: Agent says "test would fail" without running

**Step 3: Add failure verification table**

Insert after line 114:
```markdown
### Required Failure Patterns

| Test Type | Must See This Failure | Wrong Failure = Wrong Test |
|-----------|----------------------|---------------------------|
| New feature | `NameError: function not defined` or `AttributeError` | Test passing = testing existing behavior |
| Bug fix | Actual wrong output/behavior | Test passing = not testing the bug |
| Refactor | Tests pass before and after | Tests fail after = broke something |

**No failure output = didn't run = violation**
```

**Step 4: Add screenshot requirement**

Replace line 115-116 with:
```markdown
**MANDATORY. Never skip.**

```bash
npm test path/to/test.test.ts
```

**Paste the ACTUAL failure output in your response:**
```
[PASTE EXACT OUTPUT HERE]
[NO OUTPUT = VIOLATION]
```

If you can't paste output, you didn't run the test.
```

**Step 5: Add timer enforcement**

Add after line 92:
```markdown
**Time limit:** Writing a test should take <5 minutes. Longer = over-engineering.

If your test needs:
- Complex mocks → Testing wrong thing
- Lots of setup → Design too complex
- Multiple assertions → Split into multiple tests
```

**Step 6: Add explicit delete detection**

Enhance lines 37-44:
```markdown
Write code before the test? Delete it. Start over.

**Delete means DELETE:**
- `rm -rf the_file.py` ✓
- `git reset --hard` ✓
- Physically delete ✓

**These are NOT deleting (violations):**
- `git stash` - That's hiding, not deleting
- `mv file.py file.py.bak` - That's keeping
- Copy to clipboard - That's keeping
- Comment out - That's keeping
- "Mental note" - That's keeping

Delete means gone forever. No recovery possible.
```

**Step 7: Run test to verify improvements**

Run: Test with updated skill
Expected: Agent pastes actual test output

**Step 8: Commit**

```bash
git add skills/test-driven-development/SKILL.md test-tdd-improvements.md
git commit -m "feat: require actual failure output and strict delete enforcement in TDD"
```

---

## Task 3: Improve systematic-debugging skill

**Files:**
- Modify: `skills/systematic-debugging/SKILL.md`

**Step 1: Write the failing test**

Create `test-debugging-improvements.md`:
```markdown
Test: Agent must complete phase checklist before advancing
Scenario: Agent debugging a test failure
Expected: Agent completes all Phase 1 items before Phase 2
Actual: [Document baseline]
```

**Step 2: Run test to verify current behavior**

Run: Test debugging scenario
Expected: Agent jumps to hypothesis without full investigation

**Step 3: Add phase gate checklist**

Insert after line 51:
```markdown
### Phase 1 Gate Checklist

**MUST complete ALL before Phase 2:**

```
Phase 1 Investigation:
□ Error message copied verbatim: ___________
□ Reproduction confirmed: [steps documented]
□ Recent changes reviewed: [git diff output]
□ Evidence from ALL components: [list components checked]
□ Data flow traced: [origin → error location]

Status: [Cannot proceed until all checked]
```

**Copy this checklist. Check items. Include in response.**
```

**Step 4: Add forced documentation**

Add after line 126:
```markdown
### Document Before Proceeding

Before Phase 2, write findings summary:
```
PHASE 1 FINDINGS:
- Error: [exact error]
- Occurs when: [reproduction steps]
- Recent changes: [relevant commits]
- Component evidence: [what each component shows]
- Data origin: [where bad data starts]
```

No summary = return to Phase 1.
```

**Step 5: Add hypothesis counter**

Modify line 195-197 to:
```markdown
3. **Verify Before Continuing**
   - Did it work? Yes → Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T add more fixes on top

   **CRITICAL: Track hypothesis count:**
   ```
   Hypothesis #1: [what] → [result]
   Hypothesis #2: [what] → [result]
   Hypothesis #3: [what] → [STOP if fails]
   ```

   **If hypothesis_count >= 3 and all failed:**
   - STOP immediately
   - Document: "3 hypotheses failed, architecture review required"
   - Discuss with human partner before ANY more attempts
   - This is MANDATORY, not optional
```

**Step 6: Add time box**

Add new section after line 230:
```markdown
## Time Limits

**Debugging time boxes:**
- 30 minutes without root cause → Escalate to human partner
- 3 failed fixes → Architecture review required
- 1 hour total → Stop and document what you learned

**When hitting time limit:**
1. Document everything you tried
2. State "Hit debugging time limit"
3. Ask for human partner guidance
4. Don't keep trying alone
```

**Step 7: Run test to verify phase gates work**

Run: Test with updated skill
Expected: Agent completes checklist before advancing

**Step 8: Commit**

```bash
git add skills/systematic-debugging/SKILL.md test-debugging-improvements.md
git commit -m "feat: add phase gates and hypothesis limits to systematic debugging"
```

---

## Task 4: Improve verification-before-completion skill

**Files:**
- Modify: `skills/verification-before-completion/SKILL.md`

**Step 1: Write the failing test**

Create `test-verification-improvements.md`:
```markdown
Test: Agent cannot use banned phrases
Scenario: Agent completing implementation task
Expected: No weasel words, evidence required first
Actual: [Document baseline]
```

**Step 2: Run test to verify current behavior**

Run: Test completion scenario
Expected: Agent uses "appears to work" or similar

**Step 3: Add banned phrases list**

Insert after line 60:
```markdown
## Banned Phrases (Automatic Violation)

**NEVER use these without evidence:**
- "appears to" / "seems to" / "looks like"
- "should be working" / "is now working"
- "implementation complete" (without test output)
- "successfully" (without command output)
- "properly" / "correctly" (without verification)
- "all good" / "works great" (without evidence)
- ANY positive adjective before verification

**Using these = lying, not verifying**
```

**Step 4: Add command-first rule**

Add after line 35:
```markdown
## The Command-First Rule

**EVERY completion message structure:**

1. FIRST: Run verification command
2. SECOND: Paste complete output
3. THIRD: State what output proves
4. ONLY THEN: Make your claim

**Example structure:**
```
Let me verify the implementation:

$ npm test
[PASTE FULL OUTPUT]

The tests show 15/15 passing. Implementation is complete.
```

**Wrong structure (violation):**
```
Implementation is complete! Let me verify:
[This is backwards - claimed before verifying]
```
```

**Step 5: Add false positive trap**

Insert after line 72:
```markdown
## The False Positive Trap

**About to say "all tests pass"?**

Check:
- Did you run tests THIS message? (Not last message)
- Did you paste the output? (Not just claim)
- Does output show 0 failures? (Not assumed)

**No to any = you're lying**

"I ran them earlier" = NOT verification
"They should pass now" = NOT verification
"The previous output showed" = NOT verification

**Run. Paste. Then claim.**
```

**Step 6: Run test to verify banned phrases caught**

Run: Test with updated skill
Expected: Agent avoids banned phrases, provides evidence first

**Step 7: Commit**

```bash
git add skills/verification-before-completion/SKILL.md test-verification-improvements.md
git commit -m "feat: add banned phrases and command-first rule to verification skill"
```

---

## Task 5: Improve brainstorming skill

**Files:**
- Modify: `skills/brainstorming/SKILL.md`

**Step 1: Write the failing test**

Create `test-brainstorming-improvements.md`:
```markdown
Test: Agent must show recon evidence
Scenario: Agent asked to brainstorm new feature
Expected: Agent shows actual recon output before asking questions
Actual: [Document baseline]
```

**Step 2: Run test to verify current behavior**

Run: Test brainstorming scenario
Expected: Agent skips recon or doesn't show evidence

**Step 3: Add mandatory recon evidence**

Replace lines 43-48 with:
```markdown
### Prep: Autonomous Recon

**MANDATORY evidence (paste ALL):**

```
Recon Checklist:
□ Project structure:
  $ ls -la
  [PASTE OUTPUT]

□ Recent activity:
  $ git log --oneline -10
  [PASTE OUTPUT]

□ Documentation:
  $ head -50 README.md
  [PASTE OUTPUT]

□ Test coverage:
  $ find . -name "*test*" -type f | wc -l
  [PASTE OUTPUT]

□ Key frameworks/tools:
  $ [Check package.json, requirements.txt, go.mod, etc.]
  [PASTE RELEVANT SECTIONS]
```

**Only after ALL evidence pasted:** Form your model and share findings.

**Skip any evidence = not following the skill**
```

**Step 4: Add phase lock mechanism**

Add after line 54:
```markdown
### Phase Lock Rules

**CRITICAL:** Once you enter a phase, you CANNOT skip ahead.

- Asked a question? → WAIT for answer before solutions
- Proposed approaches? → WAIT for selection before design
- Started design? → COMPLETE before documentation

**Violations:**
- "While you consider that, here's my design..." → WRONG
- "I'll proceed with option 1 unless..." → WRONG
- "Moving forward with the assumption..." → WRONG

**WAIT means WAIT. No assumptions.**
```

**Step 5: Add design acceptance gate**

Modify line 85 with:
```markdown
### Phase 3: Design Presentation

- Present in coherent sections...
- Check in at natural breakpoints...

**Design Acceptance Gate:**

Design is NOT approved until human EXPLICITLY says one of:
- "Approved" / "Looks good" / "Proceed"
- "Let's implement that" / "Ship it"
- "Yes" (in response to "Shall I proceed?")

**These do NOT mean approval:**
- Silence / No response
- "Interesting" / "I see" / "Hmm"
- Questions about the design
- "What about X?" (that's requesting changes)

**No explicit approval = keep refining**
```

**Step 6: Add question budget**

Insert after line 53:
```markdown
### Question Budget

**Maximum 3 questions per phase.** More = insufficient research.

Question count:
- Phase 1: ___/3
- Phase 2: ___/3
- Phase 3: ___/3

Hit limit? Do research instead of asking.
```

**Step 7: Run test to verify recon evidence required**

Run: Test with updated skill
Expected: Agent provides all recon evidence

**Step 8: Commit**

```bash
git add skills/brainstorming/SKILL.md test-brainstorming-improvements.md
git commit -m "feat: require recon evidence and phase locks in brainstorming"
```

---

## Task 6: Improve writing-plans skill

**Files:**
- Modify: `skills/writing-plans/SKILL.md`

**Step 1: Write the failing test**

Create `test-writing-plans-improvements.md`:
```markdown
Test: Plans must include exact expected output
Scenario: Agent writes plan for API endpoint
Expected: Every command has "Expected output:" section
Actual: [Document baseline]
```

**Step 2: Run test to verify current behavior**

Run: Test plan writing
Expected: Commands lack specific expected output

**Step 3: Add zero-context verification**

Add after line 12:
```markdown
## Zero-Context Test

**Before finalizing ANY plan, verify:**

```
Can someone execute this if they:
□ Never saw our codebase
□ Don't know our framework
□ Only have this document
□ Have no context about our domain

If NO to any → Add more detail
```

**Every task must be executable in isolation.**
```

**Step 4: Add command success criteria**

Modify the task structure starting at line 49:
```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Prerequisites:**
- Tools: pytest v7.0+, Python 3.8+
- Files must exist: `src/config.py`, `tests/conftest.py`
- Environment: `TESTING=true` must be set

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`

**Expected output:**
```
FAILED tests/path/test.py::test_name - NameError: name 'function' is not defined
```

**If you see different error:** Check file paths and imports

[Continue with remaining steps...]
```

**Step 5: Add rollback steps**

Add new section after each task:
```markdown
**If Task Fails:**

1. **Test won't run:**
   - Check: `ls tests/path/` (file exists?)
   - Fix: Create missing directories first
   - Rollback: `git checkout -- .`

2. **Implementation breaks other tests:**
   - Run: `pytest` (check what broke)
   - Rollback: `git reset --hard HEAD`
   - Revisit: Design may conflict with existing code

3. **Can't recover:**
   - Document: What failed and why
   - Stop: Return to human partner
   - Don't: Try to fix without understanding
```

**Step 6: Add dependency declaration**

Enhance header section:
```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use ring:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Global Prerequisites:**
- Environment: [OS, runtime versions]
- Tools: [Exact commands to verify: `python --version`, `npm --version`]
- Access: [Any API keys, services that must be running]
- State: [Branch to work from, any required setup]

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python --version  # Expected: Python 3.8+
npm --version     # Expected: 7.0+
git status        # Expected: clean working tree
pytest --version  # Expected: 7.0+
```

---
```

**Step 7: Run test to verify expected output included**

Run: Test with updated skill
Expected: Plan includes exact expected output

**Step 8: Commit**

```bash
git add skills/writing-plans/SKILL.md test-writing-plans-improvements.md
git commit -m "feat: add zero-context verification and rollback steps to writing-plans"
```

---

## Task 7: Add Cross-Skill Universal Patterns

**Files:**
- Create: `skills/shared-patterns/state-tracking.md`
- Create: `skills/shared-patterns/failure-recovery.md`
- Create: `skills/shared-patterns/exit-criteria.md`
- Create: `skills/shared-patterns/todowrite-integration.md`

**Step 1: Create state tracking pattern**

Create `skills/shared-patterns/state-tracking.md`:
```markdown
# Universal State Tracking Pattern

Add this section to any multi-step skill:

## State Tracking (MANDATORY)

Create and maintain a status comment:

```
SKILL: [skill-name]
PHASE: [current phase/step]
COMPLETED: [✓ list what's done]
NEXT: [→ what's next]
EVIDENCE: [last verification output]
BLOCKED: [any blockers]
```

**Update after EACH phase/step.**

Example:
```
SKILL: systematic-debugging
PHASE: 2 - Pattern Analysis
COMPLETED: ✓ Error reproduced ✓ Recent changes reviewed
NEXT: → Compare with working examples
EVIDENCE: Test fails with "KeyError: 'user_id'"
BLOCKED: None
```

This comment should be included in EVERY response while using the skill.
```

**Step 2: Create failure recovery pattern**

Create `skills/shared-patterns/failure-recovery.md`:
```markdown
# Universal Failure Recovery Pattern

Add this section to any skill with potential failure points:

## When Things Go Wrong

**If you get stuck:**

1. **Attempt failed?**
   - Document exactly what happened
   - Include error messages verbatim
   - Note what you tried

2. **Can't proceed?**
   - State blocker explicitly: "Blocked by: [specific issue]"
   - Don't guess or work around
   - Ask for help

3. **Confused?**
   - Say "I don't understand [specific thing]"
   - Don't pretend to understand
   - Research or ask for clarification

4. **Multiple failures?**
   - After 3 attempts: STOP
   - Document all attempts
   - Reassess approach with human partner

**Never:** Pretend to succeed when stuck
**Never:** Continue after 3 failures
**Never:** Hide confusion or errors
**Always:** Be explicit about blockage
```

**Step 3: Create exit criteria pattern**

Create `skills/shared-patterns/exit-criteria.md`:
```markdown
# Universal Exit Criteria Pattern

Add this section to define clear completion:

## Definition of Done

You may ONLY claim completion when:

□ All checklist items complete
□ Verification commands run and passed
□ Output evidence included in response
□ No "should" or "probably" in message
□ State tracking shows all phases done
□ No unresolved blockers

**Incomplete checklist = not done**

Example claim structure:
```
Status: Task complete

Evidence:
- Tests: 15/15 passing [output shown above]
- Lint: No errors [output shown above]
- Build: Success [output shown above]
- All requirements met [checklist verified]

The implementation is complete and verified.
```

**Never claim done without this structure.**
```

**Step 4: Create TodoWrite integration pattern**

Create `skills/shared-patterns/todowrite-integration.md`:
```markdown
# Universal TodoWrite Integration

Add this requirement to skill starts:

## TodoWrite Requirement

**BEFORE starting this skill:**

1. Create todos for major phases:
```javascript
[
  {content: "Phase 1: [name]", status: "in_progress", activeForm: "Working on Phase 1"},
  {content: "Phase 2: [name]", status: "pending", activeForm: "Working on Phase 2"},
  {content: "Phase 3: [name]", status: "pending", activeForm: "Working on Phase 3"}
]
```

2. Update after each phase:
   - Mark complete when done
   - Move next to in_progress
   - Add any new discovered tasks

3. Never work without todos:
   - Skipping todos = skipping the skill
   - Mental tracking = guaranteed to miss steps
   - Todos are your external memory

**Example for debugging:**
```javascript
[
  {content: "Root cause investigation", status: "in_progress", ...},
  {content: "Pattern analysis", status: "pending", ...},
  {content: "Hypothesis testing", status: "pending", ...},
  {content: "Implementation", status: "pending", ...}
]
```

If you're not updating todos, you're not following the skill.
```

**Step 5: Run test to verify patterns work**

Create test file with multi-step skill scenario
Expected: Clear state tracking throughout

**Step 6: Commit all patterns**

```bash
git add skills/shared-patterns/
git commit -m "feat: add universal patterns for state tracking, failure recovery, exit criteria, and todos"
```

---

## Task 8: Update Skills with Universal Patterns

**Files:**
- Modify: All skill files to reference shared patterns

**Step 1: Add pattern references to each skill**

For each skill in `skills/*/SKILL.md`, add before the last section:
```markdown
## Required Patterns

This skill uses these universal patterns:
- **State Tracking:** See `skills/shared-patterns/state-tracking.md`
- **Failure Recovery:** See `skills/shared-patterns/failure-recovery.md`
- **Exit Criteria:** See `skills/shared-patterns/exit-criteria.md`
- **TodoWrite:** See `skills/shared-patterns/todowrite-integration.md`

Apply ALL patterns when using this skill.
```

**Step 2: Run verification test**

Test one updated skill with all patterns
Expected: Skill references and follows patterns

**Step 3: Commit updates**

```bash
git add skills/*/SKILL.md
git commit -m "feat: integrate universal patterns into all skills"
```

---

## Verification Checklist

Before claiming this plan is complete:

- [ ] All 8 tasks documented with exact steps
- [ ] Every command has expected output specified
- [ ] All file paths are absolute and exact
- [ ] Prerequisites stated for each task
- [ ] Rollback steps included for failures
- [ ] Zero-context test passes (someone unfamiliar could execute)
- [ ] Plan saved to `docs/plans/2025-11-01-skill-bulletproofing.md`

## Execution

Ready to execute? Choose:
1. "Execute this yourself" - I'll run the plan step by step
2. "I'll execute manually" - You'll follow the plan yourself
3. "Dispatch to subagent" - Fresh agent executes with plan

**Recommended:** Option 1 for immediate implementation with verification at each step.