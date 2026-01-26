# Module-Aware Documentation Placement Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Enable pre-dev documentation to be stored in the appropriate repository/module based on project topology (single-repo, monorepo, or multi-repo).

**Architecture:** Add a `doc_placement` field to TopologyConfig that determines where documents are written. Implement path resolution logic in each skill that generates documents. The placement strategy is derived from the `structure` field but can be explicitly configured.

**Tech Stack:** Markdown documentation, YAML frontmatter, Bash commands for directory creation

**Global Prerequisites:**
- Environment: Any Unix-like OS with Bash
- Tools: Git, text editor
- Access: Write access to Ring repository
- State: Working from `main` branch with clean working tree

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
git status        # Expected: clean working tree on main branch
ls pm-team/skills/shared-patterns/  # Expected: topology-discovery.md exists
ls pm-team/docs/standards/          # Expected: topology.md exists
```

## Historical Precedent

**Query:** "pre-dev documentation topology module placement"
**Index Status:** Empty (new project)

No historical data available. This is normal for new projects.
Proceeding with standard planning approach.

---

## Document Classification Reference

| Document | Type | Single-Repo | Monorepo | Multi-Repo |
|----------|------|-------------|----------|------------|
| research.md | Shared | `docs/pre-dev/{feature}/` | `docs/pre-dev/{feature}/` | Both repos |
| prd.md | Shared | `docs/pre-dev/{feature}/` | `docs/pre-dev/{feature}/` | Both repos |
| ux-criteria.md | Frontend | `docs/pre-dev/{feature}/` | `{frontend.path}/docs/pre-dev/{feature}/` | Frontend repo |
| wireframes/ | Frontend | `docs/pre-dev/{feature}/` | `{frontend.path}/docs/pre-dev/{feature}/` | Frontend repo |
| trd.md | Shared | `docs/pre-dev/{feature}/` | `docs/pre-dev/{feature}/` | Both repos |
| api-design.md | Backend | `docs/pre-dev/{feature}/` | `{backend.path}/docs/pre-dev/{feature}/` | Backend repo |
| data-model.md | Backend | `docs/pre-dev/{feature}/` | `{backend.path}/docs/pre-dev/{feature}/` | Backend repo |
| dependency-map.md | Split | `docs/pre-dev/{feature}/` | Per-module paths | Per-repo |
| tasks.md | Split | `docs/pre-dev/{feature}/` | Index + per-module | Index + per-repo |

---

## Task Overview

| Task | Description | Estimate |
|------|-------------|----------|
| T-001 | Add doc_placement to TopologyConfig schema | S (2-3 min) |
| T-002 | Add path resolution helper to topology-discovery.md | M (5 min) |
| T-003 | Add Section 9: Documentation Placement to topology.md | M (5 min) |
| T-004 | Update Section 6 in topology.md to remove workarounds | S (2-3 min) |
| T-005 | Update pre-dev-research skill with placement logic | M (4-5 min) |
| T-006 | Update pre-dev-prd-creation skill with placement logic | M (4-5 min) |
| T-007 | Update pre-dev-trd-creation skill with placement logic | M (4-5 min) |
| T-008 | Update pre-dev-api-design skill with placement logic | M (4-5 min) |
| T-009 | Update pre-dev-data-model skill with placement logic | M (4-5 min) |
| T-010 | Update pre-dev-task-breakdown skill with split logic | L (8-10 min) |
| T-011 | Update pre-dev-feature command with placement summary | M (5 min) |
| T-012 | Update pre-dev-full command with placement summary | M (5 min) |
| T-013 | Run Code Review | M (5 min) |

---

### Task T-001: Add doc_placement to TopologyConfig Schema

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md:198-253`

**Prerequisites:**
- File must exist: `pm-team/skills/shared-patterns/topology-discovery.md`

**Step 1: Add doc_placement field to Output: TopologyConfig section**

Locate the `## Output: TopologyConfig` section (around line 198) and add the `doc_placement` field to all schema examples.

**Edit 1:** After `doc_organization: unified` line in the Single-repo Fullstack example, add:

```yaml
topology:
  scope: fullstack
  structure: single-repo
  doc_organization: unified  # or per-module
  doc_placement: unified     # NEW: derived from structure
  api_pattern: direct        # or bff, other
```

**Edit 2:** In the Monorepo Fullstack example:

```yaml
topology:
  scope: fullstack
  structure: monorepo
  modules:
    backend:
      path: packages/api        # From Q3
      language: golang          # Auto-detected or asked
    frontend:
      path: packages/web        # From Q3
      framework: nextjs         # Auto-detected or asked
  doc_organization: unified     # From Q4
  doc_placement: per-module     # NEW: derived from structure
  api_pattern: bff              # From Q5
```

**Edit 3:** In the Multi-repo Fullstack example:

```yaml
topology:
  scope: fullstack
  structure: multi-repo
  modules:
    backend:
      path: /home/user/projects/backend-api    # From Q3
      language: typescript                      # Auto-detected
    frontend:
      path: /home/user/projects/frontend-app   # From Q3
      framework: react                          # Auto-detected
  doc_organization: per-module                  # From Q4
  doc_placement: distributed                    # NEW: derived from structure
  api_pattern: direct                           # From Q5
```

**Step 2: Verify the changes**

Run: `grep -n "doc_placement" /home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Expected output:**
```
[line numbers showing doc_placement in 3 schema examples]
```

**Step 3: Commit**

```bash
git add pm-team/skills/shared-patterns/topology-discovery.md
git commit -m "feat(topology): add doc_placement field to TopologyConfig schema"
```

**If Task Fails:**
1. **File not found:** Verify path with `ls pm-team/skills/shared-patterns/`
2. **Line numbers don't match:** Search for `## Output: TopologyConfig` and locate schema examples

---

### Task T-002: Add Path Resolution Helper to topology-discovery.md

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md` (append before Error Handling section)

**Prerequisites:**
- Task T-001 completed

**Step 1: Add Documentation Path Resolution section**

Insert this new section before the `## Error Handling` section (around line 346):

```markdown
---

## Documentation Path Resolution

### Path Resolution Function

Skills MUST use this logic to determine where to write documents:

```python
def get_doc_path(doc_type: str, feature_name: str, topology: dict) -> str | list[str]:
    """
    Returns the path(s) where a document should be written.

    Args:
        doc_type: One of 'research', 'prd', 'trd', 'ux-criteria', 'wireframes',
                  'api-design', 'data-model', 'dependency-map', 'tasks'
        feature_name: The feature name in kebab-case
        topology: The TopologyConfig dictionary

    Returns:
        Single path string, or list of paths for multi-repo shared docs
    """
    structure = topology.get('structure', 'single-repo')
    modules = topology.get('modules', {})

    # Single-repo: all docs in one place
    if structure == 'single-repo':
        return f"docs/pre-dev/{feature_name}/"

    # Shared documents (research, prd, trd)
    if doc_type in ['research', 'prd', 'trd']:
        if structure == 'monorepo':
            return f"docs/pre-dev/{feature_name}/"
        else:  # multi-repo
            # Return both paths - document must be copied to both repos
            backend_path = modules.get('backend', {}).get('path', '.')
            frontend_path = modules.get('frontend', {}).get('path', '.')
            return [
                f"{backend_path}/docs/pre-dev/{feature_name}/",
                f"{frontend_path}/docs/pre-dev/{feature_name}/"
            ]

    # Frontend documents (ux-criteria, wireframes)
    if doc_type in ['ux-criteria', 'wireframes']:
        frontend_path = modules.get('frontend', {}).get('path', '.')
        return f"{frontend_path}/docs/pre-dev/{feature_name}/"

    # Backend documents (api-design, data-model)
    if doc_type in ['api-design', 'data-model']:
        backend_path = modules.get('backend', {}).get('path', '.')
        return f"{backend_path}/docs/pre-dev/{feature_name}/"

    # Split documents (dependency-map, tasks)
    if doc_type in ['dependency-map', 'tasks']:
        # Return paths for both modules - skill handles split logic
        if structure == 'monorepo':
            backend_path = modules.get('backend', {}).get('path', '.')
            frontend_path = modules.get('frontend', {}).get('path', '.')
            return {
                'index': f"docs/pre-dev/{feature_name}/",
                'backend': f"{backend_path}/docs/pre-dev/{feature_name}/",
                'frontend': f"{frontend_path}/docs/pre-dev/{feature_name}/"
            }
        else:  # multi-repo
            backend_path = modules.get('backend', {}).get('path', '.')
            frontend_path = modules.get('frontend', {}).get('path', '.')
            return {
                'backend': f"{backend_path}/docs/pre-dev/{feature_name}/",
                'frontend': f"{frontend_path}/docs/pre-dev/{feature_name}/"
            }

    # Default fallback
    return f"docs/pre-dev/{feature_name}/"
```

### Document Classification

| Document | Classification | Placement Rule |
|----------|---------------|----------------|
| research.md | Shared | Root (monorepo) or both repos (multi-repo) |
| prd.md | Shared | Root (monorepo) or both repos (multi-repo) |
| trd.md | Shared | Root (monorepo) or both repos (multi-repo) |
| ux-criteria.md | Frontend | Frontend module/repo path |
| wireframes/ | Frontend | Frontend module/repo path |
| api-design.md | Backend | Backend module/repo path |
| data-model.md | Backend | Backend module/repo path |
| dependency-map.md | Split | Index at root, module-specific at module paths |
| tasks.md | Split | Index at root, filtered tasks at module paths |

### Multi-Repo Document Synchronization

For multi-repo with shared documents (research.md, prd.md, trd.md):

1. **Write to primary location first** (backend repo by convention)
2. **Copy to secondary location** (frontend repo)
3. **Include sync note in document footer:**

```markdown
---
**Note:** This document is synchronized across repositories.
Primary: {backend.path}/docs/pre-dev/{feature}/
Mirror: {frontend.path}/docs/pre-dev/{feature}/
```

### Directory Creation

Before writing any document, create the target directory:

```bash
# Single path
mkdir -p "{path}"

# Multi-repo (both paths)
mkdir -p "{backend_path}" "{frontend_path}"
```
```

**Step 2: Verify the changes**

Run: `grep -n "Documentation Path Resolution" /home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Expected output:**
```
[line number]: ## Documentation Path Resolution
```

**Step 3: Commit**

```bash
git add pm-team/skills/shared-patterns/topology-discovery.md
git commit -m "feat(topology): add documentation path resolution helper"
```

**If Task Fails:**
1. **Section placement wrong:** Find `## Error Handling` and insert before it
2. **Code block not rendering:** Ensure proper markdown fencing with triple backticks

---

### Task T-003: Add Section 9: Documentation Placement to topology.md

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md`

**Prerequisites:**
- Files must exist: `pm-team/docs/standards/topology.md`

**Step 1: Update Table of Contents**

Find the `## Table of Contents` section and add row 9:

```markdown
| 9 | [Documentation Placement](#9-documentation-placement) | Where docs are stored per structure |
```

**Step 2: Add Section 9 after Section 8**

Append after `## 8. API Pattern` section (after line 337):

```markdown
---

## 9. Documentation Placement

Documentation placement determines where pre-dev artifacts are written based on project structure.

### Placement Modes

| Mode | Structure | Description |
|------|-----------|-------------|
| `unified` | single-repo | All docs in `docs/pre-dev/{feature}/` |
| `per-module` | monorepo | Docs distributed to module directories |
| `distributed` | multi-repo | Docs written to each repository |

### Document Types and Placement

| Document | Type | single-repo | monorepo | multi-repo |
|----------|------|-------------|----------|------------|
| research.md | Shared | Root | Root | Both repos |
| prd.md | Shared | Root | Root | Both repos |
| trd.md | Shared | Root | Root | Both repos |
| ux-criteria.md | Frontend | Root | Frontend module | Frontend repo |
| wireframes/ | Frontend | Root | Frontend module | Frontend repo |
| api-design.md | Backend | Root | Backend module | Backend repo |
| data-model.md | Backend | Root | Backend module | Backend repo |
| dependency-map.md | Split | Root | Root + modules | Per repo |
| tasks.md | Split | Root | Root + modules | Per repo |

### Single-Repo (unified)

All documentation stays in the repository root:

```
docs/pre-dev/{feature}/
├── research.md
├── prd.md
├── ux-criteria.md
├── wireframes/
├── trd.md
├── api-design.md
├── data-model.md
├── dependency-map.md
└── tasks.md
```

### Monorepo (per-module)

Shared docs at root, module-specific docs in module directories:

```
# Root (shared)
docs/pre-dev/{feature}/
├── research.md
├── prd.md
├── trd.md
└── tasks.md           # Index with all tasks

# Backend module
{backend.path}/docs/pre-dev/{feature}/
├── api-design.md
├── data-model.md
├── dependency-map.md  # Backend dependencies
└── tasks.md           # Backend tasks only

# Frontend module
{frontend.path}/docs/pre-dev/{feature}/
├── ux-criteria.md
├── wireframes/
├── dependency-map.md  # Frontend dependencies
└── tasks.md           # Frontend tasks only
```

### Multi-Repo (distributed)

Shared docs copied to both repos, module-specific docs in respective repos:

```
# Backend repository
{backend.path}/docs/pre-dev/{feature}/
├── research.md        # Copy of shared
├── prd.md             # Copy of shared
├── trd.md             # Copy of shared
├── api-design.md
├── data-model.md
├── dependency-map.md
└── tasks.md           # Backend tasks only

# Frontend repository
{frontend.path}/docs/pre-dev/{feature}/
├── research.md        # Copy of shared
├── prd.md             # Copy of shared
├── trd.md             # Copy of shared
├── ux-criteria.md
├── wireframes/
├── dependency-map.md
└── tasks.md           # Frontend tasks only
```

### Implementation Notes

**For skills writing documents:**

1. Read `topology.structure` from research.md frontmatter
2. Use path resolution logic from `topology-discovery.md`
3. Create directories before writing
4. For multi-repo shared docs, write to both paths

**Backward Compatibility:**

- Single-repo behavior is unchanged
- Existing projects without `doc_placement` default to `unified`
- Skills MUST handle missing `topology` in frontmatter gracefully
```

**Step 3: Verify the changes**

Run: `grep -n "Documentation Placement" /home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md`

**Expected output:**
```
[line in TOC]: | 9 | [Documentation Placement]...
[line of section]: ## 9. Documentation Placement
```

**Step 4: Commit**

```bash
git add pm-team/docs/standards/topology.md
git commit -m "feat(topology): add Section 9 - Documentation Placement standards"
```

**If Task Fails:**
1. **TOC not found:** Search for `## Table of Contents`
2. **Section 8 not found:** Search for `## 8. API Pattern`

---

### Task T-004: Update Section 6 to Remove Manual Workarounds

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md:215-250`

**Prerequisites:**
- Task T-003 completed

**Step 1: Replace Task Distribution Options in Section 6**

Find Section 6 (`## 6. Multi-Repo Coordination`) and replace the "Task Distribution Options" subsection:

**Old content (lines ~225-242):**
```markdown
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
```

**New content:**
```markdown
### Task Distribution

**Automatic Placement:** Documents are now automatically written to the correct repository based on `doc_placement: distributed`.

- Shared documents (research.md, prd.md, trd.md) are written to both repos
- Backend documents (api-design.md, data-model.md, tasks.md) go to backend repo
- Frontend documents (ux-criteria.md, wireframes/, tasks.md) go to frontend repo

**See Section 9 (Documentation Placement)** for complete placement rules.

**Manual Sync (if needed):**
If automatic placement fails or repos are on different machines:

```bash
# Sync shared docs from backend to frontend
rsync -av {backend.path}/docs/pre-dev/{feature}/research.md {frontend.path}/docs/pre-dev/{feature}/
rsync -av {backend.path}/docs/pre-dev/{feature}/prd.md {frontend.path}/docs/pre-dev/{feature}/
rsync -av {backend.path}/docs/pre-dev/{feature}/trd.md {frontend.path}/docs/pre-dev/{feature}/
```
```

**Step 2: Verify the changes**

Run: `grep -n "Automatic Placement" /home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md`

**Expected output:**
```
[line number]: **Automatic Placement:** Documents are now...
```

**Step 3: Commit**

```bash
git add pm-team/docs/standards/topology.md
git commit -m "refactor(topology): replace manual workarounds with auto-placement reference"
```

**If Task Fails:**
1. **Section 6 not found:** Search for `## 6. Multi-Repo Coordination`
2. **Old content differs:** Adapt the replacement to match actual content

---

### Task T-005: Update pre-dev-research Skill with Placement Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-research/SKILL.md`

**Prerequisites:**
- Tasks T-001, T-002 completed
- File must exist: `pm-team/skills/pre-dev-research/SKILL.md`

**Step 1: Add placement logic after Step 2.5**

Find `## Step 2.5: Handle Topology Configuration` section and add placement guidance:

Insert after the TopologyConfig frontmatter example (around line 119), before the agent dispatch adjustment section:

```markdown
**Document Placement (based on topology.structure):**

| Structure | research.md Location |
|-----------|---------------------|
| single-repo | `docs/pre-dev/{feature-name}/research.md` |
| monorepo | `docs/pre-dev/{feature-name}/research.md` (root) |
| multi-repo | Write to BOTH: `{backend.path}/docs/pre-dev/{feature-name}/research.md` AND `{frontend.path}/docs/pre-dev/{feature-name}/research.md` |

**Multi-repo directory creation:**
```bash
# Create directories in both repos
mkdir -p "{backend.path}/docs/pre-dev/{feature-name}"
mkdir -p "{frontend.path}/docs/pre-dev/{feature-name}"
```

**Multi-repo sync note:** Add this footer to research.md for multi-repo:
```markdown
---
**Sync Status:** This document is maintained in both repositories.
- Primary: {backend.path}/docs/pre-dev/{feature-name}/research.md
- Mirror: {frontend.path}/docs/pre-dev/{feature-name}/research.md
```
```

**Step 2: Update Step 3 output path**

Find `## Step 3: Aggregate Research Findings` and update the output line:

**Old:**
```markdown
**Output:** `docs/pre-dev/{feature-name}/research.md`
```

**New:**
```markdown
**Output:**
- **single-repo/monorepo:** `docs/pre-dev/{feature-name}/research.md`
- **multi-repo:** Both `{backend.path}/docs/pre-dev/{feature-name}/research.md` AND `{frontend.path}/docs/pre-dev/{feature-name}/research.md`
```

**Step 3: Verify the changes**

Run: `grep -n "multi-repo" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-research/SKILL.md | head -5`

**Expected output:**
```
[line numbers showing multi-repo placement references]
```

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-research/SKILL.md
git commit -m "feat(research): add module-aware document placement logic"
```

**If Task Fails:**
1. **Section not found:** Search for `## Step 2.5` or `## Step 3`
2. **Content differs:** Adapt edits to match actual file structure

---

### Task T-006: Update pre-dev-prd-creation Skill with Placement Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-prd-creation/SKILL.md`

**Prerequisites:**
- File must exist: `pm-team/skills/pre-dev-prd-creation/SKILL.md`

**Step 1: Add Document Placement section after Phase 4**

Find `## Phase 4: UX Validation + Wireframes` section and add placement logic after the UX Validation Outputs:

Insert after line ~168 (after wireframes output description):

```markdown
### Document Placement (based on topology.structure)

**prd.md placement:**

| Structure | prd.md Location |
|-----------|-----------------|
| single-repo | `docs/pre-dev/{feature}/prd.md` |
| monorepo | `docs/pre-dev/{feature}/prd.md` (root) |
| multi-repo | Write to BOTH repos |

**ux-criteria.md and wireframes/ placement:**

| Structure | Location |
|-----------|----------|
| single-repo | `docs/pre-dev/{feature}/` |
| monorepo | `{frontend.path}/docs/pre-dev/{feature}/` |
| multi-repo | `{frontend.path}/docs/pre-dev/{feature}/` |

**Why frontend path for UX docs?** UX criteria and wireframes are consumed by frontend engineers. Placing them in the frontend module/repo ensures they are discoverable where they'll be used.

**Directory creation for multi-module:**
```bash
# Read topology from research.md frontmatter
# Create appropriate directories:

# For monorepo - frontend module
mkdir -p "{frontend.path}/docs/pre-dev/{feature}"

# For multi-repo - both repos for prd.md, frontend for UX
mkdir -p "{backend.path}/docs/pre-dev/{feature}"
mkdir -p "{frontend.path}/docs/pre-dev/{feature}"
```
```

**Step 2: Update Output & After Approval section**

Find `## Output & After Approval` section and update outputs:

**Old:**
```markdown
**Outputs:**
- `docs/pre-dev/{feature-name}/prd.md` - Business requirements document
- `docs/pre-dev/{feature-name}/ux-criteria.md` - UX acceptance criteria (from product-designer)
- `docs/pre-dev/{feature-name}/wireframes/` - Low-fidelity prototypes (if feature has UI)
```

**New:**
```markdown
**Outputs (paths depend on topology.structure):**

| Document | single-repo | monorepo | multi-repo |
|----------|-------------|----------|------------|
| prd.md | `docs/pre-dev/{feature}/` | `docs/pre-dev/{feature}/` | Both repos |
| ux-criteria.md | `docs/pre-dev/{feature}/` | `{frontend.path}/docs/pre-dev/{feature}/` | Frontend repo |
| wireframes/ | `docs/pre-dev/{feature}/` | `{frontend.path}/docs/pre-dev/{feature}/` | Frontend repo |
```

**Step 3: Verify the changes**

Run: `grep -n "frontend.path" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-prd-creation/SKILL.md | head -3`

**Expected output:**
```
[line numbers showing frontend.path references]
```

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-prd-creation/SKILL.md
git commit -m "feat(prd): add module-aware document placement for prd and UX docs"
```

**If Task Fails:**
1. **Section not found:** Search for `## Phase 4` or `## Output & After Approval`
2. **Outputs section differs:** Adapt to match actual structure

---

### Task T-007: Update pre-dev-trd-creation Skill with Placement Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-trd-creation/SKILL.md`

**Prerequisites:**
- File must exist: `pm-team/skills/pre-dev-trd-creation/SKILL.md`

**Step 1: Add Document Placement section**

Find `## Output & After Approval` section (around line 452) and add placement logic before it:

```markdown
---

## Document Placement

**trd.md is a shared document** - it defines architecture for the entire feature.

| Structure | trd.md Location |
|-----------|-----------------|
| single-repo | `docs/pre-dev/{feature}/trd.md` |
| monorepo | `docs/pre-dev/{feature}/trd.md` (root) |
| multi-repo | Write to BOTH repos |

**Multi-repo handling:**

```bash
# Read topology from research.md frontmatter
if [[ "$structure" == "multi-repo" ]]; then
    # Write to both repositories
    mkdir -p "{backend.path}/docs/pre-dev/{feature}"
    mkdir -p "{frontend.path}/docs/pre-dev/{feature}"

    # Write TRD to primary (backend)
    # Then copy to frontend
    cp "{backend.path}/docs/pre-dev/{feature}/trd.md" "{frontend.path}/docs/pre-dev/{feature}/trd.md"
fi
```

**Sync footer for multi-repo:**
```markdown
---
**Sync Status:** Architecture document maintained in both repositories.
```

---
```

**Step 2: Update Output line**

**Old (around line 452):**
```markdown
**Output to:** `docs/pre-dev/{feature-name}/trd.md`
```

**New:**
```markdown
**Output to:**
- **single-repo/monorepo:** `docs/pre-dev/{feature-name}/trd.md`
- **multi-repo:** Both `{backend.path}/docs/pre-dev/{feature}/trd.md` AND `{frontend.path}/docs/pre-dev/{feature}/trd.md`
```

**Step 3: Verify the changes**

Run: `grep -n "multi-repo" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-trd-creation/SKILL.md | head -3`

**Expected output:**
```
[line numbers showing multi-repo references]
```

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-trd-creation/SKILL.md
git commit -m "feat(trd): add module-aware document placement logic"
```

**If Task Fails:**
1. **Section not found:** Search for `## Output & After Approval`
2. **Line numbers differ:** Adjust based on actual file content

---

### Task T-008: Update pre-dev-api-design Skill with Placement Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-api-design/SKILL.md`

**Prerequisites:**
- File must exist: `pm-team/skills/pre-dev-api-design/SKILL.md`

**Step 1: Add Document Placement section before Output**

Find `## After Approval` section (around line 175) and add before it:

```markdown
---

## Document Placement

**api-design.md is a backend document** - it defines API contracts implemented by backend services.

| Structure | api-design.md Location |
|-----------|------------------------|
| single-repo | `docs/pre-dev/{feature}/api-design.md` |
| monorepo | `{backend.path}/docs/pre-dev/{feature}/api-design.md` |
| multi-repo | `{backend.path}/docs/pre-dev/{feature}/api-design.md` |

**Why backend path?** API contracts are:
- Implemented by backend engineers
- Referenced during backend code review
- Versioned with backend code

**Directory creation for multi-module:**
```bash
# Read topology from research.md frontmatter
backend_path="${topology_modules_backend_path:-"."}"
mkdir -p "${backend_path}/docs/pre-dev/{feature}"
```

---
```

**Step 2: Update Contract Template Structure output path**

Find `## Contract Template Structure` section and update output line:

**Old (around line 110):**
```markdown
Output to `docs/pre-dev/{feature-name}/api-design.md` with these sections:
```

**New:**
```markdown
Output to (path depends on topology.structure):
- **single-repo:** `docs/pre-dev/{feature-name}/api-design.md`
- **monorepo/multi-repo:** `{backend.path}/docs/pre-dev/{feature-name}/api-design.md`
```

**Step 3: Verify the changes**

Run: `grep -n "backend.path" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-api-design/SKILL.md`

**Expected output:**
```
[line numbers showing backend.path references]
```

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-api-design/SKILL.md
git commit -m "feat(api-design): add module-aware document placement logic"
```

**If Task Fails:**
1. **Section not found:** Search for `## After Approval` or `## Contract Template`
2. **Adapt to actual structure** if content differs

---

### Task T-009: Update pre-dev-data-model Skill with Placement Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-data-model/SKILL.md`

**Prerequisites:**
- File must exist: `pm-team/skills/pre-dev-data-model/SKILL.md`

**Step 1: Add Document Placement section before Output**

Find `## After Approval` section (around line 169) and add before it:

```markdown
---

## Document Placement

**data-model.md is a backend document** - it defines entity structures owned by backend services.

| Structure | data-model.md Location |
|-----------|------------------------|
| single-repo | `docs/pre-dev/{feature}/data-model.md` |
| monorepo | `{backend.path}/docs/pre-dev/{feature}/data-model.md` |
| multi-repo | `{backend.path}/docs/pre-dev/{feature}/data-model.md` |

**Why backend path?** Data models are:
- Implemented as database schemas by backend engineers
- Define entities owned by backend components
- Versioned with backend database migrations

**Directory creation for multi-module:**
```bash
# Read topology from research.md frontmatter
backend_path="${topology_modules_backend_path:-"."}"
mkdir -p "${backend_path}/docs/pre-dev/{feature}"
```

---
```

**Step 2: Update Data Model Template Structure output path**

Find `## Data Model Template Structure` section and update output line:

**Old (around line 109):**
```markdown
Output to `docs/pre-dev/{feature-name}/data-model.md` with these sections:
```

**New:**
```markdown
Output to (path depends on topology.structure):
- **single-repo:** `docs/pre-dev/{feature-name}/data-model.md`
- **monorepo/multi-repo:** `{backend.path}/docs/pre-dev/{feature-name}/data-model.md`
```

**Step 3: Verify the changes**

Run: `grep -n "backend.path" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-data-model/SKILL.md`

**Expected output:**
```
[line numbers showing backend.path references]
```

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-data-model/SKILL.md
git commit -m "feat(data-model): add module-aware document placement logic"
```

**If Task Fails:**
1. **Section not found:** Search for `## After Approval` or `## Data Model Template`
2. **Adapt to actual structure** if content differs

---

### Task T-010: Update pre-dev-task-breakdown Skill with Split Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-task-breakdown/SKILL.md`

**Prerequisites:**
- File must exist: `pm-team/skills/pre-dev-task-breakdown/SKILL.md`

**Step 1: Expand Per-Module Output section**

Find `### Per-Module Output (if doc_organization: per-module)` section (around line 218) and expand it:

**Old:**
```markdown
### Per-Module Output (if doc_organization: per-module)

When `topology.doc_organization: per-module`, generate split task files:

```
docs/pre-dev/{feature}/
├── tasks.md           # Index with all tasks (includes target tags)
├── backend/
│   └── tasks.md       # Backend tasks only (filtered by target: backend)
└── frontend/
    └── tasks.md       # Frontend tasks only (filtered by target: frontend)
```
```

**New:**
```markdown
### Per-Module Output

**Document placement depends on topology.structure:**

#### Single-Repo

All tasks in one file:
```
docs/pre-dev/{feature}/
└── tasks.md           # All tasks with target tags
```

#### Monorepo (per-module placement)

Index at root, filtered tasks in module directories:
```
docs/pre-dev/{feature}/
└── tasks.md           # Index with ALL tasks (target tags included)

{backend.path}/docs/pre-dev/{feature}/
└── tasks.md           # Backend tasks only (target: backend)

{frontend.path}/docs/pre-dev/{feature}/
└── tasks.md           # Frontend tasks only (target: frontend)
```

#### Multi-Repo (distributed placement)

Tasks distributed to respective repositories:
```
{backend.path}/docs/pre-dev/{feature}/
└── tasks.md           # Backend tasks only

{frontend.path}/docs/pre-dev/{feature}/
└── tasks.md           # Frontend tasks only
```

**Note:** For multi-repo, there is no central index. Each repo contains only its relevant tasks.

### Task Splitting Logic

```python
def split_tasks_by_module(all_tasks: list, topology: dict) -> dict:
    """
    Split tasks into module-specific files.

    Returns dict with keys: 'index', 'backend', 'frontend'
    """
    structure = topology.get('structure', 'single-repo')
    modules = topology.get('modules', {})
    backend_path = modules.get('backend', {}).get('path', '.')
    frontend_path = modules.get('frontend', {}).get('path', '.')

    backend_tasks = [t for t in all_tasks if t.get('target') == 'backend']
    frontend_tasks = [t for t in all_tasks if t.get('target') == 'frontend']
    shared_tasks = [t for t in all_tasks if t.get('target') == 'shared']

    if structure == 'single-repo':
        return {
            'index': {
                'path': f"docs/pre-dev/{feature}/tasks.md",
                'tasks': all_tasks
            }
        }

    if structure == 'monorepo':
        return {
            'index': {
                'path': f"docs/pre-dev/{feature}/tasks.md",
                'tasks': all_tasks
            },
            'backend': {
                'path': f"{backend_path}/docs/pre-dev/{feature}/tasks.md",
                'tasks': backend_tasks + shared_tasks
            },
            'frontend': {
                'path': f"{frontend_path}/docs/pre-dev/{feature}/tasks.md",
                'tasks': frontend_tasks + shared_tasks
            }
        }

    if structure == 'multi-repo':
        return {
            'backend': {
                'path': f"{backend_path}/docs/pre-dev/{feature}/tasks.md",
                'tasks': backend_tasks + shared_tasks
            },
            'frontend': {
                'path': f"{frontend_path}/docs/pre-dev/{feature}/tasks.md",
                'tasks': frontend_tasks + shared_tasks
            }
        }
```

### Module-Specific Task File Header

Each module-specific tasks.md should include:

```markdown
---
feature: {feature-name}
module: backend | frontend
filtered_from: docs/pre-dev/{feature}/tasks.md  # (monorepo only)
total_tasks: N
---

# {Feature Name} - {Module} Tasks

This file contains tasks filtered for the **{module}** module.

**Full task list:** {link to index if monorepo, or note "distributed" if multi-repo}

---
```
```

**Step 2: Update Output & After Approval section**

Find `## Output & After Approval` section and update:

**Old (around line 287):**
```markdown
**Output to:** `docs/pre-dev/{feature-name}/tasks.md`
```

**New:**
```markdown
**Output to (depends on topology.structure):**

| Structure | Files Generated |
|-----------|-----------------|
| single-repo | `docs/pre-dev/{feature}/tasks.md` |
| monorepo | Index + `{backend.path}/docs/pre-dev/{feature}/tasks.md` + `{frontend.path}/docs/pre-dev/{feature}/tasks.md` |
| multi-repo | `{backend.path}/docs/pre-dev/{feature}/tasks.md` + `{frontend.path}/docs/pre-dev/{feature}/tasks.md` |
```

**Step 3: Verify the changes**

Run: `grep -n "split_tasks_by_module" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-task-breakdown/SKILL.md`

**Expected output:**
```
[line number]: def split_tasks_by_module...
```

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-task-breakdown/SKILL.md
git commit -m "feat(tasks): add module-aware task splitting and placement logic"
```

**If Task Fails:**
1. **Section not found:** Search for `### Per-Module Output`
2. **Content differs:** Adapt to actual structure

---

### Task T-011: Update pre-dev-feature Command with Placement Summary

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-feature.md`

**Prerequisites:**
- File must exist: `pm-team/commands/pre-dev-feature.md`

**Step 1: Add doc_placement to TopologyConfig Output**

Find `**TopologyConfig Output:**` section (around line 75) and update:

**Old:**
```yaml
Topology Configuration:
  scope: fullstack | backend-only | frontend-only
  structure: single-repo | monorepo | multi-repo
  modules:  # (only if monorepo or multi-repo)
    backend:
      path: [user input]
      language: [auto-detected]
    frontend:
      path: [user input]
      framework: [auto-detected]
  doc_organization: unified | per-module
  api_pattern: direct | bff | other  # (only if fullstack)
```

**New:**
```yaml
Topology Configuration:
  scope: fullstack | backend-only | frontend-only
  structure: single-repo | monorepo | multi-repo
  modules:  # (only if monorepo or multi-repo)
    backend:
      path: [user input]
      language: [auto-detected]
    frontend:
      path: [user input]
      framework: [auto-detected]
  doc_organization: unified | per-module
  doc_placement: unified | per-module | distributed  # NEW: derived from structure
  api_pattern: direct | bff | other  # (only if fullstack)
```

**Step 2: Update After Completion section**

Find `## After Completion` section (around line 309) and update the artifacts list:

**Old:**
```markdown
Artifacts created:
- docs/pre-dev/<feature-name>/research.md (Gate 0) - includes Product/UX Research
- docs/pre-dev/<feature-name>/prd.md (Gate 1)
- docs/pre-dev/<feature-name>/ux-criteria.md (Gate 1) - UX acceptance criteria
- docs/pre-dev/<feature-name>/wireframes/ (Gate 1) - if feature has UI
  - {screen-name}.yaml - low-fidelity prototypes
  - user-flows.md - user flow diagrams
- docs/pre-dev/<feature-name>/trd.md (Gate 2)
- docs/pre-dev/<feature-name>/tasks.md (Gate 3)
```

**New:**
```markdown
Artifacts created (paths depend on topology.structure):

**For single-repo:**
- docs/pre-dev/<feature-name>/research.md
- docs/pre-dev/<feature-name>/prd.md
- docs/pre-dev/<feature-name>/ux-criteria.md
- docs/pre-dev/<feature-name>/wireframes/
- docs/pre-dev/<feature-name>/trd.md
- docs/pre-dev/<feature-name>/tasks.md

**For monorepo:**
- docs/pre-dev/<feature-name>/research.md (root - shared)
- docs/pre-dev/<feature-name>/prd.md (root - shared)
- docs/pre-dev/<feature-name>/trd.md (root - shared)
- docs/pre-dev/<feature-name>/tasks.md (root - index)
- {frontend.path}/docs/pre-dev/<feature-name>/ux-criteria.md
- {frontend.path}/docs/pre-dev/<feature-name>/wireframes/
- {frontend.path}/docs/pre-dev/<feature-name>/tasks.md (filtered)
- {backend.path}/docs/pre-dev/<feature-name>/tasks.md (filtered)

**For multi-repo:**
- Both repos: research.md, prd.md, trd.md (synchronized)
- Frontend repo: ux-criteria.md, wireframes/, tasks.md
- Backend repo: tasks.md
```

**Step 3: Verify the changes**

Run: `grep -n "doc_placement" /home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-feature.md`

**Expected output:**
```
[line number]: doc_placement: unified | per-module | distributed
```

**Step 4: Commit**

```bash
git add pm-team/commands/pre-dev-feature.md
git commit -m "feat(pre-dev-feature): add doc_placement to config and update artifact paths"
```

**If Task Fails:**
1. **Section not found:** Search for `TopologyConfig Output` or `## After Completion`
2. **Content differs:** Adapt to actual structure

---

### Task T-012: Update pre-dev-full Command with Placement Summary

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-full.md`

**Prerequisites:**
- File must exist: `pm-team/commands/pre-dev-full.md`

**Step 1: Add doc_placement to TopologyConfig Output**

Find `**TopologyConfig Output:**` section (around line 75) and update (same as T-011):

**Old:**
```yaml
Topology Configuration:
  scope: fullstack | backend-only | frontend-only
  structure: single-repo | monorepo | multi-repo
  modules:  # (only if monorepo or multi-repo)
    backend:
      path: [user input]
      language: [auto-detected]
    frontend:
      path: [user input]
      framework: [auto-detected]
  doc_organization: unified | per-module
  api_pattern: direct | bff | other  # (only if fullstack)
```

**New:**
```yaml
Topology Configuration:
  scope: fullstack | backend-only | frontend-only
  structure: single-repo | monorepo | multi-repo
  modules:  # (only if monorepo or multi-repo)
    backend:
      path: [user input]
      language: [auto-detected]
    frontend:
      path: [user input]
      framework: [auto-detected]
  doc_organization: unified | per-module
  doc_placement: unified | per-module | distributed  # NEW: derived from structure
  api_pattern: direct | bff | other  # (only if fullstack)
```

**Step 2: Update After Completion section**

Find `## After Completion` section (around line 416) and update the artifacts list:

**Old:**
```markdown
Artifacts created:
- docs/pre-dev/<feature-name>/research.md (Gate 0) - includes Product/UX Research
- docs/pre-dev/<feature-name>/prd.md (Gate 1)
- docs/pre-dev/<feature-name>/ux-criteria.md (Gate 1) <- NEW - UX acceptance criteria
- docs/pre-dev/<feature-name>/feature-map.md (Gate 2)
- docs/pre-dev/<feature-name>/user-flows.md (Gate 2) <- NEW - Detailed user flows
- docs/pre-dev/<feature-name>/wireframes/ (Gate 2) <- NEW - Wireframe specs (YAML)
- docs/pre-dev/<feature-name>/trd.md (Gate 3)
- docs/pre-dev/<feature-name>/api-design.md (Gate 4)
- docs/pre-dev/<feature-name>/data-model.md (Gate 5)
- docs/pre-dev/<feature-name>/dependency-map.md (Gate 6)
- docs/pre-dev/<feature-name>/tasks.md (Gate 7)
- docs/pre-dev/<feature-name>/subtasks.md (Gate 8)
```

**New:**
```markdown
Artifacts created (paths depend on topology.structure):

**For single-repo (all in docs/pre-dev/<feature-name>/):**
- research.md, prd.md, feature-map.md, trd.md
- ux-criteria.md, user-flows.md, wireframes/
- api-design.md, data-model.md, dependency-map.md
- tasks.md, subtasks.md

**For monorepo (distributed by module):**
*Root (shared):* research.md, prd.md, feature-map.md, trd.md, tasks.md (index)
*Backend module:* api-design.md, data-model.md, dependency-map.md, tasks.md
*Frontend module:* ux-criteria.md, user-flows.md, wireframes/, dependency-map.md, tasks.md

**For multi-repo (per-repository):**
*Both repos:* research.md, prd.md, trd.md (synchronized)
*Backend repo:* api-design.md, data-model.md, dependency-map.md, tasks.md
*Frontend repo:* ux-criteria.md, user-flows.md, wireframes/, dependency-map.md, tasks.md
```

**Step 3: Verify the changes**

Run: `grep -n "doc_placement" /home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-full.md`

**Expected output:**
```
[line number]: doc_placement: unified | per-module | distributed
```

**Step 4: Commit**

```bash
git add pm-team/commands/pre-dev-full.md
git commit -m "feat(pre-dev-full): add doc_placement to config and update artifact paths"
```

**If Task Fails:**
1. **Section not found:** Search for `TopologyConfig Output` or `## After Completion`
2. **Content differs:** Adapt to actual structure

---

### Task T-013: Run Code Review

**Prerequisites:**
- All previous tasks (T-001 through T-012) completed

**Step 1: Dispatch all 3 reviewers in parallel**

- REQUIRED SUB-SKILL: Use requesting-code-review
- All reviewers run simultaneously:
  - code-reviewer
  - business-logic-reviewer
  - security-reviewer
- Wait for all to complete

**Step 2: Handle findings by severity (MANDATORY)**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 3 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on [date], severity: Cosmetic)`

**Step 3: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments added
- All Cosmetic issues have FIXME(nitpick): comments added

**Step 4: Final Commit**

```bash
git add -A
git commit -m "chore: address code review findings for doc-placement feature"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `topology-discovery.md` has `doc_placement` in all schema examples
- [ ] `topology-discovery.md` has Documentation Path Resolution section
- [ ] `topology.md` has Section 9: Documentation Placement
- [ ] `topology.md` Section 6 references auto-placement instead of manual workarounds
- [ ] `pre-dev-research/SKILL.md` handles multi-repo document placement
- [ ] `pre-dev-prd-creation/SKILL.md` places UX docs in frontend path
- [ ] `pre-dev-trd-creation/SKILL.md` handles multi-repo sync
- [ ] `pre-dev-api-design/SKILL.md` outputs to backend path
- [ ] `pre-dev-data-model/SKILL.md` outputs to backend path
- [ ] `pre-dev-task-breakdown/SKILL.md` splits tasks by module
- [ ] `pre-dev-feature.md` shows doc_placement in config
- [ ] `pre-dev-full.md` shows doc_placement in config
- [ ] All changes pass code review

---

## Rollback Plan

If issues are discovered after implementation:

```bash
# Revert all changes (if not yet pushed)
git reset --hard HEAD~{number_of_commits}

# Or revert specific commit
git revert {commit_hash}
```

---

## Future Enhancements (Out of Scope)

1. **Automatic sync tool** - Script to keep multi-repo docs in sync
2. **Pre-commit hook** - Validate doc placement matches topology
3. **CI check** - Verify documents exist in expected locations
4. **Doc linking** - Cross-references between module docs
