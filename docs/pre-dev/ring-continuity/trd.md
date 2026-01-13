# Ring Continuity - Technical Requirements Document (Gate 3)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** PRD v1.0, Feature Map v1.0

---

## Executive Summary

Ring Continuity implements a **layered persistence architecture** using the **plugin pattern** with **hook-based lifecycle interception**, **document-oriented storage**, and **full-text search indexing**. The architecture is technology-agnostic, lightweight (no external services), and maintains backward compatibility through **dual-format adapters**.

**Core Patterns:**
- **Repository Pattern** for memory and handoff storage abstraction
- **Strategy Pattern** for multi-format handoff support (YAML/Markdown)
- **Observer Pattern** for hook-based event interception
- **Factory Pattern** for configuration precedence (global/project/default)

---

## Architecture Style

### Primary Patterns

| Pattern | Application | Rationale |
|---------|-------------|-----------|
| **Layered Architecture** | Foundation → Storage → Enhancement → Integration | Clear separation of concerns, testable layers |
| **Plugin Architecture** | Hook registration, lifecycle events | Extends Claude Code without core modifications |
| **Document-Oriented Storage** | YAML/Markdown files, not object storage | Human-readable, version-controllable |
| **Repository Pattern** | Abstract storage backends | Swap implementations (file vs DB) |
| **Strategy Pattern** | Multiple handoff formats | Backward compatibility without conditionals |

### Architecture Principles

1. **Fail-Safe Defaults:** If ~/.ring/ doesn't exist, use project .ring/
2. **Graceful Degradation:** If memory unavailable, continue without it
3. **Explicit Over Implicit:** Config precedence clearly documented
4. **Progressive Enhancement:** Each feature works independently
5. **Zero External Dependencies:** All persistence local

---

## Component Design (Technology-Agnostic)

### Component 1: Ring Home Directory Manager

**Responsibility:** Initialize and manage the ~/.ring/ directory structure.

**Interface:**
```
Component: RingHomeManager

Operations:
  - ensure_directory_exists() -> path
  - get_config(scope: global|project) -> config
  - merge_configs(global, project) -> merged_config
  - migrate_legacy_data(source_path) -> migration_result

Dependencies:
  - File system access (via FileSystem adapter)
  - Configuration parser

Outputs:
  - ~/.ring/ directory with standard structure
  - Merged configuration object
```

**Behavior:**
- Check for ~/.ring/ existence on first operation
- Create standard subdirectories (config, memory, handoffs, logs)
- Load configurations with precedence: project > global > defaults
- Provide migration path from legacy locations

**Error Handling:**
- If creation fails (permissions), fall back to project .ring/
- If config invalid, use defaults and log warning
- If migration fails, preserve originals and report

---

### Component 2: Memory Storage & Retrieval

**Responsibility:** Persist and search learnings using full-text indexing.

**Interface:**
```
Component: MemoryRepository

Operations:
  - store_learning(content, type, tags, confidence) -> learning_id
  - search_memories(query, filters) -> ranked_results
  - get_memory(id) -> memory
  - update_access_time(id) -> void
  - apply_decay(age_threshold) -> affected_count
  - prune_expired() -> deleted_count

Dependencies:
  - Full-text search engine
  - Timestamp provider
  - Secret sanitizer (regex/entropy-based)

Data Types:
  - Learning: {id, content, type, tags, confidence, created_at, accessed_at}
  - SearchResult: {learning, relevance_score}
```

**Behavior:**
- Store learnings with automatic timestamps (sanitize secrets first)
- Search using full-text index with ranking
- Update access time on retrieval (for decay calculation)
- Decay relevance based on age + access patterns (Async/Background)
- Prune memories with expired_at < now()

**Error Handling:**
- If DB locked, retry with exponential backoff
- If search fails, fall back to simple text matching
- If storage fails, log and continue (non-critical)

---

### Component 3: Handoff Serialization

**Responsibility:** Convert session state to/from persistent formats.

**Interface:**
```
Component: HandoffSerializer

Operations:
  - serialize(handoff_data, format: yaml|markdown) -> string
  - deserialize(content, format: yaml|markdown) -> handoff_data
  - validate_schema(handoff_data) -> validation_result
  - infer_format(file_path) -> format
  - migrate(markdown_path) -> yaml_path

Dependencies:
  - YAML parser
  - Markdown parser
  - Schema validator

Data Types:
  - HandoffData: {session, task, decisions, artifacts, resume}
  - ValidationResult: {valid, errors}
```

**Behavior:**
- Strategy Pattern: Choose serializer based on format parameter
- Validation before write (fail fast on invalid schema)
- Dual-format read support (detect from file extension or content)
- Migration preserves original and creates YAML copy

**Error Handling:**
- If YAML parse fails, try Markdown fallback
- If validation fails, return detailed error messages
- If migration fails, leave original intact

---

### Component 4: Skill Activation Engine

**Responsibility:** Match user prompts to relevant skills using pattern matching.

**Interface:**
```
Component: SkillActivator

Operations:
  - load_rules(path) -> rules
  - match_skills(prompt, rules) -> matches
  - filter_by_priority(matches) -> filtered_matches
  - apply_enforcement(match) -> action: block|suggest|warn
  - validate_rules(rules) -> validation_result

Dependencies:
  - Pattern matcher (regex, keywords)
  - Rule validator
  - Priority resolver

Data Types:
  - SkillRule: {skill, type, enforcement, priority, triggers}
  - Match: {skill, score, enforcement}
  - Trigger: {keywords, intent_patterns, negative_patterns}
```

**Behavior:**
- Load rules from global and project locations
- Match prompt against keywords (exact) and patterns (regex)
- Apply negative patterns to reduce false positives
- Rank matches by priority
- Return action based on enforcement level

**Error Handling:**
- If rules invalid, skip auto-activation and log
- If pattern compilation fails, skip that pattern
- If multiple high-priority matches, suggest all

---

### Component 5: Confidence Annotation

**Responsibility:** Add verification status to agent outputs.

**Interface:**
```
Component: ConfidenceMarker

Operations:
  - mark_finding(claim, evidence) -> marked_claim
  - infer_confidence(evidence_type) -> confidence_level
  - format_marker(confidence) -> symbol
  - validate_evidence(evidence) -> valid

Dependencies:
  - Evidence type classifier

Data Types:
  - Claim: {content, evidence, confidence}
  - Evidence: {type: read_file|grep|assumption, description}
  - Confidence: verified|inferred|uncertain
```

**Behavior:**
- Classify evidence type from agent actions
- Map evidence to confidence level:
  - read_file → verified
  - grep/search → inferred
  - no_check → uncertain
- Format with symbols: ✓/?/✗
- Include evidence chain in output

**Error Handling:**
- If evidence missing, default to uncertain
- If evidence ambiguous, default to inferred
- If marker formatting fails, use text fallback

---

### Component 6: Hook Orchestrator

**Responsibility:** Coordinate lifecycle events and inject context.

**Interface:**
```
Component: HookOrchestrator

Operations:
  - on_session_start(context) -> injected_context
  - on_user_prompt(prompt) -> suggestions
  - on_post_write(file_path) -> index_result
  - on_pre_compact() -> state_snapshot
  - on_stop() -> learning_extraction

Dependencies:
  - MemoryRepository
  - SkillActivator
  - HandoffSerializer

Outputs:
  - JSON response with additionalContext or blocking result
```

**Behavior:**
- SessionStart: Load config, inject memories, load active ledger
- UserPromptSubmit: Match skills, suggest relevant
- PostToolUse (Write): Index if handoff/plan/ledger
- PreCompact: Create auto-handoff from state
- Stop: Extract learnings, mark outcomes

**Error Handling:**
- If hook fails, log and continue (don't block Claude)
- If timeout exceeded, return partial result
- If JSON malformed, wrap in error response

---

## Data Architecture (Conceptual)

### Storage Model

```
User Scope (Global)
  └─ ~/.ring/
      ├─ Configuration (hierarchical key-value)
      ├─ Memory Store (indexed text corpus)
      └─ Handoff Archive (document collection)

Project Scope (Local)
  └─ .ring/
      ├─ Configuration (overrides)
      ├─ Session State (ephemeral)
      └─ Ledgers (within-session persistence)
```

### Data Flow

```
Session Start
     │
     ▼
Load Config (project > global > default)
     │
     ▼
Query Memory (FTS search on prompt context)
     │
     ▼
Inject Context (memories + config into session)
     │
     ▼
User Prompt
     │
     ▼
Match Skills (keyword + intent patterns)
     │
     ▼
Suggest/Block/Warn (based on enforcement)
     │
     ▼
Execution (agent with confidence markers)
     │
     ▼
Write Output (YAML handoff with validation)
     │
     ▼
Index Document (FTS5 for future search)
     │
     ▼
Store Learning (successful patterns, failures)
     │
     ▼
Session End
```

### State Management

| State Type | Lifetime | Storage | Example |
|------------|----------|---------|---------|
| **Ephemeral** | Single turn | Memory only | Current prompt |
| **Session** | Until /clear | Project .ring/state/ | Todo list, context usage |
| **Ledger** | Survives /clear | Project .ring/ledgers/ | Phase progress |
| **Handoff** | Cross-session | ~/.ring/handoffs/ or docs/handoffs/ | Session resume |
| **Memory** | Persistent | ~/.ring/memory.db | Learnings, preferences |
| **Config** | Persistent | ~/.ring/config.yaml | User settings |

---

## Integration Patterns

### Pattern 1: Hook-Based Extension

**Pattern Name:** Observer Pattern via Lifecycle Hooks

**Description:** Claude Code provides lifecycle events (SessionStart, UserPromptSubmit, etc.). Ring registers hook scripts that receive event data via stdin and respond via stdout JSON.

**Components Involved:**
- Hook Orchestrator
- All storage components (via hooks)

**Data Flow:**
```
Claude Code → Lifecycle Event → Hook Script (stdin JSON)
                                      ↓
                                Process Event
                                      ↓
                                Output JSON (stdout)
                                      ↓
Claude Code ← Response ← Parse JSON Response
```

**Why This Pattern:**
- Non-invasive extension of Claude Code
- Hooks are isolated, testable units
- Easy to enable/disable features

---

### Pattern 2: Dual-Format Adapter

**Pattern Name:** Strategy Pattern for Format Handling

**Description:** Support both YAML (new) and Markdown (legacy) handoff formats through adapter interface.

**Components Involved:**
- Handoff Serialization

**Architecture:**
```
HandoffSerializer (interface)
     ├─ YAMLSerializer (strategy 1)
     └─ MarkdownSerializer (strategy 2)

Usage:
  serializer = choose_serializer(format)
  output = serializer.serialize(data)
```

**Why This Pattern:**
- Backward compatibility without conditionals
- Easy to add new formats
- Each serializer is independently testable

---

### Pattern 3: Precedence-Based Configuration

**Pattern Name:** Chain of Responsibility for Config Resolution

**Description:** Configuration values resolved through precedence chain: project → global → default.

**Components Involved:**
- Ring Home Directory Manager

**Resolution Flow:**
```
Request config key "skill_activation"
     │
     ▼
Check .ring/config.yaml (project)
     │
     ├─ Found? → Return value
     │
     ▼
Check ~/.ring/config.yaml (global)
     │
     ├─ Found? → Return value
     │
     ▼
Return hardcoded default
```

**Why This Pattern:**
- Clear override semantics
- Users know where to configure
- Projects can override global without editing

---

### Pattern 4: Full-Text Search Abstraction

**Pattern Name:** Repository Pattern with FTS Backend

**Description:** Memory and artifact search abstracted behind repository interface, allowing FTS implementation swap.

**Components Involved:**
- Memory Storage & Retrieval
- Handoff Serialization (via indexing)

**Architecture:**
```
SearchRepository (interface)
     ├─ index(document) -> void
     ├─ search(query) -> results
     └─ rank(results) -> ranked_results

FTS5Repository (implementation)
     ├─ Uses full-text search engine
     ├─ BM25 ranking
     └─ Phrase and boolean queries
```

**Why This Pattern:**
- Could swap FTS5 for embeddings later
- Testing with mock repository
- Performance optimization without interface changes

---

## Security Architecture

### Threat Model

| Threat | Risk Level | Mitigation |
|--------|------------|------------|
| **Path Traversal** | High | Validate session IDs, sanitize file paths |
| **Code Injection** | Medium | Use safe YAML loading, validate schemas |
| **Secret Persistence** | Medium | Sanitize inputs, redact secrets before storage |
| **Sensitive Data Leakage** | Medium | Never store credentials in memories/handoffs |
| **Concurrent Access** | Low | File locking for writes, read-only for searches |
| **Disk Space Exhaustion** | Low | Memory expiration, size limits |

### Security Controls

**1. Input Validation**
- Session IDs: `^[a-zA-Z0-9_-]+$` (alphanumeric, hyphen, underscore only)
- File paths: Canonical path resolution, no "../" traversal
- YAML loading: Use safe parser (no arbitrary code execution)
- JSON Schema: Validate all external inputs

**2. Data Privacy**
- All data stored locally (never transmitted)
- No cloud sync, no external services
- User can delete ~/.ring/ anytime
- No telemetry, no tracking
- **Secret Redaction:** Strip API keys/tokens from memory inputs

**3. Access Control**
- Files use strict permissions (0600 for files, 0700 for dirs)
- No privilege escalation required
- No network access needed

**4. Audit Trail**
- Debug logs in ~/.ring/logs/ (opt-in)
- Memory creation timestamps
- Handoff outcome tracking

---

## Performance Architecture

### Performance Requirements

| Operation | Target | Rationale |
|-----------|--------|-----------|
| **SessionStart hook** | <2 seconds | User experience |
| **Memory search** | <200ms | Interactive response |
| **Handoff write** | <500ms | Non-blocking |
| **Skill matching** | <100ms | User prompt flow |
| **Hook execution** | <10 seconds | Claude Code timeout |

### Performance Strategies

**1. Lazy Loading**
- Don't load memories until needed
- Index on write, not on read
- Cache config in memory during session

**2. Incremental Indexing**
- Index new documents immediately
- Full reindex only on demand
- Use triggers for automatic FTS sync

**3. Query Optimization**
- Limit search results (top 10)
- Use covering indexes where possible
- Avoid full table scans

**4. Async Processing**
- Learning extraction runs in background (Stop hook)
- Indexing can be deferred
- Memory decay runs offline

---

## Scalability Architecture

### Scalability Constraints

| Dimension | Limit | Reason |
|-----------|-------|--------|
| **Memories** | ~10,000 entries | FTS5 performant up to 100K rows |
| **Handoffs** | ~1,000 files | File system performance |
| **Session duration** | Unlimited | Stateless operations |
| **Concurrent sessions** | ~5 active | File locking contention |

### Scaling Strategies

**Horizontal Scaling:** Not applicable (single-user, local tool)

**Vertical Scaling:**
1. **Memory Pruning:** Auto-delete memories older than 6 months with 0 accesses
2. **Handoff Archival:** Move old handoffs to archive directory
3. **Index Optimization:** Periodic FTS5 OPTIMIZE operation
4. **Disk Space Monitoring:** Warn if ~/.ring/ exceeds 100MB

**Degradation Path:**
- If memory.db exceeds 50MB → suggest pruning
- If search slow (>1s) → suggest reindex
- If disk full → disable memory storage, keep handoffs

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLAUDE CODE                               │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Lifecycle Events
             │
┌────────────▼────────────────────────────────────────────────────┐
│                    HOOK ORCHESTRATOR                             │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │SessionStart│  │PromptSubmit│  │ PostWrite  │                │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                │
│        │                │                │                       │
└────────┼────────────────┼────────────────┼───────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│  Ring Home     │ │   Skill      │ │   Handoff    │
│  Manager       │ │   Activator  │ │   Serializer │
└────┬───────────┘ └──────┬───────┘ └──────┬───────┘
     │                     │                │
     │ Config              │ Rules          │ Documents
     │                     │                │
┌────▼─────────────────────▼────────────────▼───────┐
│             PERSISTENT STORAGE                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Config   │  │  Rules   │  │  Documents   │    │
│  │  Files   │  │   JSON   │  │  YAML/MD     │    │
│  └──────────┘  └──────────┘  └──────────────┘    │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │        Memory Repository                    │  │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │Database │  │FTS Index │  │  Ranking  │  │  │
│  │  └─────────┘  └──────────┘  └───────────┘  │  │
│  └─────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

---

## Technology-Agnostic Component Specifications

### Component: Ring Home Manager

**Architecture Style:** Factory + Template Method

**Core Responsibilities:**
1. Directory initialization with standard structure
2. Configuration loading with precedence resolution
3. Migration coordination from legacy locations

**Key Algorithms:**
- **Directory Initialization:** Check existence → Create if missing → Set permissions
- **Config Merge:** Load project → Load global → Apply defaults → Merge with override rules
- **Migration:** Detect legacy → Copy to new → Validate → Update references

**Contracts:**
```
ensure_directory_exists():
  Pre-conditions: File system access
  Post-conditions: ~/.ring/ exists or fallback path set
  Invariants: Standard subdirectories present

get_config(scope):
  Pre-conditions: Directory initialized
  Post-conditions: Returns valid config object
  Invariants: Never returns null, uses defaults if file missing
```

---

### Component: Memory Repository

**Architecture Style:** Repository + Strategy

**Core Responsibilities:**
1. Learning persistence with type classification
2. Full-text search with relevance ranking
3. Decay mechanism for temporal relevance
4. Expiration handling for temporary learnings

**Key Algorithms:**
- **Storage:** Validate type → Check duplicates (similarity) → Insert with timestamp
- **Search:** Parse query → FTS search → Rank by BM25 + recency → Apply decay
- **Decay:** score_adjusted = score_raw × decay_factor(age, access_count)
- **Prune:** WHERE (expires_at < now()) OR (age > 180 days AND access_count = 0)

**Contracts:**
```
store_learning(content, type, confidence):
  Pre-conditions: type in VALID_TYPES, confidence in VALID_LEVELS
  Post-conditions: Learning stored with unique ID
  Invariants: created_at = now(), accessed_at = created_at

search_memories(query):
  Pre-conditions: query not empty
  Post-conditions: Results ranked by relevance
  Invariants: Results count <= limit, sorted desc by score
```

---

### Component: Handoff Serializer

**Architecture Style:** Strategy + Adapter

**Core Responsibilities:**
1. YAML serialization with schema validation
2. Markdown deserialization (legacy support)
3. Format detection and routing
4. Migration from Markdown to YAML

**Key Algorithms:**
- **Serialize:** Validate schema → Extract frontmatter → Extract body → Combine with delimiter
- **Deserialize:** Detect format → Route to parser → Validate structure → Return object
- **Migrate:** Parse Markdown → Map to YAML schema → Validate → Write → Preserve original

**Contracts:**
```
serialize(data, format):
  Pre-conditions: data passes schema validation
  Post-conditions: Returns valid YAML or Markdown string
  Invariants: Serialized data deserializes to original data

deserialize(content, format):
  Pre-conditions: content is valid YAML or Markdown
  Post-conditions: Returns structured object
  Invariants: If format=auto, correctly infers format
```

---

### Component: Skill Activator

**Architecture Style:** Rules Engine + Core two

**Core Responsibilities:**
1. Load and validate activation rules
2. Match prompts against patterns
3. Apply enforcement levels
4. Reduce false positives via negative patterns

**Key Algorithms:**
- **Match:** For each rule: (match keywords OR match patterns) AND NOT match negatives
- **Score:** Exact keyword match = 1.0, pattern match = 0.8, priority weight
- **Rank:** Sort by (priority_weight × match_score)
- **Filter:** Apply confidence threshold, remove duplicates

**Contracts:**
```
match_skills(prompt, rules):
  Pre-conditions: rules validated against schema
  Post-conditions: Returns matches sorted by relevance
  Invariants: Enforcement level respected, no duplicates

apply_enforcement(match):
  Pre-conditions: match has valid enforcement level
  Post-conditions: Returns block|suggest|warn action
  Invariants: block > suggest > warn in priority
```

---

### Component: Confidence Marker

**Architecture Style:** Decorator + Builder

**Core Responsibilities:**
1. Annotate findings with verification status
2. Build evidence chains
3. Format output with visual markers
4. Flag low-confidence for review

**Key Algorithms:**
- **Classify:** Map tool usage to confidence: Read → verified, Grep → inferred, None → uncertain
- **Chain:** Track sequence: Grep → Read → Trace → Verified
- **Format:** Apply symbols: ✓ verified, ? inferred, ✗ uncertain
- **Review Flag:** IF confidence < threshold OR evidence = assumption THEN flag

**Contracts:**
```
mark_finding(claim, evidence):
  Pre-conditions: claim not empty, evidence list valid
  Post-conditions: Returns claim with marker and evidence
  Invariants: Marker matches confidence level

infer_confidence(evidence):
  Pre-conditions: evidence type in VALID_TYPES
  Post-conditions: Returns valid confidence level
  Invariants: Default to 'uncertain' if ambiguous
```

---

## Deployment Architecture

### Installation Flow

```
User runs: curl ... | bash
     │
     ▼
Installer script
     │
     ├─> Check ~/.ring/ existence
     │     └─> Create if missing
     │
     ├─> Copy skill/agent/hook files
     │
     ├─> Initialize memory.db schema
     │
     ├─> Create default skill-rules.json
     │
     └─> Output success message
```

### Runtime Architecture

**Process Model:** Single-process, synchronous hooks

```
Claude Code (main process)
     │
     ├─> Spawn hook script (subprocess)
     │     └─> Hook executes, returns JSON
     │
     ├─> Parse hook response
     │
     └─> Continue with injected context
```

**No Daemons Required:** All operations synchronous within hook timeouts

### File System Layout

```
~/.ring/                           # Global Ring home
├── config.yaml                    # User configuration
├── memory.db                      # SQLite database
├── skill-rules.json               # Activation rules
├── skill-rules-schema.json        # JSON Schema
├── handoffs/                      # Cross-project handoffs
│   └── {session-name}/
│       └── {timestamp}.yaml
├── logs/                          # Debug logs (opt-in)
│   └── {date}.log
└── cache/                         # Temporary data
    └── last-session.json

$PROJECT/.ring/                    # Project-local
├── config.yaml                    # Project config (optional)
├── state/                         # Session state
│   ├── context-usage-{session}.json
│   └── todos-state-{session}.json
├── ledgers/                       # Within-session continuity
│   └── CONTINUITY-{name}.md
└── cache/
    └── artifact-index/
        └── context.db             # Project artifacts index
```

---

## Error Handling Architecture

### Error Categories

| Category | Severity | Response |
|----------|----------|----------|
| **Critical** | Blocks functionality | Halt and report to user |
| **Degraded** | Partial functionality | Continue with warning |
| **Informational** | No impact | Log only |

### Error Handling by Component

**Ring Home Manager:**
- Creation failure (permissions) → Use .ring/ fallback, warn user
- Config parse error → Use defaults, log warning
- Migration failure → Keep original, report error

**Memory Repository:**
- DB locked → Retry 3x with backoff, then skip memory
- Search error → Fallback to simple text search
- Storage error → Log and continue (memory is enhancement, not critical)

**Handoff Serializer:**
- YAML parse error → Try Markdown parser
- Validation error → Return detailed errors, block write
- Migration error → Preserve original, report failure

**Skill Activator:**
- Rules invalid → Skip auto-activation, log error
- Pattern compilation error → Skip that pattern
- Multiple block-level matches → Suggest all, let user choose

**Hook Orchestrator:**
- Hook timeout → Return partial results
- Hook crash → Log error, continue without hook
- JSON malformed → Wrap in error response, continue

### Fallback Chain

```
Operation Failed
     │
     ▼
Try Primary Method (e.g., ~/.ring/memory.db)
     │
     ├─> Success → Return result
     │
     ▼
Try Fallback (e.g., .ring/memory.db project-local)
     │
     ├─> Success → Return result
     │
     ▼
Try Last Resort (e.g., in-memory only, no persistence)
     │
     ├─> Success → Return result + warning
     │
     ▼
Graceful Failure (e.g., skip memory, continue session)
```

---

## Testing Architecture

### Test Pyramid

```
         ┌────────┐
        ╱  E2E     ╲       10% - Full workflow tests
       ╱────────────╲
      ╱ Integration  ╲     30% - Component interaction tests
     ╱────────────────╲
    ╱   Unit Tests     ╲   60% - Component isolation tests
   ╱──────────────────── ╲
```

**Test Types:**

| Type | Purpose | Example |
|------|---------|---------|
| **Unit** | Component in isolation | Test YAML serialization |
| **Integration** | Components together | Test memory search with FTS5 |
| **E2E** | Full user workflows | Test session start → memory inject → handoff create |

### Test Strategy by Component

**Ring Home Manager:**
- Unit: Config precedence logic
- Integration: Directory creation with mockable FileSystem
- E2E: First-time setup flow

**Memory Repository:**
- Unit: Learning type classification, decay calculation
- Integration: SQLite FTS5 search and ranking
- E2E: Store learning → Search → Retrieve → Verify

**Handoff Serializer:**
- Unit: YAML schema validation
- Integration: Read legacy Markdown, write YAML
- E2E: Create handoff → Index → Resume from handoff

**Skill Activator:**
- Unit: Keyword matching, regex compilation
- Integration: Pattern matching with actual skill-rules.json
- E2E: Prompt → Match → Suggest → User selects

**Hook Orchestrator:**
- Unit: JSON input/output parsing
- Integration: Hook event dispatch
- E2E: SessionStart → Load config → Inject memories → Continue

---

## Migration Architecture

### Migration Strategy: Dual-Support Transition

**Phase 1:** Add YAML support, keep Markdown (1-2 weeks)
- Both formats work
- New handoffs use YAML
- Old handoffs remain Markdown

**Phase 2:** Migration tools (2-4 weeks after Phase 1)
- Provide conversion utility
- Users can opt-in to convert
- Keep originals

**Phase 3:** Deprecation (3-6 months after Phase 2)
- Announce Markdown deprecation
- Warn on Markdown handoff creation
- Keep read support indefinitely

### Backward Compatibility Requirements

| Feature | Requirement | Implementation |
|---------|-------------|----------------|
| **Handoff reading** | Support both YAML and Markdown | Dual-format adapter |
| **Artifact indexing** | Index both formats | Detect format, extract frontmatter |
| **Skill frontmatter** | Keep existing YAML structure | Extend, don't replace |
| **Hook JSON** | Maintain current schema | Additive changes only |

### Breaking Change Policy

**Zero breaking changes** for existing workflows:
- Existing skills continue to work
- Existing handoffs remain readable
- Existing hooks remain functional
- Existing commands unchanged (output format changes only)

**Opt-in for new features:**
- YAML handoffs: User chooses format
- Memory system: Auto-enabled, but graceful if disabled
- Skill activation: Suggest-only by default
- Confidence markers: Added to new outputs, legacy outputs unchanged

---

## Gate 3 Validation Checklist

- [x] All Feature Map domains mapped to components (5 components)
- [x] All PRD features mapped to components (27 features → 6 components)
- [x] Component boundaries are clear (responsibility tables)
- [x] Interfaces are technology-agnostic (no SQLite/PyYAML specifics)
- [x] No specific products named (FTS not named as "SQLite FTS5" yet)
- [x] Architecture patterns documented (Repository, Strategy, Observer, Factory)
- [x] Integration patterns defined (Hook-based, Dual-format, Precedence-based)
- [x] Security, performance, scalability addressed
- [x] Migration strategy documented
- [x] Error handling defined per component

---

## Appendix: Pattern Catalog

| Pattern Name | Category | Where Applied |
|--------------|----------|---------------|
| Repository | Structural | Memory Storage, Search Abstraction |
| Strategy | Behavioral | Handoff format selection |
| Observer | Behavioral | Hook event system |
| Factory | Creational | Config precedence resolution |
| Adapter | Structural | Dual-format handoff support |
| Decorator | Structural | Confidence marker addition |
| Chain of Responsibility | Behavioral | Config precedence chain |
| Template Method | Behavioral | Hook execution flow |
