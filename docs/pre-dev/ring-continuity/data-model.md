# Ring Continuity - Data Model (Gate 5)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** API Design v1.0 (docs/pre-dev/ring-continuity/api-design.md)

---

## Executive Summary

The Ring Continuity data model consists of **7 core entities** organized into **3 data ownership domains**: User Domain (global preferences), Session Domain (ephemeral state), and Artifact Domain (persistent documents). The model uses **event sourcing** for audit trails, **soft deletion** for data safety, and **denormalized search indexes** for performance.

**Key Patterns:**
- **Event Sourcing** for memory creation/access tracking
- **Soft Deletion** for recoverable data removal
- **Denormalized Indexes** for full-text search
- **Hierarchical Configuration** for precedence resolution

---

## Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER DOMAIN                               │
│  ┌──────────────┐                    ┌──────────────────┐       │
│  │ UserConfig   │                    │ ActivationRule   │       │
│  └──────────────┘                    └──────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ influences
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SESSION DOMAIN                              │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   Session    │────────>│  SessionLog  │                      │
│  └──────┬───────┘  1:N    └──────────────┘                      │
│         │                                                        │
│         │ 1:N                                                    │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   Learning   │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ references
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ARTIFACT DOMAIN                              │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   Handoff    │         │     Plan     │                      │
│  └──────┬───────┘         └──────────────┘                      │
│         │                                                        │
│         │ 1:N                                                    │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   Artifact   │<───────────────────┐                          │
│  │  Reference   │                    │                          │
│  └──────────────┘                    │                          │
│                                      │                          │
│  ┌──────────────────────────────────┴────┐                     │
│  │      Full-Text Search Index           │                     │
│  │  (Denormalized for performance)       │                     │
│  └───────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Entities

### Entity 1: Learning

**Purpose:** Stores a single piece of knowledge extracted from sessions.

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | Identifier | Yes | Unique learning identifier |
| session_id | Identifier | Yes | Source session |
| created_at | Timestamp | Yes | When learning was created |
| accessed_at | Timestamp | Yes | Last access time |
| access_count | Integer | Yes | Number of times accessed |
| content | Text | Yes | The learning content |
| type | LearningType | Yes | Classification (enum) |
| tags | List<String> | No | Searchable tags |
| confidence | ConfidenceLevel | Yes | HIGH, MEDIUM, LOW |
| context | Text | No | Additional context |
| expires_at | Timestamp | No | Auto-deletion time |
| relevance_score | Float | Yes | Current relevance (decays) |
| source | String | Yes | Where learning came from |
| deleted_at | Timestamp | No | Soft deletion timestamp |

**Relationships:**
- `session_id` → Session (M:1)

**Constraints:**
- `type` must be in LearningType enum
- `confidence` must be in ConfidenceLevel enum
- `relevance_score` between 0.0 and 1.0
- `access_count` >= 0
- If `deleted_at` is set, learning excluded from searches

**Indexes:**
- Primary: `id`
- Search: Full-text index on `content`, `context`, `tags`
- Filter: `type`, `session_id`, `confidence`
- Cleanup: `expires_at`, `deleted_at`

---

### Entity 2: Session

**Purpose:** Tracks a Ring session for traceability.

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | Identifier | Yes | Unique session identifier |
| project_path | FilePath | Yes | Project directory |
| started_at | Timestamp | Yes | Session start time |
| ended_at | Timestamp | No | Session end time |
| duration_seconds | Integer | No | Calculated duration |
| mode | SessionMode | Yes | STARTUP, RESUME, CLEAR, COMPACT |
| git_commit | String | No | Git commit at start |
| git_branch | String | No | Git branch at start |
| outcome | Outcome | No | Session outcome |

**Relationships:**
- 1:N with Learning
- 1:N with SessionLog
- 1:1 with Handoff (optional)

**Constraints:**
- `ended_at` >= `started_at` if both set
- `duration_seconds` = `ended_at` - `started_at`
- `mode` must be in SessionMode enum

**Indexes:**
- Primary: `id`
- Query: `project_path`, `started_at`

---

### Entity 3: Handoff

**Purpose:** Captures session state for cross-session continuity.

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | Identifier | Yes | Unique handoff identifier |
| session_id | Identifier | Yes | Source session |
| created_at | Timestamp | Yes | When handoff created |
| format | HandoffFormat | Yes | YAML or MARKDOWN |
| file_path | FilePath | Yes | Storage location |
| task_summary | Text | Yes | 1-2 sentence summary |
| status | TaskStatus | Yes | COMPLETED, PAUSED, BLOCKED, FAILED |
| outcome | Outcome | No | SUCCEEDED, PARTIAL_PLUS, etc. |
| outcome_marked_at | Timestamp | No | When outcome was marked |
| skills_used | List<String> | No | Skills invoked |
| git_commit | String | Yes | Git state at handoff |
| git_branch | String | Yes | Git branch |
| key_files | List<FilePath> | No | Most relevant files (max 10) |
| next_steps | List<String> | Yes | Resume instructions |
| token_count | Integer | No | Estimated tokens in handoff |

**Relationships:**
- `session_id` → Session (M:1)
- N:M with ArtifactReference

**Constraints:**
- `format` must be YAML or MARKDOWN
- `status` must be in TaskStatus enum
- `key_files` max length 10
- `next_steps` must be non-empty
- `token_count` estimated from file size

**Indexes:**
- Primary: `id`
- Search: Full-text index on `task_summary`, decisions, learnings
- Filter: `session_id`, `status`, `outcome`, `created_at`

---

### Entity 4: UserConfig

**Purpose:** Stores user preferences and settings.

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| scope | ConfigScope | Yes | GLOBAL or PROJECT |
| key | String | Yes | Config key (dot notation) |
| value | Any | Yes | Config value (JSON-serializable) |
| source | FilePath | Yes | Which config file |
| precedence | Integer | Yes | 0=default, 1=global, 2=project |
| description | String | No | Human-readable description |
| updated_at | Timestamp | Yes | Last update time |

**Relationships:**
- None (flat key-value store)

**Constraints:**
- `key` format: `category.subcategory.setting` (dot notation)
- `precedence` must match `scope` (GLOBAL=1, PROJECT=2)
- `value` must be JSON-serializable

**Indexes:**
- Primary: `(scope, key)`
- Query: `key`, `scope`

**Access Patterns:**
- Read: `get_config(scope, key)` → merge with precedence
- Write: `set_config(scope, key, value)` → update or insert
- Query: `list_config(scope)` → all keys in scope

---

### Entity 5: ActivationRule

**Purpose:** Defines patterns for automatic skill suggestion.

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| skill | String | Yes | ring:skill-name |
| type | RuleType | Yes | GUARDRAIL, DOMAIN, WORKFLOW |
| enforcement | Enforcement | Yes | BLOCK, SUGGEST, WARN |
| priority | Priority | Yes | CRITICAL, HIGH, MEDIUM, LOW |
| description | String | No | Human-readable purpose |
| keywords | List<String> | No | Exact keyword matches |
| intent_patterns | List<String> | No | Regex patterns |
| negative_patterns | List<String> | No | Exclusion patterns |
| scope | ConfigScope | Yes | GLOBAL or PROJECT |
| enabled | Boolean | Yes | Whether rule is active |

**Relationships:**
- None (independent rules)

**Constraints:**
- `skill` must exist in Ring registry
- `enforcement` must be in Enforcement enum
- At least one of `keywords` or `intent_patterns` must be non-empty
- Regex patterns must be valid

**Indexes:**
- Primary: `skill`
- Query: `priority`, `enforcement`, `enabled`

**Access Patterns:**
- Load: Load all enabled rules, merge project > global
- Match: For each rule, check keywords and patterns against prompt

---

### Entity 6: ArtifactReference

**Purpose:** Links handoffs to related artifacts (plans, files).

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | Identifier | Yes | Unique reference ID |
| handoff_id | Identifier | Yes | Source handoff |
| artifact_type | ArtifactType | Yes | PLAN, FILE, RESEARCH, LEDGER |
| artifact_path | FilePath | Yes | Path to artifact |
| relevance | String | Yes | Why this artifact is relevant |
| created_at | Timestamp | Yes | When reference added |

**Relationships:**
- `handoff_id` → Handoff (M:1)

**Constraints:**
- `artifact_type` must be in ArtifactType enum
- `artifact_path` must be relative or absolute valid path

**Indexes:**
- Primary: `id`
- Foreign: `handoff_id`
- Query: `artifact_type`, `artifact_path`

---

### Entity 7: SessionLog

**Purpose:** Audit trail for session events.

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | Identifier | Yes | Unique log entry ID |
| session_id | Identifier | Yes | Session this log belongs to |
| timestamp | Timestamp | Yes | Event time |
| event_type | EventType | Yes | HOOK_EXECUTED, SKILL_ACTIVATED, etc. |
| component | String | Yes | Which component logged |
| level | LogLevel | Yes | DEBUG, INFO, WARN, ERROR |
| message | Text | Yes | Log message |
| metadata | JSON | No | Additional structured data |

**Relationships:**
- `session_id` → Session (M:1)

**Constraints:**
- `event_type` must be in EventType enum
- `level` must be in LogLevel enum
- Logs retained for 30 days, then pruned

**Indexes:**
- Primary: `id`
- Query: `session_id`, `timestamp`, `level`

**Access Patterns:**
- Append-only (no updates)
- Query by session for debugging
- Prune old logs periodically

---

## Entity Schemas (Database-Agnostic)

### Schema: Learning

```
Learning {
  # Identity
  id: UUID

  # Ownership
  session_id: UUID

  # Temporal
  created_at: DateTime (ISO 8601)
  accessed_at: DateTime (ISO 8601)
  access_count: UInt32
  expires_at: DateTime? (ISO 8601)
  deleted_at: DateTime? (ISO 8601)

  # Content
  content: String (max 10000 chars)
  type: Enum {
    FAILED_APPROACH
    WORKING_SOLUTION
    USER_PREFERENCE
    CODEBASE_PATTERN
    ARCHITECTURAL_DECISION
    ERROR_FIX
    OPEN_THREAD
  }
  tags: Array<String> (max 20)
  confidence: Enum { HIGH, MEDIUM, LOW }
  context: String? (max 5000 chars)

  # Metadata
  relevance_score: Float (0.0 to 1.0)
  source: String (max 200 chars)
}
```

**Validation Rules:**
- `content` required, non-empty, max 10000 chars
- `type` required, must be in enum
- `created_at` <= `accessed_at`
- `relevance_score` between 0.0 and 1.0
- If `deleted_at` set, must be >= `created_at`
- `tags` array max 20 items, each max 50 chars

---

### Schema: Handoff

```
Handoff {
  # Identity
  id: UUID

  # Ownership
  session_id: UUID

  # Temporal
  created_at: DateTime (ISO 8601)
  outcome_marked_at: DateTime? (ISO 8601)

  # Storage
  format: Enum { YAML, MARKDOWN }
  file_path: FilePath (absolute)
  token_count: UInt32?

  # Session Context
  task_summary: String (max 500 chars)
  status: Enum { COMPLETED, PAUSED, BLOCKED, FAILED }
  outcome: Enum { SUCCEEDED, PARTIAL_PLUS, PARTIAL_MINUS, FAILED, UNKNOWN }
  skills_used: Array<String>

  # Git Context
  git_commit: String (40 chars)
  git_branch: String (max 200 chars)

  # Resume Data
  key_files: Array<FilePath> (max 10)
  next_steps: Array<String> (min 1)

  # Statistics
  learnings_count: UInt32
  decisions_count: UInt32
  blockers_count: UInt32
}
```

**Validation Rules:**
- `task_summary` required, max 500 chars
- `status` required, must be in enum
- `git_commit` format: 40 hex characters
- `key_files` max 10 items
- `next_steps` min 1 item, each max 500 chars
- `skills_used` items format: `ring:skill-name`

---

### Schema: UserConfig

```
UserConfig {
  # Identity
  scope: Enum { GLOBAL, PROJECT }
  key: String (max 200 chars)

  # Value
  value: JSON

  # Metadata
  source: FilePath
  precedence: UInt8 (0, 1, or 2)
  description: String?
  updated_at: DateTime (ISO 8601)
}
```

**Validation Rules:**
- `key` format: `^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$` (dot notation)
- `precedence` must match `scope`: DEFAULT=0, GLOBAL=1, PROJECT=2
- `value` must be valid JSON
- `source` must exist and be readable

---

### Schema: ActivationRule

```
ActivationRule {
  # Identity
  skill: String (format: ring:skill-name)
  scope: Enum { GLOBAL, PROJECT }

  # Classification
  type: Enum { GUARDRAIL, DOMAIN, WORKFLOW, PROCESS, EXPLORATION }
  enforcement: Enum { BLOCK, SUGGEST, WARN }
  priority: Enum { CRITICAL, HIGH, MEDIUM, LOW }

  # Matching
  keywords: Array<String>
  intent_patterns: Array<RegexPattern>
  negative_patterns: Array<RegexPattern>

  # Metadata
  description: String?
  enabled: Boolean

  # Statistics
  match_count: UInt32       # Times this rule matched
  success_count: UInt32     # Times user used suggested skill
}
```

**Validation Rules:**
- `skill` format: `^ring:[a-z0-9-]+$`
- At least one of `keywords` or `intent_patterns` must be non-empty
- Regex patterns must compile without errors
- `match_count` >= `success_count`

---

### Schema: Session

```
Session {
  # Identity
  id: UUID

  # Context
  project_path: FilePath (absolute)
  started_at: DateTime (ISO 8601)
  ended_at: DateTime? (ISO 8601)
  duration_seconds: UInt32?

  # Mode
  mode: Enum { STARTUP, RESUME, CLEAR, COMPACT }

  # Git Context
  git_commit: String? (40 chars)
  git_branch: String?
  git_remote: String?

  # Outcome
  outcome: Enum { SUCCEEDED, PARTIAL_PLUS, PARTIAL_MINUS, FAILED, UNKNOWN }
  outcome_confidence: Enum { HIGH, LOW }

  # Statistics
  turns_count: UInt32
  tools_used: Array<String>
  skills_invoked: Array<String>
}
```

**Validation Rules:**
- `project_path` must be absolute
- `ended_at` >= `started_at` if both set
- `duration_seconds` = (`ended_at` - `started_at`) if both set
- `git_commit` format: 40 hex chars or empty

---

### Schema: ArtifactReference

```
ArtifactReference {
  # Identity
  id: UUID
  handoff_id: UUID

  # Artifact Info
  artifact_type: Enum { PLAN, FILE, RESEARCH, LEDGER }
  artifact_path: FilePath
  relevance: String (max 200 chars)

  # Temporal
  created_at: DateTime (ISO 8601)

  # Verification
  exists_at_reference: Boolean  # Did file exist when referenced?
  last_verified_at: DateTime?   # Last existence check
}
```

**Validation Rules:**
- `artifact_type` must be in enum
- `relevance` required, non-empty, max 200 chars
- `artifact_path` can be relative or absolute
- If `last_verified_at` set, must be >= `created_at`

---

### Schema: SessionLog

```
SessionLog {
  # Identity
  id: UUID
  session_id: UUID

  # Event
  timestamp: DateTime (ISO 8601)
  event_type: Enum {
    HOOK_EXECUTED,
    SKILL_ACTIVATED,
    MEMORY_STORED,
    MEMORY_RETRIEVED,
    CONFIG_LOADED,
    ERROR_OCCURRED
  }

  # Details
  component: String (max 100 chars)
  level: Enum { DEBUG, INFO, WARN, ERROR }
  message: String (max 5000 chars)
  metadata: JSON?
}
```

**Validation Rules:**
- `timestamp` must be valid ISO 8601
- `event_type` must be in enum
- `level` must be in enum
- `metadata` must be valid JSON if present

---

## Data Ownership

### Ownership Model

| Entity | Owner | Lifecycle |
|--------|-------|-----------|
| **Learning** | User (global) | Persistent, expires or pruned |
| **Session** | Project + User | Ephemeral (logs only) |
| **Handoff** | User (global) or Project | Persistent until deleted |
| **UserConfig** | User or Project | Persistent until modified |
| **ActivationRule** | User or Project | Persistent until modified |
| **ArtifactReference** | Handoff owner | Tied to handoff lifecycle |
| **SessionLog** | User (debugging) | Auto-pruned after 30 days |

### Scope Boundaries

```
GLOBAL SCOPE (~/.ring/)
├─ Learning (cross-project)
├─ UserConfig (user preferences)
├─ ActivationRule (global skill patterns)
├─ Handoff (cross-project handoffs)
└─ SessionLog (debugging)

PROJECT SCOPE (.ring/)
├─ UserConfig (project overrides)
├─ ActivationRule (project-specific patterns)
├─ Handoff (project-specific handoffs)
└─ Session state (ephemeral)
```

**Merge Strategy:**
- Config: Project overrides Global
- Rules: Project extends Global (both active)
- Handoffs: Both searched (project first)
- Learning: Global only (shared across projects)

---

## Access Patterns

### Pattern 1: Session Start - Memory Injection

```
Query:
  SELECT content, type, confidence, relevance_score
  FROM Learning
  WHERE deleted_at IS NULL
    AND (expires_at IS NULL OR expires_at > NOW())
    AND project_context_match(tags, context, $PROJECT_PATH)
  ORDER BY relevance_score DESC
  LIMIT 10

Update:
  UPDATE Learning
  SET accessed_at = NOW(),
      access_count = access_count + 1
  WHERE id IN (returned_ids)
```

**Performance:** <200ms for 10K memories

---

### Pattern 2: User Prompt - Skill Activation

```
Query:
  FOR EACH ActivationRule WHERE enabled = true:
    IF prompt CONTAINS ANY(keywords)
       OR prompt MATCHES ANY(intent_patterns):
      IF prompt NOT MATCHES ANY(negative_patterns):
        YIELD rule

Sort:
  ORDER BY priority DESC, match_confidence DESC

Filter:
  LIMIT 5  # Top 5 suggestions max
```

**Performance:** <100ms for 100 rules

---

### Pattern 3: Handoff Creation - Store and Index

```
Insert:
  1. Validate handoff data against schema
  2. Serialize to YAML
  3. Write to file: ~/.ring/handoffs/{session}/{timestamp}.yaml
  4. INSERT INTO Handoff (metadata)
  5. Trigger FTS index update

Index:
  Extract searchable text:
    - task_summary (weight: 10)
    - decisions content (weight: 5)
    - learnings content (weight: 3)
    - next_steps (weight: 1)

  INSERT INTO handoffs_fts (searchable_text)
```

**Performance:** <500ms including file write and index

---

### Pattern 4: Handoff Resume - Search and Load

```
Query:
  SELECT *
  FROM Handoff
  WHERE session_id = $SESSION_NAME
    OR file_path LIKE '%/$SESSION_NAME/%'
  ORDER BY created_at DESC
  LIMIT 1

Load:
  1. Read file from file_path
  2. Deserialize YAML or Markdown
  3. Load referenced artifacts
  4. Return structured handoff data

Update:
  UPDATE Session
  SET mode = 'RESUME',
      previous_session_id = $LOADED_HANDOFF_SESSION_ID
  WHERE id = $CURRENT_SESSION_ID
```

**Performance:** <1s including file reads

---

### Pattern 5: Memory Decay - Relevance Update

```
Update:
  UPDATE Learning
  SET relevance_score = calculate_decay(
        age_days = (NOW() - created_at) / 86400,
        access_count = access_count,
        confidence = confidence
      )
  WHERE deleted_at IS NULL

Delete:
  UPDATE Learning
  SET deleted_at = NOW()
  WHERE relevance_score < 0.1
     OR (expires_at IS NOT NULL AND expires_at < NOW())
```

**Decay Function:**
```
relevance = base_score × age_factor × access_factor

age_factor = exp(-age_days / 180)        # Half-life: 180 days
access_factor = min(access_count / 10, 1.0)  # Saturates at 10 accesses
base_score = confidence_to_score(confidence)  # HIGH=1.0, MEDIUM=0.7, LOW=0.4
```

**Performance:** Batch operation, run offline or during idle

---

## Data Migration Strategy

### Migration 1: Markdown to YAML Handoffs

**Source:** `docs/handoffs/**/*.md` (Markdown format)

**Destination:** `~/.ring/handoffs/**/*.yaml` (YAML format)

**Process:**
```
FOR EACH markdown_handoff:
  1. Parse Markdown frontmatter
  2. Extract structured sections:
     - Task Summary → task_summary
     - Key Decisions → decisions[]
     - Files Modified → artifacts.modified
     - Next Steps → resume.next_steps
  3. Validate against Handoff schema
  4. Serialize to YAML
  5. Write to ~/.ring/handoffs/
  6. Preserve original in docs/handoffs/
  7. Create backward reference link
```

**Data Mapping:**

| Markdown Section | YAML Field |
|------------------|------------|
| YAML frontmatter `status` | `task.status` |
| YAML frontmatter `outcome` | `outcome` |
| ## Task Summary | `task_summary` |
| ## Key Decisions | `decisions[]` |
| ## Files Modified | `artifacts.modified[]` |
| ## Action Items & Next Steps | `resume.next_steps[]` |
| ## Learnings → What Worked | `learnings[]` type=WORKING_SOLUTION |
| ## Learnings → What Failed | `learnings[]` type=FAILED_APPROACH |

**Validation:**
- Ensure all required fields present
- Convert timestamps to ISO 8601
- Limit arrays to schema maximums
- Estimate token count from byte size

---

### Migration 2: Project .ring/ to ~/.ring/

**Source:** `$PROJECT/.ring/` (project-local)

**Destination:** `~/.ring/` (global)

**What to Migrate:**

| Data Type | Migrate? | Reason |
|-----------|----------|--------|
| Handoffs | Yes | Cross-session continuity |
| Ledgers | No | Project-specific, keep local |
| State files | No | Ephemeral, discard |
| Artifact index | Merge | Combine into global index |

**Process:**
```
FOR EACH project with .ring/:
  1. Scan .ring/handoffs/ for handoff files
  2. Migrate handoffs to ~/.ring/handoffs/{project-name}/
  3. Update handoff.project_path to reference original project
  4. Add project tag to migrated handoffs
  5. Reindex in global FTS5
```

---

### Migration 3: Existing Skills to Activation Rules

**Source:** Skill YAML frontmatter `trigger` and `skip_when` fields

**Destination:** `~/.ring/skill-rules.json`

**Process:**
```
FOR EACH skill in Ring:
  1. Parse SKILL.md YAML frontmatter
  2. Extract trigger conditions → keywords + intent_patterns
  3. Extract skip_when conditions → negative_patterns
  4. Infer enforcement level:
     - Workflow skills → SUGGEST
     - Guardrail skills → BLOCK
     - Other → WARN
  5. Infer priority from skill category
  6. Generate ActivationRule entry
  7. Add to skill-rules.json
```

**Data Mapping:**

| Skill Frontmatter | ActivationRule Field |
|-------------------|---------------------|
| `trigger` lines | Extract keywords and patterns |
| `skip_when` lines | `negative_patterns[]` |
| Skill category | `type` (workflow/guardrail/domain) |
| Skill importance | `priority` (critical/high/medium/low) |

---

## Denormalized Indexes

### Index 1: Full-Text Search (Memories)

**Purpose:** Fast text search across learning content.

**Structure:**
```
memories_fts {
  rowid: Integer → Learning.id
  content: Text (from Learning.content)
  context: Text (from Learning.context)
  tags: Text (space-separated from Learning.tags)
}
```

**Tokenization:** Porter stemming + Unicode normalization

**Ranking:** BM25 with weights `(content: 1.0, context: 0.5, tags: 2.0)`

**Synchronization:** Automatic triggers on INSERT/UPDATE/DELETE

---

### Index 2: Full-Text Search (Handoffs)

**Purpose:** Search past handoffs for relevant context.

**Structure:**
```
handoffs_fts {
  rowid: Integer → Handoff.id
  task_summary: Text (from Handoff.task_summary)
  decisions: Text (extracted from file content)
  learnings: Text (extracted from file content)
  next_steps: Text (extracted from file content)
}
```

**Tokenization:** Porter stemming + Unicode normalization

**Ranking:** BM25 with weights `(task_summary: 10, decisions: 5, learnings: 3, next_steps: 1)`

**Synchronization:** Triggered on PostToolUse hook after Write

---

### Index 3: Skill Activation Lookup

**Purpose:** Fast lookup of skills by keyword.

**Structure:**
```
activation_index {
  keyword: String → [ActivationRule.skill]
}
```

**Example:**
```
{
  "tdd": ["ring:test-driven-development"],
  "review": ["ring:requesting-code-review", "ring:receiving-code-review"],
  "debug": ["ring:systematic-debugging", "ring:root-cause-tracing"]
}
```

**Synchronization:** Rebuilt when skill-rules.json changes

---

## Data Retention Policies

### Policy 1: Learning Retention

| Condition | Action | Reason |
|-----------|--------|--------|
| `access_count = 0` AND `age > 180 days` | Soft delete | Unused for 6 months |
| `expires_at < NOW()` | Soft delete | Explicit expiration |
| `relevance_score < 0.1` | Soft delete | Decayed below threshold |
| `deleted_at < NOW() - 30 days` | Hard delete | Soft delete grace period expired |

### Policy 2: Handoff Retention

| Condition | Action | Reason |
|-----------|--------|--------|
| `created_at < NOW() - 1 year` AND `outcome = FAILED` | Archive | Old failed attempts |
| `created_at < NOW() - 2 years` | Archive | Very old handoffs |
| User-triggered | Delete | Manual cleanup |

**Archive:** Move to `~/.ring/archive/` (still searchable, not in default results)

### Policy 3: Session Log Retention

| Condition | Action |
|-----------|--------|
| `timestamp < NOW() - 30 days` | Delete |
| `level = DEBUG` AND `timestamp < NOW() - 7 days` | Delete |

---

## Data Consistency Rules

### Consistency 1: Handoff ↔ File

**Rule:** Handoff entity `file_path` must point to existing file.

**Enforcement:**
- On handoff creation: Write file first, then create entity
- On handoff read: If file missing, mark handoff as `file_missing`
- On cleanup: Delete entity if file permanently missing

---

### Consistency 2: Session ↔ Learning

**Rule:** Learnings reference valid sessions.

**Enforcement:**
- On learning creation: Validate session_id exists or is null
- On session deletion: Keep learnings (orphan relationship OK)
- Learnings can exist without sessions (imported, migrated)

---

### Consistency 3: Config Precedence

**Rule:** Project config overrides global config for same key.

**Enforcement:**
- On config read: Merge in precedence order
- Never delete higher-precedence on lower update
- Return source attribution with value

---

### Consistency 4: FTS Index Sync

**Rule:** FTS index reflects current entity state.

**Enforcement:**
- Triggers: Automatic sync on entity changes
- Manual: Rebuild index command available
- Validation: Check rowid exists in main table

---

## Gate 5 Validation Checklist

- [x] All entities defined with relationships (7 entities)
- [x] Data ownership is clear (User/Session/Artifact domains)
- [x] Access patterns documented (5 primary patterns)
- [x] Database-agnostic (no SQLite/PostgreSQL specifics)
- [x] Entity schemas include validation rules
- [x] Indexes designed for performance
- [x] Migration strategy for 3 data sources
- [x] Retention policies defined
- [x] Consistency rules enforced

---

## Appendix: Entity Catalog

| Entity | Domain | Key Attributes | Relationships |
|--------|--------|----------------|---------------|
| Learning | User | content, type, confidence | Session (M:1) |
| Session | Session | project_path, started_at | Learning (1:N), SessionLog (1:N) |
| Handoff | Artifact | task_summary, status, file_path | Session (M:1), ArtifactReference (1:N) |
| UserConfig | User | scope, key, value | None |
| ActivationRule | User | skill, enforcement, triggers | None |
| ArtifactReference | Artifact | artifact_type, artifact_path | Handoff (M:1) |
| SessionLog | Session | event_type, message | Session (M:1) |
