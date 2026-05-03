## Step 9: Gate 7 - Chaos Testing (Per Task — WRITE ONLY)

⛔ **CADENCE:** Write mode runs ONCE per task, NOT per subtask. Execute mode runs ONCE at cycle end (Step 12.1). `external_dependencies` is the UNION across all subtasks of the task.

**REQUIRED SUB-SKILL:** Use `ring:dev-chaos-testing`

**MANDATORY GATE:** All external dependencies MUST have chaos tests for failure scenarios.

**⛔ DEFERRED EXECUTION:** Per task, this gate writes/updates chaos test code and verifies compilation. Tests are NOT executed here (no Toxiproxy). Actual execution happens at end of cycle (Step 12.1).

### Step 9.1: Prepare Input for ring:dev-chaos-testing Skill

⛔ **Input scope:** TASK-level.

```text
task = state.tasks[state.current_task_index]

chaos_testing_input = {
  // REQUIRED - TASK-level
  unit_id: task.id,  // TASK id
  language: task.language,
  mode: "write_only",  // CRITICAL: write tests, verify compilation, do NOT execute

  // REQUIRED - UNION across subtasks of the task
  external_dependencies: union(task.subtasks.map(st => st.external_dependencies || []))
    || state.detected_dependencies
    || [],
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),

  // OPTIONAL - additional context
  gate6_handoff: task.gate_progress.integration_testing  // task-level Gate 6 (write) output
}

// NOTE: external_dependencies falls back to state.detected_dependencies
// from Step 1.6 (cycle-level auto-detection) when no subtask defines them.
```

### Step 9.2: Invoke ring:dev-chaos-testing Skill (Write Mode)

```text
1. Record gate start timestamp

2. REQUIRED: Invoke ring:dev-chaos-testing skill with structured input:

   Skill("ring:dev-chaos-testing") with input:
     unit_id: chaos_testing_input.unit_id
     external_dependencies: chaos_testing_input.external_dependencies
     language: chaos_testing_input.language
     mode: "write_only"
     gate6_handoff: chaos_testing_input.gate6_handoff

   In write_only mode, the skill handles:
   - Dispatching ring:qa-analyst agent (test_mode: chaos)
   - Writing/updating chaos test code for current unit's dependencies
   - Verifying test compilation
   - Verifying dual-gate pattern (CHAOS=1 + testing.Short())
   - Verifying Toxiproxy imports present
   - NOT starting Toxiproxy or executing failure scenarios

3. Parse skill output for results:

   if compilation PASS and standards met:
     → Gate 7 (write) PASSED. Proceed to Gate 8.

   if compilation FAIL:
     → Gate 7 BLOCKED. Fix compilation errors before proceeding.

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 9.3: Gate 7 (Write) Complete

```text
5. Update state:
   - gate_progress.chaos_testing.write_status = "completed"
   - gate_progress.chaos_testing.execution_status = "deferred"  // Executed at end of cycle
   - gate_progress.chaos_testing.test_files = [list of test files written/updated]
   - gate_progress.chaos_testing.compilation_passed = true

6. Proceed to Gate 8 (Review)
```

### Gate 7 Pressure Resistance

| User Says | Your Response |
|-----------|---------------|
| "Chaos testing is overkill" | "Chaos tests verify graceful degradation. Write them now, execute at end of cycle." |
| "Skip writing, add later" | "Test code MUST be written per unit. Only execution is deferred to end of cycle." |
| "Just run the chaos tests now" | "Deferred execution avoids redundant Toxiproxy spin-ups. Tests execute once at end of cycle." |
| "No time for chaos testing" | "Writing chaos tests per unit takes minutes. Execution cost is paid once at end." |

---

