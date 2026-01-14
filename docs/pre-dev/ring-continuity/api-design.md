# Ring Continuity - API Design (Gate 4)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** TRD v1.0 (docs/pre-dev/ring-continuity/trd.md)

---

## Executive Summary

This document defines **protocol-agnostic contracts** for the 6 components in Ring Continuity. All interfaces use **data transfer objects (DTOs)** with explicit schemas, **result types** for error handling, and **command/query separation** for clarity.

**Design Principles:**
- **Contract-first:** Interfaces defined before implementation
- **Protocol-agnostic:** No HTTP/gRPC/function call specifics
- **Fail-safe:** Every operation returns success/failure status
- **Immutable data:** DTOs are read-only after creation

---

## Component Contracts

### 1. Ring Home Directory Manager

**Interface Name:** `RingHomeManager`

**Operations:**

#### Operation: Initialize

```
initialize(force_recreate: boolean) -> Result<RingHome, InitError>

Input:
  force_recreate: boolean  # If true, recreate directory structure

Output (Success):
  RingHome {
    path: FilePath            # Absolute path to ~/.ring/
    config_path: FilePath     # Path to config.yaml
    memory_path: FilePath     # Path to memory.db
    handoffs_path: FilePath   # Path to handoffs/
    created: boolean          # True if newly created
  }

Output (Error):
  InitError {
    code: enum [PERMISSION_DENIED, PATH_EXISTS, DISK_FULL]
    message: string
    fallback_path: FilePath?  # Suggested fallback if available
  }

Pre-conditions:
  - User has write access to home directory

Post-conditions:
  - ~/.ring/ exists with standard subdirectories
  - OR fallback path identified and returned
```

#### Operation: Get Config

```
get_config(scope: ConfigScope, key: string) -> Result<ConfigValue, ConfigError>

Input:
  scope: enum [GLOBAL, PROJECT, MERGED]  # Which config to query
  key: string                            # Config key (dot notation: "skill.activation.enabled")

Output (Success):
  ConfigValue {
    value: any          # The configuration value
    source: enum [GLOBAL, PROJECT, DEFAULT]
    precedence: int     # 0=default, 1=global, 2=project
  }

Output (Error):
  ConfigError {
    code: enum [KEY_NOT_FOUND, INVALID_SCOPE, PARSE_ERROR]
    message: string
    default_value: any?
  }

Pre-conditions:
  - Config file exists OR defaults available

Post-conditions:
  - Returns value with source attribution
```

#### Operation: Migrate Legacy Data

```
migrate_legacy_data(source_path: FilePath, data_type: DataType) -> Result<MigrationResult, MigrationError>

Input:
  source_path: FilePath  # Path to legacy data location
  data_type: enum [HANDOFFS, LEDGERS, STATE]

Output (Success):
  MigrationResult {
    source: FilePath
    destination: FilePath
    items_migrated: int
    items_skipped: int
    warnings: [string]
  }

Output (Error):
  MigrationError {
    code: enum [SOURCE_NOT_FOUND, PERMISSION_DENIED, VALIDATION_FAILED]
    message: string
    partially_migrated: int
  }

Pre-conditions:
  - source_path exists and is readable
  - Destination has write access

Post-conditions:
  - Source files preserved (read-only)
  - Migrated files in destination
```

---

### 2. Memory Repository

**Interface Name:** `MemoryRepository`

**Operations:**

#### Operation: Store Learning

```
store_learning(learning: LearningInput) -> Result<LearningId, StoreError>

Input:
  LearningInput {
    content: string              # The learning text
    type: LearningType           # enum [FAILED_APPROACH, WORKING_SOLUTION, ...]
    tags: [string]               # Optional tags
    confidence: ConfidenceLevel  # enum [HIGH, MEDIUM, LOW]
    context: string?             # Optional context
    session_id: string?          # Optional session association
    expires_at: Timestamp?       # Optional expiration
  }

Output (Success):
  LearningId {
    id: string        # Unique identifier
    stored_at: Timestamp
  }

Output (Error):
  StoreError {
    code: enum [DUPLICATE_DETECTED, VALIDATION_FAILED, DB_LOCKED, DISK_FULL]
    message: string
    duplicate_id: string?  # If DUPLICATE_DETECTED
  }

Pre-conditions:
  - type is valid LearningType
  - content is non-empty

Post-conditions:
  - Learning persisted with timestamps
  - Content sanitized of secrets (API keys, tokens)
  - Full-text index updated
```

#### Operation: Search Memories

```
search_memories(query: SearchQuery) -> Result<SearchResults, SearchError>

Input:
  SearchQuery {
    text: string                 # Search query
    filters: SearchFilters?      # Optional filters
    limit: int                   # Max results (default: 10)
    include_expired: boolean     # Include expired memories
  }

  SearchFilters {
    types: [LearningType]?       # Filter by learning type
    tags: [string]?              # Filter by tags
    confidence: ConfidenceLevel? # Minimum confidence
    date_range: DateRange?       # Created within range
    session_id: string?          # From specific session
  }

Output (Success):
  SearchResults {
    results: [SearchResult]
    total_count: int       # Total matches (before limit)
    query_time_ms: int     # Performance metric
  }

  SearchResult {
    learning: Learning
    relevance_score: float  # 0.0 to 1.0
    highlights: [string]    # Matched snippets
  }

Output (Error):
  SearchError {
    code: enum [QUERY_INVALID, DB_UNAVAILABLE, TIMEOUT]
    message: string
    fallback_available: boolean
  }

Pre-conditions:
  - text is non-empty
  - limit > 0 and <= 100

Post-conditions:
  - Results sorted by relevance (desc)
  - Access times updated for returned memories
```

#### Operation: Apply Decay (Async)

```
apply_decay(strategy: DecayStrategy) -> Result<DecayResult, DecayError>

Input:
  DecayStrategy {
    age_weight: float        # Weight for time since creation (0.0-1.0)
    access_weight: float     # Weight for access frequency (0.0-1.0)
    min_score: float         # Minimum score to keep (0.0-1.0)
  }

Output (Success):
  DecayResult {
    memories_decayed: int
    memories_pruned: int     # Fell below min_score
    average_age_days: float
  }

Output (Error):
  DecayError {
    code: enum [INVALID_STRATEGY, DB_LOCKED]
    message: string
  }

Pre-conditions:
  - age_weight + access_weight <= 1.0

Post-conditions:
  - Memory scores updated
  - Low-score memories deleted or marked
```

---

### 3. Handoff Serializer

**Interface Name:** `HandoffSerializer`

**Operations:**

#### Operation: Serialize

```
serialize(handoff: HandoffData, format: HandoffFormat) -> Result<SerializedHandoff, SerializeError>

Input:
  HandoffData {
    session: SessionMetadata
    task: TaskInfo
    decisions: [Decision]
    artifacts: ArtifactReferences
    resume: ResumeInstructions
  }

  format: enum [YAML, MARKDOWN]

Output (Success):
  SerializedHandoff {
    content: string      # Serialized content
    format: HandoffFormat
    byte_size: int
    token_estimate: int  # Estimated tokens
  }

Output (Error):
  SerializeError {
    code: enum [VALIDATION_FAILED, SERIALIZATION_ERROR]
    message: string
    validation_errors: [ValidationError]?
  }

Pre-conditions:
  - handoff passes schema validation

Post-conditions:
  - Content is valid YAML or Markdown
  - Deserializing content returns equivalent data
```

#### Operation: Deserialize

```
deserialize(content: string, format: HandoffFormat?) -> Result<HandoffData, DeserializeError>

Input:
  content: string          # Serialized handoff content
  format: HandoffFormat?   # If null, auto-detect

Output (Success):
  HandoffData {
    session: SessionMetadata
    task: TaskInfo
    decisions: [Decision]
    artifacts: ArtifactReferences
    resume: ResumeInstructions
    source_format: HandoffFormat  # Detected or specified
  }

Output (Error):
  DeserializeError {
    code: enum [PARSE_ERROR, UNKNOWN_FORMAT, SCHEMA_MISMATCH]
    message: string
    line_number: int?     # If parse error
  }

Pre-conditions:
  - content is non-empty

Post-conditions:
  - Returns structured handoff data
  - source_format indicates actual format used
```

#### Operation: Validate Schema

```
validate_schema(handoff: HandoffData) -> Result<ValidationSuccess, ValidationErrors>

Input:
  HandoffData (see above)

Output (Success):
  ValidationSuccess {
    valid: true
    warnings: [string]  # Non-blocking warnings
  }

Output (Error):
  ValidationErrors {
    valid: false
    errors: [ValidationError]
  }

  ValidationError {
    field: string       # JSON path to field
    constraint: string  # Which constraint failed
    message: string
  }

Pre-conditions:
  - handoff object exists

Post-conditions:
  - All required fields checked
  - Type constraints validated
  - Returns detailed error locations
```

#### Operation: Migrate

```
migrate(source_path: FilePath) -> Result<MigrationResult, MigrationError>

Input:
  source_path: FilePath  # Path to Markdown handoff

Output (Success):
  MigrationResult {
    source: FilePath
    destination: FilePath
    format_from: MARKDOWN
    format_to: YAML
    preserved_original: boolean
  }

Output (Error):
  MigrationError {
    code: enum [SOURCE_INVALID, CONVERSION_FAILED, WRITE_FAILED]
    message: string
    partial_result: HandoffData?
  }

Pre-conditions:
  - source_path exists and is valid Markdown handoff

Post-conditions:
  - Original file unchanged
  - YAML copy created (if successful)
```

---

### 4. Skill Activator

**Interface Name:** `SkillActivator`

**Operations:**

#### Operation: Load Rules

```
load_rules(paths: [FilePath]) -> Result<ActivationRules, LoadError>

Input:
  paths: [FilePath]  # Ordered by precedence (project, then global)

Output (Success):
  ActivationRules {
    skills: {skill_name: SkillRule}
    agents: {agent_name: SkillRule}
    version: string
    source_paths: [FilePath]
  }

  SkillRule {
    skill: string               # ring:skill-name
    type: RuleType              # enum [GUARDRAIL, DOMAIN, WORKFLOW]
    enforcement: Enforcement    # enum [BLOCK, SUGGEST, WARN]
    priority: Priority          # enum [CRITICAL, HIGH, MEDIUM, LOW]
    triggers: TriggerConfig
  }

Output (Error):
  LoadError {
    code: enum [FILE_NOT_FOUND, PARSE_ERROR, SCHEMA_INVALID]
    message: string
    file_path: FilePath
  }

Pre-conditions:
  - At least one path exists

Post-conditions:
  - Rules merged with project overriding global
  - All rules validated against schema
```

#### Operation: Match Skills

```
match_skills(prompt: string, rules: ActivationRules) -> Result<SkillMatches, MatchError>

Input:
  prompt: string            # User's prompt text
  rules: ActivationRules    # Loaded activation rules

Output (Success):
  SkillMatches {
    matches: [SkillMatch]
    total_checked: int
    match_time_ms: int
  }

  SkillMatch {
    skill: string           # ring:skill-name
    enforcement: Enforcement
    priority: Priority
    match_reason: MatchReason
    confidence: float       # 0.0 to 1.0
  }

  MatchReason {
    matched_keywords: [string]
    matched_patterns: [string]
    excluded_by: [string]?   # Negative patterns that didn't match
  }

Output (Error):
  MatchError {
    code: enum [INVALID_PROMPT, RULES_NOT_LOADED]
    message: string
  }

Pre-conditions:
  - prompt is non-empty
  - rules loaded and validated

Post-conditions:
  - Matches sorted by priority then confidence
  - No duplicate skill recommendations
```

#### Operation: Apply Enforcement

```
apply_enforcement(matches: [SkillMatch]) -> EnforcementAction

Input:
  matches: [SkillMatch]  # From match_skills()

Output:
  EnforcementAction {
    action: enum [BLOCK, SUGGEST, WARN, CONTINUE]
    skills: [string]         # Skill names to present
    message: string          # User-facing message
    blocking_skills: [string]?  # If action=BLOCK
  }

Pre-conditions:
  - matches is non-empty

Post-conditions:
  - BLOCK if any match has enforcement=BLOCK
  - SUGGEST if highest priority is SUGGEST
  - WARN if only WARN matches
  - CONTINUE if no matches
```

---

### 5. Confidence Marker

**Interface Name:** `ConfidenceMarker`

**Operations:**

#### Operation: Mark Finding

```
mark_finding(finding: Finding, evidence: [Evidence]) -> MarkedFinding

Input:
  Finding {
    claim: string
    location: CodeLocation?
    importance: enum [CRITICAL, IMPORTANT, MINOR]
  }

  Evidence {
    type: EvidenceType    # enum [FILE_READ, GREP_MATCH, AST_PARSE, ASSUMPTION, TRACE]
    description: string
    source: FilePath?     # If file-based evidence
    line_range: Range?    # If specific lines
  }

Output:
  MarkedFinding {
    finding: Finding
    confidence: Confidence
    marker: string        # Symbol: ✓, ?, ✗
    evidence_chain: [Evidence]
    requires_review: boolean
  }

  Confidence {
    level: enum [VERIFIED, INFERRED, UNCERTAIN]
    score: float          # 0.0 to 1.0
    reasoning: string
  }

Pre-conditions:
  - finding.claim is non-empty
  - evidence is non-empty array

Post-conditions:
  - Marker matches confidence level
  - Evidence chain is ordered by strength
```

#### Operation: Infer Confidence

```
infer_confidence(evidence: [Evidence]) -> Confidence

Input:
  evidence: [Evidence]  # Evidence supporting a claim

Output:
  Confidence {
    level: enum [VERIFIED, INFERRED, UNCERTAIN]
    score: float          # 0.0 to 1.0
    reasoning: string
  }

Algorithm:
  IF any(evidence.type == FILE_READ) AND any(evidence.type == TRACE):
    level = VERIFIED, score = 0.9

  ELSE IF any(evidence.type == FILE_READ):
    level = VERIFIED, score = 0.8

  ELSE IF all(evidence.type == GREP_MATCH):
    level = INFERRED, score = 0.5

  ELSE IF any(evidence.type == ASSUMPTION):
    level = UNCERTAIN, score = 0.2

  ELSE:
    level = UNCERTAIN, score = 0.3

Pre-conditions:
  - evidence is non-empty

Post-conditions:
  - Score matches level consistently
```

#### Operation: Format Output

```
format_output(findings: [MarkedFinding]) -> FormattedOutput

Input:
  findings: [MarkedFinding]

Output:
  FormattedOutput {
    sections: [OutputSection]
    total_findings: int
    verified_count: int
    inferred_count: int
    uncertain_count: int
  }

  OutputSection {
    title: string
    findings: [MarkedFinding]
    confidence_summary: string
  }

Pre-conditions:
  - findings is non-empty

Post-conditions:
  - Findings grouped by confidence level
  - Summary statistics accurate
```

---

### 6. Hook Orchestrator

**Interface Name:** `HookOrchestrator`

**Operations:**

#### Operation: On Session Start

```
on_session_start(context: SessionContext) -> Result<HookResponse, HookError>

Input:
  SessionContext {
    session_id: string
    mode: enum [STARTUP, RESUME, CLEAR, COMPACT]
    project_path: FilePath
    previous_session_id: string?
  }

Output (Success):
  HookResponse {
    additional_context: string   # Content to inject
    metadata: {
      memories_loaded: int
      config_source: string
      ledger_loaded: boolean
    }
  }

Output (Error):
  HookError {
    code: enum [TIMEOUT, EXECUTION_FAILED, INVALID_JSON]
    message: string
    partial_context: string?
  }

Behavior:
  1. Load configuration (global + project)
  2. Search memories relevant to project
  3. Load active continuity ledger
  4. Compile context string
  5. Return as JSON

Pre-conditions:
  - session_id is valid
  - project_path exists

Post-conditions:
  - Context injected into session
  - Memories marked as accessed
```

#### Operation: On User Prompt Submit

```
on_user_prompt_submit(prompt: UserPrompt) -> Result<HookResponse, HookError>

Input:
  UserPrompt {
    text: string
    session_id: string
    turn_number: int
  }

Output (Success):
  HookResponse {
    action: enum [BLOCK, SUGGEST, CONTINUE]
    suggestions: [SkillSuggestion]?
    blocking_reason: string?
    additional_context: string?
  }

  SkillSuggestion {
    skill: string
    reason: string
    confidence: float
  }

Output (Error):
  HookError {
    code: enum [TIMEOUT, ACTIVATION_FAILED]
    message: string
  }

Behavior:
  1. Match prompt against skill rules
  2. Rank matches by priority
  3. Apply enforcement levels
  4. Return suggestions or block

Pre-conditions:
  - prompt.text is non-empty

Post-conditions:
  - If BLOCK, must include blocking_reason
  - If SUGGEST, includes skill suggestions
```

#### Operation: On Post Write

```
on_post_write(file_info: FileInfo) -> Result<HookResponse, HookError>

Input:
  FileInfo {
    path: FilePath
    content_preview: string  # First 500 chars
    file_type: FileType      # Inferred from extension/content
    session_id: string
  }

Output (Success):
  HookResponse {
    indexed: boolean
    artifact_type: ArtifactType?  # If indexed
    metadata: {
      index_time_ms: int
    }
  }

Output (Error):
  HookError {
    code: enum [INDEX_FAILED, FILE_UNREADABLE]
    message: string
  }

Behavior:
  1. Detect if file is handoff/plan/ledger
  2. If artifact, index in FTS5
  3. Extract metadata for search
  4. Return index result

Pre-conditions:
  - file_info.path exists and is readable

Post-conditions:
  - Artifact indexed if applicable
  - Index updated atomically
```

---

## Data Transfer Objects (DTOs)

### Core Types

```
# Learning Types
enum LearningType {
  FAILED_APPROACH
  WORKING_SOLUTION
  USER_PREFERENCE
  CODEBASE_PATTERN
  ARCHITECTURAL_DECISION
  ERROR_FIX
  OPEN_THREAD
}

# Confidence Levels
enum ConfidenceLevel {
  HIGH      # Empirically verified
  MEDIUM    # Logically sound but not tested
  LOW       # Assumption or inference
}

# Verification Status
enum VerificationStatus {
  VERIFIED    # ✓ - Read files, traced code
  INFERRED    # ? - Based on grep/search
  UNCERTAIN   # ✗ - Not checked
}

# Enforcement Levels
enum Enforcement {
  BLOCK     # Must use skill
  SUGGEST   # Recommend skill
  WARN      # Log availability
}

# Priority Levels
enum Priority {
  CRITICAL  # Always trigger
  HIGH      # Trigger for most matches
  MEDIUM    # Trigger for clear matches
  LOW       # Trigger only explicit
}
```

### Handoff Schema

```
HandoffData {
  # Required fields
  session: SessionMetadata {
    id: string
    started_at: Timestamp
    ended_at: Timestamp?
    duration_seconds: int?
  }

  task: TaskInfo {
    description: string
    status: enum [COMPLETED, PAUSED, BLOCKED, FAILED]
    skills_used: [string]
  }

  context: ContextInfo {
    project_path: FilePath
    git_commit: string
    git_branch: string
    key_files: [FilePath]  # Max 10 most relevant
  }

  # Optional fields
  decisions: [Decision] {
    decision: string
    rationale: string
    alternatives: [string]
  }

  artifacts: ArtifactReferences {
    created: [FilePath]
    modified: [FilePath]
    deleted: [FilePath]
  }

  learnings: [Learning] {
    type: LearningType
    content: string
    confidence: VerificationStatus
  }

  blockers: [Blocker] {
    type: enum [TECHNICAL, CLARIFICATION, EXTERNAL]
    description: string
    severity: enum [CRITICAL, HIGH, MEDIUM]
  }

  resume: ResumeInstructions {
    next_steps: [string]
    context_needed: [string]
    warnings: [string]
  }
}
```

### Memory Schema

```
Learning {
  id: string              # Unique identifier
  session_id: string      # Source session
  created_at: Timestamp
  accessed_at: Timestamp
  access_count: int

  content: string         # The learning text
  type: LearningType
  tags: [string]
  confidence: ConfidenceLevel

  context: string?        # Optional context
  expires_at: Timestamp?  # Optional expiration

  metadata: {
    source: string        # Where learning came from
    relevance_score: float # Current relevance (decays)
  }
}
```

### Skill Rule Schema

```
SkillRule {
  skill: string          # ring:skill-name
  type: RuleType
  enforcement: Enforcement
  priority: Priority
  description: string

  triggers: TriggerConfig {
    keywords: [string]           # Exact matches
    intent_patterns: [string]    # Regex patterns
    negative_patterns: [string]? # Exclusions
  }
}
```

---

## Error Handling Specification

### Result Type Pattern

All operations return `Result<Success, Error>` type:

```
Result<T, E> =
  | Ok(value: T)
  | Err(error: E)

Usage:
  result = operation()
  match result:
    case Ok(value):
      # Handle success
    case Err(error):
      # Handle error
```

### Error Codes Catalog

| Code | Component | Meaning | Recovery |
|------|-----------|---------|----------|
| `PERMISSION_DENIED` | RingHomeManager | No write access | Use fallback path |
| `DB_LOCKED` | MemoryRepository | Concurrent access | Retry with backoff |
| `VALIDATION_FAILED` | HandoffSerializer | Schema violation | Return detailed errors |
| `QUERY_INVALID` | MemoryRepository | Malformed query | Sanitize and retry |
| `TIMEOUT` | HookOrchestrator | Hook exceeded limit | Return partial result |
| `DUPLICATE_DETECTED` | MemoryRepository | Similar learning exists | Return existing ID |
| `PARSE_ERROR` | HandoffSerializer | Invalid YAML/Markdown | Try alternate format |

### Error Response Format

```
ErrorResponse {
  code: ErrorCode
  message: string          # Human-readable description
  context: {
    component: string
    operation: string
    timestamp: Timestamp
  }
  recovery: RecoveryInfo? {
    suggested_action: string
    fallback_available: boolean
    retry_recommended: boolean
  }
  details: any?           # Operation-specific error details
}
```

---

## Integration Specifications

### Integration 1: Hook → Memory Repository

**Protocol:** Function call (in-process)

**Flow:**
```
SessionStart Hook
     │
     ▼
MemoryRepository.search_memories(query=project_context)
     │
     ▼
Return [SearchResult]
     │
     ▼
Format as context string
     │
     ▼
Include in hook JSON response
```

**Contract:**
- Hook calls repository synchronously
- Timeout: 2 seconds max for search
- If timeout: Return empty results, don't block session

---

### Integration 2: Hook → Skill Activator

**Protocol:** Function call (in-process)

**Flow:**
```
UserPromptSubmit Hook
     │
     ▼
SkillActivator.load_rules()
     │
     ▼
SkillActivator.match_skills(prompt)
     │
     ▼
SkillActivator.apply_enforcement(matches)
     │
     ▼
Return EnforcementAction in hook JSON
```

**Contract:**
- Hook calls activator synchronously
- Timeout: 1 second max for matching
- If timeout: Return CONTINUE (no blocking)

---

### Integration 3: Skill → Handoff Serializer

**Protocol:** Command invocation

**Flow:**
```
User invokes: /ring:create-handoff
     │
     ▼
Skill gathers handoff data
     │
     ▼
HandoffSerializer.validate_schema(data)
     │
     ▼
HandoffSerializer.serialize(data, format=YAML)
     │
     ▼
Write to ~/.ring/handoffs/{session}/{timestamp}.yaml
     │
     ▼
Trigger PostToolUse hook for indexing
```

**Contract:**
- Skill calls serializer via Python script
- Validation before write (fail fast)
- Returns file path on success

---

### Integration 4: Agent → Confidence Marker

**Protocol:** Template injection

**Flow:**
```
Agent Output Template
     │
     ▼
For each finding:
  ├─> Classify evidence type
  ├─> ConfidenceMarker.infer_confidence(evidence)
  ├─> ConfidenceMarker.mark_finding(finding, evidence)
  └─> Include in output section
     │
     ▼
Formatted output with markers
```

**Contract:**
- Agent includes "Verification" section in output
- Each finding has confidence marker
- Evidence chain documented

---

### Integration 5: PostToolUse Hook → Indexing

**Protocol:** Event trigger

**Flow:**
```
User writes file via Write tool
     │
     ▼
Claude Code triggers PostToolUse hook
     │
     ▼
Hook checks file type (handoff/plan/ledger?)
     │
     ├─> YES: Call indexer
     │         └─> Update FTS5 index
     │
     └─> NO: Skip indexing
```

**Contract:**
- Hook runs after Write completes
- Indexing is best-effort (non-blocking)
- Failures logged but don't interrupt session

---

## Request/Response Formats

### Hook Input Format (stdin JSON)

```json
{
  "event": "SessionStart|UserPromptSubmit|PostToolUse|PreCompact|Stop",
  "session_id": "unique-id",
  "timestamp": "2026-01-12T10:30:00Z",
  "data": {
    // Event-specific data
  }
}
```

### Hook Output Format (stdout JSON)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Context string to inject"
  }
}
```

Or for blocking:

```json
{
  "result": "block",
  "reason": "Must use ring:test-driven-development for test tasks"
}
```

Or for continuation:

```json
{
  "result": "continue"
}
```

### Memory Search Request

```json
{
  "query": "typescript async await patterns",
  "filters": {
    "types": ["WORKING_SOLUTION", "CODEBASE_PATTERN"],
    "confidence": "MEDIUM",
    "tags": ["typescript"]
  },
  "limit": 10
}
```

### Memory Search Response

```json
{
  "results": [
    {
      "id": "learning-123",
      "content": "Use async/await instead of .then() for better readability",
      "type": "WORKING_SOLUTION",
      "confidence": "HIGH",
      "relevance_score": 0.85,
      "highlights": ["async/await", "readability"],
      "created_at": "2025-12-15T14:30:00Z",
      "accessed_at": "2026-01-12T10:30:00Z"
    }
  ],
  "total_count": 15,
  "query_time_ms": 45
}
```

### Handoff YAML Format

```yaml
---
# Schema metadata
version: "1.0"
schema: ring-handoff-v1

# Session metadata
session:
  id: context-management-2026-01-12
  started_at: 2026-01-12T09:00:00Z
  ended_at: 2026-01-12T11:30:00Z
  duration_seconds: 9000

# Task information
task:
  description: Implement artifact indexing with FTS5
  status: completed
  skills_used:
    - ring:test-driven-development
    - ring:requesting-code-review

# Context
context:
  project_path: /Users/user/repos/ring
  git_commit: abc123def
  git_branch: feature/artifact-index
  key_files:
    - default/lib/artifact-index/artifact_index.py
    - default/lib/artifact-index/artifact_schema.sql

# Decisions made
decisions:
  - decision: Use FTS5 instead of FTS3
    rationale: FTS5 supports BM25 ranking
    alternatives:
      - FTS3 (lacks ranking)
      - External search engine (too heavy)

# Artifacts
artifacts:
  created:
    - default/lib/artifact-index/artifact_index.py
  modified:
    - default/lib/artifact-index/artifact_schema.sql

# Learnings
learnings:
  - type: WORKING_SOLUTION
    content: FTS5 triggers keep index in sync automatically
    confidence: verified

  - type: FAILED_APPROACH
    content: Tried FTS3, lacks BM25 ranking
    confidence: verified

# Resume instructions
resume:
  next_steps:
    - Add query script for artifact search
    - Test with real handoff documents
  context_needed:
    - Review artifact_schema.sql for table structure
  warnings:
    - FTS5 requires SQLite 3.35+
---

# Session Notes

## Summary
Implemented artifact indexing using SQLite FTS5...

## Open Questions
- Should we support external search engines in future?
```

---

## Gate 4 Validation Checklist

- [x] All component interfaces defined (6 components)
- [x] Contracts are clear and complete (operations, DTOs, errors)
- [x] Error cases covered (error codes catalog, recovery strategies)
- [x] Protocol-agnostic (no REST/gRPC, just data contracts)
- [x] Request/response formats specified
- [x] Integration specifications documented (5 integrations)
- [x] DTOs with explicit schemas
- [x] Pre/post-conditions for operations

---

## Appendix: Interface Catalog

| Interface | Operations | Dependencies |
|-----------|------------|--------------|
| RingHomeManager | initialize, get_config, migrate_legacy_data | File system, Config parser |
| MemoryRepository | store_learning, search_memories, apply_decay | FTS engine, Timestamp provider |
| HandoffSerializer | serialize, deserialize, validate_schema, migrate | YAML parser, Markdown parser, Schema validator |
| SkillActivator | load_rules, match_skills, apply_enforcement | Pattern matcher, Rule validator |
| ConfidenceMarker | mark_finding, infer_confidence, format_output | Evidence classifier |
| HookOrchestrator | on_session_start, on_user_prompt_submit, on_post_write | All above components |
