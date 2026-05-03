# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **AGENTS.md is a symlink to this file** — edit CLAUDE.md only; changes propagate automatically.

---

## ⛔ CRITICAL RULES (READ FIRST)

### 1. Agent Modification = Mandatory Verification

When creating or modifying any agent in `*/agents/*.md`:

- MUST verify agent has all required sections — see [docs/AGENT_DESIGN.md](docs/AGENT_DESIGN.md#agent-modification-verification-mandatory)
- MUST include positive `<example>` blocks showing correct behavior
- MUST use selective standards loading via `_index.md` manifesto (not monolithic WebFetch)
- MUST keep agents under 300 lines (implementation) or 200 lines (reviewers)
- If any section is missing → Agent is INCOMPLETE

### 2. Agents are EXECUTORS, Not DECISION-MAKERS

- Agents **VERIFY**, they DO NOT **ASSUME**
- Agents **REPORT** blockers, they DO NOT **SOLVE** ambiguity autonomously
- Agents **FOLLOW** gates, they DO NOT **SKIP** gates
- Agents **ASK** when uncertain, they DO NOT **GUESS**

### 3. Anti-Patterns (MUST NOT do these)

1. **MUST NOT skip ring:using-ring** — mandatory, not optional
2. **MUST NOT run reviewers sequentially** — dispatch in parallel
3. **MUST NOT skip TDD's RED phase** — test must fail before implementation
4. **MUST NOT ignore skill when applicable** — "simple task" is not an excuse
5. **ZERO PANIC POLICY** — `panic()`, `log.Fatal()`, and `Must*` helpers are FORBIDDEN everywhere (including bootstrap/init). Return `(T, error)` instead. Only exception: `regexp.MustCompile()` with compile-time constants.
6. **MUST NOT commit manually** — use `ring:commit` skill
7. **MUST NOT assume compliance** — VERIFY with evidence

### 4. Unified Ring Namespace (MANDATORY)

All Ring components use the unified `ring:` prefix.

- ✅ `ring:code-reviewer`, `ring:backend-engineer-golang`
- ❌ omitting `ring:` prefix (FORBIDDEN)
- ❌ `ring-default:ring:code-reviewer` (deprecated plugin-specific prefix)

### 5. Standards-Agent Synchronization (MUST CHECK)

When modifying `platforms/opencode/standards/{stack}/*.md` files:

**⛔ FOUR-FILE UPDATE RULE** (all in same commit):

1. Edit `platforms/opencode/standards/{stack}/{module}.md` — add `## Section Name`
2. Update `platforms/opencode/standards/{stack}/_index.md` — add module entry with "Load When"
3. Edit `dev-team/skills/shared-patterns/standards-coverage-table.md` — add section to agent index
4. Edit `dev-team/agents/{agent}.md` — verify agent references `_index.md` for selective loading

**⛔ TOC MAINTENANCE RULE:** Every standards file has a `## Table of Contents` that MUST stay in sync. Section count in TOC MUST match `standards-coverage-table.md`.

**⛔ AGENT INLINE CATEGORIES ARE FORBIDDEN:** Agents MUST reference `standards-coverage-table.md`, not inline comparison tables.

**Standards Directory → Agent Mapping:**

| Standards Directory        | Agents That Use It                                                                              |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| `golang/` (30 modules)     | `ring:backend-engineer-golang`, `ring:qa-analyst`                                               |
| `typescript/` (21 modules) | `ring:backend-engineer-typescript`, `ring:frontend-bff-engineer-typescript`, `ring:qa-analyst`  |
| `frontend/` (21 modules)   | `ring:frontend-engineer`, `ring:frontend-designer`                                              |
| `devops/` (9 modules)      | `ring:devops-engineer`                                                                          |
| `sre/` (7 modules)         | `ring:sre`                                                                                      |

**Section Index Location:** `dev-team/skills/shared-patterns/standards-coverage-table.md`

### 6. CLAUDE.md ↔ AGENTS.md Synchronization

**⛔ AGENTS.md IS A SYMLINK TO CLAUDE.md — MUST NOT break:**

- Edit CLAUDE.md — changes automatically appear in AGENTS.md
- MUST NOT delete the AGENTS.md symlink or replace it with a regular file
- If symlink is broken → restore with: `ln -sf CLAUDE.md AGENTS.md`

### 7. Content Duplication Prevention (MUST CHECK)

Before adding any content: **SEARCH FIRST** with `grep -r "keyword" --include="*.md"`.

- If content exists → **REFERENCE it**, DO NOT duplicate
- If adding new content → add to the canonical source

See [docs/WORKFLOWS.md](docs/WORKFLOWS.md#content-duplication-prevention) for canonical source table and shared patterns rule.

### 8. Reviewer-Pool Synchronization (MUST CHECK)

When adding/removing a code review agent in `ring:codereview` pool:

**⛔ SEVEN-FILE UPDATE RULE** (all in same commit) — see [docs/WORKFLOWS.md](docs/WORKFLOWS.md#reviewer-pool-synchronization) for the complete checklist and secondary consumers sweep.

---

## Selective Context Loading (Agentic Search)

Standards are modularized into focused files. Each stack has an `_index.md` manifesto:

```
platforms/opencode/standards/
├── golang/_index.md          ← Module list + "Load When" descriptions (30 modules)
├── typescript/_index.md      ← (21 modules)
├── frontend/_index.md        ← (21 modules)
├── devops/_index.md          ← (9 modules)
└── sre/_index.md             ← (7 modules)
```

**Agent Standards Loading pattern:**
1. Read `platforms/opencode/standards/{stack}/_index.md`
2. Match current task against "Load When" column
3. Fetch only matching module files — do NOT load all modules

---

## Quick Navigation

| Topic | Location |
|-------|----------|
| Critical Rules | This file (above) |
| Agent verification checklist + example blocks | [docs/AGENT_DESIGN.md](docs/AGENT_DESIGN.md) |
| Frontmatter schema | [docs/FRONTMATTER_SCHEMA.md](docs/FRONTMATTER_SCHEMA.md) |
| Lexical salience, enforcement words, prompt patterns | [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) |
| Reviewer-pool sync, Documentation sync, Content duplication | [docs/WORKFLOWS.md](docs/WORKFLOWS.md) |
| Repository overview, installation, architecture | [README.md](README.md) |
| Architecture diagrams | [ARCHITECTURE.md](ARCHITECTURE.md) |

---

## Architecture (Plugin Summary)

| Plugin           | Path           | Skills | Agents |
| ---------------- | -------------- | ------ | ------ |
| ring-default     | `default/`     | 24     | 10     |
| ring-dev-team    | `dev-team/`    | 37     | 15     |
| ring-pm-team     | `pm-team/`     | 17     | 4      |
| ring-pmo-team    | `pmo-team/`    | 9      | 6      |
| ring-finops-team | `finops-team/` | 7      | 3      |
| ring-tw-team     | `tw-team/`     | 6      | 3      |

**Total: 100 skills, 41 agents across 6 plugins.** Plugin versions in `.claude-plugin/marketplace.json`.

Each plugin contains: `skills/`, `agents/`, `hooks/`. See [README.md](README.md#architecture) for full directory structure.

---

## Key Workflows

| Workflow | Quick Reference |
|----------|-----------------|
| Add skill | Create `*/skills/name/SKILL.md` with frontmatter per [Frontmatter Schema](docs/FRONTMATTER_SCHEMA.md) |
| Add agent | Create `*/agents/name.md` → verify required sections per [Agent Design](docs/AGENT_DESIGN.md) |
| Modify hooks | Edit `*/hooks/hooks.json` → test with `bash */hooks/session-start.sh` |
| Code review | `ring:codereview` dispatches 10 parallel reviewers |
| Pre-dev (small) | `ring:pre-dev-feature` → 5-gate workflow |
| Pre-dev (large) | `ring:pre-dev-full` → 10-gate workflow |
| Dev cycle backend | `ring:dev-cycle` → 10-gate workflow |
| Dev cycle frontend | `ring:dev-cycle-frontend` → 9-gate workflow |

See [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for detailed instructions.

---

## Compliance Rules

```text
# TDD compliance (default/skills/test-driven-development/SKILL.md)
- Test file must exist before implementation
- Test must produce failure output (RED)
- Only then write implementation (GREEN)

# Review compliance (default/skills/codereview/SKILL.md)
- All 10 reviewers must pass
- Critical findings = immediate fix required
- Re-run all 10 reviewers after fixes

# Skill compliance (default/skills/using-ring/SKILL.md)
- Check for applicable skills before any task
- If skill exists for task → MUST use it

# Commit compliance (default/skills/commit/SKILL.md)
- MUST use ring:commit skill for all commits
- MUST NOT write git commit commands manually
- Format: git commit -m "msg" --trailer "Generated-by: Claude" --trailer "AI-Model: <model>"
- MUST NOT use HEREDOC to include trailers in message body
```

---

## Session Context

System loads at SessionStart (from `default/` plugin):

1. `default/hooks/session-start.sh` — loads skill quick reference via `generate-skills-ref.py`
2. `ring:using-ring` skill — injected as mandatory workflow

Active branch: `main` | Remote: `github.com/LerianStudio/ring`
