## Step 5: Gate 3 - Unit Testing (Per Execution Unit)

ℹ️ **CADENCE:** Subtask-level. Execution unit = a subtask (or the task itself when no subtasks). Writes to `state.tasks[i].subtasks[j].gate_progress.unit_testing`.

**REQUIRED SUB-SKILL:** Use `ring:dev-unit-testing`

### Step 5.1: Prepare Input for ring:dev-unit-testing Skill

```text
Gather from previous gates:

testing_input = {
  // REQUIRED - from current execution unit
  unit_id: state.current_unit.id,
  acceptance_criteria: state.current_unit.acceptance_criteria,  // list of ACs to test
  implementation_files: agent_outputs.implementation.files_changed,
  language: state.current_unit.language,  // "go" | "typescript" | "python"
  
  // OPTIONAL - additional context
  coverage_threshold: 85,  // Ring minimum, PROJECT_RULES.md can raise
  gate0_handoff: agent_outputs.implementation,  // full Gate 0 output
  existing_tests: [check for existing test files]
}
```

### Step 5.2: Invoke ring:dev-unit-testing Skill

```text
1. Record gate start timestamp

2. Invoke ring:dev-unit-testing skill with structured input:

   Skill("ring:dev-unit-testing") with input:
     unit_id: testing_input.unit_id
     acceptance_criteria: testing_input.acceptance_criteria
     implementation_files: testing_input.implementation_files
     language: testing_input.language
     coverage_threshold: testing_input.coverage_threshold
     gate0_handoff: testing_input.gate0_handoff
     existing_tests: testing_input.existing_tests

   The skill handles:
   - Dispatching ring:qa-analyst agent
   - Test creation following TDD methodology
   - Coverage measurement and validation (85%+ required)
   - Traceability matrix (AC → Test mapping)
   - Dispatching fixes to implementation agent if coverage < threshold
   - Re-validation loop (max 3 iterations)

3. Parse skill output for results:
   
   Expected output sections:
   - "## Testing Summary" → status, iterations
   - "## Coverage Report" → threshold vs actual
   - "## Traceability Matrix" → AC-to-test mapping
   - "## Handoff to Next Gate" → ready_for_review: YES/no
   
   if skill output contains "Status: PASS" and "Ready for Next Gate: YES":
     → Gate 3 PASSED. Proceed to Step 5.3.

   if skill output contains "Status: FAIL" or "Ready for Next Gate: NO":
     → Gate 3 BLOCKED.
     → Skill already dispatched fixes to implementation agent
     → Skill already re-ran coverage check
     → If "ESCALATION" in output: STOP and report to user

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 5.3: Gate 3 Complete

```text
5. When ring:dev-unit-testing skill returns PASS:
   
   Parse from skill output:
   - coverage_actual: extract percentage from "## Coverage Report"
   - coverage_threshold: extract from "## Coverage Report"
   - criteria_covered: extract from "## Traceability Matrix"
   - iterations: extract from "Iterations:" line
   
   - agent_outputs.testing = {
       skill: "ring:dev-unit-testing",
       output: "[full skill output]",
       verdict: "PASS",
       coverage_actual: [X%],
       coverage_threshold: [85%],
       criteria_covered: "[X/Y]",
       iterations: [count],
       timestamp: "[ISO timestamp]",
       duration_ms: [execution time],
       failures: [],  // Empty when PASS; see schema below for FAIL
       uncovered_criteria: []  // Empty when all ACs covered
     }
   
   **If iterations > 1 (tests failed before passing), populate `failures[]`:**
   ```json
   failures: [
     {
       "test_name": "TestUserCreate_InvalidEmail",
       "test_file": "internal/handler/user_test.go",
       "error_type": "assertion|panic|timeout|compilation",
       "expected": "[expected value]",
       "actual": "[actual value]",
       "message": "[error message from test output]",
       "stack_trace": "[relevant stack trace]",
       "fixed_in_iteration": [iteration number when fixed]
     }
   ]
   ```
   
   **If coverage < 100% of acceptance criteria, populate `uncovered_criteria[]`:**
   ```json
   uncovered_criteria: [
     {
       "criterion_id": "AC-001",
       "description": "User should receive email confirmation",
       "reason": "No test found for email sending functionality"
     }
   ]
   ```

6. Update state:
   - gate_progress.testing.status = "completed"
   - gate_progress.testing.coverage = [coverage_actual]

7. Proceed to Gate 4 (Fuzz Testing)
```

### Gate 3 Thresholds

- **Minimum:** 85% (Ring standard - CANNOT be lowered)
- **Project-specific:** Can be higher if defined in `docs/PROJECT_RULES.md`
- **Validation:** Threshold < 85% → Use 85%

### Gate 3 Pressure Resistance

| User Says | Your Response |
|-----------|---------------|
| "84% is close enough" | "85% is Ring minimum. ring:dev-unit-testing skill enforces this." |
| "Skip testing, deadline" | "Testing is MANDATORY. ring:dev-unit-testing skill handles iterations." |
| "Manual testing covers it" | "Gate 3 requires executable unit tests. Invoking ring:dev-unit-testing now." |

