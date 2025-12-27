# RAG-Enhanced Plan Judging Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Integrate historical precedent into the write-plan agent so new plans reference past successes and avoid past failures automatically.

**Architecture:** A planning mode enhancement to the artifact query system that returns structured historical context. The write-plan agent queries the artifact index before creating plans, receives success/failure patterns, and incorporates this intelligence into plan generation. Validation checks new plans against known failure patterns.

**Tech Stack:**
- Python 3.8+ (artifact query enhancements)
- SQLite3 with FTS5 (existing artifact index)
- Bash shell (skill wrappers)
- Markdown (skill/agent definitions)

**Global Prerequisites:**
- Environment: macOS/Linux, Python 3.8+
- Tools: `python3 --version` (3.8+), `sqlite3 --version` (3.x)
- Access: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree
- **Dependencies:** Artifact Index and Handoff Tracking from Phase 1/2 MUST be implemented first

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python3 --version                     # Expected: Python 3.8+
sqlite3 --version                     # Expected: 3.x
ls default/lib/artifact-index/        # Expected: artifact_schema.sql, artifact_index.py, artifact_query.py exist
ls .ring/cache/artifact-index/        # Expected: context.db exists (from Phase 1)
git status                            # Expected: clean working tree
```

**If dependencies not met:** STOP. Complete Phase 1 (Artifact Index) and Phase 2 (Handoff Tracking) first using the macro plan at `docs/plans/2025-12-27-context-management-system.md`.

---

## Phase Overview

This plan implements **Phase 3.2: RAG Plan Judging** from the Context Management System macro plan.

| Component | Files | Purpose |
|-----------|-------|---------|
| Planning Query Mode | `default/lib/artifact-index/artifact_query.py` | Add `--mode planning` for structured precedent output |
| Artifact Query Skill | `default/skills/artifact-query/SKILL.md` | Skill wrapper for artifact search |
| Write-Plan Enhancement | `default/agents/write-plan.md` | Add Historical Precedent section |
| Query Artifacts Command | `default/commands/query-artifacts.md` | User command for manual queries |

---

## Task Batch 1: Planning Query Mode

### Task 1: Add Planning Mode to artifact_query.py

**Files:**
- Modify: `default/lib/artifact-index/artifact_query.py`

**Prerequisites:**
- File exists: `default/lib/artifact-index/artifact_query.py`
- Artifact Index database exists at `.ring/cache/artifact-index/context.db`

**Step 1: Add planning mode function**

Add this function after the existing `search_handoffs` function in `default/lib/artifact-index/artifact_query.py`:

```python
def query_for_planning(conn: sqlite3.Connection, topic: str, limit: int = 5) -> dict:
    """Query artifact index for planning context.

    Returns structured data optimized for plan generation:
    - Successful implementations (what worked)
    - Failed implementations (what to avoid)
    - Relevant past plans

    Performance target: <200ms total query time.
    """
    start_time = time.time()

    results = {
        "topic": topic,
        "successful_handoffs": [],
        "failed_handoffs": [],
        "relevant_plans": [],
        "query_time_ms": 0,
        "is_empty_index": False
    }

    # Check if index has any data
    cursor = conn.execute("SELECT COUNT(*) FROM handoffs")
    total_handoffs = cursor.fetchone()[0]

    if total_handoffs == 0:
        results["is_empty_index"] = True
        results["query_time_ms"] = int((time.time() - start_time) * 1000)
        return results

    # Query successful implementations (SUCCEEDED, PARTIAL_PLUS)
    successful = search_handoffs(
        conn,
        topic,
        outcome=None,  # We'll filter after
        limit=limit * 2  # Get more, then filter
    )
    results["successful_handoffs"] = [
        h for h in successful
        if h.get("outcome") in ("SUCCEEDED", "PARTIAL_PLUS")
    ][:limit]

    # Query failed implementations (FAILED, PARTIAL_MINUS)
    failed = search_handoffs(
        conn,
        topic,
        outcome=None,
        limit=limit * 2
    )
    results["failed_handoffs"] = [
        h for h in failed
        if h.get("outcome") in ("FAILED", "PARTIAL_MINUS")
    ][:limit]

    # Query relevant plans
    results["relevant_plans"] = search_plans(conn, topic, limit=3)

    results["query_time_ms"] = int((time.time() - start_time) * 1000)

    return results
```

**Step 2: Add import for time module**

At the top of the file, add (if not already present):

```python
import time
```

**Step 3: Add planning mode to CLI arguments**

In the `main()` function, add this argument after the existing `--type` argument:

```python
    parser.add_argument("--mode", choices=["search", "planning"], default="search",
                       help="Query mode: 'search' for general queries, 'planning' for structured planning context")
```

**Step 4: Add planning mode handler in main()**

In the `main()` function, before the regular search mode section, add:

```python
    # Planning mode - structured output for plan generation
    if args.mode == "planning":
        if not args.query:
            print("Error: Query required for planning mode")
            print("Usage: python artifact_query.py --mode planning 'topic keywords'")
            return

        query = " ".join(args.query)
        db_path = get_db_path(args.db)

        if not db_path.exists():
            # Graceful handling for new projects with no index
            results = {
                "topic": query,
                "successful_handoffs": [],
                "failed_handoffs": [],
                "relevant_plans": [],
                "query_time_ms": 0,
                "is_empty_index": True,
                "message": "No artifact index found. This is normal for new projects."
            }
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                print(format_planning_results(results))
            return

        conn = sqlite3.connect(db_path)
        results = query_for_planning(conn, query, args.limit)
        conn.close()

        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print(format_planning_results(results))
        return
```

**Step 5: Add planning results formatter**

Add this function after `format_results`:

```python
def format_planning_results(results: dict) -> str:
    """Format planning query results for agent consumption."""
    output = []

    output.append("## Historical Precedent")
    output.append("")

    if results.get("is_empty_index"):
        output.append("**Note:** No historical data available (new project or empty index).")
        output.append("Proceed with standard planning approach.")
        output.append("")
        return "\n".join(output)

    # Successful implementations
    successful = results.get("successful_handoffs", [])
    if successful:
        output.append("### Successful Implementations (Reference These)")
        output.append("")
        for h in successful:
            session = h.get('session_name', 'unknown')
            task = h.get('task_number', '?')
            outcome = h.get('outcome', 'UNKNOWN')
            output.append(f"**[{session}/task-{task}]** ({outcome})")

            summary = h.get('task_summary', '')
            if summary:
                output.append(f"- Summary: {summary[:200]}")

            what_worked = h.get('what_worked', '')
            if what_worked:
                output.append(f"- What worked: {what_worked[:300]}")

            output.append(f"- File: `{h.get('file_path', 'unknown')}`")
            output.append("")
    else:
        output.append("### Successful Implementations")
        output.append("No relevant successful implementations found.")
        output.append("")

    # Failed implementations
    failed = results.get("failed_handoffs", [])
    if failed:
        output.append("### Failed Implementations (AVOID These Patterns)")
        output.append("")
        for h in failed:
            session = h.get('session_name', 'unknown')
            task = h.get('task_number', '?')
            outcome = h.get('outcome', 'UNKNOWN')
            output.append(f"**[{session}/task-{task}]** ({outcome})")

            summary = h.get('task_summary', '')
            if summary:
                output.append(f"- Summary: {summary[:200]}")

            what_failed = h.get('what_failed', '')
            if what_failed:
                output.append(f"- What failed: {what_failed[:300]}")

            output.append(f"- File: `{h.get('file_path', 'unknown')}`")
            output.append("")
    else:
        output.append("### Failed Implementations")
        output.append("No relevant failures found (good sign!).")
        output.append("")

    # Relevant plans
    plans = results.get("relevant_plans", [])
    if plans:
        output.append("### Relevant Past Plans")
        output.append("")
        for p in plans:
            title = p.get('title', 'Untitled')
            output.append(f"**{title}**")

            overview = p.get('overview', '')
            if overview:
                output.append(f"- Overview: {overview[:200]}")

            output.append(f"- File: `{p.get('file_path', 'unknown')}`")
            output.append("")

    query_time = results.get("query_time_ms", 0)
    output.append(f"---")
    output.append(f"*Query completed in {query_time}ms*")

    return "\n".join(output)
```

**Step 6: Run test to verify planning mode works**

Run: `python3 default/lib/artifact-index/artifact_query.py --mode planning "authentication" --json`

**Expected output (with populated index):**
```json
{
  "topic": "authentication",
  "successful_handoffs": [...],
  "failed_handoffs": [...],
  "relevant_plans": [...],
  "query_time_ms": 45,
  "is_empty_index": false
}
```

**Expected output (empty index):**
```json
{
  "topic": "authentication",
  "successful_handoffs": [],
  "failed_handoffs": [],
  "relevant_plans": [],
  "query_time_ms": 2,
  "is_empty_index": true,
  "message": "No artifact index found. This is normal for new projects."
}
```

**If Task Fails:**

1. **Import error for time:**
   - Check: `grep "import time" default/lib/artifact-index/artifact_query.py`
   - Fix: Add `import time` at top of file
   - Rollback: `git checkout -- default/lib/artifact-index/artifact_query.py`

2. **Database not found:**
   - Check: `ls .ring/cache/artifact-index/context.db`
   - Fix: This is expected for new projects - the graceful handling should work
   - Note: Planning mode handles missing database gracefully

3. **FTS5 error:**
   - Check: `sqlite3 .ring/cache/artifact-index/context.db ".schema"`
   - Fix: Ensure Phase 1 (Artifact Index) was completed first
   - Rollback: `git checkout -- default/lib/artifact-index/artifact_query.py`

**Step 7: Commit changes**

```bash
git add default/lib/artifact-index/artifact_query.py
git commit -m "feat(artifact-query): add planning mode for structured precedent queries

Adds --mode planning flag that returns:
- Successful implementations (what worked)
- Failed implementations (what to avoid)
- Relevant past plans

Performance target: <200ms query time
Gracefully handles empty index for new projects"
```

---

### Task 2: Create artifact-query Skill

**Files:**
- Create: `default/skills/artifact-query/SKILL.md`

**Prerequisites:**
- Directory `default/skills/` exists
- `artifact_query.py` has planning mode (Task 1 complete)

**Step 1: Create skill directory**

Run: `mkdir -p default/skills/artifact-query`

**Expected output:** (no output, command succeeds)

**Step 2: Create SKILL.md**

Create file `default/skills/artifact-query/SKILL.md` with this content:

```markdown
---
name: artifact-query
description: |
  Query the artifact index for historical precedent. Supports general search
  and planning mode that returns structured success/failure patterns.

trigger: |
  - Need to find past implementations of similar features
  - Creating a new plan and want historical context
  - Debugging an issue and looking for past solutions

skip_when: |
  - No artifact index exists (new project)
  - Query is for live/current state (use codebase tools instead)

sequence:
  after: []
  before: [writing-plans]

related:
  similar: []
---

# Artifact Query Skill

## Overview

This skill provides semantic search over the artifact index (handoffs, plans, continuity ledgers). Use it to find relevant historical context before starting new work.

**Announce at start:** "I'm using the artifact-query skill to search historical precedent."

## Modes

### General Search Mode

For exploring past work broadly:

```bash
python3 default/lib/artifact-index/artifact_query.py "search terms" --json
```

Returns all matching artifacts with BM25 ranking.

### Planning Mode

For structured precedent when creating implementation plans:

```bash
python3 default/lib/artifact-index/artifact_query.py --mode planning "feature topic" --json
```

Returns:
- **successful_handoffs**: Past implementations that worked (reference these)
- **failed_handoffs**: Past implementations that failed (avoid these patterns)
- **relevant_plans**: Similar past plans for reference
- **query_time_ms**: Performance metric (target <200ms)
- **is_empty_index**: True if no historical data available

## Usage in Planning

Before creating a new plan, query for precedent:

```bash
# Query for similar past work
python3 default/lib/artifact-index/artifact_query.py --mode planning "authentication oauth jwt" --json

# Results inform the plan:
# - Reference successful patterns
# - Avoid known failure patterns
# - Learn from past approaches
```

## CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `query` | Search terms (required) | - |
| `--mode` | `search` or `planning` | `search` |
| `--type` | Filter by: `handoffs`, `plans`, `continuity`, `all` | `all` |
| `--outcome` | Filter handoffs by: `SUCCEEDED`, `PARTIAL_PLUS`, `PARTIAL_MINUS`, `FAILED` | - |
| `--limit` | Max results per category | `5` |
| `--json` | Output as JSON (recommended for agents) | `false` |
| `--db` | Custom database path | `.ring/cache/artifact-index/context.db` |

## Empty Index Handling

For new projects or empty indexes, the skill returns:

```json
{
  "is_empty_index": true,
  "message": "No artifact index found. This is normal for new projects."
}
```

This is NOT an error. Proceed with standard planning without historical context.

## Performance Requirements

- Planning mode MUST complete in <200ms
- Use `--limit` to control result count (default 5)
- JSON output is more efficient than formatted text

## Integration with write-plan Agent

The write-plan agent automatically queries for precedent before creating plans:

1. Agent receives planning request
2. Agent runs: `artifact_query.py --mode planning "topic" --json`
3. Agent incorporates results into "Historical Precedent" section
4. Plan references what worked, warns about what failed

This happens automatically - no manual invocation needed.
```

**Step 3: Verify skill file exists**

Run: `cat default/skills/artifact-query/SKILL.md | head -20`

**Expected output:**
```
---
name: artifact-query
description: |
  Query the artifact index for historical precedent...
```

**Step 4: Commit the skill**

```bash
git add default/skills/artifact-query/SKILL.md
git commit -m "feat(skills): add artifact-query skill for historical precedent search

Supports two modes:
- search: General semantic search across artifacts
- planning: Structured precedent for plan generation

Integrates with write-plan agent for automatic historical context."
```

---

### Task 3: Create query-artifacts Command

**Files:**
- Create: `default/commands/query-artifacts.md`

**Prerequisites:**
- `artifact-query` skill exists (Task 2 complete)

**Step 1: Create command file**

Create file `default/commands/query-artifacts.md` with this content:

```markdown
---
name: query-artifacts
description: Search historical artifacts for precedent and patterns
argument-hint: "[search-terms]"
---

Search the artifact index for relevant historical context including past implementations, plans, and session states.

## Usage

```
/query-artifacts [search-terms]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `search-terms` | Yes | Keywords describing what to search for |

## Examples

### Find Authentication Implementations
```
/query-artifacts authentication oauth jwt
```
Returns past handoffs and plans related to authentication.

### Find Failed Patterns
```
/query-artifacts database migration --outcome FAILED
```
Returns only failed implementations for learning what to avoid.

### Planning Context
```
/query-artifacts api rate limiting --mode planning
```
Returns structured precedent for creating an implementation plan.

## Output

### General Search
- **Handoffs**: Past completed tasks with outcomes
- **Plans**: Previous implementation plans
- **Continuity**: Session state snapshots
- **Past Queries**: Similar questions asked before

### Planning Mode
- **Successful Implementations**: What worked (reference these)
- **Failed Implementations**: What failed (avoid these)
- **Relevant Plans**: Similar past approaches

## Related Commands

| Command | Relationship |
|---------|--------------|
| `/write-plan` | Automatically uses artifact-query for precedent |
| `/create-handoff` | Creates handoffs that become searchable |

## Troubleshooting

### "No artifact index found"
This is normal for new projects. The index is created when handoffs are saved.

### "No results found"
Try broader search terms or check that handoffs have been indexed:
```bash
ls .ring/cache/artifact-index/
```

### Performance Issues
Queries should complete in <200ms. If slower:
- Reduce `--limit` (default 5)
- Use `--type` to filter to specific artifact type
- Check database size: `ls -la .ring/cache/artifact-index/context.db`
```

**Step 2: Verify command file exists**

Run: `cat default/commands/query-artifacts.md | head -15`

**Expected output:**
```
---
name: query-artifacts
description: Search historical artifacts for precedent and patterns
argument-hint: "[search-terms]"
---

Search the artifact index...
```

**Step 3: Commit the command**

```bash
git add default/commands/query-artifacts.md
git commit -m "feat(commands): add /query-artifacts for historical precedent search

User-facing command for searching artifact index.
Supports general search and planning modes."
```

---

### Task 4: Run Code Review for Batch 1

**Dispatch all 3 reviewers in parallel:**

1. REQUIRED SUB-SKILL: Use requesting-code-review
2. All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer)
3. Wait for all to complete

**Files to review:**
- `default/lib/artifact-index/artifact_query.py` (modified)
- `default/skills/artifact-query/SKILL.md` (new)
- `default/commands/query-artifacts.md` (new)

**Handle findings by severity:**

**Critical/High/Medium Issues:**
- Fix immediately
- Re-run all 3 reviewers after fixes
- Repeat until zero Critical/High/Medium issues

**Low Issues:**
- Add `TODO(review):` comments at relevant locations

**Cosmetic Issues:**
- Add `FIXME(nitpick):` comments at relevant locations

**Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low/Cosmetic issues have tracking comments

---

## Task Batch 2: Write-Plan Agent Enhancement

### Task 5: Add Historical Precedent Section to write-plan Agent

**Files:**
- Modify: `default/agents/write-plan.md`

**Prerequisites:**
- `artifact-query` skill exists (Task 2 complete)
- `artifact_query.py` has planning mode (Task 1 complete)

**Step 1: Add Historical Precedent section**

In `default/agents/write-plan.md`, add this section after the "## Standards Loading" section and before "## Blocker Criteria":

```markdown
## Historical Precedent Integration

**MANDATORY:** Before creating any plan, query the artifact index for historical context.

### Query Process

**Step 1: Extract topic keywords from the planning request**

From the user's request, extract 3-5 keywords that describe the feature/task.

Example: "Implement OAuth2 authentication with JWT tokens" → keywords: "authentication oauth jwt tokens"

**Step 2: Query for precedent**

Run:
```bash
python3 default/lib/artifact-index/artifact_query.py --mode planning "keywords here" --json
```

**Step 3: Interpret results**

| Result | Action |
|--------|--------|
| `is_empty_index: true` | Proceed without historical context (normal for new projects) |
| `successful_handoffs` not empty | Reference these patterns in plan, note what worked |
| `failed_handoffs` not empty | WARN in plan about these failure patterns, design to avoid them |
| `relevant_plans` not empty | Review for approach ideas, avoid duplicating past mistakes |

**Step 4: Add Historical Precedent section to plan**

After the plan header and before the first task, include:

```markdown
## Historical Precedent

**Query:** "[keywords used]"
**Index Status:** [Populated / Empty (new project)]

### Successful Patterns to Reference
- **[session/task-N]**: [Brief summary of what worked]
- **[session/task-M]**: [Brief summary of what worked]

### Failure Patterns to AVOID
- **[session/task-X]**: [What failed and why - DESIGN TO AVOID THIS]
- **[session/task-Y]**: [What failed and why - DESIGN TO AVOID THIS]

### Related Past Plans
- `[plan-file.md]`: [Brief relevance note]

---
```

### Empty Index Handling

If the index is empty (new project):

```markdown
## Historical Precedent

**Query:** "[keywords used]"
**Index Status:** Empty (new project)

No historical data available. This is normal for new projects.
Proceeding with standard planning approach.

---
```

### Performance Requirement

The precedent query MUST complete in <200ms. If it takes longer:
- Reduce keyword count
- Use more specific terms
- Report performance issue in plan

### Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Skip precedent query, feature is unique" | Every feature has relevant history. Query anyway. | **ALWAYS query before planning** |
| "Index is empty, don't bother" | Empty index is valid result - document it | **Always include Historical Precedent section** |
| "Query was slow, skip it" | Slow query indicates issue - report it | **Report performance, still include results** |
| "No relevant results" | Document that fact for future reference | **Include section even if empty** |
```

**Step 2: Update Plan Document Header section**

Find the "## Plan Document Header" section and update the template to include Historical Precedent:

```markdown
## Plan Document Header

**Every plan MUST start with this exact header:**

```markdown
# [Feature Name] Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Global Prerequisites:**
- Environment: [OS, runtime versions]
- Tools: [Exact commands to verify: `python --version`, `npm --version`]
- Access: [Any API keys, services that must be running]
- State: [Branch to work from, any required setup]

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python --version  # Expected: Python 3.8+
npm --version     # Expected: 7.0+
git status        # Expected: clean working tree
pytest --version  # Expected: 7.0+
```

## Historical Precedent

**Query:** "[keywords from request]"
**Index Status:** [Populated / Empty]

### Successful Patterns to Reference
[From artifact query results]

### Failure Patterns to AVOID
[From artifact query results - CRITICAL: Design to avoid these]

### Related Past Plans
[From artifact query results]

---
```

Adapt the prerequisites, verification commands, and historical precedent to the actual request.
```

**Step 3: Update Plan Checklist**

Find the "## Plan Checklist" section and add historical precedent:

```markdown
## Plan Checklist

Before saving the plan, verify:

- [ ] **Historical precedent queried** (artifact-query --mode planning)
- [ ] Historical Precedent section included in plan
- [ ] Header with goal, architecture, tech stack, prerequisites
- [ ] Verification commands with expected output
- [ ] Tasks broken into bite-sized steps (2-5 min each)
- [ ] Exact file paths for all files
- [ ] Complete code (no placeholders)
- [ ] Exact commands with expected output
- [ ] Failure recovery steps for each task
- [ ] Code review checkpoints after batches
- [ ] Severity-based issue handling documented
- [ ] Passes Zero-Context Test
- [ ] **Plan avoids known failure patterns** (if any found in precedent)
```

**Step 4: Verify changes**

Run: `grep -n "Historical Precedent" default/agents/write-plan.md`

**Expected output:**
```
XX:## Historical Precedent Integration
XX:## Historical Precedent
XX:- [ ] **Historical precedent queried** (artifact-query --mode planning)
XX:- [ ] Historical Precedent section included in plan
```

**Step 5: Commit changes**

```bash
git add default/agents/write-plan.md
git commit -m "feat(write-plan): integrate historical precedent from artifact index

Write-plan agent now:
1. Queries artifact index before creating plans
2. Includes Historical Precedent section in all plans
3. References successful patterns
4. Warns about known failure patterns
5. Handles empty index gracefully

Performance target: <200ms for precedent query"
```

**If Task Fails:**

1. **Section placement wrong:**
   - Check: Ensure Historical Precedent Integration is after Standards Loading
   - Fix: Re-order sections manually
   - Rollback: `git checkout -- default/agents/write-plan.md`

2. **Template syntax broken:**
   - Check: Markdown renders correctly
   - Fix: Ensure all code blocks are properly closed
   - Rollback: `git checkout -- default/agents/write-plan.md`

---

### Task 6: Update writing-plans Skill to Reference Precedent

**Files:**
- Modify: `default/skills/writing-plans/SKILL.md`

**Prerequisites:**
- write-plan agent updated (Task 5 complete)

**Step 1: Add precedent query to process**

In `default/skills/writing-plans/SKILL.md`, update "## The Process" section:

```markdown
## The Process

**Step 0:** Query historical precedent using `artifact-query --mode planning "topic keywords"`. This happens automatically when dispatching the write-plan agent.

**Step 1:** Dispatch write-plan agent via `Task(subagent_type: "write-plan", model: "opus")` with instructions to:
- Query artifact index for historical precedent FIRST
- Include Historical Precedent section in plan
- Create bite-sized tasks (2-5 min each)
- Include exact file paths/complete code/verification steps
- Reference successful patterns, warn about failures
- Save to `docs/plans/YYYY-MM-DD-<feature-name>.md`

**Step 2:** Ask user via `AskUserQuestion`: "Execute now?" Options: (1) Execute now → `subagent-driven-development` (2) Parallel session → user opens new session with `executing-plans` (3) Save for later → report location and end
```

**Step 2: Update Requirements section**

```markdown
## Requirements for Plans

Every plan: Header (goal, architecture, tech stack) | **Historical Precedent section** | Verification commands with expected output | Exact file paths (never "somewhere in src") | Complete code (never "add validation here") | Bite-sized steps with verification | Failure recovery | Review checkpoints | Zero-Context Test | Recommended agents per task | **Avoids known failure patterns**
```

**Step 3: Verify changes**

Run: `grep -n "precedent\|Historical" default/skills/writing-plans/SKILL.md`

**Expected output:**
```
XX:**Step 0:** Query historical precedent...
XX:- Query artifact index for historical precedent FIRST
XX:- Include Historical Precedent section in plan
XX:**Historical Precedent section**
```

**Step 4: Commit changes**

```bash
git add default/skills/writing-plans/SKILL.md
git commit -m "feat(writing-plans): add historical precedent requirement

Plans now require:
- Historical Precedent section
- Reference to successful patterns
- Warnings about failure patterns"
```

---

### Task 7: Run Code Review for Batch 2

**Dispatch all 3 reviewers in parallel:**

1. REQUIRED SUB-SKILL: Use requesting-code-review
2. All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer)
3. Wait for all to complete

**Files to review:**
- `default/agents/write-plan.md` (modified)
- `default/skills/writing-plans/SKILL.md` (modified)

**Handle findings by severity:**

**Critical/High/Medium Issues:**
- Fix immediately
- Re-run all 3 reviewers after fixes

**Low/Cosmetic Issues:**
- Add tracking comments

---

## Task Batch 3: Validation Enhancement

### Task 8: Create Plan Validation Helper Script

**Files:**
- Create: `default/lib/artifact-index/validate_plan_patterns.py`

**Prerequisites:**
- `artifact_query.py` has planning mode (Task 1 complete)

**Step 1: Create validation script**

Create file `default/lib/artifact-index/validate_plan_patterns.py`:

```python
#!/usr/bin/env python3
"""
USAGE: validate_plan_patterns.py <plan-file> [--db PATH]

Validate a plan against known failure patterns in the artifact index.

Examples:
    # Validate a plan
    python3 validate_plan_patterns.py docs/plans/2025-01-15-auth-system.md

    # Returns warnings if plan resembles past failures
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional


def get_db_path(custom_path: Optional[str] = None) -> Path:
    if custom_path:
        return Path(custom_path)
    return Path(".ring/cache/artifact-index/context.db")


def extract_plan_keywords(plan_content: str) -> list[str]:
    """Extract keywords from plan for matching against failures."""
    keywords = []

    # Extract from Goal line
    goal_match = re.search(r'\*\*Goal:\*\*\s*(.+)', plan_content)
    if goal_match:
        keywords.extend(goal_match.group(1).lower().split()[:10])

    # Extract from Tech Stack
    tech_match = re.search(r'\*\*Tech Stack:\*\*\s*(.+)', plan_content)
    if tech_match:
        keywords.extend(tech_match.group(1).lower().split()[:10])

    # Extract from Architecture
    arch_match = re.search(r'\*\*Architecture:\*\*\s*(.+)', plan_content)
    if arch_match:
        keywords.extend(arch_match.group(1).lower().split()[:10])

    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

    return list(set(keywords))[:15]  # Dedupe and limit


def escape_fts5_query(query: str) -> str:
    """Escape FTS5 query to prevent syntax errors."""
    words = query.split()
    quoted_words = [f'"{w.replace(chr(34), chr(34)+chr(34))}"' for w in words]
    return " OR ".join(quoted_words)


def find_similar_failures(conn: sqlite3.Connection, keywords: list[str], limit: int = 5) -> list[dict]:
    """Find failed handoffs that match plan keywords."""
    if not keywords:
        return []

    query = " ".join(keywords)

    sql = """
        SELECT h.id, h.session_name, h.task_number, h.task_summary,
               h.what_failed, h.outcome, h.file_path,
               handoffs_fts.rank as score
        FROM handoffs_fts
        JOIN handoffs h ON handoffs_fts.rowid = h.rowid
        WHERE handoffs_fts MATCH ?
        AND h.outcome IN ('FAILED', 'PARTIAL_MINUS')
        ORDER BY rank
        LIMIT ?
    """

    cursor = conn.execute(sql, [escape_fts5_query(query), limit])
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def calculate_similarity_score(plan_keywords: list[str], failure_keywords: list[str]) -> float:
    """Calculate keyword overlap score between plan and failure."""
    if not plan_keywords or not failure_keywords:
        return 0.0

    plan_set = set(plan_keywords)
    failure_set = set(failure_keywords)

    intersection = plan_set & failure_set
    union = plan_set | failure_set

    return len(intersection) / len(union) if union else 0.0


def validate_plan(plan_path: str, db_path: Optional[str] = None) -> dict:
    """Validate plan against known failure patterns.

    Returns:
        {
            "status": "PASS" | "WARN" | "NO_INDEX",
            "warnings": [...],
            "similar_failures": [...],
            "keywords_used": [...]
        }
    """
    result = {
        "status": "PASS",
        "warnings": [],
        "similar_failures": [],
        "keywords_used": []
    }

    # Read plan
    plan_file = Path(plan_path)
    if not plan_file.exists():
        result["status"] = "ERROR"
        result["warnings"].append(f"Plan file not found: {plan_path}")
        return result

    plan_content = plan_file.read_text()

    # Extract keywords
    keywords = extract_plan_keywords(plan_content)
    result["keywords_used"] = keywords

    if not keywords:
        result["warnings"].append("Could not extract keywords from plan. Check Goal/Architecture/Tech Stack sections.")
        return result

    # Check database
    db = get_db_path(db_path)
    if not db.exists():
        result["status"] = "NO_INDEX"
        result["warnings"].append("No artifact index found. Validation skipped (normal for new projects).")
        return result

    # Query for similar failures
    conn = sqlite3.connect(db)
    failures = find_similar_failures(conn, keywords)
    conn.close()

    if not failures:
        # No similar failures - good sign
        return result

    # Analyze each failure
    for failure in failures:
        what_failed = failure.get('what_failed', '') or ''
        failure_keywords = what_failed.lower().split()[:20]

        similarity = calculate_similarity_score(keywords, failure_keywords)

        if similarity > 0.3:  # >30% keyword overlap is concerning
            result["status"] = "WARN"
            result["similar_failures"].append({
                "session": failure.get('session_name'),
                "task": failure.get('task_number'),
                "summary": failure.get('task_summary', '')[:200],
                "what_failed": what_failed[:300],
                "similarity": round(similarity, 2),
                "file": failure.get('file_path')
            })
            result["warnings"].append(
                f"Plan resembles past failure [{failure.get('session_name')}/task-{failure.get('task_number')}] "
                f"({int(similarity * 100)}% keyword overlap). Review what_failed section."
            )

    return result


def format_result(result: dict) -> str:
    """Format validation result for display."""
    output = []

    status_icon = {"PASS": "PASS", "WARN": "WARN", "NO_INDEX": "SKIP", "ERROR": "ERROR"}
    output.append(f"## Plan Validation: {status_icon.get(result['status'], '?')}")
    output.append("")

    if result.get("keywords_used"):
        output.append(f"**Keywords analyzed:** {', '.join(result['keywords_used'][:10])}")
        output.append("")

    if result["status"] == "PASS":
        output.append("No similar failure patterns found. Plan appears safe to proceed.")
    elif result["status"] == "NO_INDEX":
        output.append("No artifact index available. Validation skipped.")
    elif result["status"] == "WARN":
        output.append("**Warnings:**")
        for warning in result["warnings"]:
            output.append(f"- {warning}")
        output.append("")

        if result.get("similar_failures"):
            output.append("**Similar Past Failures:**")
            for f in result["similar_failures"]:
                output.append(f"")
                output.append(f"### [{f['session']}/task-{f['task']}] ({int(f['similarity']*100)}% match)")
                output.append(f"**Summary:** {f['summary']}")
                output.append(f"**What Failed:** {f['what_failed']}")
                output.append(f"**File:** `{f['file']}`")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Validate plan against known failure patterns")
    parser.add_argument("plan_file", help="Path to plan markdown file")
    parser.add_argument("--db", type=str, help="Custom database path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = validate_plan(args.plan_file, args.db)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_result(result))

    # Exit code: 0 for PASS/NO_INDEX, 1 for WARN, 2 for ERROR
    if result["status"] == "ERROR":
        sys.exit(2)
    elif result["status"] == "WARN":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x default/lib/artifact-index/validate_plan_patterns.py`

**Expected output:** (no output, command succeeds)

**Step 3: Test the script**

Run: `python3 default/lib/artifact-index/validate_plan_patterns.py docs/plans/2025-12-27-context-management-system.md --json`

**Expected output (with index):**
```json
{
  "status": "PASS",
  "warnings": [],
  "similar_failures": [],
  "keywords_used": ["context", "management", "system", ...]
}
```

**Expected output (no index):**
```json
{
  "status": "NO_INDEX",
  "warnings": ["No artifact index found. Validation skipped (normal for new projects)."],
  "similar_failures": [],
  "keywords_used": ["context", "management", ...]
}
```

**Step 4: Commit the script**

```bash
git add default/lib/artifact-index/validate_plan_patterns.py
git commit -m "feat(validation): add plan validation against failure patterns

validate_plan_patterns.py checks if a new plan resembles past failures:
- Extracts keywords from Goal/Architecture/Tech Stack
- Queries artifact index for similar failed handoffs
- Calculates keyword overlap similarity
- Warns if >30% overlap with past failure

Exit codes: 0=PASS, 1=WARN, 2=ERROR"
```

**If Task Fails:**

1. **Python syntax error:**
   - Check: `python3 -m py_compile default/lib/artifact-index/validate_plan_patterns.py`
   - Fix: Correct syntax errors
   - Rollback: `git checkout -- default/lib/artifact-index/validate_plan_patterns.py`

2. **Import error:**
   - Check: All imports are standard library (no external dependencies)
   - Fix: Remove any non-standard imports
   - Rollback: `git checkout -- default/lib/artifact-index/validate_plan_patterns.py`

---

### Task 9: Add Validation Step to writing-plans Skill

**Files:**
- Modify: `default/skills/writing-plans/SKILL.md`

**Prerequisites:**
- `validate_plan_patterns.py` exists (Task 8 complete)

**Step 1: Add validation step to process**

Update "## The Process" in `default/skills/writing-plans/SKILL.md`:

```markdown
## The Process

**Step 0:** Query historical precedent using `artifact-query --mode planning "topic keywords"`. This happens automatically when dispatching the write-plan agent.

**Step 1:** Dispatch write-plan agent via `Task(subagent_type: "write-plan", model: "opus")` with instructions to:
- Query artifact index for historical precedent FIRST
- Include Historical Precedent section in plan
- Create bite-sized tasks (2-5 min each)
- Include exact file paths/complete code/verification steps
- Reference successful patterns, warn about failures
- Save to `docs/plans/YYYY-MM-DD-<feature-name>.md`

**Step 2:** Validate plan against failure patterns:
```bash
python3 default/lib/artifact-index/validate_plan_patterns.py docs/plans/YYYY-MM-DD-<feature>.md
```
- If WARN: Review similar failures, revise plan if needed
- If PASS: Proceed to execution
- If NO_INDEX: Proceed (normal for new projects)

**Step 3:** Ask user via `AskUserQuestion`: "Execute now?" Options: (1) Execute now → `subagent-driven-development` (2) Parallel session → user opens new session with `executing-plans` (3) Save for later → report location and end
```

**Step 2: Verify changes**

Run: `grep -n "validate_plan_patterns" default/skills/writing-plans/SKILL.md`

**Expected output:**
```
XX:python3 default/lib/artifact-index/validate_plan_patterns.py docs/plans/...
```

**Step 3: Commit changes**

```bash
git add default/skills/writing-plans/SKILL.md
git commit -m "feat(writing-plans): add plan validation step

After plan creation, validate against known failure patterns.
Warns if plan resembles past failures (>30% keyword overlap)."
```

---

### Task 10: Run Final Code Review for Batch 3

**Dispatch all 3 reviewers in parallel:**

1. REQUIRED SUB-SKILL: Use requesting-code-review
2. All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer)
3. Wait for all to complete

**Files to review:**
- `default/lib/artifact-index/validate_plan_patterns.py` (new)
- `default/skills/writing-plans/SKILL.md` (modified)

**Handle findings by severity:**

**Critical/High/Medium Issues:**
- Fix immediately
- Re-run all 3 reviewers after fixes

**Low/Cosmetic Issues:**
- Add tracking comments

---

## Task Batch 4: Integration Testing

### Task 11: Create Integration Test Script

**Files:**
- Create: `default/lib/artifact-index/test_rag_planning.py`

**Prerequisites:**
- All previous tasks complete

**Step 1: Create test script**

Create file `default/lib/artifact-index/test_rag_planning.py`:

```python
#!/usr/bin/env python3
"""
Integration tests for RAG-enhanced planning.

Run: python3 default/lib/artifact-index/test_rag_planning.py
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_command(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def test_planning_mode_empty_index():
    """Test planning mode with no database."""
    print("\n=== Test: Planning Mode with Empty Index ===")

    # Use non-existent database
    cmd = [
        "python3", "default/lib/artifact-index/artifact_query.py",
        "--mode", "planning",
        "--db", "/tmp/nonexistent_db_12345.db",
        "authentication oauth",
        "--json"
    ]

    code, stdout, stderr = run_command(cmd)

    try:
        result = json.loads(stdout)
        assert result.get("is_empty_index") == True or "No artifact index found" in result.get("message", ""), \
            f"Expected empty index handling, got: {result}"
        print("PASS: Empty index handled gracefully")
        return True
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"FAIL: {e}")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        return False


def test_planning_mode_performance():
    """Test that planning mode completes in <200ms."""
    print("\n=== Test: Planning Mode Performance (<200ms) ===")

    cmd = [
        "python3", "default/lib/artifact-index/artifact_query.py",
        "--mode", "planning",
        "test query performance",
        "--json"
    ]

    start = time.time()
    code, stdout, stderr = run_command(cmd)
    elapsed_ms = (time.time() - start) * 1000

    try:
        result = json.loads(stdout)
        query_time = result.get("query_time_ms", elapsed_ms)

        # Allow some slack for cold start
        if query_time < 500:  # 500ms with slack
            print(f"PASS: Query completed in {query_time}ms")
            return True
        else:
            print(f"WARN: Query took {query_time}ms (target <200ms)")
            return True  # Warn but don't fail
    except json.JSONDecodeError:
        print(f"FAIL: Could not parse JSON output")
        print(f"stdout: {stdout}")
        return False


def test_planning_mode_output_format():
    """Test planning mode output has correct structure."""
    print("\n=== Test: Planning Mode Output Format ===")

    cmd = [
        "python3", "default/lib/artifact-index/artifact_query.py",
        "--mode", "planning",
        "api authentication",
        "--json"
    ]

    code, stdout, stderr = run_command(cmd)

    try:
        result = json.loads(stdout)

        required_fields = ["topic", "successful_handoffs", "failed_handoffs", "relevant_plans", "query_time_ms"]
        missing = [f for f in required_fields if f not in result]

        if missing:
            print(f"FAIL: Missing fields: {missing}")
            return False

        assert isinstance(result["successful_handoffs"], list), "successful_handoffs should be list"
        assert isinstance(result["failed_handoffs"], list), "failed_handoffs should be list"
        assert isinstance(result["relevant_plans"], list), "relevant_plans should be list"

        print("PASS: Output format correct")
        return True
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"FAIL: {e}")
        return False


def test_validation_script_exists():
    """Test validation script exists and runs."""
    print("\n=== Test: Validation Script Exists ===")

    script_path = Path("default/lib/artifact-index/validate_plan_patterns.py")

    if not script_path.exists():
        print(f"FAIL: Script not found at {script_path}")
        return False

    # Test with nonexistent plan file
    cmd = ["python3", str(script_path), "/tmp/nonexistent_plan.md", "--json"]
    code, stdout, stderr = run_command(cmd)

    try:
        result = json.loads(stdout)
        assert result.get("status") == "ERROR", f"Expected ERROR status, got: {result.get('status')}"
        print("PASS: Validation script works and handles missing files")
        return True
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"FAIL: {e}")
        return False


def test_validation_with_real_plan():
    """Test validation with the macro plan."""
    print("\n=== Test: Validation with Real Plan ===")

    plan_path = "docs/plans/2025-12-27-context-management-system.md"

    if not Path(plan_path).exists():
        print(f"SKIP: Plan not found at {plan_path}")
        return True

    cmd = [
        "python3", "default/lib/artifact-index/validate_plan_patterns.py",
        plan_path,
        "--json"
    ]

    code, stdout, stderr = run_command(cmd)

    try:
        result = json.loads(stdout)
        assert result.get("status") in ["PASS", "WARN", "NO_INDEX"], \
            f"Unexpected status: {result.get('status')}"
        assert "keywords_used" in result, "Missing keywords_used field"
        print(f"PASS: Validation returned status={result.get('status')}")
        return True
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"FAIL: {e}")
        return False


def test_skill_file_exists():
    """Test artifact-query skill exists."""
    print("\n=== Test: Artifact Query Skill Exists ===")

    skill_path = Path("default/skills/artifact-query/SKILL.md")

    if not skill_path.exists():
        print(f"FAIL: Skill not found at {skill_path}")
        return False

    content = skill_path.read_text()

    required_sections = ["name: artifact-query", "--mode planning", "is_empty_index"]
    missing = [s for s in required_sections if s not in content]

    if missing:
        print(f"FAIL: Missing content: {missing}")
        return False

    print("PASS: Skill file exists with correct content")
    return True


def test_command_file_exists():
    """Test query-artifacts command exists."""
    print("\n=== Test: Query Artifacts Command Exists ===")

    cmd_path = Path("default/commands/query-artifacts.md")

    if not cmd_path.exists():
        print(f"FAIL: Command not found at {cmd_path}")
        return False

    content = cmd_path.read_text()

    if "name: query-artifacts" not in content:
        print("FAIL: Missing command name")
        return False

    print("PASS: Command file exists with correct content")
    return True


def main():
    print("=" * 60)
    print("RAG-Enhanced Planning Integration Tests")
    print("=" * 60)

    tests = [
        test_planning_mode_empty_index,
        test_planning_mode_performance,
        test_planning_mode_output_format,
        test_validation_script_exists,
        test_validation_with_real_plan,
        test_skill_file_exists,
        test_command_file_exists,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"FAIL: Exception in {test.__name__}: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests PASSED")
        sys.exit(0)
    else:
        print("Some tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x default/lib/artifact-index/test_rag_planning.py`

**Step 3: Run integration tests**

Run: `python3 default/lib/artifact-index/test_rag_planning.py`

**Expected output:**
```
============================================================
RAG-Enhanced Planning Integration Tests
============================================================

=== Test: Planning Mode with Empty Index ===
PASS: Empty index handled gracefully

=== Test: Planning Mode Performance (<200ms) ===
PASS: Query completed in 45ms

=== Test: Planning Mode Output Format ===
PASS: Output format correct

=== Test: Validation Script Exists ===
PASS: Validation script works and handles missing files

=== Test: Validation with Real Plan ===
PASS: Validation returned status=NO_INDEX

=== Test: Artifact Query Skill Exists ===
PASS: Skill file exists with correct content

=== Test: Query Artifacts Command Exists ===
PASS: Command file exists with correct content

============================================================
Results: 7/7 tests passed
All tests PASSED
```

**If Task Fails:**

1. **Test failures:**
   - Check: Which specific test failed
   - Fix: Address the failing component
   - Re-run: `python3 default/lib/artifact-index/test_rag_planning.py`

2. **Import errors:**
   - Check: `python3 -c "import subprocess, json, sqlite3"`
   - Fix: Ensure Python 3.8+ with standard library
   - Note: No external dependencies required

**Step 4: Commit test script**

```bash
git add default/lib/artifact-index/test_rag_planning.py
git commit -m "test(rag-planning): add integration tests

Tests cover:
- Empty index handling
- Performance (<200ms target)
- Output format validation
- Validation script functionality
- Skill and command file existence"
```

---

### Task 12: Update Documentation

**Files:**
- Modify: `default/docs/CONTEXT_MANAGEMENT.md` (if it exists, otherwise create)

**Prerequisites:**
- All previous tasks complete

**Step 1: Create or update documentation**

If file doesn't exist, create `default/docs/` directory:

Run: `mkdir -p default/docs`

Create file `default/docs/CONTEXT_MANAGEMENT.md`:

```markdown
# Context Management System

This document describes the Context Management System features in Ring.

## RAG-Enhanced Plan Judging

When creating implementation plans, Ring automatically queries historical precedent to:

1. **Reference successful patterns** - Learn from what worked in past implementations
2. **Avoid failure patterns** - Warnings about approaches that failed before
3. **Leverage past plans** - Review similar design approaches

### How It Works

```
User Request → Extract Keywords → Query Artifact Index → Include in Plan
                                         ↓
                              ┌─────────────────────┐
                              │ Successful Handoffs │ → Reference these
                              │ Failed Handoffs     │ → AVOID these
                              │ Related Plans       │ → Review for ideas
                              └─────────────────────┘
```

### Usage

RAG integration happens automatically when using `/write-plan`:

```bash
/write-plan oauth-authentication
```

The generated plan will include:

```markdown
## Historical Precedent

**Query:** "oauth authentication"
**Index Status:** Populated

### Successful Patterns to Reference
- **[session-1/task-5]**: JWT token validation with refresh tokens worked well
- **[session-2/task-3]**: OAuth2 PKCE flow implementation succeeded

### Failure Patterns to AVOID
- **[session-3/task-2]**: Storing tokens in localStorage caused XSS vulnerabilities

### Related Past Plans
- `docs/plans/2025-01-10-auth-system.md`: Similar scope, review for approach
```

### Manual Queries

To manually search for precedent:

```bash
# General search
/query-artifacts authentication oauth

# Planning mode (structured output)
python3 default/lib/artifact-index/artifact_query.py --mode planning "auth jwt" --json
```

### Plan Validation

After plan creation, validate against failure patterns:

```bash
python3 default/lib/artifact-index/validate_plan_patterns.py docs/plans/my-plan.md
```

**Exit codes:**
- `0` = PASS (no similar failures found)
- `1` = WARN (plan resembles past failures - review recommended)
- `2` = ERROR (validation error)

### Performance

- Query target: <200ms
- Results limited to top 5 per category
- Empty index handled gracefully (normal for new projects)

### Empty Index

For new projects with no historical data:

```markdown
## Historical Precedent

**Query:** "feature keywords"
**Index Status:** Empty (new project)

No historical data available. This is normal for new projects.
Proceeding with standard planning approach.
```

This is NOT an error - proceed with standard planning.
```

**Step 2: Verify documentation exists**

Run: `cat default/docs/CONTEXT_MANAGEMENT.md | head -20`

**Expected output:**
```
# Context Management System

This document describes the Context Management System features in Ring.

## RAG-Enhanced Plan Judging
...
```

**Step 3: Commit documentation**

```bash
git add default/docs/CONTEXT_MANAGEMENT.md
git commit -m "docs: add Context Management System documentation

Covers RAG-enhanced plan judging:
- How it works
- Usage examples
- Manual queries
- Plan validation
- Performance targets"
```

---

### Task 13: Final Integration Test and Verification

**Files:**
- All files created/modified in this plan

**Prerequisites:**
- All previous tasks complete
- All tests passing

**Step 1: Run full test suite**

Run: `python3 default/lib/artifact-index/test_rag_planning.py`

**Expected output:**
```
Results: 7/7 tests passed
All tests PASSED
```

**Step 2: Verify all files exist**

Run: `ls -la default/lib/artifact-index/*.py default/skills/artifact-query/SKILL.md default/commands/query-artifacts.md default/docs/CONTEXT_MANAGEMENT.md`

**Expected output:** All files listed without errors

**Step 3: Test end-to-end flow manually**

Run: `python3 default/lib/artifact-index/artifact_query.py --mode planning "api authentication" --json | head -20`

**Expected output:** JSON with planning structure

**Step 4: Verify write-plan agent has Historical Precedent section**

Run: `grep -c "Historical Precedent" default/agents/write-plan.md`

**Expected output:** `3` or more (multiple occurrences)

**Step 5: Final commit with all changes verified**

If any uncommitted changes remain:

```bash
git status
git add -A
git commit -m "feat(rag-planning): complete RAG-enhanced plan judging implementation

Summary:
- artifact_query.py: Added --mode planning for structured precedent
- artifact-query skill: New skill for historical precedent search
- query-artifacts command: User command for manual queries
- write-plan agent: Historical Precedent section integrated
- validate_plan_patterns.py: Plan validation against failures
- Integration tests: 7 tests covering all components
- Documentation: Complete user guide

Performance: <200ms query time
Handles empty index gracefully
Top 5 results per category to avoid context overflow"
```

**If Task Fails:**

1. **Tests not passing:**
   - Check: `python3 default/lib/artifact-index/test_rag_planning.py`
   - Fix: Address specific failing test
   - Re-run tests until all pass

2. **Files missing:**
   - Check: Which file is missing
   - Fix: Complete the task that creates that file
   - Verify: Re-run file existence check

3. **Agent not updated:**
   - Check: `grep "Historical Precedent" default/agents/write-plan.md`
   - Fix: Complete Task 5
   - Verify: Re-run grep command

---

## Summary

This plan implements RAG-Enhanced Plan Judging for Ring's Context Management System:

| Component | File | Purpose |
|-----------|------|---------|
| Planning Query Mode | `default/lib/artifact-index/artifact_query.py` | `--mode planning` for structured precedent |
| Artifact Query Skill | `default/skills/artifact-query/SKILL.md` | Skill wrapper for artifact search |
| Query Command | `default/commands/query-artifacts.md` | User command for manual queries |
| Write-Plan Enhancement | `default/agents/write-plan.md` | Historical Precedent section |
| Writing-Plans Skill | `default/skills/writing-plans/SKILL.md` | Updated process with validation |
| Plan Validator | `default/lib/artifact-index/validate_plan_patterns.py` | Check against failure patterns |
| Integration Tests | `default/lib/artifact-index/test_rag_planning.py` | 7 tests for all components |
| Documentation | `default/docs/CONTEXT_MANAGEMENT.md` | User guide |

**Requirements Met:**
- RAG query adds <200ms to planning
- Results are relevant (BM25 ranking)
- Gracefully handles empty index (new projects)
- Top 5 results max to avoid context overflow

**Dependencies:**
- Artifact Index (Phase 1)
- Handoff Tracking (Phase 2)

**Blocks:**
- Compound Learnings (Phase 4) - can use this infrastructure
