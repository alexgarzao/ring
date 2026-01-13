# Ring Continuity - Research Phase (Gate 0)

> **Generated:** 2026-01-12
> **Research Mode:** Modification (extending existing Ring functionality)
> **Agents Used:** repo-research-analyst, best-practices-researcher, framework-docs-researcher

---

## Executive Summary

Ring already has significant infrastructure for continuity (handoff tracking, continuity ledger, SQLite FTS5 indexing). The implementation will extend these patterns to add:
1. **~/.ring/** global directory (currently only project-local `.ring/`)
2. **Persistent memory** with SQLite FTS5 (lightweight, no dependencies)
3. **YAML handoffs** (~400 tokens vs ~2000 markdown)
4. **skill-rules.json** for activation routing
5. **Confidence markers** in agent outputs

---

## Codebase Research Findings

### Existing Handoff System

| Aspect | Current State | File Reference |
|--------|---------------|----------------|
| **Skill Location** | `default/skills/handoff-tracking/SKILL.md` | Lines 1-208 |
| **Format** | Markdown with YAML frontmatter | Lines 57-123 |
| **Token Cost** | ~1200-2000 tokens per handoff | Measured from examples |
| **Storage Path** | `docs/handoffs/{session-name}/*.md` | Lines 46-55 |
| **Indexing** | Auto-indexed via PostToolUse hook | `default/hooks/artifact-index-write.sh` |

**Current Handoff Template (frontmatter):**
```yaml
---
date: {ISO timestamp}
session_name: {session-name}
git_commit: {hash}
branch: {branch}
repository: {repo}
topic: "{description}"
tags: [implementation, ...]
status: {complete|in_progress|blocked}
outcome: UNKNOWN
---
```

### Skill Discovery & Activation

| Aspect | Current State | File Reference |
|--------|---------------|----------------|
| **Discovery Script** | `default/hooks/generate-skills-ref.py` | Lines 1-308 |
| **Frontmatter Fields** | name, description, trigger, skip_when, sequence, related | Lines 1-15 |
| **Session Start** | `default/hooks/session-start.sh` | Lines 1-299 |
| **No skill-rules.json** | Manual skill invocation only | Opportunity identified |

**Existing Skill Frontmatter Schema:**
```yaml
---
name: ring:skill-name
description: |
  What the skill does
trigger: |
  - When to use condition 1
skip_when: |
  - Skip condition 1
sequence:
  before: [skill1]
  after: [skill2]
related:
  similar: [skill-a]
---
```

### Agent Output Schemas

**Location:** `docs/AGENT_DESIGN.md:1-275`

| Schema Type | Purpose | Key Sections |
|-------------|---------|--------------|
| Implementation | Code changes | Summary, Implementation, Files Changed, Testing |
| Analysis | Research findings | Analysis, Findings, Recommendations |
| Reviewer | Code review | VERDICT, Issues Found, What Was Done Well |
| Exploration | Codebase analysis | Key Findings, Architecture Insights |
| Planning | Implementation plans | Goal, Architecture, Tasks |

**Existing Confidence Field:**
```sql
-- artifact_schema.sql:37-40
confidence TEXT CHECK(confidence IN ('HIGH', 'INFERRED')) DEFAULT 'INFERRED'
```

### Hook System Architecture

**Location:** `default/hooks/hooks.json:1-90`

| Event | Hooks | Purpose |
|-------|-------|---------|
| SessionStart | session-start.sh | Load ledgers, generate skills overview |
| UserPromptSubmit | claude-md-reminder.sh, context-usage-check.sh | Context injection |
| PostToolUse | artifact-index-write.sh, task-completion-check.sh | Indexing, validation |
| PreCompact | ledger-save.sh | State preservation |
| Stop | ledger-save.sh, outcome-inference.sh, learning-extract.sh | Session end |

**Hook Output Schema:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "escaped content string"
  }
}
```

### Directory Conventions

| Directory | Purpose | Scope |
|-----------|---------|-------|
| `.ring/ledgers/` | Continuity ledger files | Project-local |
| `.ring/cache/artifact-index/` | SQLite database (context.db) | Project-local |
| `.ring/state/` | Session state files | Project-local |
| `docs/handoffs/` | Handoff documents | Project-local |
| **~/.ring/** | **NOT YET IMPLEMENTED** | Global (new) |

### SQLite FTS5 Implementation

**Schema Location:** `default/lib/artifact-index/artifact_schema.sql:1-343`

| Table | Purpose | FTS5 Index |
|-------|---------|------------|
| handoffs | Task records | handoffs_fts |
| plans | Design documents | plans_fts |
| continuity | Session snapshots | continuity_fts |
| queries | Compound learning Q&A | queries_fts |
| learnings | Extracted patterns | learnings_fts |

---

## Best Practices Research Findings

### Memory System Design

**Memory Type Taxonomy (Industry Standard):**

| Memory Type | Purpose | Storage Strategy |
|-------------|---------|------------------|
| **Episodic** | Interaction events | Timestamped logs |
| **Semantic** | Extracted knowledge | Key-value pairs |
| **Procedural** | Behavioral patterns | Policy rules |

**Key Recommendations:**
- Never rely on LLM implicit weights for facts
- Implement utility-based deletion (10% performance gain)
- Define explicit retention policies (what, how long, when to delete)
- Use semantic deduplication (0.85 similarity threshold)

**Learning Types for Ring:**
```python
LEARNING_TYPES = [
    "FAILED_APPROACH",        # Things that didn't work
    "WORKING_SOLUTION",       # Successful approaches
    "USER_PREFERENCE",        # User style/preferences
    "CODEBASE_PATTERN",       # Discovered code patterns
    "ARCHITECTURAL_DECISION", # Design choices made
    "ERROR_FIX",              # Error->solution pairs
    "OPEN_THREAD",            # Unfinished work/TODOs
]
```

### Session Continuity Patterns

**YAML vs Markdown:**
- YAML: Machine-parseable, ~400 tokens, schema-validatable
- Markdown: Human-readable, ~2000 tokens, flexible
- **Hybrid recommended:** YAML frontmatter + Markdown body

**Essential Handoff Fields:**

| Field | Purpose | Required |
|-------|---------|----------|
| session_id | Unique identifier | Yes |
| timestamp | Creation time | Yes |
| task_summary | 1-2 sentence summary | Yes |
| current_state | planning/implementing/testing/blocked | Yes |
| key_decisions | Architectural choices | Yes |
| blockers | What prevented completion | If applicable |
| next_steps | What to do on resume | Yes |

**Anthropic's Context Engineering:**
1. Treat context as finite "attention budget"
2. Just-in-time loading (identifiers, not content)
3. Compaction (summarize, preserve decisions)
4. Progressive disclosure

### Skill Activation Patterns

**Three-Tier Enforcement:**

| Level | Behavior | Use Case |
|-------|----------|----------|
| **Block** | Must use skill | Critical workflows (TDD) |
| **Suggest** | Offer, allow skip | Helpful optimizations |
| **Warn** | Log availability | Analytics/learning |

**Layered Matching Approach:**
1. Rules/Regex (fast, deterministic)
2. Lemmatization (word forms)
3. Fuzzy matching (typos)
4. Semantic fallback (novel expressions)

**False Positive Reduction:**
- Negative patterns (exclude non-matches)
- Context-aware matching (verb+noun, not just nouns)
- Confidence thresholds (>0.85 auto, 0.6-0.85 suggest)

### Confidence Markers

**Critical Finding:** Natural language epistemic markers are unreliable in out-of-distribution scenarios.

**Recommended Approach:** Structured verification status

```yaml
verification:
  status: verified|unverified|partially_verified|needs_review
  evidence:
    - type: test_passed|code_review|manual_check|assumption
      description: string
  confidence_factors:
    code_exists: boolean
    tests_pass: boolean
    reviewed: boolean
```

**Confidence Markers for Ring:**

| Marker | Symbol | Meaning |
|--------|--------|---------|
| VERIFIED | ✓ | Read the file, traced the code |
| INFERRED | ? | Based on grep/search |
| UNCERTAIN | ✗ | Haven't checked |

### SQLite FTS5 Best Practices

**When FTS5 is Sufficient:**
- Keyword search
- Exact phrase matching
- Known vocabulary
- Typo tolerance (with trigram)

**When Embeddings Needed:**
- Semantic similarity
- Cross-language search
- Synonym expansion

**Recommended Tokenizer:**
```sql
CREATE VIRTUAL TABLE memories USING fts5(
    content,
    category,
    tags,
    tokenize = 'porter unicode61 remove_diacritics 1',
    prefix = '2 3'
);
```

**BM25 Column Weighting:**
```sql
SELECT *, bm25(memories, 10.0, 5.0, 1.0) as relevance
-- title:10x, tags:5x, content:1x
FROM memories WHERE memories MATCH 'query'
ORDER BY relevance;
```

---

## Framework Documentation Findings

### Claude Code Hook System

**Input Format (stdin):**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "prompt": "string"
}
```

**Output Format (stdout):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Content injected into context"
  }
}
```

**Blocking Response (PreToolUse):**
```json
{
  "result": "block",
  "reason": "Reason for blocking"
}
```

**Environment Variables:**
- `CLAUDE_PLUGIN_ROOT` - Plugin directory
- `CLAUDE_PROJECT_DIR` - Project directory
- `CLAUDE_SESSION_ID` - Session identifier

### SQLite FTS5 Python Implementation

```python
import sqlite3

def create_memory_database(db_path: str):
    conn = sqlite3.connect(db_path)

    # Main table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            context TEXT,
            tags TEXT,
            confidence TEXT DEFAULT 'medium'
        )
    """)

    # FTS5 virtual table
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            content, context, tags,
            content_rowid='id',
            tokenize='porter unicode61'
        )
    """)

    # Auto-sync triggers
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS memories_ai
        AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, content, context, tags)
            VALUES (new.id, new.content, new.context, new.tags);
        END
    """)

    return conn
```

### YAML Schema Design

**PyYAML Safe Loading:**
```python
import yaml

def load_handoff(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        content = f.read()

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return {'frontmatter': frontmatter, 'body': body}

    return yaml.safe_load(content)
```

### JSON Schema for Skill Rules

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["version", "skills"],
  "properties": {
    "version": {"type": "string"},
    "skills": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["type", "enforcement", "priority"],
        "properties": {
          "type": {"enum": ["guardrail", "domain", "workflow"]},
          "enforcement": {"enum": ["block", "suggest", "warn"]},
          "priority": {"enum": ["critical", "high", "medium", "low"]},
          "promptTriggers": {
            "type": "object",
            "properties": {
              "keywords": {"type": "array", "items": {"type": "string"}},
              "intentPatterns": {"type": "array", "items": {"type": "string"}}
            }
          }
        }
      }
    }
  }
}
```

### Version Constraints

| Dependency | Version | Notes |
|------------|---------|-------|
| Python | 3.9+ | match statements, type hints |
| PyYAML | >=6.0 | safe_load by default |
| SQLite | 3.35+ | FTS5 in stdlib |
| jsonschema | >=4.0 | Draft 2020-12 support |
| Bash | 4.0+ | associative arrays |

---

## Potential Conflicts & Risks

### Database Location Conflict
- **Current:** `.ring/cache/artifact-index/context.db` (project-local)
- **New:** Need both project-local AND `~/.ring/` global databases
- **Resolution:** Dual database support with merge queries

### Handoff Format Change
- **Current:** Markdown with YAML frontmatter
- **New:** Pure YAML
- **Resolution:** Migration script + dual-format indexer support

### Hook Timing
- **Current:** Stop hook runs outcome-inference.sh, learning-extract.sh sequentially
- **Risk:** Adding memory writes may cause timeout
- **Resolution:** Background write or async processing

### Session Isolation
- **Current:** State files use `${SESSION_ID}` in filenames
- **Risk:** Global memory needs cross-session identifier strategy
- **Resolution:** User-scoped vs project-scoped memory distinction

---

## Recommended Architecture

### ~/.ring/ Directory Structure

```
~/.ring/
├── config.yaml              # User preferences
├── memory.db                # Global SQLite + FTS5
├── skill-rules.json         # Activation rules
├── skill-rules-schema.json  # JSON Schema for validation
├── state/                   # Session state
│   └── context-usage-{session}.json
├── ledgers/                 # Global continuity ledgers
│   └── CONTINUITY-{name}.md
├── handoffs/                # Global handoffs
│   └── {session}/
│       └── {timestamp}.yaml
└── logs/                    # Debug logs
    └── {date}.log
```

### Phased Implementation

| Phase | Components | Effort | Impact |
|-------|------------|--------|--------|
| **1** | ~/.ring/ structure + migration | Low | Foundation |
| **2** | YAML handoff format | Medium | High (5x token efficiency) |
| **3** | Confidence markers in agents | Low | High (reduces false claims) |
| **4** | skill-rules.json + activation hook | Medium | Medium (better routing) |
| **5** | Global memory system | High | High (cross-session learning) |

---

## Gate 0 Validation Checklist

- [x] Research mode determined: **Modification** (extending existing functionality)
- [x] All 3 agents dispatched and returned
- [x] File:line references included (see Codebase Research Findings)
- [x] External URLs included (see Best Practices Research Findings)
- [x] Tech stack versions documented (Python 3.9+, SQLite 3.35+, etc.)
- [x] Existing patterns identified for reuse
- [x] Potential conflicts documented with resolutions

---

## Sources

### Codebase References
- `default/skills/handoff-tracking/SKILL.md:1-208`
- `default/hooks/generate-skills-ref.py:1-308`
- `default/hooks/session-start.sh:1-299`
- `default/hooks/hooks.json:1-90`
- `default/lib/artifact-index/artifact_schema.sql:1-343`
- `docs/AGENT_DESIGN.md:1-275`

### External Sources
- [SQLite FTS5 Documentation](https://sqlite.org/fts5.html)
- [Anthropic - Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Mem0 Research Paper](https://arxiv.org/abs/2504.19413)
- [IBM - What Is AI Agent Memory](https://www.ibm.com/think/topics/ai-agent-memory)
- [Skywork - AI Agent Orchestration Best Practices](https://skywork.ai/blog/ai-agent-orchestration-best-practices-handoffs/)
- [ACL 2025 - Epistemic Markers](https://aclanthology.org/2025.acl-short.18/)
