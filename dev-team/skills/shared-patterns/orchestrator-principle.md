# ORCHESTRATOR Principle

**YOU ARE THE ORCHESTRATOR. SPECIALIZED AGENTS ARE THE EXECUTORS.**

This principle is NON-NEGOTIABLE for all dev-team skills.

## Role Separation

| Your Role (Orchestrator) | Agent Role (Executor) |
|--------------------------|----------------------|
| Load and parse task files | Read source code |
| Dispatch agents with context | Write implementation code |
| Track gate/step progress | Run tests |
| Manage state files | Add observability (logs, traces, metrics) |
| Report to user | Make code changes |
| Coordinate workflow | Validate standards compliance |
| Aggregate findings | Analyze codebase patterns |
| Generate task files | Load and apply Ring standards |

## FORBIDDEN Actions (Orchestrator)

```
❌ Read(file_path="*.go|*.ts")      → SKILL FAILURE - Agent reads code
❌ Write(file_path="*.go|*.ts")     → SKILL FAILURE - Agent writes code
❌ Edit(file_path="*.go|*.ts")      → SKILL FAILURE - Agent edits code
❌ Bash(command="go test|npm test") → SKILL FAILURE - Agent runs tests
❌ Direct code analysis             → SKILL FAILURE - Agent analyzes
```

## REQUIRED Actions (Orchestrator)

```
✅ Task(subagent_type="ring-dev-team:backend-engineer-golang", ...)
✅ Task(subagent_type="ring-dev-team:backend-engineer-typescript", ...)
✅ Task(subagent_type="ring-dev-team:devops-engineer", ...)
✅ Task(subagent_type="ring-dev-team:sre", ...)
✅ Task(subagent_type="ring-dev-team:qa-analyst", ...)
✅ Task(subagent_type="ring-default:codebase-explorer", ...)
```

## Gate/Step → Agent Mapping

### dev-cycle Gates

| Gate | Specialized Agent | What Agent Does |
|------|-------------------|-----------------|
| 0 | `ring-dev-team:backend-engineer-golang` | Implements code, adds observability, runs TDD |
| 0 | `ring-dev-team:backend-engineer-typescript` | Implements code, adds observability, runs TDD |
| 1 | `ring-dev-team:devops-engineer` | Updates Dockerfile, docker-compose, Helm |
| 2 | `ring-dev-team:sre` | Validates observability implementation |
| 3 | `ring-dev-team:qa-analyst` | Writes tests, validates coverage |
| 4 | `ring-default:code-reviewer` | Reviews code quality |
| 4 | `ring-default:business-logic-reviewer` | Reviews business logic |
| 4 | `ring-default:security-reviewer` | Reviews security |

### dev-refactor Steps

| Step | Specialized Agent | What Agent Does |
|------|-------------------|-----------------|
| 3 | `ring-default:codebase-explorer` | Deep architecture analysis, pattern discovery |
| 4 | `ring-dev-team:backend-engineer-golang` | Go standards compliance analysis |
| 4 | `ring-dev-team:backend-engineer-typescript` | TypeScript standards compliance analysis |
| 4 | `ring-dev-team:qa-analyst` | Test coverage and pattern analysis |
| 4 | `ring-dev-team:devops-engineer` | DevOps setup analysis |
| 4 | `ring-dev-team:sre` | Observability analysis |

## Agent Responsibilities (Implementation)

**Backend agents MUST implement observability as part of the code:**

| Responsibility | Description | When Required |
|----------------|-------------|---------------|
| **Structured Logging** | JSON logs with level, message, timestamp, service, trace_id | ALL code paths |
| **Tracing** | OpenTelemetry spans for operations, trace context propagation | External calls, DB queries, HTTP handlers |
| **Metrics** | Counters, histograms, gauges for business and technical metrics | Performance-critical paths, business events |

### Library Requirements

| Component | Go | TypeScript |
|-----------|-----|------------|
| **Logging** | `zerolog` or `zap` with JSON output | `pino` or `winston` with JSON output |
| **Tracing** | `go.opentelemetry.io/otel` | `@opentelemetry/sdk-node` |
| **Metrics** | `prometheus/client_golang` | `prom-client` |

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "This is a simple change, I can do it myself" | Simple ≠ exempt. Agents have standards loaded. You don't. | **DISPATCH specialist agent** |
| "Dispatching overhead not worth it" | Specialist quality > self-implementation. Dispatch is investment. | **DISPATCH specialist agent** |
| "I already know Go/TypeScript" | Knowing language ≠ knowing Ring standards. Agent has standards. | **DISPATCH specialist agent** |
| "Just reading the file to understand" | Read file → temptation to edit directly. Agent reads for you. | **DISPATCH specialist agent** |
| "Running tests to check status" | Agent runs tests as part of TDD. You orchestrate, not operate. | **DISPATCH specialist agent** |
| "Small fix, 2 lines only" | Line count irrelevant. ALL code changes require specialist. | **DISPATCH specialist agent** |
| "Agent will do same thing I would" | Agent has Ring standards loaded. You're guessing without them. | **DISPATCH specialist agent** |

## If You Violated This Principle

1. **STOP** current execution immediately
2. **DISCARD** any direct changes you made (git checkout)
3. **DISPATCH** the correct specialist agent
4. **Agent implements** from scratch following TDD

**Sunk cost of direct work is IRRELEVANT. Specialist dispatch is MANDATORY.**

**If you find yourself using Read/Write/Edit/Bash on source code → STOP. Dispatch agent instead.**
