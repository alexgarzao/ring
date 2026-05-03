## Step 4: Gate 2 - SRE (Per Task — after all subtasks complete Gate 0 + Gate 3 + Gate 9)

⛔ **CADENCE:** This gate runs ONCE per task, NOT per subtask. Input `implementation_files` is the UNION of all subtasks' changed files; `gate0_handoffs` is an ARRAY.

**REQUIRED SUB-SKILL:** Use `ring:dev-sre`

### Step 4.1: Prepare Input for ring:dev-sre Skill

⛔ **Input scope:** TASK-level. Aggregate from all subtasks of the current task.

```text
Gather from completed subtask-level gates:

task = state.tasks[state.current_task_index]

sre_input = {
  // REQUIRED - TASK-level identifiers
  unit_id: task.id,  // TASK id
  language: task.language,
  service_type: task.service_type,

  // REQUIRED - UNION across subtasks
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),

  // REQUIRED - ARRAY of per-subtask Gate 0 handoffs
  gate0_handoffs: task.subtasks.map(st => st.gate_progress.implementation),

  // REQUIRED - implementation_agent (consistent across subtasks of the same task)
  implementation_agent: task.subtasks[0].gate_progress.implementation.agent,

  // OPTIONAL - additional context
  external_dependencies: task.external_deps || state.detected_dependencies || [],
  gate1_handoff: task.gate_progress.devops  // task-level Gate 1 output (just completed)
}
```

### Step 4.2: Invoke ring:dev-sre Skill

```text
1. Record gate start timestamp

2. Invoke ring:dev-sre skill with structured input:

   Skill("ring:dev-sre") with input:
     unit_id: sre_input.unit_id                       # TASK id
     language: sre_input.language
     service_type: sre_input.service_type
     implementation_agent: sre_input.implementation_agent
     implementation_files: sre_input.implementation_files  # UNION across subtasks
     external_dependencies: sre_input.external_dependencies
     gate0_handoffs: sre_input.gate0_handoffs          # ARRAY of subtask handoffs
     gate1_handoff: sre_input.gate1_handoff

   The skill handles:
   - Dispatching SRE agent for validation
   - Structured logging validation
   - Distributed tracing validation
   - Code instrumentation coverage (90%+ required)
   - Context propagation validation (InjectHTTPContext/InjectGRPCContext)
   - Dispatching fixes to implementation agent if needed
   - Re-validation loop (max 3 iterations)

3. Parse skill output for validation results:
   
   Expected output sections:
   - "## Validation Result" → status, iterations, coverage
   - "## Instrumentation Coverage" → table with per-layer coverage
   - "## Issues Found" → list or "None"
   - "## Handoff to Next Gate" → ready_for_testing: YES/no
   
   if skill output contains "Status: PASS" and "Ready for Gate 3: YES":
     → Gate 2 PASSED. Proceed to Step 4.3.
   
   if skill output contains "Status: FAIL" or "Ready for Gate 3: no":
     → Gate 2 BLOCKED. 
     → Skill already dispatched fixes to implementation agent
     → Skill already re-ran validation
     → If "ESCALATION" in output: STOP and report to user

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 4.3: Gate 2 Complete

```text
5. When ring:dev-sre skill returns PASS:
   
   Parse from skill output:
   - status: extract from "## Validation Result"
   - instrumentation_coverage: extract percentage from coverage table
   - iterations: extract from "Iterations:" line
   
   - agent_outputs.sre = {
       skill: "ring:dev-sre",
       output: "[full skill output]",
       validation_result: "PASS",
       instrumentation_coverage: "[X%]",
       iterations: [count],
       timestamp: "[ISO timestamp]",
       duration_ms: [execution time]
     }

6. Update state:
   - gate_progress.sre.status = "completed"
   - gate_progress.sre.observability_validated = true
   - gate_progress.sre.instrumentation_coverage = "[X%]"

7. Proceed to Gate 3
```

### Gate 2 Anti-Rationalization Table

See [ring:dev-sre/SKILL.md](../dev-sre/SKILL.md) for complete anti-rationalization tables covering:
- Observability deferral rationalizations
- Instrumentation coverage rationalizations
- Context propagation rationalizations

### Gate 2 Pressure Resistance

| User Says | Your Response |
|-----------|---------------|
| "Skip SRE validation, we'll add observability later" | "Observability is MANDATORY for Gate 2. Invoking ring:dev-sre skill now." |
| "SRE found issues but let's continue" | "Gate 2 is a HARD GATE. ring:dev-sre skill handles fix dispatch and re-validation." |
| "Instrumentation coverage is low but code works" | "90%+ instrumentation coverage is REQUIRED. ring:dev-sre skill will not pass until met." |

