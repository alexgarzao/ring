# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**ring** is a Claude Code plugin providing a comprehensive skills library. Skills are specialized process documents that guide AI assistants through proven techniques, patterns, and workflows.

The repository contains:
- **28 skills** covering testing, debugging, collaboration, development, and meta-skills
- **3 slash commands** that activate key skills
- **1 code reviewer agent** for systematic code review
- **SessionStart hook** that loads the skills system automatically

## Architecture

### Skills System

Skills use Claude Code's first-party skills system with:
- **Frontmatter** (YAML): Only `name` and `description` fields (max 1024 chars)
- **Description format**: "Use when [triggers] - [what it does]" in third person
- **Flat namespace**: All skills in `skills/` with kebab-case names
- **Namespaced references**: Skills reference each other as `ring:skill-name`

Directory structure:
```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Optional: tools, heavy reference docs
```

### Key Skills Categories

**Testing** - TDD workflows, async patterns, anti-patterns
**Debugging** - Systematic debugging, root cause tracing, verification
**Collaboration** - Brainstorming, planning, code review, parallel agents
**Development** - Git worktrees, branch finishing, subagent workflows
**Pre-Dev Workflow** - PRD → Feature Map → TRD → API → Data Model → Dependencies → Tasks → Subtasks
**Meta** - Creating, testing, and sharing skills

### Commands

Commands are thin wrappers in `commands/*.md` that activate skills:
- `/ring:brainstorm` → activates `brainstorming` skill
- `/ring:write-plan` → activates `writing-plans` skill
- `/ring:execute-plan` → activates `executing-plans` skill

### Hooks

**session-start.sh** - Loads `using-ring/SKILL.md` into every conversation, establishing mandatory workflows for finding and using skills

### Agents

**code-reviewer.md** - Provides systematic code review against plans and standards. Referenced as `ring:code-reviewer` in skills.

## Development Workflow

### Testing Skills

Skills follow TDD for documentation:
1. **RED**: Write pressure scenarios, run WITHOUT skill, document baseline failures
2. **GREEN**: Write skill addressing specific failures, verify agents comply
3. **REFACTOR**: Find new rationalizations, add counters, re-test

Use `testing-skills-with-subagents` skill for complete methodology.

### Skill Creation Standards

**Frontmatter requirements:**
- Name: letters, numbers, hyphens only (no parentheses/special chars)
- Description: starts with "Use when...", includes triggers and what it does
- Third person voice throughout

**Claude Search Optimization (CSO):**
- Rich descriptions with concrete triggers and symptoms
- Keyword coverage (error messages, symptoms, tools)
- Verb-first naming (`creating-skills` not `skill-creation`)

**Content structure:**
1. Overview (core principle in 1-2 sentences)
2. When to Use (bullets with symptoms)
3. Implementation (inline code or file reference)
4. Common Mistakes (what fails + fixes)

**Token efficiency targets:**
- Getting-started workflows: <150 words
- Frequently-loaded skills: <200 words
- Other skills: <500 words

### Cross-Referencing Skills

Use explicit requirement markers:
- `**REQUIRED BACKGROUND:**` - Prerequisites to understand
- `**REQUIRED SUB-SKILL:**` - Must be used in workflow
- `**Complementary skills:**` - Optional related skills

Format: `ring:skill-name` (no path, no @ syntax)

### Flowcharts

Use graphviz ONLY for non-obvious decision points. See `skills/writing-skills/graphviz-conventions.dot` for style rules.

Never use for: reference material (use tables), code examples (use markdown), linear instructions (use lists).

## Pre-Development Workflow

Eight-gate sequence for planning major features:

1. **PRD** (Gate 1) - Business requirements (WHAT/WHY only)
2. **Feature Map** (Gate 2) - Feature relationships and domain groupings
3. **TRD** (Gate 3) - Technical architecture patterns (HOW/WHERE, abstract)
4. **API Design** (Gate 4) - Component contracts (protocol-agnostic)
5. **Data Model** (Gate 5) - Entities and relationships (database-agnostic)
6. **Dependency Map** (Gate 6) - Technology and version selection
7. **Task Breakdown** (Gate 7) - High-level deliverable increments
8. **Subtask Creation** (Gate 8) - Atomic, zero-context work units

Each gate validates completeness before next phase.

## Philosophy

Core principles throughout the skills library:

- **Test-Driven Development** - Write tests first, always
- **Systematic over ad-hoc** - Process over guessing
- **Complexity reduction** - Simplicity as primary goal
- **Evidence over claims** - Verify before declaring success
- **Domain over implementation** - Work at problem level, not solution level
- **Skills are mandatory** - If a skill exists for your task, using it is required

## Contributing

Skills live directly in this repository:

1. Follow `writing-skills` skill for creation methodology
2. Use `testing-skills-with-subagents` to validate quality
3. Create branch, commit, push to fork (if configured)
4. Submit PR using `sharing-skills` workflow

## Installation & Updates

Users install via plugin marketplace:
```
/plugin marketplace add lerianstudio/ring-marketplace
/plugin install ring@ring-marketplace
```

Skills update when plugin updates:
```
/plugin update ring
```

## Related Resources

- Blog post: https://blog.fsck.com/2025/10/09/ring/
- Marketplace: https://github.com/lerianstudio/ring-marketplace
- Issues: https://github.com/lerianstudio/ring/issues
