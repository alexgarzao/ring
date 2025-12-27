# Context Management System - Macro Architecture Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Integrate 6 interconnected features from Continuous-Claude-v2 into Ring's `default/` plugin to create a self-improving, context-aware agent system.

**Architecture:** A unified context management system that persists session state across `/clear` operations, indexes all execution artifacts for semantic search, monitors context usage with proactive warnings, tracks outcome success/failure for learning, and compounds learnings into permanent rules that improve agent behavior over time.

**Tech Stack:**
- Python 3.8+ (artifact indexing, querying, learning extraction)
- SQLite3 with FTS5 (full-text search)
- Bash shell scripts (hook wrappers)
- JSON (hook configuration, state files)

**Global Prerequisites:**
- Environment: macOS/Linux, Python 3.8+
- Tools: `python3 --version` (3.8+), `sqlite3 --version` (3.x)
- Access: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree

---

## 1. Executive Summary

This system enables Ring users to:

| Capability | User Benefit |
|------------|--------------|
| **Session Continuity** | Never lose work context when running `/clear` - ledger auto-saves and auto-restores |
| **Semantic Search** | Find relevant past work by meaning ("authentication issues") not just keywords |
| **Context Awareness** | Get proactive warnings at 50%/70%/85% context usage before hitting limits |
| **Outcome Tracking** | Know which approaches succeeded vs failed historically |
| **Self-Improvement** | System learns from successes/failures and creates permanent rules automatically |
| **RAG-Enhanced Planning** | New plans reference historical precedent for better decisions |

**Key Insight:** These 6 features form a **compounding loop** - outcomes feed learnings, learnings become rules, rules improve outcomes, better outcomes generate richer learnings.

---

## 2. Architecture Diagram

```
                            RING CONTEXT MANAGEMENT SYSTEM
    ================================================================================

    +-----------------+     +------------------+     +-------------------+
    |   SESSION       |     |    ARTIFACT      |     |   CONTEXT USAGE   |
    |   CONTINUITY    |---->|    INDEX         |<----|   WARNINGS        |
    |   (Ledger)      |     |   (SQLite+FTS5)  |     |   (% Monitor)     |
    +-----------------+     +------------------+     +-------------------+
           |                        ^  |                      |
           |                        |  |                      |
           v                        |  v                      v
    +------------+           +------+------+           +-------------+
    |  Session   |           |  FTS5 Query |           |  Hook:      |
    |  State     |           |  Engine     |           |  Prompt     |
    |  Files     |           +-------------+           |  Submit     |
    +------------+                  |                  +-------------+
           |                        |
           |                        v
           |               +------------------+
           +-------------->|   RAG-ENHANCED   |
                           |   PLAN JUDGING   |
                           +------------------+
                                    |
                                    v
                           +------------------+
                           |   HANDOFF/       |
                           |   OUTCOME        |<----- User Feedback
                           |   TRACKING       |       (Success/Fail)
                           +------------------+
                                    |
                                    v
                           +------------------+
                           |   COMPOUND       |
                           |   LEARNINGS      |------> New Rules
                           |   -> RULES       |        New Skills
                           +------------------+        New Hooks

    ================================================================================
                              HOOK INTEGRATION POINTS

    SessionStart          UserPromptSubmit       PostToolUse            Stop/SessionEnd
         |                       |                    |                       |
         v                       v                    v                       v
    +----------+           +----------+         +----------+            +----------+
    | Load     |           | Context  |         | Index    |            | Save     |
    | Ledger   |           | Usage    |         | Artifact |            | Ledger   |
    | State    |           | Check    |         | (Write)  |            | Extract  |
    +----------+           +----------+         +----------+            | Learnings|
                                                                        +----------+

    ================================================================================
                                DATA FLOW

    User Session --> Ledger State --> Artifacts --> Index --> Query --> Planning
         |                                                        |
         v                                                        v
    Outcomes -----> Learnings -----> Rules -----> Better Behavior -----> Loop
```

---

## 3. Shared Infrastructure

These components are used by multiple features and MUST be implemented first:

### 3.1 Artifact Index Database

**Used by:** Handoff Tracking, Outcome Tracking, RAG Plan Judging, Compound Learnings

**Location:** `default/lib/artifact-index/`

**Components:**
- `artifact_schema.sql` - Database schema (handoffs, plans, continuity, queries tables with FTS5)
- `artifact_index.py` - Indexing script (parse markdown, insert into SQLite)
- `artifact_query.py` - Query script (FTS5 search, BM25 ranking)
- `artifact_mark.py` - Outcome marking script

**Database Location:** `$PROJECT_ROOT/.ring/cache/artifact-index/context.db`

**Schema Tables:**
| Table | Purpose | FTS5 Index |
|-------|---------|------------|
| `handoffs` | Task completion records with outcomes | `handoffs_fts` |
| `plans` | Implementation plan documents | `plans_fts` |
| `continuity` | Session state snapshots | `continuity_fts` |
| `queries` | Past searches (for compound learning) | `queries_fts` |

### 3.2 State File Structure

**Used by:** Continuity Ledger, Context Warnings, Outcome Tracking

**Location:** `$PROJECT_ROOT/.ring/state/`

```
.ring/
  state/
    current-session.json     # Active session metadata
    context-usage.json       # Real-time context tracking
  cache/
    artifact-index/
      context.db             # SQLite database
    learnings/
      YYYY-MM-DD-*.md        # Extracted learnings per session
  ledgers/
    CONTINUITY-<session>.md  # Session state files
```

### 3.3 Shared Shell Library

**Used by:** All hooks

**Location:** `default/lib/shell/`

**Components:**
- `json-escape.sh` - RFC 8259 JSON string escaping
- `hook-utils.sh` - Common hook patterns (stdin reading, JSON output)
- `context-check.sh` - Context usage estimation utilities

---

## 4. Feature Dependency Graph

```
Implementation Order (Critical Path):
======================================

Phase 0: Foundation (No Dependencies)
  [0.1] Shared Shell Library
  [0.2] State File Structure
  [0.3] Artifact Index Schema

Phase 1: Core Storage (Depends on Phase 0)
  [1.1] Artifact Index Database -----> [0.3]
  [1.2] Continuity Ledger System ----> [0.2]

Phase 2: Data Capture (Depends on Phase 1)
  [2.1] Handoff Tracking ------------> [1.1]
  [2.2] Outcome Marking -------------> [1.1], [2.1]

Phase 3: Intelligence (Depends on Phase 1, 2)
  [3.1] Context Usage Warnings ------> [0.2]
  [3.2] RAG Plan Judging ------------> [1.1], [2.1]

Phase 4: Self-Improvement (Depends on Phase 2, 3)
  [4.1] Compound Learnings ---------> [1.1], [2.2], [3.2]
```

**Dependency Matrix:**

| Feature | Depends On | Blocks |
|---------|------------|--------|
| Shared Shell Library | (none) | All hooks |
| State File Structure | (none) | Ledger, Context |
| Artifact Index Schema | (none) | Artifact Index |
| Artifact Index Database | Schema | Handoffs, RAG, Learnings |
| Continuity Ledger | State Files | (none - independent) |
| Handoff Tracking | Artifact Index | Outcome Marking |
| Outcome Marking | Artifact Index, Handoffs | Learnings |
| Context Usage Warnings | State Files | (none - independent) |
| RAG Plan Judging | Artifact Index, Handoffs | Learnings |
| Compound Learnings | All above | (none - terminal) |

---

## 5. Directory Structure

**New directories and files in `default/` plugin:**

```
default/
  hooks/
    hooks.json                           # UPDATE: Add new hook registrations
    session-start.sh                     # UPDATE: Add ledger loading
    context-usage-check.sh               # NEW: Context % monitoring
    ledger-save.sh                       # NEW: Pre-compact/stop ledger save
    artifact-index-write.sh              # NEW: Index on Write tool
    session-outcome.sh                   # NEW: SessionEnd outcome prompt

  lib/                                   # NEW: Shared libraries
    shell/
      json-escape.sh                     # JSON escaping utilities
      hook-utils.sh                      # Common hook patterns
      context-check.sh                   # Context estimation
    artifact-index/
      artifact_schema.sql                # SQLite schema
      artifact_index.py                  # Indexing script
      artifact_query.py                  # Query script
      artifact_mark.py                   # Outcome marking

  skills/
    continuity-ledger/                   # NEW: Session state skill
      SKILL.md
    handoff-tracking/                    # NEW: Handoff creation skill
      SKILL.md
    compound-learnings/                  # NEW: Learning extraction skill
      SKILL.md
    artifact-query/                      # NEW: RAG search skill
      SKILL.md

  commands/
    create-handoff.md                    # NEW: /create-handoff command
    resume-handoff.md                    # NEW: /resume-handoff command
    query-artifacts.md                   # NEW: /query-artifacts command
    compound-learnings.md                # NEW: /compound-learnings command

  agents/
    (no new agents - features use existing orchestration)

  docs/
    CONTEXT_MANAGEMENT.md                # NEW: User documentation
```

---

## 6. Hook Integration Map

**How each feature connects to Ring's hook system:**

### 6.1 SessionStart Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` (UPDATE) | `startup\|resume\|compact\|clear` | Load ledger, inject critical rules |

**Changes to existing `session-start.sh`:**
- Add ledger detection: `ls .ring/ledgers/CONTINUITY-*.md`
- Auto-load active ledger content into `additionalContext`
- Inject context usage status

### 6.2 UserPromptSubmit Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `context-usage-check.sh` (NEW) | `*` (all prompts) | Monitor context %, inject warnings |

**Warning Tiers:**
- 50%: Informational ("Context at 50%, consider summarizing soon")
- 70%: Warning ("Context at 70%, recommend /clear with ledger")
- 85%: Critical ("Context at 85%, MUST clear soon or risk losing work")

### 6.3 PostToolUse Hooks

| Hook | Core two | Purpose |
|------|---------|---------|
| `artifact-index-write.sh` (NEW) | `Write` | Index handoffs/plans on creation |

**Behavior:**
- Detect if written file is in `handoffs/` or `plans/` directory
- Run `artifact_index.py --file <path>` for immediate indexing
- Fast path: Single file index takes <100ms

### 6.4 PreCompact Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `ledger-save.sh` (NEW) | PreCompact | Auto-save ledger before compaction |

**Behavior:**
- Check if active ledger exists
- Update ledger with current state
- Warn user: "Ledger saved. After compact, state will auto-restore."

### 6.5 Stop/SessionEnd Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `ledger-save.sh` (NEW) | Stop | Save ledger when agent stops |
| `session-outcome.sh` (NEW) | SessionEnd | Prompt for outcome, extract learnings |

**Outcome Flow:**
1. Agent stops
2. User prompted: "How did this session go?" (SUCCEEDED/PARTIAL_PLUS/PARTIAL_MINUS/FAILED)
3. Outcome saved to most recent handoff
4. Learnings extracted to `.ring/cache/learnings/`

---

## 7. Data Flow

### 7.1 Session Lifecycle

```
1. Session Start
   SessionStart hook fires
   ├── Check for active ledger in .ring/ledgers/
   ├── If found: Load into additionalContext
   └── Inject: Context usage status, critical rules

2. User Works
   UserPromptSubmit hook fires (every prompt)
   ├── Estimate context usage from session state
   ├── If >50%: Inject appropriate warning
   └── Continue processing

3. Artifacts Created
   PostToolUse(Write) hook fires
   ├── Check if file is handoff/plan
   ├── If yes: Run artifact_index.py --file <path>
   └── Artifact now searchable

4. Context Pressure
   User runs /clear OR PreCompact triggers
   ├── ledger-save.sh saves current state
   └── User informed: "State preserved in ledger"

5. Session Ends
   SessionEnd hook fires
   ├── Prompt for outcome (SUCCEEDED/PARTIAL/FAILED)
   ├── Mark outcome on latest handoff
   └── Extract learnings to cache
```

### 7.2 RAG-Enhanced Planning Flow

```
1. User requests new plan
   ├── Agent recognizes planning task
   └── Invokes artifact_query.py

2. Query artifacts
   ├── Search handoffs: "similar past implementations"
   ├── Search plans: "similar design approaches"
   └── Return: Top 5 relevant results with outcomes

3. Plan creation informed
   ├── Agent sees: "Authentication: SUCCEEDED (3x), FAILED (1x)"
   ├── Agent sees: What worked / What failed from past attempts
   └── New plan avoids past failures, reuses successes

4. Plan executed
   ├── Outcomes tracked
   └── Cycle continues (compounding)
```

### 7.3 Compound Learning Flow

```
1. Trigger
   ├── User runs /compound-learnings
   └── OR: Automatic on session end (if learnings exist)

2. Gather learnings
   ├── Read .ring/cache/learnings/*.md
   └── Aggregate patterns across sessions

3. Pattern detection
   ├── Frequency analysis: Which patterns appear 3+ times?
   ├── Consolidate similar patterns
   └── Categorize: Rule vs Skill vs Hook

4. Proposal
   ├── Present draft rules/skills to user
   └── Get approval

5. Creation
   ├── Write approved rules to .claude/rules/
   ├── Write approved skills to default/skills/
   └── System permanently improved
```

---

## 8. Implementation Phases

### Phase 0: Foundation (Day 1)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `default/lib/shell/` with utilities | 1hr | None |
| Create `default/lib/artifact-index/` structure | 30min | None |
| Create `.ring/` directory structure | 30min | None |
| Copy and adapt `artifact_schema.sql` | 1hr | None |

**Deliverable:** Empty directory structure with schema

---

### Phase 1: Core Storage (Days 2-3)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Implement `artifact_index.py` | 3hr | Schema |
| Implement `artifact_query.py` | 2hr | Index |
| Create `continuity-ledger` skill | 2hr | State structure |
| Update `session-start.sh` for ledger loading | 2hr | Ledger skill |
| Create `ledger-save.sh` hook | 1hr | Ledger skill |

**Deliverable:** Working ledger system, empty artifact index

---

### Phase 2: Data Capture (Days 4-5)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `handoff-tracking` skill | 3hr | Index |
| Implement `artifact-index-write.sh` hook | 2hr | Index |
| Create `create-handoff` command | 1hr | Skill |
| Implement `artifact_mark.py` | 2hr | Index |
| Create `session-outcome.sh` hook | 2hr | Mark script |

**Deliverable:** Handoffs indexed automatically, outcomes tracked

---

### Phase 3: Intelligence (Days 6-7)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Implement `context-usage-check.sh` hook | 3hr | State structure |
| Create `artifact-query` skill | 2hr | Query script |
| Create `query-artifacts` command | 1hr | Skill |
| Integrate RAG into `write-plan` agent | 3hr | Query skill |

**Deliverable:** Context warnings active, plans reference history

---

### Phase 4: Self-Improvement (Days 8-10)

| Task | Effort | Dependencies |
|------|--------|--------------|
| Create `compound-learnings` skill | 4hr | All above |
| Create `compound-learnings` command | 1hr | Skill |
| Implement learning extraction in `session-outcome.sh` | 2hr | Outcomes |
| Create user documentation | 2hr | All features |

**Deliverable:** Complete system with compounding loop

---

## 9. Individual Plan References

Each feature will have its own detailed implementation plan:

| Feature | Plan Location | Status |
|---------|---------------|--------|
| Shared Infrastructure | `docs/plans/YYYY-MM-DD-context-shared-infra.md` | PENDING |
| Continuity Ledger | `docs/plans/YYYY-MM-DD-context-continuity-ledger.md` | PENDING |
| Artifact Index | `docs/plans/YYYY-MM-DD-context-artifact-index.md` | PENDING |
| Handoff/Outcome Tracking | `docs/plans/YYYY-MM-DD-context-handoff-tracking.md` | PENDING |
| Context Usage Warnings | `docs/plans/YYYY-MM-DD-context-usage-warnings.md` | PENDING |
| RAG Plan Judging | `docs/plans/YYYY-MM-DD-context-rag-planning.md` | PENDING |
| Compound Learnings | `docs/plans/YYYY-MM-DD-context-compound-learnings.md` | PENDING |

**Creation Order:** Follow dependency graph in Section 4.

---

## 10. Success Criteria

### 10.1 Feature Acceptance Criteria

| Feature | Success Criteria |
|---------|------------------|
| Continuity Ledger | User runs `/clear`, ledger auto-saves, new session auto-loads state |
| Artifact Index | `artifact_query.py "auth"` returns relevant handoffs within 100ms |
| Context Warnings | Warning appears at 50%, 70%, 85% thresholds accurately |
| Handoff Tracking | New handoff automatically indexed, searchable immediately |
| Outcome Tracking | SessionEnd prompts for outcome, marks in database |
| RAG Planning | `write-plan` agent includes historical context in output |
| Compound Learnings | Pattern appearing 3+ times generates rule proposal |

### 10.2 Integration Acceptance Criteria

| Test | Expected Result |
|------|-----------------|
| Full session lifecycle | Start -> Work -> Clear -> Resume -> End with outcome |
| Cross-session search | Query finds handoffs from previous sessions |
| Learning loop | Failed approach in session 1 -> Rule created -> Avoided in session 2 |

---

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hook performance overhead | Medium | High | Fast-path single file indexing, async where possible |
| SQLite concurrency issues | Low | Medium | Use WAL mode, single writer pattern |
| Context estimation inaccuracy | Medium | Low | Conservative estimates, err toward earlier warnings |
| User adoption | Medium | Medium | Gradual rollout, clear documentation, sensible defaults |

---

## 12. Reference Implementation

**Source:** `/Users/fredamaral/repos/lerianstudio/ring/.references/Continuous-Claude-v2/`

| Reference File | Ring Adaptation |
|----------------|-----------------|
| `scripts/artifact_index.py` | `default/lib/artifact-index/artifact_index.py` |
| `scripts/artifact_schema.sql` | `default/lib/artifact-index/artifact_schema.sql` |
| `scripts/artifact_query.py` | `default/lib/artifact-index/artifact_query.py` |
| `.claude/hooks/` | `default/hooks/` (adapt to Ring hook patterns) |
| `.claude/skills/continuity_ledger/` | `default/skills/continuity-ledger/` |
| `.claude/skills/compound-learnings/` | `default/skills/compound-learnings/` |
| `.claude/skills/create_handoff/` | `default/skills/handoff-tracking/` |

---

## Next Steps

1. **Approve this macro plan** - Review architecture decisions
2. **Run `/write-plan` for Phase 0** - Generate detailed plan for shared infrastructure
3. **Iterate through phases** - Each phase generates its own detailed plan
4. **Code review at each phase** - Ensure quality gates before proceeding

---

**Plan complete and saved to `docs/plans/2025-12-27-context-management-system.md`.**
