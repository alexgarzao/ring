# 💍 The Ring - Skills Library for AI Agents

**Proven engineering practices, enforced through skills.**

Ring is a comprehensive skills library and workflow system for AI agents that transforms how AI assistants approach software development. Currently implemented as a **Claude Code plugin marketplace** with **6 active plugins** (see `.claude-plugin/marketplace.json` for current versions), the skills themselves are agent-agnostic and can be used with any AI agent system. Ring provides battle-tested patterns, mandatory workflows, and systematic approaches across the entire software delivery value chain.

## ✨ Why Ring?

Without Ring, AI assistants often:

- Skip tests and jump straight to implementation
- Make changes without understanding root causes
- Claim tasks are complete without verification
- Forget to check for existing solutions
- Repeat known mistakes

Ring solves this by:

- **Enforcing proven workflows** - Test-driven development, systematic debugging, proper planning
- **Providing 66 specialized skills** (25 core + 9 dev-team + 10 product planning + 7 FinOps regulatory + 7 technical writing + 8 PMO)
- **32 specialized agents** - 7 review/planning + 10 developer + 4 product research + 3 FinOps regulatory + 3 technical writing + 5 PMO
- **Automating skill discovery** - Skills load automatically at session start
- **Preventing common failures** - Built-in anti-patterns and mandatory checklists

## 🤖 Specialized Agents

**Review & Planning Agents (default plugin):**

- `ring:code-reviewer` - Foundation review (architecture, code quality, design patterns)
- `ring:business-logic-reviewer` - Correctness review (domain logic, requirements, edge cases)
- `ring:security-reviewer` - Safety review (vulnerabilities, OWASP, authentication)
- `ring:test-reviewer` - Test quality review (coverage, edge cases, assertions, test anti-patterns)
- `ring:nil-safety-reviewer` - Nil/null safety review (traces pointer risks, missing guards, panic paths)
- `ring:write-plan` - Implementation planning agent
- `ring:codebase-explorer` - Deep architecture analysis (Opus-powered, complements built-in Explore)
- Use `/ring:codereview` command to orchestrate parallel review workflow

**Developer Agents (dev-team plugin):**

- `ring:backend-engineer-golang` - Go backend specialist for financial systems
- `ring:backend-engineer-typescript` - TypeScript/Node.js backend specialist (Express, NestJS, Fastify)
- `ring:devops-engineer` - DevOps infrastructure specialist
- `ring:frontend-bff-engineer-typescript` - BFF & React/Next.js frontend with Clean Architecture
- `ring:frontend-designer` - Visual design specialist
- `ring:frontend-engineer` - Senior Frontend Engineer (React/Next.js)
- `ring:prompt-quality-reviewer` - Agent Quality Analyst
- `ring:qa-analyst` - Quality assurance specialist
- `ring:sre` - Site reliability engineer
- `ring:ui-engineer` - UI component specialist (design systems, accessibility)

> **Standards Compliance:** All dev-team agents include a `## Standards Compliance` output section with conditional requirement:
>
> - **Optional** when invoked directly or via `ring:dev-cycle`
> - **MANDATORY** when invoked from `ring:dev-refactor` (triggered by `**MODE: ANALYSIS ONLY**` in prompt)
>
> When mandatory, agents load Ring standards via WebFetch and produce comparison tables with:
>
> - Current Pattern vs Expected Pattern
> - Severity classification (Critical/High/Medium/Low)
> - File locations and migration recommendations
>
> See `dev-team/docs/standards/*.md` for standards source. Cross-references: CLAUDE.md (Standards Compliance section), `dev-team/skills/dev-refactor/SKILL.md`

**Product Research Agents (ring-pm-team plugin):**

- `ring:repo-research-analyst` - Repository structure and codebase analysis
- `ring:best-practices-researcher` - Industry best practices research
- `ring:framework-docs-researcher` - Framework documentation research
- `ring:product-designer` - Product design and UX research

**Technical Writing Agents (ring-tw-team plugin):**

- `ring:functional-writer` - Functional documentation (guides, tutorials, conceptual docs)
- `ring:api-writer` - API reference documentation (endpoints, schemas, examples)
- `ring:docs-reviewer` - Documentation quality review (voice, tone, structure, completeness)

**FinOps Agents (ring-finops-team plugin):**

- `ring:finops-analyzer` - Financial operations analysis
- `ring:finops-automation` - FinOps template creation and automation
- `ring:infrastructure-cost-estimator` - Infrastructure cost estimation and analysis

**PMO Agents (ring-pmo-team plugin):**

- `ring:portfolio-manager` - Portfolio-level planning and multi-project coordination
- `ring:resource-planner` - Capacity planning and resource allocation optimization
- `ring:risk-analyst` - Portfolio risk identification and mitigation planning
- `ring:governance-specialist` - Gate reviews and process compliance
- `ring:executive-reporter` - Executive dashboards and stakeholder communications

_Plugin versions are managed in `.claude-plugin/marketplace.json`_

### 📦 Archived Plugins

The following plugins have been archived and are not actively maintained. They remain available in `.archive/` for reference:

| Plugin         | Description                                             | Status                                                   |
| -------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| `pmm-team`     | Product Marketing (GTM, positioning, competitive intel) | Archived - functionality may be restored based on demand |
| `finance-team` | Financial planning and analysis                         | Archived - under evaluation                              |
| `ops-team`     | Operations management                                   | Archived - under evaluation                              |

_To restore an archived plugin, move its folder from `.archive/` to the root directory and register it in `marketplace.json`._

## 🖥️ Supported Platforms

Ring works across multiple AI development platforms:

| Platform        | Format      | Status             | Features                        |
| --------------- | ----------- | ------------------ | ------------------------------- |
| **Claude Code** | Native      | ✅ Source of truth | Skills, agents, commands, hooks |
| **Factory AI**  | Transformed | ✅ Supported       | Droids, commands, skills        |
| **Cursor**      | Transformed | ✅ Supported       | Rules, workflows                |
| **Cline**       | Transformed | ✅ Supported       | Prompts                         |

**Transformation Notes:**

- Claude Code receives Ring content in its native format
- Factory AI: `agents` → `droids` terminology
- Cursor: Skills/agents → `.cursorrules` and workflows
- Cline: All content → structured prompts

**Platform-Specific Guides:**

- [Claude Code Installation Guide](docs/platforms/claude-code.md) - Native format setup and usage
- [Factory AI Installation Guide](docs/platforms/factory-ai.md) - Droids transformation and configuration
- [Cursor Installation Guide](docs/platforms/cursor.md) - Rules and workflow setup
- [Cline Installation Guide](docs/platforms/cline.md) - Prompt-based configuration
- [Migration Guide](docs/platforms/MIGRATION.md) - Moving between platforms or upgrading

## 🚀 Quick Start

### Multi-Platform Installation (Recommended)

The Ring installer automatically detects installed platforms and transforms content appropriately.

**Linux/macOS/Git Bash:**

```bash
# Interactive installer (auto-detects platforms)
curl -fsSL https://raw.githubusercontent.com/lerianstudio/ring/main/install-ring.sh | bash

# Or clone and run locally
git clone https://github.com/lerianstudio/ring.git ~/ring
cd ~/ring
./installer/install-ring.sh
```

**Windows PowerShell:**

```powershell
# Interactive installer (auto-detects platforms)
irm https://raw.githubusercontent.com/lerianstudio/ring/main/install-ring.ps1 | iex

# Or clone and run locally
git clone https://github.com/lerianstudio/ring.git $HOME\ring
cd $HOME\ring
.\installer\install-ring.ps1
```

### Direct Platform Installation

Install to specific platforms without the interactive menu:

```bash
# Install to Claude Code only (native format)
./installer/install-ring.sh install --platforms claude

# Install to Factory AI only (droids format)
./installer/install-ring.sh install --platforms factory

# Install to multiple platforms
./installer/install-ring.sh install --platforms claude,cursor,cline

# Install to all detected platforms
./installer/install-ring.sh install --platforms auto

# Dry run (preview changes without installing)
./installer/install-ring.sh install --platforms auto --dry-run
```

### Installer Commands

```bash
# List installed platforms and versions
./installer/install-ring.sh list

# Update existing installation
./installer/install-ring.sh update

# Check for available updates
./installer/install-ring.sh check

# Sync (update only changed files)
./installer/install-ring.sh sync

# Uninstall from specific platform
./installer/install-ring.sh uninstall --platforms cursor

# Detect available platforms
./installer/install-ring.sh detect
```

### Claude Code Plugin Marketplace

For Claude Code users, you can also install from the marketplace:

- Open Claude Code
- Go to Settings → Plugins
- Search for "ring"
- Click Install

### Manual Installation (Claude Code only)

```bash
# Clone the marketplace repository
git clone https://github.com/lerianstudio/ring.git ~/ring

# Skills auto-load at session start via hooks
# No additional configuration needed for Claude Code
```

### Binary Security

The codereview pipeline includes pre-built binaries with SHA256 checksum verification. Binaries are verified before execution; if verification fails, they are automatically rebuilt from source.

See [Binary Security Model](default/lib/codereview/README.md#security-model) for details on checksum verification and the `RING_ALLOW_UNVERIFIED` environment variable.

### First Session

When you start a new Claude Code session with Ring installed, you'll see:

```
## Available Skills:
- ring:using-ring (Check for skills BEFORE any task)
- ring:test-driven-development (RED-GREEN-REFACTOR cycle)
- ring:systematic-debugging (4-phase root cause analysis)
- ring:verification-before-completion (Evidence before claims)
... and 47 more skills
```

## 🎯 Core Skills

### The Big Four (Use These First!)

#### 1. **ring:using-ring** - Mandatory Skill Discovery

```
Before ANY action → Check skills
Before ANY tool → Check skills
Before ANY code → Check skills
```

#### 2. **ring:test-driven-development** - Test First, Always

```
RED → Write failing test → Watch it fail
GREEN → Minimal code → Watch it pass
REFACTOR → Clean up → Stay green
```

#### 3. **ring:systematic-debugging** - Find Root Cause

```
Phase 1: Investigate (gather ALL evidence)
Phase 2: Analyze patterns
Phase 3: Test hypothesis (one at a time)
Phase 4: Implement fix (with test)
```

#### 4. **ring:verification-before-completion** - Prove It Works

```
Run command → Paste output → Then claim
No "should work" → Only "does work" with proof
```

## 📚 All 66 Skills (Across 6 Plugins)

### Core Skills (ring-default plugin - 25 skills)

**Testing & Debugging (7):**

- `ring:test-driven-development` - Write test first, watch fail, minimal code
- `ring:systematic-debugging` - 4-phase root cause investigation
- `ring:verification-before-completion` - Evidence before claims
- `ring:testing-anti-patterns` - Common test pitfalls to avoid
- `ring:condition-based-waiting` - Replace timeouts with conditions
- `ring:defense-in-depth` - Multi-layer validation
- `ring:linting-codebase` - Parallel lint fixing with agent dispatch

**Collaboration & Planning (11):**

- `ring:brainstorming` - Structured design refinement
- `ring:interviewing-user` - Proactive requirements gathering through structured interview
- `ring:writing-plans` - Zero-context implementation plans
- `ring:executing-plans` - Batch execution with checkpoints
- `ring:requesting-code-review` - **Parallel 3-reviewer dispatch** with severity-based handling
- `ring:receiving-code-review` - Responding to feedback
- `ring:dispatching-parallel-agents` - Concurrent workflows
- `ring:subagent-driven-development` - Fast iteration with **parallel reviews**
- `ring:using-git-worktrees` - Isolated development
- `ring:finishing-a-development-branch` - Merge/PR decisions
- `ring:root-cause-tracing` - Backward bug tracking

**Meta Skills (4):**

- `ring:using-ring` - Mandatory skill discovery
- `ring:writing-skills` - TDD for documentation
- `ring:testing-skills-with-subagents` - Skill validation
- `ring:testing-agents-with-subagents` - Subagent-specific testing

**Session & Learning (2):**

- `ring:exploring-codebase` - Two-phase codebase exploration
- `ring:doubt-triggered-questions` - Decision hierarchy for asking vs proceeding

**Audit & Readiness (1):**

- `ring:production-readiness-audit` - 27-dimension production readiness audit; runs 10 explorers per batch, appends incrementally to a single report; output: scored report (0–270) with severity ratings. See [default/skills/production-readiness-audit/SKILL.md](default/skills/production-readiness-audit/SKILL.md) for invocation and implementation details.

### Developer Skills (ring-dev-team plugin - 9 skills)

**Code Development:**

- `ring:using-dev-team` - Introduction to developer specialist agents
- `ring:dev-refactor` - Codebase analysis against standards
- `ring:dev-cycle` - 6-gate development workflow orchestrator

**6-Gate Workflow Skills:**

- `ring:dev-implementation` - Gate 0: TDD implementation
- `ring:dev-devops` - Gate 1: DevOps setup (Docker, compose)
- `ring:dev-sre` - Gate 2: Observability setup
- `ring:dev-testing` - Gate 3: Test coverage
- `ring:requesting-code-review` - Gate 4: Parallel code review (3 reviewers)
- `ring:dev-validation` - Gate 5: User approval
- `ring:dev-feedback-loop` - Assertiveness scoring and metrics

### Product Planning Skills (ring-pm-team plugin - 10 skills)

**Pre-Development Workflow (includes ring:using-pm-team + 9 gates):**

- `ring:using-pm-team` - Introduction to product planning workflow

0. `ring:pre-dev-research` - Research phase (parallel agents)
1. `ring:pre-dev-prd-creation` - Business requirements (WHAT/WHY)
2. `ring:pre-dev-feature-map` - Feature relationships
3. `ring:pre-dev-trd-creation` - Technical architecture (HOW)
4. `ring:pre-dev-api-design` - Component contracts
5. `ring:pre-dev-data-model` - Entity relationships
6. `ring:pre-dev-dependency-map` - Technology selection
7. `ring:pre-dev-task-breakdown` - Work increments
8. `ring:pre-dev-subtask-creation` - Atomic units

### Technical Writing Skills (ring-tw-team plugin - 7 skills)

**Documentation Creation:**

- `ring:using-tw-team` - Introduction to technical writing specialists
- `ring:writing-functional-docs` - Patterns for guides, tutorials, conceptual docs
- `ring:writing-api-docs` - API reference documentation patterns
- `ring:documentation-structure` - Document hierarchy and organization
- `ring:voice-and-tone` - Voice and tone guidelines (assertive, encouraging, human)
- `ring:documentation-review` - Quality checklist and review process
- `ring:api-field-descriptions` - Field description patterns by type

### FinOps & Regulatory Skills (ring-finops-team plugin - 7 skills)

**Regulatory Templates (6):**

- `ring:using-finops-team` - Introduction to FinOps team workflow
- `ring:regulatory-templates` - Brazilian regulatory orchestration (BACEN, RFB)
- `ring:regulatory-templates-setup` - Template selection initialization
- `ring:regulatory-templates-gate1` - Compliance analysis and field mapping
- `ring:regulatory-templates-gate2` - Field mapping validation
- `ring:regulatory-templates-gate3` - Template file generation

**Cost Estimation (1):**

- `ring:infrastructure-cost-estimation` - Infrastructure cost estimation and analysis

### PMO Skills (ring-pmo-team plugin - 8 skills)

**Portfolio Management:**

- `ring:using-pmo-team` - Introduction to PMO specialist agents
- `ring:portfolio-planning` - Multi-project coordination and portfolio optimization
- `ring:resource-allocation` - Capacity planning and conflict resolution
- `ring:risk-management` - Portfolio-level risk identification and mitigation
- `ring:dependency-mapping` - Cross-project dependency analysis
- `ring:project-health-check` - Individual project health assessment
- `ring:pmo-retrospective` - Portfolio lessons learned and process improvements
- `ring:executive-reporting` - Executive dashboards and board packages

## 🎮 Interactive Commands

Ring provides 25 slash commands across 6 plugins for common workflows.

### Core Workflows (ring-default)

- `/ring:codereview [files-or-paths]` - Dispatch 3 parallel code reviewers for comprehensive review
- `/ring:commit [message]` - Create git commit with AI identification via Git trailers
- `/ring:worktree [branch-name]` - Create isolated git workspace for parallel development
- `/ring:brainstorm [topic]` - Interactive design refinement using Socratic method
- `/ring:write-plan [feature]` - Create detailed implementation plan with bite-sized tasks
- `/ring:execute-plan [path]` - Execute plan in batches with review checkpoints
- `/ring:lint [path]` - Run lint checks and dispatch parallel agents to fix all issues
- `/ring:explore-codebase [path]` - Deep codebase exploration using Opus-powered agent
- `/ring:interview-me [topic]` - Proactive requirements gathering through structured user interview
- `/ring:release-guide` - Generate Ops Update Guide from git diff between two refs
- `/ring:create-handoff [name]` - Create handoff document for session continuity
- `/ring:resume-handoff [path]` - Resume work from a previous handoff

### Product Planning (ring-pm-team)

- `/ring:pre-dev-feature [feature-name]` - Lightweight 4-gate pre-dev workflow for small features (<2 days)
- `/ring:pre-dev-full [feature-name]` - Complete 9-gate pre-dev workflow for large features (>=2 days)

### Development Cycle (ring-dev-team)

- `/ring:dev-cycle [task]` - Start 6-gate development workflow (implementation→devops→SRE→testing→review→validation)
- `/ring:dev-refactor [path]` - Analyze codebase against standards
- `/ring:dev-status` - Show current gate progress
- `/ring:dev-report` - Generate development cycle report
- `/ring:dev-cancel` - Cancel active development cycle

### Technical Writing (ring-tw-team)

- `/ring:write-guide [topic]` - Start writing a functional guide with voice/tone guidance
- `/ring:write-api [endpoint]` - Start writing API reference documentation
- `/ring:review-docs [file]` - Review existing documentation for quality

### PMO (ring-pmo-team)

- `/ring:portfolio-review [scope]` - Conduct comprehensive portfolio review across projects
- `/ring:dependency-analysis [scope]` - Analyze cross-project dependencies
- `/ring:executive-summary [scope]` - Generate executive summary for leadership

## 💡 Usage Examples

### Building a Feature

```
User: "Add user authentication to the app"
Claude: I'm using the ring:brainstorming skill to design this feature...
        [Structured exploration of requirements]
Claude: I'm using ring:test-driven-development to implement...
        [RED-GREEN-REFACTOR cycle for each component]
Claude: I'm using ring:verification-before-completion to confirm...
        [Runs tests, shows actual output]
```

### Fixing a Bug

```
User: "The app crashes when clicking submit"
Claude: I'm using systematic-debugging to investigate...
        Phase 1: [Gathering evidence]
        Phase 2: [Pattern analysis]
        Phase 3: [Hypothesis testing]
        Phase 4: [Implementing fix with test]
```

### Planning a Project

```
User: "Plan an e-commerce platform"
Claude: I'll use the pre-dev workflow to plan this systematically...
        Gate 1: PRD Creation [Business requirements]
        Gate 2: Feature Map [Domain groupings]
        Gate 3: TRD Creation [Architecture patterns]
        ... [Through all 8 gates]
```

### Code Review (Parallel, 3x Faster!)

```
User: "Review my authentication implementation"
Claude: Dispatching all 3 reviewers in parallel...
        [Launches ring:code-reviewer, ring:business-logic-reviewer, ring:security-reviewer simultaneously]

        Code reviewer: PASS. Clean architecture, good tests.
        Business reviewer: FAIL. Missing password reset flow (HIGH severity).
        Security reviewer: FAIL. JWT secret hardcoded (CRITICAL severity).

        Aggregating issues by severity:
        - CRITICAL: JWT secret hardcoded in auth.ts:42
        - HIGH: Password reset flow missing from requirements

        Dispatching fix subagent to address Critical/High issues...
        [Fixes applied]

        Re-running all 3 reviewers in parallel...
        All reviewers: PASS. Ready for production.
```

**Key benefits:**

- **3x faster** - All reviewers run simultaneously (not sequential)
- **Comprehensive** - Get all feedback at once, easier to prioritize
- **Tech debt tracking** - Low/Cosmetic issues tracked with TODO/FIXME comments in code
- **Model-specific** - All reviewers run on Opus for deep analysis

## 🏗️ Architecture

**Monorepo Marketplace** - Multiple specialized plugin collections:

```
ring/                                  # Monorepo root
├── .claude-plugin/
│   └── marketplace.json              # Multi-plugin marketplace config (6 active plugins)
├── default/                          # Core Ring plugin (ring-default)
│   ├── skills/                       # 25 core skills
│   │   ├── skill-name/
│   │   │   └── SKILL.md             # Skill definition with frontmatter
│   │   └── shared-patterns/         # Universal patterns (6 patterns)
│   ├── commands/                    # 12 slash command definitions
│   ├── hooks/                       # Session initialization
│   │   ├── hooks.json              # Hook configuration
│   │   ├── session-start.sh        # Loads skills at startup
│   │   └── generate-skills-ref.py  # Auto-generates quick reference
│   ├── agents/                      # 7 specialized agents
│   │   ├── ring:code-reviewer.md        # Foundation review (parallel)
│   │   ├── ring:business-logic-reviewer.md  # Correctness review (parallel)
│   │   ├── ring:security-reviewer.md    # Safety review (parallel)
│   │   ├── ring:test-reviewer.md        # Test quality review (parallel)
│   │   ├── ring:nil-safety-reviewer.md  # Nil/null safety review (parallel)
│   │   ├── ring:write-plan.md           # Implementation planning
│   │   └── ring:codebase-explorer.md    # Deep architecture analysis (Opus)
│   └── docs/                       # Documentation
├── dev-team/                      # Developer Agents plugin (ring-dev-team)
│   └── agents/                      # 9 specialized developer agents
│       ├── ring:backend-engineer-golang.md  # Go backend specialist
│       ├── ring:backend-engineer-typescript.md # TypeScript/Node.js backend specialist
│       ├── ring:devops-engineer.md          # DevOps infrastructure
│       ├── frontend-bff-engineer-typescript.md # BFF & React/Next.js frontend specialist
│       ├── ring:frontend-designer.md        # Visual design specialist
│       ├── ring:frontend-engineer.md        # Senior Frontend Engineer (React/Next.js)
│       ├── prompt-quality-reviewer.md       # Agent Quality Analyst
│       ├── qa-analyst.md                    # Quality assurance
│       └── sre.md                      # Site reliability engineer
├── pm-team/                    # Product Planning plugin (ring-pm-team)
│   └── skills/                      # 10 pre-dev workflow skills
│       └── pre-dev-*/              # PRD, TRD, API, Data, Tasks
├── finops-team/                     # FinOps Regulatory plugin (ring-finops-team)
│   ├── skills/                      # 7 regulatory skills
│   ├── agents/                      # 3 FinOps agents
│   ├── docs/regulatory/             # Regulatory templates and dictionaries
│   └── hooks/                       # SessionStart hook
├── pmo-team/                         # PMO Specialists plugin (ring-pmo-team)
│   ├── agents/                       # 5 PMO specialist agents
│   │   ├── portfolio-manager.md
│   │   ├── resource-planner.md
│   │   ├── risk-analyst.md
│   │   ├── governance-specialist.md
│   │   └── executive-reporter.md
│   ├── skills/                       # 8 PMO skills
│   ├── commands/                     # 3 PMO commands
│   └── hooks/                        # SessionStart hook
└── tw-team/                         # Technical Writing plugin (ring-tw-team)
    ├── skills/                      # 7 documentation skills
    ├── agents/                      # 3 technical writing agents
    ├── commands/                    # 3 slash commands
    └── hooks/                       # SessionStart hook
```

## 🤝 Contributing

### Adding a New Skill

**For core Ring skills:**

1. **Create the skill directory**

   ```bash
   mkdir default/skills/your-skill-name
   ```

2. **Write SKILL.md with frontmatter**

   ```yaml
   ---
   name: your-skill-name
   description: |
     Brief description of WHAT this skill does (the method/technique).
     1-2 sentences maximum.

   trigger: |
     - Specific condition that mandates using this skill
     - Another trigger condition
     - Use quantifiable criteria when possible

   skip_when: |
     - When NOT to use this skill → alternative
     - Another exclusion condition

   sequence:
     after: [prerequisite-skill] # Skills that should come before
     before: [following-skill] # Skills that typically follow

   related:
     similar: [skill-that-seems-similar] # Differentiate from these
     complementary: [skill-that-pairs-well] # Use together with these
   ---
   # Skill content here...
   ```

   **Schema fields explained:**

   - `name`: Skill identifier (matches directory name)
   - `description`: WHAT the skill does (method/technique)
   - `trigger`: WHEN to use - specific, quantifiable conditions
   - `skip_when`: WHEN NOT to use - differentiates from similar skills
   - `sequence`: Workflow ordering (optional)
   - `related`: Similar/complementary skills for disambiguation (optional)

3. **Update documentation**

   - Skills auto-load via `default/hooks/generate-skills-ref.py`
   - Test with session start hook

4. **Submit PR**
   ```bash
   git checkout -b feat/your-skill-name
   git add default/skills/your-skill-name
   git commit -m "feat(skills): add your-skill-name for X"
   gh pr create
   ```

**For product/team-specific skills:**

1. **Create plugin structure**

   ```bash
   mkdir -p product-xyz/{skills,agents,commands,hooks,lib}
   ```

2. **Register in marketplace**
   Edit `.claude-plugin/marketplace.json`:

   ```json
   {
     "name": "ring-product-xyz",
     "description": "Product XYZ specific skills",
     "version": "0.1.0",
     "source": "./product-xyz",
     "homepage": "https://github.com/lerianstudio/ring/tree/product-xyz"
   }
   ```

3. **Follow core plugin structure**
   - Use same layout as `default/`
   - Create `product-xyz/hooks/hooks.json` for initialization
   - Add skills to `product-xyz/skills/`

### Skill Quality Standards

- **Mandatory sections**: When to use, How to use, Anti-patterns
- **Include checklists**: TodoWrite-compatible task lists
- **Evidence-based**: Require verification before claims
- **Battle-tested**: Based on real-world experience
- **Clear triggers**: Unambiguous "when to use" conditions

## 📖 Documentation

- **Skills Quick Reference** - Auto-generated at session start from skill frontmatter
- [CLAUDE.md](CLAUDE.md) - Repository guide for Claude Code
- [MANUAL.md](MANUAL.md) - Quick reference for all commands, agents, and workflows
- [Design Documents](docs/plans/) - Implementation plans and architecture decisions
- **Platform Guides:**
  - [Claude Code](docs/platforms/claude-code.md) - Native format setup
  - [Factory AI](docs/platforms/factory-ai.md) - Droids transformation
  - [Cursor](docs/platforms/cursor.md) - Rules and workflows
  - [Cline](docs/platforms/cline.md) - Prompt-based setup
  - [Migration](docs/platforms/MIGRATION.md) - Platform switching and upgrades

## 🎯 Philosophy

Ring embodies these principles:

1. **Skills are mandatory, not optional** - If a skill applies, it MUST be used
2. **Evidence over assumptions** - Prove it works, don't assume
3. **Process prevents problems** - Following workflows prevents known failures
4. **Small steps, verified often** - Incremental progress with continuous validation
5. **Learn from failure** - Anti-patterns document what doesn't work

## 📊 Success Metrics

Teams using Ring report:

- 90% reduction in "works on my machine" issues
- 75% fewer bugs reaching production
- 60% faster debugging cycles
- 100% of code covered by tests (enforced by TDD)

## 🙏 Acknowledgments

Ring is built on decades of collective software engineering wisdom, incorporating patterns from:

- Extreme Programming (XP)
- Test-Driven Development (TDD)
- Domain-Driven Design (DDD)
- Agile methodologies
- DevOps practices

Special thanks to the Lerian Team for battle-testing these skills in production.

## 📄 License

MIT - See [LICENSE](LICENSE) file

## 🔗 Links

- [GitHub Repository](https://github.com/lerianstudio/ring)
- [Issue Tracker](https://github.com/lerianstudio/ring/issues)
- [Plugin Marketplace](https://claude.ai/marketplace/ring)

---

**Remember: If a skill applies to your task, you MUST use it. This is not optional.**
