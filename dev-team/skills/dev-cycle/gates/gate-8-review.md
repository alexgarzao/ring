## Step 10: Gate 8 - Review (Per Task — after all subtasks complete Gate 0 + Gate 3 + Gate 9)

⛔ **CADENCE:** This gate runs ONCE per task, NOT per subtask. Reviewers see the CUMULATIVE diff of all subtasks in the task — cross-subtask interaction bugs (contract drift, hidden coupling, duplicated logic) are MORE visible at this cadence, not less.

**REQUIRED SUB-SKILL:** Use `ring:codereview`

### Step 10.1: Prepare Input for ring:codereview Skill

⛔ **Input scope:** TASK-level. `base_sha` is the SHA before the FIRST subtask's Gate 0 (i.e., the task's starting commit); `head_sha` is the current HEAD after all subtasks and task-level gates up to this point. The resulting diff covers ALL subtasks of the task.

```text
task = state.tasks[state.current_task_index]

review_input = {
  // REQUIRED - TASK-level
  unit_id: task.id,  // TASK id
  base_sha: task.base_sha,            // SHA before the FIRST subtask started
  head_sha: [current HEAD],           // SHA after all subtasks + task-level gates so far

  // REQUIRED - summary and requirements aggregated from task + subtasks
  implementation_summary: task.title + "\n" +
    task.subtasks.map(st => "- " + st.title + ": " + (st.summary || "")).join("\n"),
  requirements: task.acceptance_criteria
    || flatten(task.subtasks.map(st => st.acceptance_criteria || [])),

  // OPTIONAL - additional context
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),  // UNION across subtasks
  gate0_handoffs: task.subtasks.map(st => st.gate_progress.implementation)  // ARRAY
}
```

### Step 10.2: Invoke ring:codereview Skill

```text
1. Record gate start timestamp

2. Invoke ring:codereview skill with structured input:

   Skill("ring:codereview") with input:
     unit_id: review_input.unit_id                    # TASK id
     base_sha: review_input.base_sha                  # SHA before first subtask
     head_sha: review_input.head_sha                  # Current HEAD (cumulative diff)
     implementation_summary: review_input.implementation_summary
     requirements: review_input.requirements
     implementation_files: review_input.implementation_files  # UNION across subtasks
     gate0_handoffs: review_input.gate0_handoffs      # ARRAY of subtask handoffs

   The skill handles:
   - Dispatching all 10 reviewers in PARALLEL (single message with 10 Task calls)
   - ring:code-reviewer, ring:business-logic-reviewer, ring:security-reviewer, ring:nil-safety-reviewer, ring:test-reviewer, ring:consequences-reviewer, ring:dead-code-reviewer, ring:performance-reviewer, ring:multi-tenant-reviewer, ring:lib-commons-reviewer
   - Aggregating issues by severity (CRITICAL/HIGH/MEDIUM/LOW/COSMETIC)
   - Dispatching fixes to implementation agent for blocking issues
   - Re-running all 10 reviewers after fixes
   - Iteration tracking (max 3 attempts)
   - Adding TODO/FIXME comments for non-blocking issues

3. Parse skill output for results:
   
   Expected output sections:
   - "## Review Summary" → status, iterations
   - "## Issues by Severity" → counts per severity level
   - "## Reviewer Verdicts" → all 10 reviewers
   - "## Handoff to Next Gate" → ready_for_validation: YES/NO

   if skill output contains "Status: PASS" and "Ready for Gate 9: YES":
     → Gate 8 PASSED. Proceed to Step 10.3.

   if skill output contains "Status: FAIL" or "Ready for Gate 9: NO":
     → Gate 8 BLOCKED.
     → Skill already dispatched fixes to implementation agent
      → Skill already re-ran all 10 reviewers
     → If "ESCALATION" in output: STOP and report to user

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 10.3: Gate 8 Complete

```text
5. When ring:codereview skill returns PASS:

   Parse from skill output:
   - reviewers_passed: extract from "## Reviewer Verdicts" (should be "5/5")
   - issues_critical: extract count from "## Issues by Severity"
   - issues_high: extract count from "## Issues by Severity"
   - issues_medium: extract count from "## Issues by Severity"
   - iterations: extract from "Iterations:" line

   - agent_outputs.review = {
       skill: "ring:codereview",
       output: "[full skill output]",
       iterations: [count],
       timestamp: "[ISO timestamp]",
       duration_ms: [execution time],
       reviewers_passed: "5/5",
       code_reviewer: {
         verdict: "PASS",
         issues_count: N,
         issues: []  // Structured issues - see schema below
       },
       business_logic_reviewer: {
         verdict: "PASS",
         issues_count: N,
         issues: []
       },
       security_reviewer: {
         verdict: "PASS",
         issues_count: N,
         issues: []
       },
       nil_safety_reviewer: {
         verdict: "PASS",
         issues_count: N,
         issues: []
       },
       test_reviewer: {
         verdict: "PASS",
         issues_count: N,
         issues: []
       }
     }
   
   **Populate `issues[]` for each reviewer with all issues found (even if fixed):**
   ```json
   issues: [
     {
       "severity": "CRITICAL|HIGH|MEDIUM|LOW|COSMETIC",
       "category": "error-handling|security|performance|maintainability|business-logic|...",
       "description": "[detailed description of the issue]",
       "file": "internal/handler/user.go",
       "line": 45,
       "code_snippet": "return err",
       "suggestion": "Use fmt.Errorf(\"failed to create user: %w\", err)",
       "fixed": true|false,
       "fixed_in_iteration": [iteration number when fixed, null if not fixed]
     }
   ]
   ```
   
   **Issue tracking rules:**
   - all issues found across all iterations MUST be recorded
   - `fixed: true` + `fixed_in_iteration: N` for issues resolved during review
   - `fixed: false` + `fixed_in_iteration: null` for LOW/COSMETIC (TODO/FIXME added)
   - This enables feedback-loop to analyze recurring issue patterns

6. Update state:
   - gate_progress.review.status = "completed"
   - gate_progress.review.reviewers_passed = "5/5"

7. Proceed to Gate 9
```

### Gate 8 Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Only 1 MEDIUM issue, can proceed" | MEDIUM = MUST FIX. Quantity is irrelevant. | **Fix the issue, re-run all 10 reviewers** |
| "Issue is cosmetic, not really MEDIUM" | Reviewer decided severity. Accept their judgment. | **Fix the issue, re-run all 10 reviewers** |
| "Will fix in next sprint" | Deferred fixes = technical debt = production bugs. | **Fix NOW before Gate 9** |
| "User approved, can skip fix" | User approval ≠ reviewer override. Fixes are mandatory. | **Fix the issue, re-run all 10 reviewers** |
| "Same issue keeps appearing, skip it" | Recurring issue = fix is wrong. Debug properly. | **Root cause analysis, then fix** |
| "Only one reviewer found it" | One reviewer = valid finding. All findings matter. | **Fix the issue, re-run all 10 reviewers** |
| "Iteration limit reached, just proceed" | Limit = escalate, not bypass. Quality is non-negotiable. | **Escalate to user, DO NOT proceed** |
| "Tests pass, review issues don't matter" | Tests ≠ review. Different quality dimensions. | **Fix the issue, re-run all 10 reviewers** |

### Gate 8 Pressure Resistance

| User Says | Your Response |
|-----------|---------------|
| "Just skip this MEDIUM issue" | "MEDIUM severity issues are blocking by definition. I MUST dispatch a fix to the appropriate agent before proceeding. This protects code quality." |
| "I'll fix it later, let's continue" | "Gate 8 is a HARD GATE. All CRITICAL/HIGH/MEDIUM issues must be resolved NOW. I'm dispatching the fix to [agent] and will re-run all 10 reviewers after." |
| "We're running out of time" | "Proceeding with known issues creates larger problems later. The fix dispatch is automated and typically takes 2-5 minutes. Quality gates exist to save time overall." |
| "Override the gate, I approve" | "User approval cannot override reviewer findings. The gate ensures code quality. I'll dispatch the fix now." |
| "It's just a style issue" | "If it's truly cosmetic, reviewers would mark it COSMETIC (non-blocking). MEDIUM means it affects maintainability or correctness. Fixing now." |

---

