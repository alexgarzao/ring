# 💍 The Ring - Skills Library for AI Agents

**Proven engineering practices, enforced through skills.**

Ring is a comprehensive skills library and workflow system for AI agents that transforms how AI assistants approach software development. Currently implemented as a **Claude Code plugin marketplace** with **5 active plugins** (see `.claude-plugin/marketplace.json` for current versions), the skills themselves are agent-agnostic and can be used with any AI agent system. Ring provides battle-tested patterns, mandatory workflows, and systematic approaches across the entire software delivery value chain.

## ✨ Why Ring?

Without Ring, AI assistants often:
- Skip tests and jump straight to implementation
- Make changes without understanding root causes
- Claim tasks are complete without verification
- Forget to check for existing solutions
- Repeat known mistakes

Ring solves this by:
- **Enforcing proven workflows** - Test-driven development, systematic debugging, proper planning
- **Providing 59 specialized skills** (27 core + 9 dev-team + 10 product planning + 6 FinOps regulatory + 7 technical writing)
- **22 specialized agents** - 5 review/planning + 9 developer + 3 product research + 2 FinOps regulatory + 3 technical writing
- **Automating skill discovery** - Skills load automatically at session start
- **Preventing common failures** - Built-in anti-patterns and mandatory checklists

## 🤖 Specialized Agents

**Review & Planning Agents (default plugin):**
- `ring:code-reviewer` - Foundation review (architecture, code quality, design patterns)
- `ring:business-logic-reviewer` - Correctness review (domain logic, requirements, edge cases)
- `ring:security-reviewer` - Safety review (vulnerabilities, OWASP, authentication)
- `ring:write-plan` - Implementation planning agent
- `ring:codebase-explorer` - Deep architecture analysis (Opus-powered, complements built-in Explore)
- Use `/ring:codereview` command to orchestrate parallel review workflow

**Developer Agents (dev-team plugin):**
- `ring:backend-engineer-golang` - Go backend specialist for financial systems
- `ring:backend-engineer-typescript` - TypeScript/Node.js backend specialist (Express, NestJS, Fastify)
- `ring:devops-engineer` - DevOps infrastructure specialist
- `frontend-bff-engineer-typescript` - BFF & React/Next.js frontend with Clean Architecture
- `ring:frontend-designer` - Visual design specialist
- `ring:qa-analyst` - Quality assurance specialist
- `ring:sre` - Site reliability engineer
- `ring:frontend-engineer` - Senior Frontend Engineer (React/Next.js)
- `prompt-quality-reviewer` - Agent Quality Analyst

> **Standards Compliance:** All dev-team agents include a `## Standards Compliance` output section with conditional requirement:
> - **Optional** when invoked directly or via `ring:dev-cycle`
> - **MANDATORY** when invoked from `ring:dev-refactor` (triggered by `**MODE: ANALYSIS ONLY**` in prompt)
>
> When mandatory, agents load Ring standards via WebFetch and produce comparison tables with:
> - Current Pattern vs Expected Pattern
> - Severity classification (Critical/High/Medium/Low)
> - File locations and migration recommendations
>
> See `dev-team/docs/standards/*.md` for standards source. Cross-references: CLAUDE.md (Standards Compliance section), `dev-team/skills/dev-refactor/SKILL.md`

**Technical Writing Agents (ring-tw-team plugin):**
- `functional-writer` - Functional documentation (guides, tutorials, conceptual docs)
- `api-writer` - API reference documentation (endpoints, schemas, examples)
- `docs-reviewer` - Documentation quality review (voice, tone, structure, completeness)

**FinOps Agents (ring-finops-team plugin):**
- `finops-analyzer` - Financial operations analysis
- `finops-automation` - FinOps template creation and automation

*Plugin versions are managed in `.claude-plugin/marketplace.json`*

## 🖥️ Supported Platforms

Ring works across multiple AI development platforms:

| Platform | Format | Status | Features |
|----------|--------|--------|----------|
| **Claude Code** | Native | ✅ Source of truth | Skills, agents, commands, hooks |
| **Factory AI** | Transformed | ✅ Supported | Droids, commands, skills |
| **Cursor** | Transformed | ✅ Supported | Rules, workflows |
| **Cline** | Transformed | ✅ Supported | Prompts |

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

### First Session

When you start a new Claude Code session with Ring installed, you'll see:

```
## Available Skills:
- ring:using-ring (Check for skills BEFORE any task)
- ring:test-driven-development (RED-GREEN-REFACTOR cycle)
- ring:systematic-debugging (4-phase root cause analysis)
- ring:verification-before-completion (Evidence before claims)
... and 50 more skills
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

## 📚 All 59 Skills (Across 5 Plugins)

### Core Skills (ring-default plugin - 27 skills)

**Testing & Debugging (7):**
- `ring:test-driven-development` - Write test first, watch fail, minimal code
- `ring:systematic-debugging` - 4-phase root cause investigation
- `ring:verification-before-completion` - Evidence before claims
- `testing-anti-patterns` - Common test pitfalls to avoid
- `condition-based-waiting` - Replace timeouts with conditions
- `defense-in-depth` - Multi-layer validation
- `ring:linting-codebase` - Parallel lint fixing with agent dispatch

**Collaboration & Planning (11):**
- `brainstorming` - Structured design refinement
- `ring:interviewing-user` - Proactive requirements gathering through structured interview
- `ring:writing-plans` - Zero-context implementation plans
- `ring:executing-plans` - Batch execution with checkpoints
- `ring:requesting-code-review` - **Parallel 3-reviewer dispatch** with severity-based handling
- `ring:receiving-code-review` - Responding to feedback
- `dispatching-parallel-agents` - Concurrent workflows
- `ring:subagent-driven-development` - Fast iteration with **parallel reviews**
- `ring:using-git-worktrees` - Isolated development
- `finishing-a-development-branch` - Merge/PR decisions
- `root-cause-tracing` - Backward bug tracking

**Meta Skills (4):**
- `ring:using-ring` - Mandatory skill discovery
- `ring:writing-skills` - TDD for documentation
- `testing-skills-with-subagents` - Skill validation
- `testing-agents-with-subagents` - Subagent-specific testing

**Session & Learning (5):**
- `ring:handoff-tracking` - Task handoff management and session continuity
- `compound-learnings` - Pattern detection from session history
- `artifact-query` - Semantic search over past artifacts
- `ring:exploring-codebase` - Two-phase codebase exploration
- `doubt-triggered-questions` - Decision hierarchy for asking vs proceeding

### Developer Skills (ring-dev-team plugin - 9 skills)

**Code Development:**
- `ring:using-dev-team` - Introduction to developer specialist agents
- `ring:dev-refactor` - Codebase analysis against standards
- `ring:dev-cycle` - 6-gate development workflow orchestrator

**6-Gate Workflow Skills:**
- `ring:dev-implementation` - Gate 0: TDD implementation
- `ring:dev-devops` - Gate 1: DevOps setup (Docker, compose)
- `ring:dev-ring:sre` - Gate 2: Observability setup
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
- `using-tw-team` - Introduction to technical writing specialists
- `writing-functional-docs` - Patterns for guides, tutorials, conceptual docs
- `writing-api-docs` - API reference documentation patterns
- `documentation-structure` - Document hierarchy and organization
- `voice-and-tone` - Voice and tone guidelines (assertive, encouraging, human)
- `documentation-review` - Quality checklist and review process
- `api-field-descriptions` - Field description patterns by type

### FinOps & Regulatory Skills (ring-finops-team plugin - 6 skills)

**Regulatory Templates (6):**
- `using-finops-team` - Introduction to FinOps team workflow
- `regulatory-templates` - Brazilian regulatory orchestration (BACEN, RFB)
- `regulatory-templates-setup` - Template selection initialization
- `regulatory-templates-gate1` - Compliance analysis and field mapping
- `regulatory-templates-gate2` - Field mapping validation
- `regulatory-templates-gate3` - Template file generation

## 🎮 Interactive Commands

Ring provides 23 slash commands across 5 plugins for common workflows.

### Core Workflows (ring-default)

- `/ring:codereview [files-or-paths]` - Dispatch 3 parallel code reviewers for comprehensive review
- `/ring:commit [message]` - Create git commit with AI identification via Git trailers
- `/ring:worktree [branch-name]` - Create isolated git workspace for parallel development
- `/ring:brainstorm [topic]` - Interactive design refinement using Socratic method
- `/ring:write-plan [feature]` - Create detailed implementation plan with bite-sized tasks
- `/ring:execute-plan [path]` - Execute plan in batches with review checkpoints
- `/ring:lint [path]` - Run lint checks and dispatch parallel agents to fix all issues
- `/ring:explore-codebase [path]` - Deep codebase exploration using Opus-powered agent
- `/ring:create-handoff [task]` - Create task handoff document for session continuity
- `/ring:resume-handoff [path]` - Resume work from a previous handoff
- `/query-artifacts [query]` - Search indexed artifacts for precedent
- `/compound-learnings` - Extract learnings from session history

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

- `/write-guide [topic]` - Start writing a functional guide with voice/tone guidance
- `/write-api [endpoint]` - Start writing API reference documentation
- `/review-docs [file]` - Review existing documentation for quality

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
│   └── marketplace.json              # Multi-plugin marketplace config (5 active plugins)
├── default/                          # Core Ring plugin (ring-default)
│   ├── skills/                       # 26 core skills
│   │   ├── skill-name/
│   │   │   └── SKILL.md             # Skill definition with frontmatter
│   │   └── shared-patterns/         # Universal patterns (6 patterns)
│   ├── commands/                    # 12 slash command definitions
│   ├── hooks/                       # Session initialization
│   │   ├── hooks.json              # Hook configuration
│   │   ├── session-start.sh        # Loads skills at startup
│   │   └── generate-skills-ref.py  # Auto-generates quick reference
│   ├── agents/                      # 5 specialized agents
│   │   ├── ring:code-reviewer.md        # Foundation review (parallel)
│   │   ├── ring:business-logic-reviewer.md  # Correctness review (parallel)
│   │   ├── ring:security-reviewer.md    # Safety review (parallel)
│   │   ├── ring:write-plan.md           # Implementation planning
│   │   └── ring:codebase-explorer.md    # Deep architecture analysis (Opus)
│   └── docs/                       # Documentation
├── dev-team/                      # Developer Agents plugin (ring-dev-team)
│   └── agents/                      # 7 specialized developer agents
│       ├── ring:backend-engineer-golang.md  # Go backend specialist
│       ├── ring:backend-engineer-typescript.md # TypeScript/Node.js backend specialist
│       ├── ring:devops-engineer.md          # DevOps infrastructure
│       ├── frontend-bff-engineer-typescript.md # BFF & React/Next.js frontend specialist
│       ├── ring:frontend-designer.md        # Visual design specialist
│       ├── ring:qa-analyst.md               # Quality assurance
│       └── sre.md                      # Site reliability engineer
├── pm-team/                    # Product Planning plugin (ring-pm-team)
│   └── skills/                      # 10 pre-dev workflow skills
│       └── pre-dev-*/              # PRD, TRD, API, Data, Tasks
├── finops-team/                     # FinOps Regulatory plugin (ring-finops-team)
│   ├── skills/                      # 6 regulatory skills
│   ├── agents/                      # 2 FinOps agents
│   ├── docs/regulatory/             # Regulatory templates and dictionaries
│   └── hooks/                       # SessionStart hook
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
     after: [prerequisite-skill]   # Skills that should come before
     before: [following-skill]     # Skills that typically follow

   related:
     similar: [skill-that-seems-similar]      # Differentiate from these
     complementary: [skill-that-pairs-well]   # Use together with these
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