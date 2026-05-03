## Step 7: Gate 5 - Property-Based Testing (Per Task — after all subtasks complete Gate 0 + Gate 3 + Gate 9)

⛔ **CADENCE:** This gate runs ONCE per task, NOT per subtask. Input `implementation_files` is the UNION of all subtasks' changed files; `domain_invariants` is the UNION across subtasks.

**REQUIRED SUB-SKILL:** Use `ring:dev-property-testing`

**MANDATORY GATE:** Domain invariants MUST be verified with property-based tests.

### Step 7.1: Prepare Input for ring:dev-property-testing Skill

⛔ **Input scope:** TASK-level.

```text
task = state.tasks[state.current_task_index]

property_testing_input = {
  // REQUIRED - TASK-level
  unit_id: task.id,  // TASK id
  language: task.language,

  // REQUIRED - UNION across subtasks
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),

  // Domain invariants — UNION across subtasks of the task
  domain_invariants: union(task.subtasks.map(st => st.domain_invariants || []))
}
```

### Step 7.2: Invoke ring:dev-property-testing Skill

```text
1. Record gate start timestamp

2. Invoke ring:dev-property-testing skill with structured input:

   Skill("ring:dev-property-testing") with input:
     unit_id: property_testing_input.unit_id
     implementation_files: property_testing_input.implementation_files
     language: property_testing_input.language
     domain_invariants: property_testing_input.domain_invariants

   The skill handles:
   - Dispatching ring:qa-analyst agent (test_mode: property)
   - Property function creation (TestProperty_* naming)
   - quick.Check pattern validation
   - Invariant verification
   - Dispatching fixes if properties fail
   - Re-validation loop (max 3 iterations)

3. Parse skill output for results:

   if skill output contains "Status: PASS":
     → Gate 5 PASSED. Proceed to Gate 6.

   if skill output contains "Status: FAIL":
     → Gate 5 BLOCKED.

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 7.3: Gate 5 Complete

```text
5. Update state:
   - gate_progress.property_testing.status = "completed"
   - gate_progress.property_testing.properties_tested = [count]

6. Proceed to Gate 6 (Integration Testing)
```

---

