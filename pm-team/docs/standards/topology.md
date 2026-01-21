# Project Topology Standards

Standards for project structure discovery and multi-module coordination in Ring workflows.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Feature Scope](#1-feature-scope) | backend-only, frontend-only, fullstack |
| 2 | [Repository Structure](#2-repository-structure) | single-repo, monorepo, multi-repo |
| 3 | [TopologyConfig Schema](#3-topologyconfig-schema) | YAML schema for topology configuration |
| 4 | [Module Organization](#4-module-organization) | unified vs per-module docs |
| 5 | [Context Switching](#5-context-switching) | when to prompt for directory change |
| 6 | [Multi-Repo Coordination](#6-multi-repo-coordination) | handling separate repositories |
| 7 | [PROJECT_RULES.md Hierarchy](#7-project_rulesmd-hierarchy) | rule precedence in multi-module projects |

---

## 1. Feature Scope

Feature scope determines how many working directories are needed and which agents to dispatch.

| Scope | Description | Working Directories | Agents |
|-------|-------------|---------------------|--------|
| `backend-only` | API, services, data layer only | Single | backend-engineer-* |
| `frontend-only` | UI, BFF routes only | Single | frontend-*-engineer-* |
| `fullstack` | Both backend and frontend | May require multiple | Both backend and frontend agents |

### When to Use Each Scope

| Scope | Examples |
|-------|----------|
| `backend-only` | REST API endpoint, database migration, background job |
| `frontend-only` | UI component, page layout, client-side validation |
| `fullstack` | User authentication, CRUD feature with UI, real-time updates |

---

## 2. Repository Structure

Repository structure affects how docs are organized and how tasks are distributed.

| Structure | When | Doc Location | Task Distribution |
|-----------|------|--------------|-------------------|
| `single-repo` | All code in one repo, same directory | Unified in `docs/pre-dev/{feature}/` | All tasks in single `tasks.md` |
| `monorepo` | Multiple packages in one repo (e.g., `packages/*`) | Per-module optional | Tasks tagged with `target:` |
| `multi-repo` | Separate repos for backend/frontend | Coordinator repo | Tasks split into `_{module}.tasks.md` |

### Structure Detection Hints

| Indicator | Likely Structure |
|-----------|------------------|
| Single `package.json` or `go.mod` at root | `single-repo` |
| `packages/`, `apps/`, `libs/` directories | `monorepo` |
| User specifies external path | `multi-repo` |

---

## 3. TopologyConfig Schema

TopologyConfig is persisted in the `research.md` frontmatter and propagated through all gates.

```yaml
topology:
  # Required
  scope: fullstack | backend-only | frontend-only
  structure: single-repo | monorepo | multi-repo

  # Required for monorepo and multi-repo
  modules:
    backend:
      path: string          # Relative path (monorepo) or absolute path (multi-repo)
      language: golang | typescript
    frontend:
      path: string          # Relative path (monorepo) or absolute path (multi-repo)
      framework: nextjs | react | vue | angular

  # Required for fullstack
  doc_organization: unified | per-module
```

### Example Configurations

**Single-repo (backend-only):**
```yaml
topology:
  scope: backend-only
  structure: single-repo
```

**Monorepo (fullstack):**
```yaml
topology:
  scope: fullstack
  structure: monorepo
  modules:
    backend:
      path: packages/api
      language: golang
    frontend:
      path: packages/web
      framework: nextjs
  doc_organization: unified
```

**Multi-repo (fullstack):**
```yaml
topology:
  scope: fullstack
  structure: multi-repo
  modules:
    backend:
      path: /home/user/projects/my-api
      language: typescript
    frontend:
      path: /home/user/projects/my-frontend
      framework: react
  doc_organization: per-module
```

---

## 4. Module Organization

### Unified Organization (Default)

All tasks in single `tasks.md` with `target:` tags:

```
docs/pre-dev/{feature}/
├── research.md
├── prd.md
├── trd.md
└── tasks.md          # All tasks with target: tags
```

**Task format:**
```markdown
## Task 3: Create User API Endpoint

**Target:** backend
**Working Directory:** packages/api
**Agent:** ring:backend-engineer-golang

...task details...
```

### Per-Module Organization

Separate task files per module:

```
docs/pre-dev/{feature}/
├── research.md
├── prd.md
├── trd.md
├── tasks.md          # Index with all tasks
├── backend/
│   └── tasks.md      # Backend tasks only
└── frontend/
    └── tasks.md      # Frontend tasks only
```

### When to Use Each

| Organization | When | Benefits |
|--------------|------|----------|
| `unified` | Small features, tight integration | Single source of truth, easier to track |
| `per-module` | Large features, separate teams, multi-repo | Independent execution, easier distribution |

---

## 5. Context Switching

### When Context Switch Occurs

| Scenario | Action |
|----------|--------|
| Task `target:` differs from current module | Prompt user for confirmation |
| First task of execution | Set initial module (no prompt) |
| Returning to previously visited module | No prompt (context cached) |
| Shared task (`target: shared`) | Execute in root directory |

### Context Switch Prompt

```
AskUserQuestion:
  question: "Switching to {module} module at {path}. Continue?"
  header: "Context"
  options:
    - label: "Continue"
      description: "Switch to {module} and execute task"
    - label: "Skip task"
      description: "Skip this task and continue"
    - label: "Stop"
      description: "Stop execution"
```

### Optimizing Context Switches

To minimize context switches, execution skills SHOULD batch tasks by module:

```
Original order: [backend, frontend, backend, frontend]
Optimized order: [backend, backend, frontend, frontend]
```

**Note:** Only reorder if tasks have no dependencies between modules.

---

## 6. Multi-Repo Coordination

### Coordinator Repository

When `structure: multi-repo`, the repository where `/pre-dev-feature` is run becomes the "coordinator":

- All pre-dev docs stay in coordinator
- Task files are generated with clear module markers
- Execution requires manual or scripted distribution

### Task Distribution Options

**Option A: Manual Copy**
```bash
# After pre-dev completes
cp docs/pre-dev/feature/_backend.tasks.md /path/to/backend/docs/
cp docs/pre-dev/feature/_frontend.tasks.md /path/to/frontend/docs/
```

**Option B: Symlinks (same machine)**
```bash
ln -s /coordinator/docs/pre-dev/feature/_backend.tasks.md /backend/docs/feature-tasks.md
```

**Option C: Git Submodules**
Include coordinator as submodule in each repo.

### Execution in Multi-Repo

When executing multi-repo tasks:
1. Skill reads task's `working_directory`
2. Prompts for context switch (includes full path)
3. Instructs agent to `cd` to target directory
4. Agent reads `PROJECT_RULES.md` from target if exists

---

## 7. PROJECT_RULES.md Hierarchy

### Precedence Rules

In multi-module projects, PROJECT_RULES.md files are merged with clear precedence:

| Level | Location | Precedence |
|-------|----------|------------|
| Root | `./PROJECT_RULES.md` | Lowest (base rules) |
| Module | `{module_path}/PROJECT_RULES.md` | Highest (overrides root) |

### Merge Behavior

```
Root PROJECT_RULES.md:
  - Use conventional commits
  - All code must have tests

Backend PROJECT_RULES.md:
  - Use Go 1.22+
  - Tests use testify

Result for backend tasks:
  - Use conventional commits (from root)
  - All code must have tests (from root)
  - Use Go 1.22+ (from module)
  - Tests use testify (from module)
```

### Conflict Resolution

When same rule exists in both:
- **Module rule wins** - more specific context
- Agent MUST note in output: "Using module-specific rule for X"

---

## Checklist

When implementing topology support:

- [ ] TopologyConfig persisted in research.md frontmatter
- [ ] All gates read topology from frontmatter
- [ ] Tasks have `target:` and `working_directory:` fields
- [ ] Execution skills implement context switching
- [ ] Multi-repo generates per-module task files
- [ ] PROJECT_RULES.md hierarchy respected
