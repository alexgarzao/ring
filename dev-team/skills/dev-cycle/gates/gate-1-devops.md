## Step 3: Gate 1 - DevOps (Per Task — after all subtasks complete Gate 0 + Gate 3 + Gate 9)

⛔ **CADENCE:** This gate runs ONCE per task, NOT per subtask. Do NOT dispatch during the subtask loop. Input `implementation_files` is the UNION of all subtasks' changed files; `gate0_handoffs` is an ARRAY of per-subtask implementation handoffs.

**REQUIRED SUB-SKILLS:** Use ring:dev-devops, then ring:dev-docker-security (audit)

### ⛔ HARD GATE: Required Artifacts MUST Be Created

**Gate 1 is a BLOCKING gate.** DevOps agent MUST create all required artifacts. If any artifact is missing:
- You CANNOT proceed to Gate 2
- You MUST re-dispatch to ring:devops-engineer to create missing artifacts
- You MUST verify all artifacts exist before proceeding

### Required Artifacts

**See [shared-patterns/standards-coverage-table.md](../skills/shared-patterns/standards-coverage-table.md) → "ring:devops-engineer → devops.md" for all required sections.**

**Key artifacts from devops.md:**
- Containers (Dockerfile + Docker Compose)
- Makefile Standards (all required commands)
- Infrastructure as Code (if applicable)
- Helm charts (if K8s deployment)

### Step 3.1: Prepare Input for ring:dev-devops Skill

⛔ **Input scope:** TASK-level. `implementation_files` is the UNION of `files_changed` across all subtasks of the current task; `gate0_handoffs` is an ARRAY (one per subtask).

```text
Gather from completed subtask-level gates of the current task:

task = state.tasks[state.current_task_index]

devops_input = {
  // REQUIRED - TASK-level identifiers (NOT subtask)
  unit_id: task.id,  // TASK id (e.g., "T-001"), not subtask id
  language: task.language,  // "go" | "typescript" | "python"
  service_type: task.service_type,  // "api" | "worker" | "batch" | "cli"

  // REQUIRED - UNION of files changed across all subtasks of this task
  implementation_files: flatten(task.subtasks.map(st =>
    st.gate_progress.implementation.files_changed || []
  )),

  // REQUIRED - ARRAY of per-subtask Gate 0 handoffs (one per subtask)
  gate0_handoffs: task.subtasks.map(st => st.gate_progress.implementation),

  // OPTIONAL - additional context (union across subtasks where applicable)
  new_dependencies: union(task.subtasks.map(st => st.new_deps || [])),
  new_env_vars: union(task.subtasks.map(st => st.env_vars || [])),
  new_services: union(task.subtasks.map(st => st.services || [])),
  existing_dockerfile: [check if Dockerfile exists],
  existing_compose: [check if docker-compose.yml exists]
}
```

### Step 3.2: Invoke ring:dev-devops Skill

```text
1. Record gate start timestamp

2. Invoke ring:dev-devops skill with structured input:

   Skill("ring:dev-devops") with input:
     unit_id: devops_input.unit_id                    # TASK id
     language: devops_input.language
     service_type: devops_input.service_type
     implementation_files: devops_input.implementation_files  # UNION across subtasks
     gate0_handoffs: devops_input.gate0_handoffs      # ARRAY of subtask handoffs
     new_dependencies: devops_input.new_dependencies
     new_env_vars: devops_input.new_env_vars
     new_services: devops_input.new_services
     existing_dockerfile: devops_input.existing_dockerfile
     existing_compose: devops_input.existing_compose

   The skill handles:
   - Dispatching ring:devops-engineer agent
   - Dockerfile creation/update
   - docker-compose.yml configuration
   - .env.example documentation
   - Verification commands execution
   - Fix iteration loop (max 3 attempts)

3. Parse skill output for results:
   
   Expected output sections:
   - "## DevOps Summary" → status, iterations
   - "## Files Changed" → Dockerfile, docker-compose, .env.example actions
   - "## Verification Results" → build, startup, health checks
   - "## Handoff to Next Gate" → ready_for_sre: YES/no
   
   if skill output contains "Status: PASS" and "Ready for Gate 2: YES":
     → Gate 1 PASSED. Proceed to Step 3.3.
   
   if skill output contains "Status: FAIL" or "Ready for Gate 2: no":
     → Gate 1 BLOCKED.
     → Skill already dispatched fixes to ring:devops-engineer
     → Skill already re-ran verification
     → If "ESCALATION" in output: STOP and report to user

4. **MANDATORY: ⛔ Save state to file — Write tool → [state.state_path]**
```

### Step 3.2.1: Docker Security Audit

```text
After ring:dev-devops PASSES, run Docker Hub Health Score compliance audit
on the created/updated Dockerfile:

   Skill("ring:dev-docker-security") with input:
     dockerfile_path: [extract from devops "## Files Changed" table, or default to "Dockerfile"]
     language: devops_input.language
     service_type: devops_input.service_type
     mode: "audit"

   The skill validates:
   - Non-root USER directive
   - Minimal base image (distroless/alpine)
   - No AGPL v3 license risk
   - Supply chain attestations in pipeline
   - Audit checklist compliance

   if skill output contains "Result: PASS":
     → Proceed to Step 3.3.

   if skill output contains "Result: FAIL":
     → Re-dispatch ring:devops-engineer with the failing policies
     → Re-run ring:dev-docker-security audit
     → Max 3 total attempts (2 retries). If still FAIL: STOP and report to user
```

### Step 3.3: Gate 1 Complete

```text
5. When ring:dev-devops skill returns PASS:
   
   Parse from skill output:
   - status: extract from "## DevOps Summary"
   - dockerfile_action: extract from "## Files Changed" table
   - compose_action: extract from "## Files Changed" table
   - verification_passed: extract from "## Verification Results"
   
   - agent_outputs.devops = {
       skill: "ring:dev-devops",
       output: "[full skill output]",
       artifacts_created: ["Dockerfile", "docker-compose.yml", ".env.example"],
       verification_passed: true,
       timestamp: "[ISO timestamp]",
       duration_ms: [execution time]
     }

6. Update state:
   - gate_progress.devops.status = "completed"
   - gate_progress.devops.artifacts = [list from skill output]

7. Proceed to Gate 2
```

### Gate 1 Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Dockerfile exists, skip other artifacts" | all artifacts required. 1/4 ≠ complete. | **Create all artifacts** |
| "docker-compose not needed locally" | docker-compose is MANDATORY for local dev. | **Create docker-compose.yml** |
| "Makefile is optional" | Makefile is MANDATORY for standardized commands. | **Create Makefile** |
| ".env.example can be added later" | .env.example documents required config NOW. | **Create .env.example** |
| "Small service doesn't need all this" | Size is irrelevant. Standards apply uniformly. | **Create all artifacts** |

