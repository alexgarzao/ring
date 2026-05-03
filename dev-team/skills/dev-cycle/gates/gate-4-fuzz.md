## Step 6: Gate 4 - Fuzz Testing (Per Task — after all subtasks complete Gate 0 + Gate 3 + Gate 9)

⛔ **CADENCE:** This gate runs ONCE per task, NOT per subtask. Input `implementation_files` is the UNION of all subtasks' changed files.

**REQUIRED SUB-SKILL:** Use `ring:dev-fuzz-testing`

**MANDATORY GATE:** All code paths MUST have fuzz tests to discover edge cases and crashes.

### Step 6.1: Prepare Input for ring:dev-fuzz-testing Skill

⛔ **Input scope:** TASK-level. Aggregate from all subtasks of the current task.

```text
task = state.tasks[state.current_task_index]

fuzz_testing_input = {
  // REQUIRED - TASK-level
  unit_id: task.id,  // TASK id
  language: task.language,  // "go" | "typescript"

  // REQUIRED - UNION across subtasks
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),

  // REQUIRED - ARRAY of per-subtask unit-testing handoffs (Gate 3 is per subtask)
  gate3_handoffs: task.subtasks.map(st => st.gate_progress.unit_testing)
}
```

### Step 6.2: Invoke ring:dev-fuzz-testing Skill

```text
1. Record gate start timestamp

2. Invoke ring:dev-fuzz-testing skill with structured input:

   Skill("ring:dev-fuzz-testing") with input:
     unit_id: fuzz_testing_input.unit_id               # TASK id
     implementation_files: fuzz_testing_input.implementation_files  # UNION across subtasks
     language: fuzz_testing_input.language
     gate3_handoffs: fuzz_testing_input.gate3_handoffs # ARRAY of per-subtask handoffs

   The skill handles:
   - Dispatching ring:qa-analyst agent (test_mode: fuzz)
   - Fuzz function creation (FuzzXxx naming)
   - Seed corpus generation (minimum 5 entries)
   - f.Add() pattern validation
   - Dispatching fixes if crashes found
   - Re-validation loop (max 3 iterations)

3. Parse skill output for results:

   if skill output contains "Status: PASS":
     → Gate 4 PASSED. Proceed to Gate 5.

   if skill output contains "Status: FAIL":
     → Gate 4 BLOCKED.

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 6.3: Gate 4 Complete

```text
5. Update state:
   - gate_progress.fuzz_testing.status = "completed"
   - gate_progress.fuzz_testing.corpus_entries = [count]

6. Proceed to Gate 5 (Property Testing)
```

---

