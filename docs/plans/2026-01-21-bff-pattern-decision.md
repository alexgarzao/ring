# BFF Pattern Decision Support Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add BFF (Backend-for-Frontend) pattern decision support to Ring's pre-dev workflow, capturing the decision during Topology Discovery and propagating it through TRD, Task Breakdown, and Writing Plans.

**Architecture:** Extend existing TopologyConfig schema to include `api_pattern` field. The pattern decision flows through all pre-dev gates, influencing agent assignment in Task Breakdown and Writing Plans.

**Tech Stack:** Markdown documentation, YAML frontmatter, Ring pre-dev workflow skills

**Global Prerequisites:**
- Environment: Linux/macOS with bash
- Tools: Text editor, git
- Access: Write access to Ring repository
- State: Clean working tree on main branch or feature branch

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
git status        # Expected: clean working tree or feature branch
ls pm-team/skills/shared-patterns/  # Expected: topology-discovery.md exists
ls pm-team/docs/standards/          # Expected: topology.md exists
```

## Historical Precedent

**Query:** "bff backend frontend topology api pattern"
**Index Status:** Empty (new project)

No historical data available. This is normal for new projects.
Proceeding with standard planning approach.

---

## Task 1: Add Q5 API Pattern Question to Topology Discovery

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Prerequisites:**
- File must exist at the path above

**Step 1: Read the current topology-discovery.md**

Verify the file structure and locate the Questions Flow section.

Run: `head -80 /home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Expected output:** Shows the Questions Flow section with Q1-Q4

**Step 2: Add Q5 to Questions Flow diagram**

After the Q4 block in the Questions Flow section (around line 37), add:

```markdown
Q5: API Pattern? (only if scope=fullstack)
├─ direct → Set api_pattern: direct
├─ bff → Set api_pattern: bff
└─ other → Ask for specification, set api_pattern: other
```

**Step 3: Add Q5 AskUserQuestion Implementation**

After the Q4: Doc Organization section (around line 150), add a new section:

```markdown
### Q5: Frontend API Pattern

**Only ask if `scope: fullstack`**

```json
{
  "question": "How will the frontend communicate with backend services?",
  "header": "API Pattern",
  "multiSelect": false,
  "options": [
    {
      "label": "Direct API calls (Recommended for simple features)",
      "description": "Frontend calls backend APIs directly. Best for single backend service, no aggregation needed."
    },
    {
      "label": "BFF (Backend-for-Frontend) layer",
      "description": "Frontend calls BFF which aggregates/transforms data from multiple backends. Best for complex data needs."
    },
    {
      "label": "Other (specify)",
      "description": "Custom pattern - describe your approach"
    }
  ]
}
```

**Processing:**
- "Direct API calls" → `api_pattern: direct`
- "BFF" → `api_pattern: bff`
- "Other" → Ask follow-up: "Describe your API pattern", set `api_pattern: other`, store description

**When to recommend each pattern:**

| Pattern | Recommend When |
|---------|---------------|
| **Direct** | Single backend service, simple CRUD, no aggregation, <3 API calls per page |
| **BFF** | Multiple backend services, data aggregation needed, complex transformations, sensitive keys to hide |
| **Other** | GraphQL federation, tRPC, custom gateway, existing patterns |
```

**Step 4: Run verification**

Run: `grep -n "Q5:" /home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Expected output:** Shows line numbers where Q5 was added

**Step 5: Commit**

```bash
git add pm-team/skills/shared-patterns/topology-discovery.md
git commit -m "feat(pre-dev): add Q5 API Pattern question to topology discovery

Add question to determine frontend-backend communication pattern:
- Direct API calls (recommended for simple features)
- BFF layer (for data aggregation and transformation)
- Other (custom patterns)

Question only appears for fullstack scope features."
```

---

## Task 2: Add api_pattern to TopologyConfig Schema

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Prerequisites:**
- Task 1 completed

**Step 1: Locate the TopologyConfig section**

Run: `grep -n "TopologyConfig" /home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md | head -5`

**Expected output:** Shows line numbers for TopologyConfig sections

**Step 2: Update the Output: TopologyConfig section**

Find the TopologyConfig examples and add `api_pattern` field to fullstack configurations.

Update the "Single-repo Fullstack" example:

```yaml
### Single-repo Fullstack

```yaml
topology:
  scope: fullstack
  structure: single-repo
  doc_organization: unified  # or per-module
  api_pattern: direct | bff | other  # NEW: API communication pattern
```
```

Update the "Monorepo Fullstack" example:

```yaml
### Monorepo Fullstack

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
  api_pattern: bff              # From Q5 - NEW
```
```

Update the "Multi-repo Fullstack" example:

```yaml
### Multi-repo Fullstack

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
  api_pattern: direct                           # From Q5 - NEW
```
```

**Step 3: Verify changes**

Run: `grep -A2 "api_pattern" /home/drax/Documentos/vscode/ring/pm-team/skills/shared-patterns/topology-discovery.md`

**Expected output:** Shows api_pattern in multiple TopologyConfig examples

**Step 4: Commit**

```bash
git add pm-team/skills/shared-patterns/topology-discovery.md
git commit -m "feat(pre-dev): add api_pattern field to TopologyConfig schema

Add api_pattern field to fullstack topology configurations.
Values: direct | bff | other

This field is determined by Q5 and propagated through all gates."
```

---

## Task 3: Update Topology Standards with API Pattern Section

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md`

**Prerequisites:**
- Tasks 1-2 completed

**Step 1: Read current topology.md structure**

Run: `head -30 /home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md`

**Expected output:** Shows Table of Contents with 7 sections

**Step 2: Update Table of Contents**

Add a new row to the Table of Contents after section 7:

```markdown
| 8 | [API Pattern](#8-api-pattern) | direct, bff, or custom patterns |
```

**Step 3: Add Section 8: API Pattern**

After the "## 7. PROJECT_RULES.md Hierarchy" section and before the "## Checklist" section, add:

```markdown
---

## 8. API Pattern

API Pattern determines how the frontend communicates with backend services and affects agent assignment.

### Pattern Options

| Pattern | Description | Use When |
|---------|-------------|----------|
| `direct` | Frontend calls backend APIs directly | Single backend, simple CRUD, no aggregation |
| `bff` | Frontend calls BFF layer which aggregates backends | Multiple backends, complex transformations, sensitive keys |
| `other` | Custom pattern (GraphQL, tRPC, gateway) | Existing patterns, specific requirements |

### Pattern Decision Criteria

| Criteria | Direct | BFF |
|----------|--------|-----|
| Number of backend services | 1 | 2+ |
| Data aggregation needed | No | Yes |
| Complex transformations | No | Yes |
| API calls per page | <3 | 3+ |
| Sensitive keys to hide | No | Yes |
| Request optimization | Not needed | Needed |

### Agent Assignment by Pattern

| API Pattern | Frontend Tasks | Agent |
|-------------|----------------|-------|
| `direct` | UI components, pages, forms | `frontend-engineer` |
| `direct` | Server Actions, data fetching | `frontend-engineer` (Next.js Server Components) |
| `bff` | API routes, data aggregation | `frontend-bff-engineer-typescript` |
| `bff` | UI components, pages | `frontend-engineer` |

### Pattern in TopologyConfig

```yaml
topology:
  scope: fullstack
  structure: single-repo
  api_pattern: bff  # Determines agent assignment
```

### Defaults

| Scope | Default Pattern | Rationale |
|-------|-----------------|-----------|
| `fullstack` | `direct` | Simpler architecture, most features don't need BFF |
| `frontend-only` | N/A | Frontend-only already implies client-side |
| `backend-only` | N/A | No frontend to consider |
```

**Step 4: Update Checklist**

Add a new checkbox to the Checklist section:

```markdown
- [ ] api_pattern captured for fullstack features
```

**Step 5: Verify structure**

Run: `grep -n "## 8" /home/drax/Documentos/vscode/ring/pm-team/docs/standards/topology.md`

**Expected output:** Shows section 8 at expected line number

**Step 6: Commit**

```bash
git add pm-team/docs/standards/topology.md
git commit -m "feat(pre-dev): add API Pattern section to topology standards

Document the api_pattern field with:
- Pattern options (direct, bff, other)
- Decision criteria table
- Agent assignment rules
- Default behaviors

This guides pre-dev workflow in capturing the pattern decision."
```

---

## Task 4: Update pre-dev-research to Persist api_pattern

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-research/SKILL.md`

**Prerequisites:**
- Tasks 1-3 completed

**Step 1: Locate frontmatter template in pre-dev-research**

Run: `grep -n "frontmatter" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-research/SKILL.md`

**Expected output:** Shows lines referencing frontmatter

**Step 2: Update the frontmatter template**

Find the "Persist in research.md frontmatter" section (around line 99-118) and add `api_pattern`:

```yaml
---
feature: {feature-name}
gate: 0
date: {YYYY-MM-DD}
research_mode: greenfield | modification | integration
agents_dispatched: 4
topology:
  scope: fullstack | backend-only | frontend-only
  structure: single-repo | monorepo | multi-repo
  modules:  # Only if monorepo or multi-repo
    backend:
      path: {path}
      language: golang | typescript
    frontend:
      path: {path}
      framework: nextjs | react | vue
  doc_organization: unified | per-module
  api_pattern: direct | bff | other  # NEW: Only if scope=fullstack
---
```

**Step 3: Verify the change**

Run: `grep -A20 "Persist in research.md" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-research/SKILL.md | grep "api_pattern"`

**Expected output:** Shows api_pattern in the frontmatter template

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-research/SKILL.md
git commit -m "feat(pre-dev): persist api_pattern in research.md frontmatter

Add api_pattern field to the TopologyConfig persisted in Gate 0.
This ensures the pattern decision flows through all subsequent gates."
```

---

## Task 5: Add Integration Patterns Section to TRD Creation

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-trd-creation/SKILL.md`

**Prerequisites:**
- Tasks 1-4 completed

**Step 1: Read TRD creation structure**

Run: `grep -n "##" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-trd-creation/SKILL.md | head -30`

**Expected output:** Shows section headers

**Step 2: Add Integration Patterns section**

After the "## Authentication/Authorization Architecture" section (around line 201), add:

```markdown
## Frontend-Backend Integration Pattern (If Fullstack)

**⛔ HARD GATE:** If the feature is fullstack (`topology.scope: fullstack`), this section is MANDATORY.

### Step 1: Read api_pattern from research.md

The api_pattern was determined during Topology Discovery (Q5) and persisted in research.md frontmatter.

```yaml
# From research.md frontmatter
topology:
  scope: fullstack
  api_pattern: direct | bff | other
```

### Step 2: Document Pattern in TRD

**TRD must include a `## Integration Patterns` section:**

```markdown
## Integration Patterns

### Frontend-Backend Communication

**Pattern:** [direct | bff | other]

**Rationale:** [Why this pattern was chosen]

**Architecture Implications:**
- [List architectural decisions driven by this pattern]
```

### Pattern-Specific Documentation

**If `api_pattern: direct`:**

```markdown
### Frontend-Backend Communication

**Pattern:** Direct API calls

**Rationale:** Single backend service, simple CRUD operations, no data aggregation needed.

**Architecture Implications:**
- Frontend components call backend API directly via fetch/axios
- No intermediate layer required
- Authentication tokens managed client-side (httpOnly cookies recommended)
- Error handling at component level

**Data Flow:**
```
Frontend Component → Backend API → Database
```
```

**If `api_pattern: bff`:**

```markdown
### Frontend-Backend Communication

**Pattern:** BFF (Backend-for-Frontend) layer

**Rationale:** [Multiple backend services | Complex data aggregation | Sensitive keys to hide | Request optimization needed]

**Architecture Implications:**
- Frontend calls BFF API routes (Next.js API Routes recommended)
- BFF aggregates data from multiple backend services
- Sensitive API keys stored server-side in BFF
- Response transformation happens in BFF layer
- Frontend receives optimized, frontend-specific data shapes

**Data Flow:**
```
Frontend Component → BFF API Route → Backend Service(s) → Database(s)
```

**BFF Responsibilities:**
- Data aggregation from multiple services
- Response transformation for frontend consumption
- Authentication token management
- Rate limiting and caching
- Error normalization
```

**If `api_pattern: other`:**

```markdown
### Frontend-Backend Communication

**Pattern:** [User-specified pattern]

**Rationale:** [User-provided rationale]

**Architecture Implications:**
- [Document specific implications]
```

### Rationalization Table for Integration Patterns

| Excuse | Reality |
|--------|---------|
| "API pattern doesn't affect architecture" | Pattern determines data flow, error handling, and layer responsibilities. Document it. |
| "We can decide direct vs BFF later" | Architecture depends on this choice. Decide now to inform component design. |
| "BFF is overkill for our feature" | If research.md says `api_pattern: bff`, honor the decision. It was made with context. |
| "Just use direct for simplicity" | Simplicity isn't always correct. Follow the topology decision. |
```

**Step 3: Verify the change**

Run: `grep -n "Integration Pattern" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-trd-creation/SKILL.md`

**Expected output:** Shows the new section at expected line

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-trd-creation/SKILL.md
git commit -m "feat(pre-dev): add Integration Patterns section to TRD creation

Add documentation requirements for api_pattern in TRD:
- Read pattern from research.md frontmatter
- Document pattern with rationale
- Include pattern-specific architecture implications
- Add rationalization table for pattern decisions

This ensures the topology decision is properly documented in Gate 3."
```

---

## Task 6: Update Task Breakdown with Agent Assignment Rules

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-task-breakdown/SKILL.md`

**Prerequisites:**
- Tasks 1-5 completed

**Step 1: Locate Task Target Assignment section**

Run: `grep -n "Task Target Assignment" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-task-breakdown/SKILL.md`

**Expected output:** Shows line number (around line 136)

**Step 2: Update Task Target Assignment section**

Replace the existing table with an expanded version that includes api_pattern:

```markdown
### Task Target Assignment

Each task MUST have `target:` and `working_directory:` fields when topology is multi-module.

**Agent assignment depends on both `target` and `api_pattern`:**

| Target | API Pattern | Task Type | Agent |
|--------|-------------|-----------|-------|
| `backend` | any | API endpoints, services, data layer, CLI | `ring:backend-engineer-golang` or `ring:backend-engineer-typescript` |
| `frontend` | `direct` | UI components, pages, forms, Server Components | `ring:frontend-engineer` |
| `frontend` | `direct` | Server Actions, data fetching hooks | `ring:frontend-engineer` |
| `frontend` | `bff` | API routes, data aggregation, transformation | `ring:frontend-bff-engineer-typescript` |
| `frontend` | `bff` | UI components, pages, forms | `ring:frontend-engineer` |
| `shared` | any | CI/CD, configs, docs, cross-module utilities | DevOps or general |

### How to Determine Agent for Frontend Tasks

**Read `api_pattern` from research.md frontmatter:**

```yaml
# From research.md
topology:
  scope: fullstack
  api_pattern: direct | bff | other
```

**Decision Flow:**

```
Is task target: frontend?
├─ NO → Use backend-engineer-* based on language
└─ YES → Check api_pattern
    ├─ direct → ALL frontend tasks use frontend-engineer
    └─ bff → Split tasks:
        ├─ API routes, aggregation, transformation → frontend-bff-engineer-typescript
        └─ UI components, pages, forms → frontend-engineer
```

### Task Format with Agent Assignment

```markdown
## T-003: User Login API Endpoint

**Target:** backend
**Working Directory:** packages/api
**Agent:** ring:backend-engineer-golang

**Deliverable:** Working login API that validates credentials and returns JWT token.

...rest of task...
```

```markdown
## T-004: User Dashboard Data Aggregation

**Target:** frontend
**Working Directory:** packages/web
**Agent:** ring:frontend-bff-engineer-typescript  # Because api_pattern: bff

**Deliverable:** BFF endpoint that aggregates user profile, recent activity, and notifications.

...rest of task...
```

```markdown
## T-005: User Dashboard UI

**Target:** frontend
**Working Directory:** packages/web
**Agent:** ring:frontend-engineer  # UI task, even with BFF pattern

**Deliverable:** Dashboard page component consuming aggregated data from BFF.

...rest of task...
```

### Validation for Agent Assignment

| Check | Requirement |
|-------|-------------|
| All tasks have `Agent:` field | MANDATORY |
| Agent matches api_pattern rules | If frontend + bff → check task type |
| BFF tasks clearly separated | Data aggregation vs UI clearly split |
| No mixed responsibilities | One task = one agent |
```

**Step 3: Verify the change**

Run: `grep -n "api_pattern" /home/drax/Documentos/vscode/ring/pm-team/skills/pre-dev-task-breakdown/SKILL.md`

**Expected output:** Shows api_pattern references in multiple places

**Step 4: Commit**

```bash
git add pm-team/skills/pre-dev-task-breakdown/SKILL.md
git commit -m "feat(pre-dev): add api_pattern-based agent assignment to task breakdown

Add agent assignment rules based on api_pattern:
- direct: all frontend tasks use frontend-engineer
- bff: API routes use frontend-bff-engineer-typescript, UI uses frontend-engineer

Includes decision flow, task format examples, and validation checklist."
```

---

## Task 7: Update Writing Plans with Agent Selection Logic

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/default/skills/writing-plans/SKILL.md`

**Prerequisites:**
- Tasks 1-6 completed

**Step 1: Locate Agent Selection section**

Run: `grep -n "Agent Selection" /home/drax/Documentos/vscode/ring/default/skills/writing-plans/SKILL.md`

**Expected output:** Shows line number (around line 147)

**Step 2: Update Agent Selection table**

Replace the existing Agent Selection section with:

```markdown
## Agent Selection

### Backend Tasks

| Task Type | Agent |
|-----------|-------|
| Go backend API/services | `backend-engineer-golang` |
| TypeScript backend API/services | `backend-engineer-typescript` |

### Frontend Tasks (api_pattern aware)

**Read `api_pattern` from topology configuration to determine correct agent:**

| API Pattern | Task Type | Agent |
|-------------|-----------|-------|
| `direct` | UI components, pages, forms | `frontend-engineer` |
| `direct` | Server Actions, data fetching | `frontend-engineer` |
| `direct` | Server Components with data loading | `frontend-engineer` |
| `bff` | API routes (`/api/*`) | `frontend-bff-engineer-typescript` |
| `bff` | Data aggregation, transformation | `frontend-bff-engineer-typescript` |
| `bff` | External service integration | `frontend-bff-engineer-typescript` |
| `bff` | UI components, pages, forms | `frontend-engineer` |
| `other` | Depends on pattern | Ask user or use frontend-engineer default |

### Decision Logic for Frontend Tasks

```
def get_frontend_agent(task, topology):
    api_pattern = topology.get('api_pattern', 'direct')

    if api_pattern == 'direct':
        return 'frontend-engineer'

    if api_pattern == 'bff':
        if is_bff_task(task):  # API routes, aggregation, transformation
            return 'frontend-bff-engineer-typescript'
        else:  # UI components, pages
            return 'frontend-engineer'

    return 'frontend-engineer'  # Default for 'other'

def is_bff_task(task):
    bff_indicators = [
        'API route', 'api route', '/api/',
        'aggregat', 'transform', 'BFF',
        'external service', 'backend service',
        'data layer', 'HTTP client'
    ]
    return any(ind in task.description for ind in bff_indicators)
```

### Infrastructure and Other Tasks

| Task Type | Agent |
|-----------|-------|
| Infra/CI/CD | `devops-engineer` |
| Testing | `qa-analyst` |
| Reliability | `sre` |
| Fallback | `general-purpose` (built-in, no prefix) |

### Task Format with api_pattern

When TopologyConfig includes `api_pattern`, include it in task metadata:

```markdown
## Task 3: Aggregate Dashboard Data

**Target:** frontend
**Working Directory:** packages/web
**API Pattern:** bff
**Agent:** ring:frontend-bff-engineer-typescript

**Files to Create/Modify:**
- `packages/web/app/api/dashboard/route.ts`
- `packages/web/lib/services/dashboard-aggregator.ts`

...rest of task...
```
```

**Step 3: Verify the change**

Run: `grep -n "api_pattern" /home/drax/Documentos/vscode/ring/default/skills/writing-plans/SKILL.md`

**Expected output:** Shows api_pattern references throughout the Agent Selection section

**Step 4: Commit**

```bash
git add default/skills/writing-plans/SKILL.md
git commit -m "feat(writing-plans): add api_pattern-aware agent selection

Update Agent Selection section with:
- Pattern-based frontend agent assignment table
- Decision logic pseudocode for frontend tasks
- BFF task indicators list
- Task format example with api_pattern

This ensures plans recommend correct agents based on topology decisions."
```

---

## Task 8: Update pre-dev-feature Command with Q5 Question

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-feature.md`

**Prerequisites:**
- Tasks 1-7 completed

**Step 1: Locate Question 6 (Styling) section**

Run: `grep -n "Question 6" /home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-feature.md`

**Expected output:** Shows Question 6 around line 150

**Step 2: Add Question 7 (API Pattern) after styling questions**

After the Q6 styling section and before "UI Configuration Summary", add:

```markdown
**Question 7 (MANDATORY if scope=fullstack):** "How will the frontend communicate with backend services?"
- **Trigger:** Only ask if topology scope = "Fullstack" (from Q1.1)
- Header: "API Pattern"
- Options:
  - "Direct API calls (Recommended for simple features)" - Frontend calls backend APIs directly
  - "BFF (Backend-for-Frontend) layer" - Frontend calls BFF which aggregates/transforms data
  - "Other (specify)" - Custom pattern (GraphQL, tRPC, custom gateway)
- **Auto-recommend based on feature complexity:**
  - If research.md indicates multiple backend services → Pre-select "BFF"
  - If simple CRUD feature → Pre-select "Direct API calls"
  - Otherwise → No pre-selection
- **Why this matters:** Determines which agent handles frontend tasks:
  - Direct → All frontend tasks use `frontend-engineer`
  - BFF → Data aggregation uses `frontend-bff-engineer-typescript`, UI uses `frontend-engineer`
- **CANNOT be skipped for fullstack features**
```

**Step 3: Update UI Configuration Summary**

Find "UI Configuration Summary" and update to include API Pattern:

```markdown
**Configuration Summary:** After topology and UI questions, display:
```
Feature Configuration:
- Scope: [fullstack | backend-only | frontend-only]
- Structure: [single-repo | monorepo | multi-repo]
- API Pattern: [direct | bff | other] (only for fullstack)
- Has UI: Yes/No
- UI Library: [choice] (if UI)
- Styling: [choice] (if UI)
```

**GATE BLOCKER:** If scope=fullstack but Q7 was not answered, DO NOT proceed to Gate 0. Return and ask the missing question.
```

**Step 4: Update TopologyConfig Output section**

Find the TopologyConfig Output section (around line 80) and add api_pattern:

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

**Step 5: Verify changes**

Run: `grep -n "Question 7\|api_pattern\|API Pattern" /home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-feature.md`

**Expected output:** Shows multiple references to Q7 and api_pattern

**Step 6: Commit**

```bash
git add pm-team/commands/pre-dev-feature.md
git commit -m "feat(pre-dev): add Q7 API Pattern question to /pre-dev-feature command

Add Question 7 for fullstack features to determine frontend-backend pattern:
- Direct API calls (recommended for simple features)
- BFF layer (for complex data aggregation)
- Other (custom patterns)

Update configuration summary and TopologyConfig output to include api_pattern.
Add gate blocker to ensure question is answered for fullstack features."
```

---

## Task 9: Update pre-dev-full Command with Q5 Question

**Files:**
- Modify: `/home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-full.md`

**Prerequisites:**
- Task 8 completed

**Step 1: Read pre-dev-full structure**

Run: `grep -n "Question\|Topology" /home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-full.md | head -20`

**Expected output:** Shows question structure similar to pre-dev-feature

**Step 2: Apply same changes as Task 8**

The pre-dev-full command should have the same API Pattern question (Q7) as pre-dev-feature. Apply identical changes:

1. Add Question 7 after styling questions (or after topology if no styling questions)
2. Update Configuration Summary to include api_pattern
3. Update TopologyConfig Output to include api_pattern
4. Add gate blocker for fullstack features

**Step 3: Verify changes**

Run: `grep -n "Question 7\|api_pattern\|API Pattern" /home/drax/Documentos/vscode/ring/pm-team/commands/pre-dev-full.md`

**Expected output:** Shows references to Q7 and api_pattern (similar to pre-dev-feature)

**Step 4: Commit**

```bash
git add pm-team/commands/pre-dev-full.md
git commit -m "feat(pre-dev): add Q7 API Pattern question to /pre-dev-full command

Mirror the API Pattern question from /pre-dev-feature:
- Same question, options, and processing
- Same configuration summary update
- Same gate blocker for fullstack features

Ensures consistency between small and full track workflows."
```

---

## Task 10: Run Code Review

**Prerequisites:**
- Tasks 1-9 completed

**Step 1: Dispatch all reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

Run 3 reviewers in parallel:
- code-reviewer
- business-logic-reviewer
- security-reviewer

**Step 2: Handle findings by severity**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments)
- Re-run all 3 reviewers after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments at relevant locations

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments at relevant locations

**Step 3: Proceed only when:**

- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments
- All Cosmetic issues have FIXME(nitpick): comments

---

## Task 11: Final Verification and Summary

**Prerequisites:**
- Tasks 1-10 completed

**Step 1: Verify all files modified**

Run: `git diff --name-only HEAD~9`

**Expected files:**
```
pm-team/skills/shared-patterns/topology-discovery.md
pm-team/docs/standards/topology.md
pm-team/skills/pre-dev-research/SKILL.md
pm-team/skills/pre-dev-trd-creation/SKILL.md
pm-team/skills/pre-dev-task-breakdown/SKILL.md
default/skills/writing-plans/SKILL.md
pm-team/commands/pre-dev-feature.md
pm-team/commands/pre-dev-full.md
```

**Step 2: Verify api_pattern flow**

Run: `grep -r "api_pattern" pm-team/ default/skills/writing-plans/`

**Expected output:** Shows api_pattern in:
- topology-discovery.md (question + schema)
- topology.md (standards)
- pre-dev-research/SKILL.md (frontmatter)
- pre-dev-trd-creation/SKILL.md (documentation)
- pre-dev-task-breakdown/SKILL.md (agent assignment)
- writing-plans/SKILL.md (agent selection)
- pre-dev-feature.md (question)
- pre-dev-full.md (question)

**Step 3: Run tests if available**

Run: `npm test 2>/dev/null || echo "No tests configured"`

**Step 4: Summary**

After all tasks complete, the BFF pattern decision support is fully integrated:

| Gate | File | Integration |
|------|------|-------------|
| Topology Discovery | topology-discovery.md | Q5 asks about API pattern |
| Gate 0 Research | pre-dev-research/SKILL.md | api_pattern persisted in frontmatter |
| Gate 3 TRD | pre-dev-trd-creation/SKILL.md | Integration Patterns section |
| Gate 7 Tasks | pre-dev-task-breakdown/SKILL.md | Agent assignment rules |
| Writing Plans | writing-plans/SKILL.md | Agent selection logic |
| Commands | pre-dev-feature.md, pre-dev-full.md | Q7 question added |

---

## If Task Fails

**General Recovery:**

1. **File not found:**
   - Check: `ls <path>` (file exists?)
   - Fix: Verify path is correct
   - Rollback: `git checkout -- <file>`

2. **Edit breaks syntax:**
   - Check: Read the file to verify structure
   - Fix: Re-apply edit with correct context
   - Rollback: `git checkout -- <file>`

3. **Git commit fails:**
   - Check: `git status` (files staged?)
   - Fix: Stage files with `git add`
   - Rollback: N/A

4. **Code review fails:**
   - Document: What reviewers flagged
   - Fix: Address issues per severity
   - Re-run: All reviewers after fixes

**If you cannot recover:**
- Document: What failed and why
- Stop: Return to human partner
- Do not: Try to fix without understanding
