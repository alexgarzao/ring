# Ring Marketplace Manual

Quick reference guide for the Ring skills library and workflow system. This monorepo provides 5 plugins with 56 skills, 24 agents, and 22 slash commands for enforcing proven software engineering practices across the entire software delivery value chain.

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              MARKETPLACE (5 PLUGINS)                               │
│                     (monorepo: .claude-plugin/marketplace.json)                    │
│                                                                                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│  │ ring-default  │  │ ring-dev-team │  │ ring-pm-team  │  │ring-finops-   │      │
│  │  Skills(24)   │  │  Skills(9)    │  │  Skills(10)   │  │  team         │      │
│  │  Agents(7)    │  │  Agents(9)    │  │  Agents(3)    │  │  Skills(6)    │      │
│  │  Cmds(12)     │  │  Cmds(5)      │  │  Cmds(2)      │  │  Agents(2)    │      │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘      │
│  ┌───────────────┐                                                                │
│  │ ring-tw-team  │                                                                │
│  │  Skills(7)    │                                                                │
│  │  Agents(3)    │                                                                │
│  │  Cmds(3)      │                                                                │
│  └───────────────┘                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘

                              HOW IT WORKS
                              ────────────

    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │   SESSION    │         │    USER      │         │  CLAUDE CODE │
    │    START     │────────▶│   PROMPT     │────────▶│   WORKING    │
    └──────────────┘         └──────────────┘         └──────────────┘
           │                        │                        │
           ▼                        ▼                        ▼
    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │    HOOKS     │         │   COMMANDS   │         │    SKILLS    │
    │ auto-inject  │         │ user-invoked │         │ auto-applied │
    │   context    │         │  /ring:...   │         │  internally  │
    └──────────────┘         └──────────────┘         └──────────────┘
           │                        │                        │
           │                        ▼                        │
           │                 ┌──────────────┐                │
           └────────────────▶│    AGENTS    │◀───────────────┘
                             │  dispatched  │
                             │  for work    │
                             └──────────────┘

                            COMPONENT ROLES
                            ───────────────

    ┌────────────┬──────────────────────────────────────────────────┐
    │ Component  │ Purpose                                          │
    ├────────────┼──────────────────────────────────────────────────┤
    │ MARKETPLACE│ Monorepo containing all plugins                  │
    │ PLUGIN     │ Self-contained package (skills+agents+commands)  │
    │ HOOK       │ Auto-runs at session events (injects context)    │
    │ SKILL      │ Workflow pattern (Claude Code uses internally)   │
    │ COMMAND    │ User-invokable action (/ring:codereview)         │
    │ AGENT      │ Specialized subprocess (Task tool dispatch)      │
    └────────────┴──────────────────────────────────────────────────┘
```

---

## 🎯 Quick Start

Ring is auto-loaded at session start. Three ways to invoke Ring capabilities:

1. **Slash Commands** – `/command-name`
2. **Skills** – `Skill tool: "ring:skill-name"`
3. **Agents** – `Task tool with subagent_type: "ring:agent-name"`

---

## 📋 Slash Commands

Commands are invoked directly: `/command-name`.

### Project & Feature Workflows

| Command | Use Case | Example |
|---------|----------|---------|
| `/ring:brainstorm [topic]` | Interactive design refinement before coding | `/ring:brainstorm user-authentication` |
| `/ring:explore-codebase [path]` | Autonomous two-phase codebase exploration | `/ring:explore-codebase payment/` |
| `/ring:interview-me [topic]` | Proactive requirements gathering interview | `/ring:interview-me auth-system` |
| `/ring:release-guide` | Generate step-by-step release instructions | `/ring:release-guide` |
| `/ring:pre-dev-feature [name]` | Plan simple features (<2 days) – 3 gates | `/ring:pre-dev-feature logout-button` |
| `/ring:pre-dev-full [name]` | Plan complex features (≥2 days) – 8 gates | `/ring:pre-dev-full payment-system` |
| `/ring:worktree [branch-name]` | Create isolated git workspace | `/ring:worktree auth-system` |
| `/ring:write-plan [feature]` | Generate detailed task breakdown | `/ring:write-plan dashboard-redesign` |
| `/ring:execute-plan [path]` | Execute plan in batches with checkpoints | `/ring:execute-plan docs/pre-dev/feature/tasks.md` |

### Code & Integration Workflows

| Command | Use Case | Example |
|---------|----------|---------|
| `/ring:codereview [files-or-paths]` | Dispatch 3 parallel code reviewers | `/ring:codereview src/auth/` |
| `/ring:commit [message]` | Create git commit with AI trailers | `/ring:commit "fix(auth): improve token validation"` |
| `/ring:lint [path]` | Run lint and dispatch agents to fix all issues | `/ring:lint src/` |

### Session Management

| Command | Use Case | Example |
|---------|----------|---------|
| `/ring:create-handoff [name]` | Create handoff document before /clear | `/ring:create-handoff auth-refactor` |
| `/ring:resume-handoff [path]` | Resume from handoff after /clear | `/ring:resume-handoff docs/handoffs/auth-refactor/...` |

### Development Cycle (ring-dev-team)

| Command | Use Case | Example |
|---------|----------|---------|
| `/ring:dev-cycle [task]` | Start 6-gate development workflow | `/ring:dev-cycle "implement user auth"` |
| `/ring:dev-refactor [path]` | Analyze codebase against standards | `/ring:dev-refactor src/` |
| `/ring:dev-status` | Show current gate progress | `/ring:dev-status` |
| `/ring:dev-report` | Generate development cycle report | `/ring:dev-report` |
| `/ring:dev-cancel` | Cancel active development cycle | `/ring:dev-cancel` |

### Technical Writing (Documentation)

| Command | Use Case | Example |
|---------|----------|---------|
| `/ring:write-guide [topic]` | Start writing a functional guide | `/ring:write-guide authentication` |
| `/ring:write-api [endpoint]` | Start writing API documentation | `/ring:write-api POST /accounts` |
| `/ring:review-docs [file]` | Review documentation for quality | `/ring:review-docs docs/guide.md` |

---

## 💡 About Skills

Skills (56) are workflows that Claude Code invokes automatically when it detects they're applicable. They handle testing, debugging, verification, planning, and code review enforcement. You don't call them directly – Claude Code uses them internally to enforce best practices.

Examples: ring:test-driven-development, ring:systematic-debugging, ring:requesting-code-review, verification-before-completion, etc.

### Skill Selection Criteria

Each skill has structured frontmatter that helps Claude Code determine which skill to use:

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | WHAT the skill does | "Four-phase debugging framework..." |
| `trigger` | WHEN to use (specific conditions) | "Bug reported", "Test failure observed" |
| `skip_when` | WHEN NOT to use (exclusions) | "Root cause already known → just fix it" |
| `sequence` | Workflow ordering (optional) | `after: [prd-creation]` |
| `related` | Similar/complementary skills | `similar: [root-cause-tracing]` |

**How Claude Code chooses skills:**
1. Checks `trigger` conditions against current context
2. Uses `skip_when` to differentiate from similar skills
3. Considers `sequence` for workflow ordering
4. References `related` for disambiguation when multiple skills match

---

## 🤖 Available Agents

Invoke via `Task tool with subagent_type: "..."`.

### Code Review (ring-default)

**Always dispatch all 5 in parallel** (single message, 5 Task calls):

| Agent | Purpose | Model |
|-------|---------|-------|
| `ring:code-reviewer` | Architecture, patterns, maintainability | Opus |
| `ring:business-logic-reviewer` | Domain correctness, edge cases, requirements | Opus |
| `ring:security-reviewer` | Vulnerabilities, OWASP, auth, validation | Opus |
| `ring:test-reviewer` | Test coverage, quality, and completeness | Opus |
| `ring:nil-safety-reviewer` | Nil/null pointer safety analysis | Opus |

**Example:** Before merging, run all 5 parallel reviewers via `/ring:codereview src/`

### Planning & Analysis (ring-default)

| Agent | Purpose | Model |
|-------|---------|-------|
| `ring:write-plan` | Generate implementation plans for zero-context execution | Opus |
| `ring:codebase-explorer` | Deep architecture analysis (vs `Explore` for speed) | Opus |

### Developer Specialists (ring-dev-team)

Use when you need expert depth in specific domains:

| Agent | Specialization | Technologies |
|-------|----------------|--------------|
| `ring:backend-engineer-golang` | Go microservices & APIs | Fiber, gRPC, PostgreSQL, MongoDB, Kafka, OAuth2 |
| `ring:backend-engineer-typescript` | TypeScript/Node.js backend | Express, NestJS, Prisma, TypeORM, GraphQL |
| `ring:devops-engineer` | Infrastructure & CI/CD | Docker, Kubernetes, Terraform, GitHub Actions |
| `ring:frontend-bff-engineer-typescript` | BFF & React/Next.js frontend | Next.js API Routes, Clean Architecture, DDD, React |
| `ring:frontend-designer` | Visual design & aesthetics | Typography, motion, CSS, distinctive UI |
| `ring:frontend-engineer` | General frontend development | React, TypeScript, CSS, component architecture |
| `ring:prompt-quality-reviewer` | AI prompt quality review | Prompt engineering, clarity, effectiveness |
| `ring:qa-analyst` | Quality assurance | Test strategy, automation, coverage |
| `ring:sre` | Site reliability & ops | Monitoring, alerting, incident response, SLOs |

**Standards Compliance Output:** All ring-dev-team agents include a `## Standards Compliance` output section with conditional requirement:

| Invocation Context | Standards Compliance | Trigger |
|--------------------|---------------------|---------|
| Direct agent call | Optional | N/A |
| Via `ring:dev-cycle` | Optional | N/A |
| Via `ring:dev-refactor` | **MANDATORY** | Prompt contains `**MODE: ANALYSIS ONLY**` |

**How it works:**
1. `ring:dev-refactor` dispatches agents with `**MODE: ANALYSIS ONLY**` in prompt
2. Agents detect this pattern and load Ring standards via WebFetch
3. Agents produce comparison tables: Current Pattern vs Expected Pattern
4. Output includes severity, location, and migration recommendations

**Example output when non-compliant:**
```markdown
## Standards Compliance

| Category | Current | Expected | Status | Location |
|----------|---------|----------|--------|----------|
| Logging | fmt.Println | lib-commons/zap | ⚠️ | service/*.go |
```

**Cross-references:** CLAUDE.md (Standards Compliance section), `dev-team/skills/dev-refactor/SKILL.md`

### Product Planning Research (ring-pm-team)

For best practices research and repository analysis:

| Agent | Purpose | Use For |
|-------|---------|---------|
| `ring:best-practices-researcher` | Best practices research | Industry patterns, framework standards |
| `ring:framework-docs-researcher` | Framework documentation research | Official docs, API references, examples |
| `ring:repo-research-analyst` | Repository analysis | Codebase patterns, structure analysis |

### Technical Writing (ring-tw-team)

For documentation creation and review:

| Agent | Purpose | Use For |
|-------|---------|---------|
| `functional-writer` | Functional documentation | Guides, tutorials, conceptual docs |
| `api-writer` | API reference documentation | Endpoints, schemas, examples |
| `docs-reviewer` | Documentation quality review | Voice, tone, structure, completeness |

### Regulatory & FinOps (ring-finops-team)

For Brazilian financial compliance workflows:

| Agent | Purpose | Use For |
|-------|---------|---------|
| `finops-analyzer` | Regulatory compliance analysis | Field mapping, BACEN/RFB validation (Gates 1-2) |
| `finops-automation` | Template generation | Create .tpl files (Gate 3) |

---

## 📖 Common Workflows

### New Feature Development

1. **Design** → `/ring:brainstorm feature-name`
2. **Plan** → `/ring:pre-dev-feature feature-name` (or `ring:pre-dev-full` if complex)
3. **Isolate** → `/ring:worktree feature-branch`
4. **Implement** → Use `ring:test-driven-development` skill
5. **Review** → `/ring:codereview src/` (dispatches 3 reviewers)
6. **Commit** → `/ring:commit "message"`

### Bug Investigation

1. **Investigate** → Use `ring:systematic-debugging` skill
2. **Trace** → Use `ring:root-cause-tracing` if needed
3. **Implement** → Use `ring:test-driven-development` skill
4. **Verify** → Use `ring:verification-before-completion` skill
5. **Review & Merge** → `/ring:codereview` + `/ring:commit`

### Code Review

```
/ring:codereview [files-or-paths]
    ↓
Runs in parallel:
  • ring:code-reviewer (Opus)
  • ring:business-logic-reviewer (Opus)
  • ring:security-reviewer (Opus)
  • ring:test-reviewer (Opus)
  • ring:nil-safety-reviewer (Opus)
    ↓
Consolidated report with recommendations
```

---

## 🎓 Mandatory Rules

These enforce quality standards:

1. **TDD is enforced** – Test must fail (RED) before implementation
2. **Skill check is mandatory** – Use `ring:using-ring` before any task
3. **Reviewers run parallel** – Never sequential review (use `/ring:codereview`)
4. **Verification required** – Don't claim complete without evidence
5. **No incomplete code** – No "TODO" or placeholder comments
6. **Error handling required** – Don't ignore errors

---

## 💡 Best Practices

### Command Selection

| Situation | Use This |
|-----------|----------|
| New feature, unsure about design | `/ring:brainstorm` |
| Feature will take < 2 days | `/ring:pre-dev-feature` |
| Feature will take ≥ 2 days or has complex dependencies | `/ring:pre-dev-full` |
| Need implementation tasks | `/ring:write-plan` |
| Before merging code | `/ring:codereview` |


### Agent Selection

| Need | Agent to Use |
|------|-------------|
| General code quality review | 3 parallel reviewers via `/ring:codereview` |
| Implementation planning | `ring:write-plan` |
| Deep codebase analysis | `ring:codebase-explorer` |
| Go backend expertise | `ring:backend-engineer-golang` |
| TypeScript/Node.js backend | `ring:backend-engineer-typescript` |
| Infrastructure/DevOps | `ring:devops-engineer` |
| React/Next.js frontend & BFF | `ring:frontend-bff-engineer-typescript` |
| General frontend development | `ring:frontend-engineer` |
| Visual design & aesthetics | `ring:frontend-designer` |
| AI prompt quality review | `ring:prompt-quality-reviewer` |
| Quality assurance & testing | `ring:qa-analyst` |
| Site reliability & operations | `ring:sre` |
| Best practices research | `ring:best-practices-researcher` |
| Framework documentation research | `ring:framework-docs-researcher` |
| Repository analysis | `ring:repo-research-analyst` |
| Functional documentation (guides) | `functional-writer` |
| API reference documentation | `api-writer` |
| Documentation quality review | `docs-reviewer` |
| Regulatory compliance analysis | `finops-analyzer` |
| Regulatory template generation | `finops-automation` |

---

## 🔧 How Ring Works

### Session Startup

1. SessionStart hook runs automatically
2. All 56 skills are auto-discovered and available
3. `ring:using-ring` workflow is activated (skill checking is now mandatory)

### Agent Dispatching

```
Task tool:
  subagent_type: "ring:code-reviewer"
  model: "opus"
  prompt: [context]
    ↓
Runs agent with Opus model
    ↓
Returns structured output per agent's output_schema
```

### Parallel Review Pattern

```
Single message with 3 Task calls (not sequential):

Task #1: ring:code-reviewer
Task #2: ring:business-logic-reviewer
Task #3: ring:security-reviewer
    ↓
All run in parallel (saves ~15 minutes vs sequential)
    ↓
Consolidated report
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RING_ALLOW_UNVERIFIED` | `false` | Bypass binary checksum verification (development only) |
| `CLAUDE_PLUGIN_ROOT` | (auto) | Path to installed plugin directory |

> **Security Note:** Setting `RING_ALLOW_UNVERIFIED=true` disables checksum verification for codereview binaries. Only use in development environments where you trust the binary source.

---

## 📚 More Information

- **Full Documentation** → `default/skills/*/SKILL.md` files
- **Agent Definitions** → `default/agents/*.md` files
- **Commands** → `default/commands/*.md` files
- **Plugin Config** → `.claude-plugin/marketplace.json`
- **CLAUDE.md** → Project-specific instructions (checked into repo)

---

## ❓ Need Help?

- **How to use Claude Code?** → Ask about Claude Code features, MCP servers, slash commands
- **How to use Ring?** → Check skill names in this manual or in `ring:using-ring` skill
- **Feature/bug tracking?** → https://github.com/lerianstudio/ring/issues
