# Commands Call Skills Refactor Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Refactor all Ring commands to call their corresponding skills, making skills the single source of truth for workflows.

**Architecture:** Commands become lightweight wrappers that (1) parse arguments, (2) provide usage documentation, and (3) delegate to skills via `Use Skill tool: skill-name`. All workflow logic, anti-rationalization tables, and pressure resistance scenarios live in skills.

**Tech Stack:** Markdown files, YAML frontmatter, Ring command/skill structure

**Global Prerequisites:**
- Environment: macOS/Linux with Ring plugin installed
- Tools: Git, text editor
- Access: Write access to Ring repository
- State: Clean working tree on `main` branch (or feature branch)

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
git status        # Expected: clean working tree or feature branch
ls default/commands/*.md  # Expected: list of command files
ls default/skills/*/SKILL.md  # Expected: list of skill files
```

## Historical Precedent

**Query:** "command skill refactor single source truth"
**Index Status:** Empty (new project / query returned no results)

No historical data available for this specific refactoring pattern. Proceeding with standard planning approach based on existing good patterns found in:
- `finance-team/commands/analyze-financials.md` - Good pattern template
- `dev-team/commands/dev-cycle.md` - Good pattern template
- `pmo-team/commands/portfolio-review.md` - Good pattern template

---

## Command Refactoring Summary

| Phase | Commands | Effort per Command | Total Tasks |
|-------|----------|-------------------|-------------|
| 1 | 10 (Low-hanging fruit) | 1-2 tasks | 15 |
| 2 | 8 (Medium refactor) | 2-3 tasks | 20 |
| 3 | 5 (Major refactor) | 3-5 tasks | 18 |
| **Total** | **23 commands** | | **53 tasks** |

---

## Good Pattern Template

All refactored commands MUST include this section after the command documentation:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: [skill-name]
```

The skill contains the complete workflow with:
- [Feature 1 from skill]
- [Feature 2 from skill]
- [Feature 3 from skill]
```

---

# Phase 1: Low-Hanging Fruit (10 Commands)

These commands already mention skills but lack the formal `## MANDATORY: Load Full Skill` section.

## Batch 1.1: Default Plugin Commands (4 commands)

### Task 1: Refactor /lint command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/lint.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/linting-codebase/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/lint.md`
- Skill exists: `default/skills/linting-codebase/SKILL.md`

**Step 1: Read current lint.md content**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/default/commands/lint.md | head -50`

**Expected:** Command file with YAML frontmatter and workflow description

**Step 2: Add MANDATORY section to lint.md**

Append the following section at the end of the file (before any existing `---` footer if present):

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: linting-codebase
```

The skill contains the complete workflow with:
- Parallel lint fixing pattern
- Stream analysis for independent fix groups
- Agent dispatch rules
- Verification loop with max iterations
- Critical constraints (no scripts, direct fixes only)
```

**Step 3: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/lint.md`

**Expected output:** The MANDATORY section appears at the end

**If different:** Check for duplicate sections or formatting issues

---

### Task 2: Refactor /explore-codebase command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/explore-codebase.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/exploring-codebase/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/explore-codebase.md`
- Skill exists: `default/skills/exploring-codebase/SKILL.md`

**Step 1: Add MANDATORY section to explore-codebase.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: exploring-codebase
```

The skill contains the complete workflow with:
- Two-phase autonomous exploration (Discovery + Deep Dive)
- Red flag detection table
- Violation consequences documentation
- Discovery agent prompt templates
- Deep dive adaptive prompts
- Synthesis document format
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/explore-codebase.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 3: Refactor /worktree command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/worktree.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/using-git-worktrees/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/worktree.md`
- Skill exists: `default/skills/using-git-worktrees/SKILL.md`

**Step 1: Add MANDATORY section to worktree.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: using-git-worktrees
```

The skill contains the complete workflow with:
- Worktree naming conventions
- Branch isolation patterns
- Cleanup procedures
- Integration with Ring workflows
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/worktree.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 4: Refactor /write-plan command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/write-plan.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/writing-plans/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/write-plan.md`
- Skill exists: `default/skills/writing-plans/SKILL.md`

**Step 1: Add MANDATORY section to write-plan.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: writing-plans
```

The skill contains the complete workflow with:
- Plan document structure
- Task granularity requirements (2-5 min per task)
- Zero-context test criteria
- Historical precedent integration
- Code review checkpoint requirements
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/write-plan.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 5: Commit Batch 1.1

**Prerequisites:**
- Tasks 1-4 completed successfully
- All modified files pass verification

**Step 1: Stage and commit changes**

Run:
```bash
git add default/commands/lint.md default/commands/explore-codebase.md default/commands/worktree.md default/commands/write-plan.md && git commit -m "refactor(commands): add MANDATORY skill sections to default commands

Add formal skill delegation sections to:
- /lint -> linting-codebase
- /explore-codebase -> exploring-codebase
- /worktree -> using-git-worktrees
- /write-plan -> writing-plans

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 4 files changed

**Step 2: Verify commit**

Run: `git log -1 --stat`

**Expected output:** Shows commit with 4 files changed

---

### Task 6: Run Code Review for Batch 1.1

**Prerequisites:**
- Task 5 commit completed

**Step 1: Dispatch all 3 reviewers in parallel**

Use REQUIRED SUB-SKILL: requesting-code-review

**Step 2: Handle findings by severity**

- **Critical/High/Medium:** Fix immediately, re-run reviewers
- **Low:** Add `TODO(review):` comments
- **Cosmetic:** Add `FIXME(nitpick):` comments

**Step 3: Proceed only when zero Critical/High/Medium issues remain**

---

## Batch 1.2: PMM-Team Commands (3 commands)

### Task 7: Refactor /market-analysis command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/pmm-team/commands/market-analysis.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/pmm-team/skills/market-analysis/SKILL.md`

**Prerequisites:**
- File exists: `pmm-team/commands/market-analysis.md`
- Skill exists: `pmm-team/skills/market-analysis/SKILL.md`

**Step 1: Add MANDATORY section to market-analysis.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: market-analysis
```

The skill contains the complete workflow with:
- Market sizing methodology (TAM/SAM/SOM)
- Segment analysis framework
- Competitor landscape mapping
- ICP definition process
- Data source integration
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/pmm-team/commands/market-analysis.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 8: Refactor /competitive-intel command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/pmm-team/commands/competitive-intel.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/pmm-team/skills/competitive-intelligence/SKILL.md`

**Prerequisites:**
- File exists: `pmm-team/commands/competitive-intel.md`
- Skill exists: `pmm-team/skills/competitive-intelligence/SKILL.md`

**Step 1: Add MANDATORY section to competitive-intel.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: competitive-intelligence
```

The skill contains the complete workflow with:
- Competitor categorization (direct/indirect/potential)
- Feature matrix creation
- Battlecard generation
- Win/loss analysis framework
- Competitive tracking plan
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/pmm-team/commands/competitive-intel.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 9: Refactor /gtm-plan command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/pmm-team/commands/gtm-plan.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/pmm-team/skills/gtm-planning/SKILL.md`

**Prerequisites:**
- File exists: `pmm-team/commands/gtm-plan.md`
- Skill exists: `pmm-team/skills/gtm-planning/SKILL.md`

**Step 1: Add MANDATORY section to gtm-plan.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: gtm-planning
```

The skill contains the complete workflow with:
- GTM strategy framework
- Channel selection and prioritization
- Budget allocation methodology
- Timeline and milestone planning
- Launch tier definitions
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/pmm-team/commands/gtm-plan.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 10: Commit Batch 1.2

**Prerequisites:**
- Tasks 7-9 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add pmm-team/commands/market-analysis.md pmm-team/commands/competitive-intel.md pmm-team/commands/gtm-plan.md && git commit -m "refactor(pmm-commands): add MANDATORY skill sections to PMM commands

Add formal skill delegation sections to:
- /market-analysis -> market-analysis
- /competitive-intel -> competitive-intelligence
- /gtm-plan -> gtm-planning

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 3 files changed

---

## Batch 1.3: Ops-Team Commands (3 commands)

### Task 11: Refactor /incident command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/incident.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/skills/ops-incident-response/SKILL.md`

**Prerequisites:**
- File exists: `ops-team/commands/incident.md`
- Skill exists: `ops-team/skills/ops-incident-response/SKILL.md`

**Step 1: Add MANDATORY section to incident.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ops-incident-response
```

The skill contains the complete workflow with:
- Severity classification (SEV1-SEV4)
- Incident timeline tracking
- Stakeholder communication templates
- Post-incident review framework
- Escalation procedures
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/incident.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 12: Refactor /capacity-review command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/capacity-review.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/skills/ops-capacity-planning/SKILL.md`

**Prerequisites:**
- File exists: `ops-team/commands/capacity-review.md`
- Skill exists: `ops-team/skills/ops-capacity-planning/SKILL.md`

**Step 1: Add MANDATORY section to capacity-review.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ops-capacity-planning
```

The skill contains the complete workflow with:
- Capacity baseline assessment
- Utilization trend analysis
- Growth forecasting methodology
- Gap analysis framework
- Scaling recommendations
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/capacity-review.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 13: Refactor /cost-analysis command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/cost-analysis.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/skills/ops-cost-optimization/SKILL.md`

**Prerequisites:**
- File exists: `ops-team/commands/cost-analysis.md`
- Skill exists: `ops-team/skills/ops-cost-optimization/SKILL.md`

**Step 1: Add MANDATORY section to cost-analysis.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ops-cost-optimization
```

The skill contains the complete workflow with:
- Cost breakdown analysis
- Rightsizing recommendations
- Reserved instance optimization
- Cost anomaly detection
- ROI calculation framework
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/cost-analysis.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 14: Commit Batch 1.3

**Prerequisites:**
- Tasks 11-13 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add ops-team/commands/incident.md ops-team/commands/capacity-review.md ops-team/commands/cost-analysis.md && git commit -m "refactor(ops-commands): add MANDATORY skill sections to Ops commands

Add formal skill delegation sections to:
- /incident -> ops-incident-response
- /capacity-review -> ops-capacity-planning
- /cost-analysis -> ops-cost-optimization

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 3 files changed

---

### Task 15: Run Code Review for Phase 1 (Batches 1.1-1.3)

**Prerequisites:**
- All Phase 1 commits completed (Tasks 5, 10, 14)

**Step 1: Dispatch all 3 reviewers in parallel**

Use REQUIRED SUB-SKILL: requesting-code-review

Review scope: All 10 command files modified in Phase 1

**Step 2: Handle findings by severity**

- **Critical/High/Medium:** Fix immediately, re-run reviewers
- **Low:** Add `TODO(review):` comments
- **Cosmetic:** Add `FIXME(nitpick):` comments

**Step 3: Proceed only when zero Critical/High/Medium issues remain**

---

# Phase 2: Medium Refactor (8 Commands)

These commands have workflow logic inline that should be moved to skills. The commands keep usage documentation but delegate execution to skills.

## Batch 2.1: Default Plugin Commands (4 commands)

### Task 16: Refactor /brainstorm command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/brainstorm.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/brainstorming/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/brainstorm.md`
- Skill exists: `default/skills/brainstorming/SKILL.md`

**Step 1: Read current brainstorm.md content**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/default/commands/brainstorm.md`

**Expected:** Line count to understand file size

**Step 2: Identify content to keep vs delegate**

Keep in command:
- YAML frontmatter
- Usage section
- Arguments section
- Examples section

Delegate to skill (add MANDATORY section):
- The actual workflow steps

**Step 3: Add MANDATORY section to brainstorm.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: brainstorming
```

The skill contains the complete workflow with:
- Socratic questioning framework
- Design refinement phases
- Challenge identification
- Solution exploration
- Decision documentation
```

**Step 4: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/brainstorm.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 17: Refactor /execute-plan command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/execute-plan.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/executing-plans/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/execute-plan.md`
- Skill exists: `default/skills/executing-plans/SKILL.md`

**Step 1: Add MANDATORY section to execute-plan.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: executing-plans
```

The skill contains the complete workflow with:
- Batch execution with review checkpoints
- Task state management
- Failure recovery procedures
- Progress tracking
- Code review integration
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/execute-plan.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 18: Refactor /create-handoff command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/create-handoff.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/create-handoff.md`
- Skill exists: `default/skills/handoff-tracking/SKILL.md`

**Step 1: Add MANDATORY section to create-handoff.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: handoff-tracking
```

The skill contains the complete workflow with:
- Handoff document template
- Metadata gathering process
- Automatic indexing integration
- Outcome tracking
- Session trace correlation
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/create-handoff.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 19: Refactor /resume-handoff command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/resume-handoff.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`

**Prerequisites:**
- File exists: `default/commands/resume-handoff.md`
- Skill exists: `default/skills/handoff-tracking/SKILL.md`

**Step 1: Add MANDATORY section to resume-handoff.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: handoff-tracking
```

The skill contains the complete workflow with:
- Handoff location and reading process
- State verification procedures
- Action plan creation
- Learnings application
- Interactive resumption guidelines
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/resume-handoff.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 20: Commit Batch 2.1

**Prerequisites:**
- Tasks 16-19 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add default/commands/brainstorm.md default/commands/execute-plan.md default/commands/create-handoff.md default/commands/resume-handoff.md && git commit -m "refactor(commands): add MANDATORY skill sections to workflow commands

Add formal skill delegation sections to:
- /brainstorm -> brainstorming
- /execute-plan -> executing-plans
- /create-handoff -> handoff-tracking
- /resume-handoff -> handoff-tracking

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 4 files changed

---

### Task 21: Run Code Review for Batch 2.1

**Prerequisites:**
- Task 20 commit completed

**Step 1: Dispatch all 3 reviewers in parallel**

Use REQUIRED SUB-SKILL: requesting-code-review

**Step 2: Handle findings by severity**

- **Critical/High/Medium:** Fix immediately, re-run reviewers
- **Low:** Add `TODO(review):` comments
- **Cosmetic:** Add `FIXME(nitpick):` comments

---

## Batch 2.2: Ops-Team and TW-Team Commands (4 commands)

### Task 22: Refactor /security-audit command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/security-audit.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/ops-team/skills/ops-security-audit/SKILL.md`

**Prerequisites:**
- File exists: `ops-team/commands/security-audit.md`
- Skill exists: `ops-team/skills/ops-security-audit/SKILL.md`

**Step 1: Add MANDATORY section to security-audit.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: ops-security-audit
```

The skill contains the complete workflow with:
- Automated security scanning integration
- Compliance framework mapping (SOC2, PCI, GDPR, HIPAA)
- Vulnerability prioritization
- Remediation planning
- Risk assessment methodology
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/ops-team/commands/security-audit.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 23: Refactor /write-guide command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/tw-team/commands/write-guide.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/tw-team/skills/writing-functional-docs/SKILL.md`

**Prerequisites:**
- File exists: `tw-team/commands/write-guide.md`
- Skill exists: `tw-team/skills/writing-functional-docs/SKILL.md`

**Step 1: Add MANDATORY section to write-guide.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: writing-functional-docs
```

The skill contains the complete workflow with:
- Document type selection (conceptual, getting-started, how-to, best-practices)
- Voice and tone guidelines
- Structure templates
- Review integration
- Quality checklist
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/tw-team/commands/write-guide.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 24: Refactor /write-api command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/tw-team/commands/write-api.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/tw-team/skills/writing-api-docs/SKILL.md`

**Prerequisites:**
- File exists: `tw-team/commands/write-api.md`
- Skill exists: `tw-team/skills/writing-api-docs/SKILL.md`

**Step 1: Add MANDATORY section to write-api.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: writing-api-docs
```

The skill contains the complete workflow with:
- Required sections (method, parameters, request/response, errors)
- Field description patterns
- Example quality requirements
- Data types reference
- HTTP status codes mapping
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/tw-team/commands/write-api.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 25: Refactor /review-docs command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/tw-team/commands/review-docs.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/tw-team/skills/documentation-review/SKILL.md`

**Prerequisites:**
- File exists: `tw-team/commands/review-docs.md`
- Skill exists: `tw-team/skills/documentation-review/SKILL.md`

**Step 1: Add MANDATORY section to review-docs.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: documentation-review
```

The skill contains the complete workflow with:
- Five-dimension review (voice, structure, completeness, clarity, accuracy)
- Verdict criteria (PASS, NEEDS_REVISION, MAJOR_ISSUES)
- Common issues reference
- Quick checklist
- docs-reviewer agent dispatch
```

**Step 2: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/tw-team/commands/review-docs.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 26: Commit Batch 2.2

**Prerequisites:**
- Tasks 22-25 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add ops-team/commands/security-audit.md tw-team/commands/write-guide.md tw-team/commands/write-api.md tw-team/commands/review-docs.md && git commit -m "refactor(commands): add MANDATORY skill sections to ops and tw commands

Add formal skill delegation sections to:
- /security-audit -> ops-security-audit
- /write-guide -> writing-functional-docs
- /write-api -> writing-api-docs
- /review-docs -> documentation-review

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 4 files changed

---

### Task 27: Run Code Review for Phase 2

**Prerequisites:**
- All Phase 2 commits completed (Tasks 20, 26)

**Step 1: Dispatch all 3 reviewers in parallel**

Use REQUIRED SUB-SKILL: requesting-code-review

Review scope: All 8 command files modified in Phase 2

**Step 2: Handle findings by severity**

- **Critical/High/Medium:** Fix immediately, re-run reviewers
- **Low:** Add `TODO(review):` comments
- **Cosmetic:** Add `FIXME(nitpick):` comments

---

# Phase 3: Major Refactor (5 Commands)

These commands have significant inline logic that requires careful migration to ensure skills become the single source of truth.

## Batch 3.1: Default Plugin Complex Commands (2 commands)

### Task 28: Analyze /codereview command current state

**Files:**
- Read: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/codereview.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/requesting-code-review/SKILL.md`

**Prerequisites:**
- Both files exist

**Step 1: Identify duplicate content**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/default/commands/codereview.md`

**Expected:** ~237 lines of content (per analysis)

**Step 2: Compare with skill**

The skill `requesting-code-review/SKILL.md` contains the complete workflow. The command should be simplified to:
- Usage documentation
- Quick reference
- MANDATORY skill section

---

### Task 29: Refactor /codereview command (streamline)

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/codereview.md`

**Step 1: Replace content with streamlined version**

Replace the entire file content with:

```markdown
---
name: codereview
description: Run comprehensive parallel code review with all 3 specialized reviewers
argument-hint: "[options]"
---

# Code Review Command

Dispatch all three reviewer subagents in **parallel** for fast, comprehensive feedback.

## Usage

```
/codereview [options]
```

## Options

| Option | Description | Example |
|--------|-------------|---------|
| `--scope` | Limit review to specific files | `--scope src/auth/` |
| `--base` | Base SHA for diff (default: merge-base) | `--base abc123` |
| `--skip` | Skip specific reviewers | `--skip security-reviewer` |

## Examples

```bash
# Full review of current branch
/codereview

# Review specific directory
/codereview --scope src/api/

# Review from specific commit
/codereview --base HEAD~5
```

## Reviewers Dispatched

| Reviewer | Focus | Model |
|----------|-------|-------|
| `code-reviewer` | Architecture, patterns, quality | opus |
| `business-logic-reviewer` | Domain, rules, edge cases | opus |
| `security-reviewer` | Vulnerabilities, OWASP | opus |

## Output

- **PASS:** All 3 reviewers pass, zero Critical/High/Medium issues
- **NEEDS_FIXES:** Blocking issues found, must fix and re-run
- **FAIL:** Max iterations (3) reached with unresolved issues

## Related Commands

| Command | Description |
|---------|-------------|
| `/dev-cycle` | Full development cycle with review at Gate 4 |

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: requesting-code-review
```

The skill contains the complete workflow with:
- Auto-detection of git context (base_sha, head_sha, files)
- Parallel dispatch of all 3 reviewers in single message
- Issue aggregation by severity
- Iteration loop with fix dispatching
- Escalation handling at max iterations
- Anti-rationalization tables
- Pressure resistance scenarios
```

**Step 2: Verify the change**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/default/commands/codereview.md`

**Expected output:** ~70-80 lines (significantly reduced from 237)

---

### Task 30: Refactor /query-artifacts command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/query-artifacts.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/artifact-query/SKILL.md`

**Step 1: Read current state**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/default/commands/query-artifacts.md`

**Step 2: Add MANDATORY section to query-artifacts.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: artifact-query
```

The skill contains the complete workflow with:
- Query formulation guidance
- Mode selection (search, planning)
- Result interpretation
- Learnings application
- Index initialization
```

**Step 3: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/query-artifacts.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 31: Commit Batch 3.1

**Prerequisites:**
- Tasks 28-30 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add default/commands/codereview.md default/commands/query-artifacts.md && git commit -m "refactor(commands): streamline codereview and add skill section to query-artifacts

- /codereview: Simplified from 237 lines to ~75 lines, delegates to requesting-code-review skill
- /query-artifacts: Add MANDATORY section for artifact-query skill

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 2 files changed

---

### Task 32: Run Code Review for Batch 3.1

**Prerequisites:**
- Task 31 commit completed

**Step 1: Dispatch all 3 reviewers in parallel**

Use REQUIRED SUB-SKILL: requesting-code-review

Focus on:
- Ensuring no workflow logic was lost in /codereview streamlining
- Verifying skill delegation is complete

---

## Batch 3.2: Dev-Team Command (1 command)

### Task 33: Refactor /dev-report command

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/dev-team/commands/dev-report.md`
- Reference: `/Users/fredamaral/repos/lerianstudio/ring/dev-team/skills/dev-feedback-loop/SKILL.md`

**Prerequisites:**
- File exists: `dev-team/commands/dev-report.md`
- Skill exists: `dev-team/skills/dev-feedback-loop/SKILL.md`

**Step 1: Read current state**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/dev-team/commands/dev-report.md`

**Step 2: Add MANDATORY section to dev-report.md**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: dev-feedback-loop
```

The skill contains the complete workflow with:
- Metrics collection from dev-cycle
- Pattern analysis
- Improvement recommendations
- Report generation format
- Historical comparison
```

**Step 3: Verify the change**

Run: `tail -20 /Users/fredamaral/repos/lerianstudio/ring/dev-team/commands/dev-report.md`

**Expected output:** The MANDATORY section appears at the end

---

### Task 34: Commit Batch 3.2

**Prerequisites:**
- Task 33 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add dev-team/commands/dev-report.md && git commit -m "refactor(dev-team): add MANDATORY skill section to dev-report command

Add formal skill delegation section to:
- /dev-report -> dev-feedback-loop

Skills become single source of truth for workflows." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 1 file changed

---

## Batch 3.3: PM-Team Orchestration Commands (2 commands)

These commands orchestrate multiple skills and require special handling.

### Task 35: Analyze /pre-dev-feature command pattern

**Files:**
- Read: `/Users/fredamaral/repos/lerianstudio/ring/pm-team/commands/pre-dev-feature.md`

**Step 1: Understand orchestration pattern**

The `/pre-dev-feature` command orchestrates 4 pre-dev-* skills:
1. `pre-dev-research`
2. `pre-dev-feature-map`
3. `pre-dev-dependency-map`
4. `pre-dev-task-breakdown`

**Decision:** This is an orchestration command. It should NOT delegate to a single skill but should reference all skills it orchestrates.

---

### Task 36: Refactor /pre-dev-feature command (orchestration pattern)

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/pm-team/commands/pre-dev-feature.md`

**Step 1: Add MANDATORY section for orchestration**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Skills Orchestration

**This command orchestrates multiple skills in a gated workflow.**

### Gate Sequence

| Gate | Skill | Purpose |
|------|-------|---------|
| 1 | `pre-dev-research` | Domain and technical research |
| 2 | `pre-dev-feature-map` | Feature scope definition |
| 3 | `pre-dev-dependency-map` | Dependency identification |
| 4 | `pre-dev-task-breakdown` | Task decomposition |

### Execution Pattern

```
For each gate:
  Use Skill tool: [gate-skill]
  Wait for human approval
  Proceed to next gate
```

Each skill contains its own:
- Anti-rationalization tables
- Gate pass criteria
- Output format requirements

**Do NOT skip gates.** Each gate builds on the previous gate's output.
```

**Step 2: Verify the change**

Run: `tail -30 /Users/fredamaral/repos/lerianstudio/ring/pm-team/commands/pre-dev-feature.md`

**Expected output:** The Skills Orchestration section appears at the end

---

### Task 37: Refactor /pre-dev-full command (orchestration pattern)

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/pm-team/commands/pre-dev-full.md`

**Step 1: Add MANDATORY section for orchestration**

Append the following section at the end of the file:

```markdown
---

## MANDATORY: Skills Orchestration

**This command orchestrates multiple skills in a 9-gate workflow.**

### Gate Sequence

| Gate | Skill | Purpose |
|------|-------|---------|
| 0 | `pre-dev-problem-statement` | Problem definition |
| 1 | `pre-dev-user-journey` | User journey mapping |
| 2 | `pre-dev-technical-vision` | Technical approach |
| 3 | `pre-dev-data-requirements` | Data needs |
| 4 | `pre-dev-security-requirements` | Security analysis |
| 5 | `pre-dev-research` | Domain/technical research |
| 6 | `pre-dev-feature-map` | Feature scope |
| 7 | `pre-dev-dependency-map` | Dependencies |
| 8 | `pre-dev-task-breakdown` | Task decomposition |

### Execution Pattern

```
For each gate:
  Use Skill tool: [gate-skill]
  Wait for human approval
  Proceed to next gate
```

Each skill contains its own:
- Anti-rationalization tables
- Gate pass criteria
- Output format requirements

**Do NOT skip gates.** Each gate builds on the previous gate's output.
```

**Step 2: Verify the change**

Run: `tail -35 /Users/fredamaral/repos/lerianstudio/ring/pm-team/commands/pre-dev-full.md`

**Expected output:** The Skills Orchestration section appears at the end

---

### Task 38: Commit Batch 3.3

**Prerequisites:**
- Tasks 35-37 completed successfully

**Step 1: Stage and commit changes**

Run:
```bash
git add pm-team/commands/pre-dev-feature.md pm-team/commands/pre-dev-full.md && git commit -m "refactor(pm-team): add Skills Orchestration sections to pre-dev commands

Add formal orchestration documentation to:
- /pre-dev-feature: 4-gate workflow
- /pre-dev-full: 9-gate workflow

Documents which skills are called at each gate without moving workflow logic." --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:** Commit created with 2 files changed

---

### Task 39: Run Code Review for Phase 3

**Prerequisites:**
- All Phase 3 commits completed (Tasks 31, 34, 38)

**Step 1: Dispatch all 3 reviewers in parallel**

Use REQUIRED SUB-SKILL: requesting-code-review

Review scope: All 5 command files modified in Phase 3

Focus areas:
- No workflow logic lost in /codereview streamlining
- Orchestration pattern is clear for pre-dev commands
- All MANDATORY sections complete

**Step 2: Handle findings by severity**

- **Critical/High/Medium:** Fix immediately, re-run reviewers
- **Low:** Add `TODO(review):` comments
- **Cosmetic:** Add `FIXME(nitpick):` comments

---

# Final Verification

## Task 40: Verify all commands have MANDATORY sections

**Step 1: Check all modified commands**

Run:
```bash
for cmd in \
  default/commands/lint.md \
  default/commands/explore-codebase.md \
  default/commands/worktree.md \
  default/commands/write-plan.md \
  default/commands/brainstorm.md \
  default/commands/execute-plan.md \
  default/commands/create-handoff.md \
  default/commands/resume-handoff.md \
  default/commands/codereview.md \
  default/commands/query-artifacts.md \
  pmm-team/commands/market-analysis.md \
  pmm-team/commands/competitive-intel.md \
  pmm-team/commands/gtm-plan.md \
  ops-team/commands/incident.md \
  ops-team/commands/capacity-review.md \
  ops-team/commands/cost-analysis.md \
  ops-team/commands/security-audit.md \
  tw-team/commands/write-guide.md \
  tw-team/commands/write-api.md \
  tw-team/commands/review-docs.md \
  dev-team/commands/dev-report.md \
  pm-team/commands/pre-dev-feature.md \
  pm-team/commands/pre-dev-full.md; do
  echo "=== $cmd ===" && grep -c "MANDATORY" "$cmd" || echo "MISSING!"
done
```

**Expected output:** Each file shows count >= 1 for MANDATORY

**Step 2: Verify skill references**

Run:
```bash
for cmd in default/commands/*.md pmm-team/commands/*.md ops-team/commands/*.md tw-team/commands/*.md dev-team/commands/*.md pm-team/commands/*.md; do
  if grep -q "Use Skill tool:" "$cmd"; then
    echo "OK: $cmd"
  fi
done
```

**Expected output:** All 23 modified commands listed

---

## Task 41: Final commit (if any fixes needed)

**Prerequisites:**
- Task 40 verification passed

If any fixes were needed:

**Step 1: Stage and commit fixes**

Run:
```bash
git add -A && git commit -m "fix: address verification issues in command skill sections" --trailer "Generated-by: Claude" --trailer "AI-Model: claude-opus-4-5-20251101"
```

---

## Task 42: Run Final Code Review

**Prerequisites:**
- All tasks completed

**Step 1: Dispatch all 3 reviewers for final review**

Use REQUIRED SUB-SKILL: requesting-code-review

Full scope: All 23 command files

**Step 2: Verify PASS from all reviewers**

---

# Summary

## Commands Refactored

| Plugin | Commands | Pattern |
|--------|----------|---------|
| default | 10 | MANDATORY skill section |
| pmm-team | 3 | MANDATORY skill section |
| ops-team | 4 | MANDATORY skill section |
| tw-team | 3 | MANDATORY skill section |
| dev-team | 1 | MANDATORY skill section |
| pm-team | 2 | Skills Orchestration section |
| **Total** | **23** | |

## Commands That Already Had Pattern

| Plugin | Commands | Notes |
|--------|----------|-------|
| dev-team | 2 | `/dev-cycle`, `/dev-refactor` |
| finance-team | 3 | `/analyze-financials`, `/build-model`, `/create-budget` |
| pmo-team | 3 | `/portfolio-review`, `/executive-summary`, `/dependency-analysis` |

## Commands That Don't Need Skills

| Plugin | Commands | Reason |
|--------|----------|--------|
| default | `/commit` | Self-contained git operation |
| dev-team | `/dev-status`, `/dev-cancel` | Simple state operations |
| default | `/compound-learnings` | Orchestration command |

---

# Failure Recovery

**If any task fails:**

1. **Read error message carefully**
2. **Check file path exists:** `ls -la [path]`
3. **Check skill exists:** `ls -la [skill-path]/SKILL.md`
4. **Rollback if needed:** `git checkout -- [file]`
5. **Document failure:** Note what failed and why
6. **Resume from last successful task**

**If verification fails:**

1. **Identify missing MANDATORY section**
2. **Re-run the specific task that should have added it**
3. **Commit the fix**
4. **Continue with verification**
