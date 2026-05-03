## Step 8: Gate 6 - Integration Testing (Per Task — WRITE ONLY)

⛔ **CADENCE:** Write mode runs ONCE per task, NOT per subtask. Execute mode runs ONCE at cycle end (Step 12.1). Input `implementation_files` is the UNION of all subtasks' changed files.

**REQUIRED SUB-SKILL:** Use `ring:dev-integration-testing`

**MANDATORY GATE:** All code MUST have integration tests using testcontainers.

**⛔ DEFERRED EXECUTION:** Per task, this gate writes/updates integration test code and verifies compilation. Tests are NOT executed here (no containers). Actual execution happens at end of cycle (Step 12.1).

### Step 8.1: Prepare Input for ring:dev-integration-testing Skill

⛔ **Input scope:** TASK-level.

```text
task = state.tasks[state.current_task_index]

integration_testing_input = {
  // REQUIRED - TASK-level
  unit_id: task.id,  // TASK id
  language: task.language,
  mode: "write_only",  // CRITICAL: write tests, verify compilation, do NOT execute

  // REQUIRED - UNION across subtasks of the task
  integration_scenarios: union(task.subtasks.map(st => st.integration_scenarios || [])),
  external_dependencies: union(task.subtasks.map(st => st.external_dependencies || []))
    || state.detected_dependencies
    || [],
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),

  // OPTIONAL - additional context
  gate5_handoff: task.gate_progress.property_testing  // task-level Gate 5 output
}

// NOTE: external_dependencies falls back to state.detected_dependencies
// from Step 1.6 (cycle-level auto-detection) when no subtask defines them.
```

### Step 8.2: Invoke ring:dev-integration-testing Skill (Write Mode)

```text
1. Record gate start timestamp

2. REQUIRED: Invoke ring:dev-integration-testing skill with structured input:

   Skill("ring:dev-integration-testing") with input:
     unit_id: integration_testing_input.unit_id
     integration_scenarios: integration_testing_input.integration_scenarios
     external_dependencies: integration_testing_input.external_dependencies
     language: integration_testing_input.language
     mode: "write_only"
     gate5_handoff: integration_testing_input.gate5_handoff
     implementation_files: integration_testing_input.implementation_files

   In write_only mode, the skill handles:
   - Dispatching ring:qa-analyst agent (test_mode: integration)
   - Writing/updating integration test code for current unit's changes
   - Verifying test compilation (go build ./... or tsc --noEmit)
   - Verifying build tags (//go:build integration) present
   - Verifying testcontainers imports present
   - NOT spinning up containers or executing tests

3. REQUIRED: Parse skill output for results:

   Expected output:
   - "## Integration Test Code" → files written/updated
   - "## Compilation Check" → PASS/FAIL
   - "## Standards Compliance" → build tags, naming, testcontainers

   if compilation PASS and standards met:
     → Gate 6 (write) PASSED. Proceed to Step 8.3.

   if compilation FAIL:
     → Gate 6 BLOCKED. Fix compilation errors before proceeding.

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 8.3: Gate 6 (Write) Complete

```text
5. Update state:
   - gate_progress.integration_testing.write_status = "completed"
   - gate_progress.integration_testing.execution_status = "deferred"  // Executed at end of cycle
   - gate_progress.integration_testing.test_files = [list of test files written/updated]
   - gate_progress.integration_testing.compilation_passed = true

6. Proceed to Gate 7 (Chaos Testing — Write Only)
```

### Gate 6 Pressure Resistance

| User Says | Your Response |
|-----------|---------------|
| "Unit tests cover integration" | "Unit tests mock dependencies. Integration tests verify real behavior. Write the tests now, execute at end of cycle." |
| "Skip writing, we'll add tests later" | "Test code MUST be written per unit to stay current. Only execution is deferred." |
| "No external dependencies to test" | "Verify internal integration too. Write the tests, they'll execute at end of cycle." |
| "Just run the tests now" | "Deferred execution avoids redundant container spin-ups. Tests execute once at end of cycle." |

---

