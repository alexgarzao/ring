# Ring Continuity - Task Breakdown (Gate 7)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** Dependency Map v1.0 (docs/pre-dev/ring-continuity/dependency-map.md)

---

## Executive Summary

Ring Continuity implementation is broken into **5 phases** with **15 tasks** total. Each task delivers **independently deployable value** and includes **comprehensive testing**. Phases build on each other but each phase can ship to users separately.

**Total Estimated Effort:** 8-12 days (1.5-2.5 weeks)

**Phased Rollout:**
- Phase 1-2: Core foundation (3-4 days)
- Phase 3-4: Enhancements (3-4 days)
- Phase 5: Advanced features (2-4 days)

---

## Phase Overview

| Phase | Tasks | Value Delivered | Effort | Risk |
|-------|-------|-----------------|--------|------|
| **Phase 1: Foundation** | 3 | ~/.ring/ directory, config precedence | 2-3 days | Low |
| **Phase 2: YAML Handoffs** | 4 | 5x token efficiency, machine-parseable | 2-3 days | Low |
| **Phase 3: Confidence Markers** | 2 | Reduced false claims (80% → <20%) | 1-2 days | Low |
| **Phase 4: Skill Activation** | 3 | Auto-suggestion, better discovery | 2-3 days | Medium |
| **Phase 5: Persistent Memory** | 3 | Cross-session learning | 2-4 days | Medium |

---

## Phase 1: Foundation

**Goal:** Establish ~/.ring/ as Ring's global home with config precedence.

**User Value:** Single source of truth for Ring configuration and data across all projects.

**Success Criteria:** Users can customize Ring globally, projects can override.

---

### Task 1.1: Create ~/.ring/ Directory Structure

**Description:** Initialize ~/.ring/ with standard subdirectories on first Ring use.

**Value:** Foundation for all persistent Ring data.

**Acceptance Criteria:**
- [ ] ~/.ring/ created with subdirectories: config/, handoffs/, logs/, cache/, state/
- [ ] Directory creation is idempotent (safe to run multiple times)
- [ ] Falls back to .ring/ in project if home directory not writable
- [ ] Logs creation to ~/.ring/logs/installation.log

**Files to Create:**
- `default/lib/ring_home.py` - Directory manager
- `default/lib/ring_home_test.py` - Unit tests
- `install-ring-home.sh` - Standalone install script

**Testing Strategy:**
```bash
# Unit tests
pytest default/lib/ring_home_test.py

# Integration test
bash install-ring-home.sh
test -d ~/.ring/handoffs || exit 1
test -f ~/.ring/config.yaml || exit 1

# Fallback test (simulate permission error)
chmod 000 ~/.ring && bash install-ring-home.sh
# Should create .ring/ in current project
```

**Dependencies:** None

**Estimated Effort:** 0.5 days

**Risk:** Low (straightforward directory creation)

---

### Task 1.2: Implement Config Precedence System

**Description:** Load and merge configuration from project → global → defaults.

**Value:** Users can set global preferences and override per project.

**Acceptance Criteria:**
- [ ] Load config from ~/.ring/config.yaml (global)
- [ ] Load config from .ring/config.yaml (project, if exists)
- [ ] Merge with precedence: project > global > hardcoded defaults
- [ ] Return config value with source attribution (which file it came from)
- [ ] Handle missing config files gracefully (use defaults)

**Files to Create:**
- `default/lib/config_loader.py` - Config precedence logic
- `default/lib/config_loader_test.py` - Unit tests
- `~/.ring/config.yaml` - Default global config (created by install script)

**Testing Strategy:**
```python
# Test precedence
def test_config_precedence():
    # Setup: global config has value A, project has value B
    global_config = {'memory': {'enabled': True}}
    project_config = {'memory': {'enabled': False}}

    merged = merge_configs(global_config, project_config)

    # Project should win
    assert merged['memory']['enabled'] == False
    assert merged['_source']['memory.enabled'] == 'project'

# Test graceful degradation
def test_missing_config_files():
    # Neither global nor project exists
    merged = load_config()

    # Should use hardcoded defaults
    assert merged['memory']['enabled'] == True
    assert merged['_source']['memory.enabled'] == 'default'
```

**Dependencies:** Task 1.1 (directory structure)

**Estimated Effort:** 1 day

**Risk:** Low (well-understood pattern)

---

### Task 1.3: Create Migration Utilities

**Description:** Migrate existing .ring/ data to ~/.ring/ with safety checks.

**Value:** Users can adopt new structure without losing existing data.

**Acceptance Criteria:**
- [ ] Detect existing .ring/ directories in projects
- [ ] Migrate handoffs to ~/.ring/handoffs/{project-name}/
- [ ] Preserve original files (read-only copy, not move)
- [ ] Log migration results to ~/.ring/logs/migration.log
- [ ] Provide rollback script in case of issues

**Files to Create:**
- `default/lib/migrate_to_ring_home.py` - Migration script
- `default/lib/migrate_to_ring_home_test.py` - Tests
- `scripts/migrate-ring-data.sh` - User-facing script

**Testing Strategy:**
```bash
# Setup test project with old .ring/
mkdir -p test-project/.ring/handoffs/session1/
echo "---" > test-project/.ring/handoffs/session1/handoff.md

# Run migration
python3 default/lib/migrate_to_ring_home.py test-project

# Verify
test -f ~/.ring/handoffs/test-project/session1/handoff.md || exit 1
test -f test-project/.ring/handoffs/session1/handoff.md || exit 1  # Original preserved
```

**Dependencies:** Task 1.1 (directory structure), Task 1.2 (config loading)

**Estimated Effort:** 0.5-1 day

**Risk:** Low (copy operations, no deletion)

---

## Phase 2: YAML Handoffs

**Goal:** Replace Markdown handoffs with token-efficient YAML format.

**User Value:** 5x token savings (2000 → 400 tokens), machine-parseable for tools.

**Success Criteria:** New handoffs use YAML, legacy Markdown still readable.

---

### Task 2.1: Define YAML Handoff Schema

**Description:** Create JSON Schema for handoff validation and documentation.

**Value:** Prevents invalid handoffs, enables tooling.

**Acceptance Criteria:**
- [ ] JSON Schema file defines all handoff fields
- [ ] Schema includes required vs optional fields
- [ ] Schema includes validation constraints (max lengths, enums)
- [ ] Schema documented with examples
- [ ] Schema version field for future evolution

**Files to Create:**
- `default/schemas/handoff-schema-v1.json` - JSON Schema definition
- `default/schemas/handoff-example.yaml` - Example handoff
- `default/schemas/README.md` - Schema documentation

**Testing Strategy:**
```python
# Validate example against schema
def test_schema_example():
    import json, yaml
    from jsonschema import validate

    with open('default/schemas/handoff-schema-v1.json') as f:
        schema = json.load(f)

    with open('default/schemas/handoff-example.yaml') as f:
        example = yaml.safe_load(f)

    # Should validate without errors
    validate(instance=example, schema=schema)
```

**Dependencies:** None

**Estimated Effort:** 0.5 days

**Risk:** Low (schema definition)

---

### Task 2.2: Implement YAML Serialization

**Description:** Create Python module to serialize/deserialize handoffs in YAML.

**Value:** Core capability for YAML handoff creation.

**Acceptance Criteria:**
- [ ] Serialize HandoffData to YAML string
- [ ] Deserialize YAML string to HandoffData
- [ ] Support frontmatter + body format (--- delimited)
- [ ] Validate against schema before write (if jsonschema available)
- [ ] Token count estimation from serialized output
- [ ] Handles Unicode correctly

**Files to Create:**
- `default/lib/handoff_serializer.py` - Serialization logic
- `default/lib/handoff_serializer_test.py` - Unit tests

**Testing Strategy:**
```python
def test_serialize_deserialize():
    original = HandoffData(
        session={'id': 'test-session'},
        task={'description': 'Test task', 'status': 'completed'},
        # ... full handoff data
    )

    # Serialize
    yaml_str = serialize(original, format='yaml')

    # Deserialize
    restored = deserialize(yaml_str, format='yaml')

    # Should be equivalent
    assert original == restored

def test_token_count():
    handoff = create_sample_handoff()
    yaml_str = serialize(handoff, format='yaml')

    token_count = estimate_tokens(yaml_str)

    # Should be under 500 tokens
    assert token_count < 500
```

**Dependencies:** Task 2.1 (schema), PyYAML

**Estimated Effort:** 1 day

**Risk:** Low (straightforward serialization)

---

### Task 2.3: Update ring:handoff-tracking Skill for YAML

**Description:** Modify ring:handoff-tracking skill to output YAML instead of Markdown.

**Value:** Users immediately benefit from token savings.

**Acceptance Criteria:**
- [ ] Skill generates YAML format by default
- [ ] User can choose format via parameter: `--format=yaml|markdown`
- [ ] YAML output validated against schema
- [ ] Token count logged to session
- [ ] Backward compatible with existing skill invocation

**Files to Modify:**
- `default/skills/handoff-tracking/SKILL.md` - Update template and instructions
- `default/skills/handoff-tracking/handoff-template.yaml` - New YAML template

**Testing Strategy:**
```bash
# Test YAML handoff creation
echo "Create handoff for test session" | claude-code

# Verify YAML format
file_path=$(ls -t docs/handoffs/*/2026-*.yaml | head -1)
python3 -c "import yaml; yaml.safe_load(open('$file_path'))"  # Should not error

# Verify token count
tokens=$(wc -w < "$file_path" | awk '{print $1 * 1.3}')  # Rough estimate
test "$tokens" -lt 500 || exit 1
```

**Dependencies:** Task 2.2 (serialization)

**Estimated Effort:** 1 day

**Risk:** Low (skill update only)

---

### Task 2.4: Implement Dual-Format Indexing

**Description:** Update artifact indexer to handle both YAML and Markdown handoffs.

**Value:** All handoffs searchable regardless of format.

**Acceptance Criteria:**
- [ ] Detect handoff format from file extension (.yaml, .yml, .md)
- [ ] Extract frontmatter from both formats
- [ ] Parse YAML body sections (decisions, learnings, etc.)
- [ ] Index with same FTS5 schema regardless of source format
- [ ] Migration flag to convert Markdown to YAML during indexing

**Files to Modify:**
- `default/lib/artifact-index/artifact_index.py` - Add YAML parsing
- `default/lib/artifact-index/artifact_index_test.py` - Add YAML tests

**Testing Strategy:**
```python
def test_index_yaml_handoff():
    # Create YAML handoff
    yaml_path = create_test_handoff_yaml()

    # Index it
    index_handoff(yaml_path)

    # Search should find it
    results = search_handoffs("test task")
    assert len(results) > 0
    assert yaml_path in [r['file_path'] for r in results]

def test_index_markdown_handoff():
    # Existing Markdown handoff
    md_path = create_test_handoff_markdown()

    # Should still index
    index_handoff(md_path)

    # Search should find it
    results = search_handoffs("test task")
    assert md_path in [r['file_path'] for r in results]
```

**Dependencies:** Task 2.2 (serialization), existing artifact-index

**Estimated Effort:** 0.5-1 day

**Risk:** Low (extends existing indexer)

---

## Phase 3: Confidence Markers

**Goal:** Add verification status to agent outputs to reduce false claims.

**User Value:** Users know which findings are verified vs inferred (80% → <20% false claim rate).

**Success Criteria:** Agents output ✓/?/✗ markers with evidence chains.

---

### Task 3.1: Update Agent Output Schemas

**Description:** Add "Verification" section to all agent output schemas in AGENT_DESIGN.md.

**Value:** Standardized confidence reporting across all agents.

**Acceptance Criteria:**
- [ ] Add "Verification" section to 5 schema archetypes
- [ ] Define confidence marker format (✓ VERIFIED, ? INFERRED, ✗ UNCERTAIN)
- [ ] Include evidence chain requirement
- [ ] Update schema validation examples
- [ ] Document when verification is required vs optional

**Files to Modify:**
- `docs/AGENT_DESIGN.md` - Add Verification section to schemas
- `docs/AGENT_DESIGN.md` - Update examples with confidence markers

**Testing Strategy:**
```bash
# Verify schema completeness
grep -c "## Verification" docs/AGENT_DESIGN.md
# Should return 5 (one per schema archetype)

# Verify examples include markers
grep -c "✓ VERIFIED" docs/AGENT_DESIGN.md
grep -c "? INFERRED" docs/AGENT_DESIGN.md
grep -c "✗ UNCERTAIN" docs/AGENT_DESIGN.md
```

**Dependencies:** None (documentation only)

**Estimated Effort:** 0.5 days

**Risk:** Low (documentation update)

---

### Task 3.2: Integrate Confidence Markers in ring:codebase-explorer

**Description:** Update ring:codebase-explorer agent to include confidence markers in findings.

**Value:** Most-used exploration agent immediately benefits from verification.

**Acceptance Criteria:**
- [ ] Agent output includes ## Verification section
- [ ] Each finding marked with ✓/?/✗
- [ ] Evidence chain documented (Glob → Read → Trace → ✓)
- [ ] Low-confidence findings flagged for review
- [ ] Agent prompt updated to enforce marker usage

**Files to Modify:**
- `default/agents/codebase-explorer.md` - Add Verification requirements
- `default/agents/codebase-explorer.md` - Add anti-rationalization table for skipping verification

**Testing Strategy:**
```bash
# Run explorer on test codebase
Task(subagent_type="ring:codebase-explorer", prompt="Find auth implementation")

# Verify output contains markers
output=$(cat .claude/cache/agents/codebase-explorer/latest-output.md)
echo "$output" | grep "## Verification" || exit 1
echo "$output" | grep -E "✓|✗|\?" || exit 1
```

**Dependencies:** Task 3.1 (schema definition)

**Estimated Effort:** 1 day

**Risk:** Low (single agent update)

---

## Phase 4: Skill Activation

**Goal:** Auto-suggest relevant skills based on user prompt patterns.

**User Value:** Users discover skills without memorizing names.

**Success Criteria:** 80% of applicable skills suggested automatically.

---

### Task 4.1: Create skill-rules.json with Core Skills

**Description:** Generate initial skill-rules.json from existing skill frontmatter.

**Value:** Immediate skill suggestions for most common workflows.

**Acceptance Criteria:**
- [ ] Parse all SKILL.md files for trigger/skip_when fields
- [ ] Generate skill-rules.json with keyword mappings
- [ ] Include 20+ core skills (TDD, code review, systematic debugging, etc.)
- [ ] Validate generated JSON against schema
- [ ] Install to ~/.ring/skill-rules.json

**Files to Create:**
- `scripts/generate-skill-rules.py` - Generator script
- `default/schemas/skill-rules-schema.json` - JSON Schema for rules
- `~/.ring/skill-rules.json` - Generated rules file

**Testing Strategy:**
```python
def test_generate_rules():
    rules = generate_skill_rules_from_skills()

    # Should have entries for key skills
    assert 'ring:test-driven-development' in rules['skills']
    assert 'ring:requesting-code-review' in rules['skills']

    # Should have valid structure
    validate(rules, skill_rules_schema)

def test_keyword_extraction():
    skill_md = """
---
trigger: |
  - When writing tests
  - For test-driven development
---
"""
    keywords = extract_keywords(skill_md)
    assert 'test' in keywords or 'tdd' in keywords
```

**Dependencies:** Existing skills with trigger frontmatter

**Estimated Effort:** 1 day

**Risk:** Medium (mapping logic may need tuning)

---

### Task 4.2: Implement Skill Matching Engine

**Description:** Create Python module to match prompts against skill rules.

**Value:** Core logic for skill auto-suggestion.

**Acceptance Criteria:**
- [ ] Load skill-rules.json with validation
- [ ] Match prompt text against keywords (case-insensitive)
- [ ] Match prompt against regex patterns (intent patterns)
- [ ] Apply negative patterns to filter false positives
- [ ] Rank matches by priority (critical > high > medium > low)
- [ ] Return top 5 matches with confidence scores

**Files to Create:**
- `default/lib/skill_matcher.py` - Matching engine
- `default/lib/skill_matcher_test.py` - Unit tests

**Testing Strategy:**
```python
def test_keyword_matching():
    rules = load_test_rules()
    prompt = "I want to implement TDD for this feature"

    matches = match_skills(prompt, rules)

    assert 'ring:test-driven-development' in [m.skill for m in matches]
    assert matches[0].confidence > 0.8

def test_negative_patterns():
    rules = {
        'ring:test-driven-development': {
            'keywords': ['test'],
            'negative_patterns': [r'test.*data', r'test.*environment']
        }
    }

    # Should NOT match
    prompt1 = "Load test data from database"
    matches = match_skills(prompt1, rules)
    assert 'ring:test-driven-development' not in [m.skill for m in matches]

    # Should match
    prompt2 = "Write test for authentication"
    matches = match_skills(prompt2, rules)
    assert 'ring:test-driven-development' in [m.skill for m in matches]
```

**Dependencies:** Task 4.1 (skill-rules.json)

**Estimated Effort:** 1-2 days

**Risk:** Medium (false positive tuning needed)

---

### Task 4.3: Create UserPromptSubmit Hook for Activation

**Description:** Hook that suggests skills on user prompt submission.

**Value:** Users see skill suggestions in real-time.

**Acceptance Criteria:**
- [ ] Hook runs on UserPromptSubmit event
- [ ] Calls skill matcher with user prompt
- [ ] Returns suggestions in additionalContext
- [ ] Respects enforcement levels (block/suggest/warn)
- [ ] Completes within 1 second timeout
- [ ] Gracefully handles matcher failures

**Files to Create:**
- `default/hooks/skill-activation.sh` - Bash hook wrapper
- `default/hooks/skill-activation.py` - Python matcher caller
- Update `default/hooks/hooks.json` - Register new hook

**Testing Strategy:**
```bash
# Mock hook input
cat <<EOF | default/hooks/skill-activation.sh
{
  "event": "UserPromptSubmit",
  "session_id": "test",
  "prompt": "I want to use TDD for this feature"
}
EOF

# Verify output suggests TDD skill
output=$(cat)
echo "$output" | jq '.hookSpecificOutput.additionalContext' | grep "ring:test-driven-development"
```

**Dependencies:** Task 4.2 (matching engine)

**Estimated Effort:** 1 day

**Risk:** Medium (hook timing sensitive)

---

## Phase 5: Persistent Memory

**Goal:** Store and recall learnings across sessions.

**User Value:** AI remembers what worked/failed, user preferences, patterns.

**Success Criteria:** Learnings retrieved and injected at session start.

---

### Task 5.1: Create Memory Database Schema

**Description:** Initialize SQLite database with FTS5 for memory storage.

**Value:** Foundation for persistent learning.

**Acceptance Criteria:**
- [ ] Create memories table with all fields (id, content, type, confidence, etc.)
- [ ] Create memories_fts virtual table for full-text search
- [ ] Create triggers for automatic FTS sync
- [ ] Create indexes for common queries (type, session_id, created_at)
- [ ] Schema supports soft deletion (deleted_at field)
- [ ] Schema supports expiration (expires_at field)

**Files to Create:**
- `default/lib/memory-schema.sql` - Database schema
- `default/lib/memory_repository.py` - Repository implementation
- `default/lib/memory_repository_test.py` - Unit tests

**Testing Strategy:**
```python
def test_memory_storage():
    repo = MemoryRepository('~/.ring/memory.db')

    learning_id = repo.store_learning(
        content="Use async/await for better readability",
        type="WORKING_SOLUTION",
        confidence="HIGH"
    )

    assert learning_id is not None

def test_fts_search():
    repo = MemoryRepository('~/.ring/memory.db')

    # Store learning
    repo.store_learning("TypeScript async patterns work well", type="WORKING_SOLUTION")

    # Search should find it
    results = repo.search_memories("typescript async")
    assert len(results) > 0
    assert "async" in results[0].content.lower()
```

**Dependencies:** Task 1.1 (directory structure)

**Estimated Effort:** 1-2 days

**Risk:** Low (similar to existing artifact-index)

---

### Task 5.2: Implement Memory Search & Retrieval

**Description:** Create search interface with BM25 ranking and filters.

**Value:** Users can find relevant learnings quickly.

**Acceptance Criteria:**
- [ ] Search by text query using FTS5
- [ ] Filter by learning type, tags, confidence
- [ ] Rank by BM25 relevance score
- [ ] Apply recency weighting (recent learnings rank higher)
- [ ] Update access_count and accessed_at on retrieval
- [ ] Return top 10 results with highlights

**Files to Modify:**
- `default/lib/memory_repository.py` - Add search methods

**Testing Strategy:**
```python
def test_search_with_filters():
    repo = MemoryRepository('~/.ring/memory.db')

    results = repo.search_memories(
        query="async await",
        filters={'types': ['WORKING_SOLUTION'], 'confidence': 'HIGH'},
        limit=5
    )

    assert len(results) <= 5
    assert all(r.type == 'WORKING_SOLUTION' for r in results)
    assert all(r.confidence == 'HIGH' for r in results)

def test_relevance_ranking():
    repo = MemoryRepository('~/.ring/memory.db')

    results = repo.search_memories("error handling")

    # Results should be sorted by relevance
    for i in range(len(results) - 1):
        assert results[i].relevance_score >= results[i+1].relevance_score
```

**Dependencies:** Task 5.1 (database schema)

**Estimated Effort:** 1 day

**Risk:** Low (FTS5 handles ranking)

---

### Task 5.3: Create SessionStart Hook for Memory Injection

**Description:** Hook that searches memories on session start and injects relevant ones.

**Value:** Users automatically get context from past sessions.

**Acceptance Criteria:**
- [ ] Hook runs on SessionStart event
- [ ] Searches memories using project path as context
- [ ] Injects top 5 relevant memories into session
- [ ] Formats memories for readability
- [ ] Completes within 2 seconds timeout
- [ ] Handles missing memory.db gracefully

**Files to Create:**
- `default/hooks/memory-awareness.sh` - Hook wrapper
- `default/hooks/memory-awareness.py` - Python memory searcher
- Update `default/hooks/hooks.json` - Register hook

**Testing Strategy:**
```bash
# Store test learning
python3 -c "
from memory_repository import MemoryRepository
repo = MemoryRepository('~/.ring/memory.db')
repo.store_learning('Test learning about async', type='WORKING_SOLUTION')
"

# Mock SessionStart hook
cat <<EOF | default/hooks/memory-awareness.sh
{
  "event": "SessionStart",
  "session_id": "test",
  "project_path": "$PWD"
}
EOF

# Verify memories injected
output=$(cat)
echo "$output" | jq '.hookSpecificOutput.additionalContext' | grep "async"
```

**Dependencies:** Task 5.2 (search), Task 1.2 (config for enable/disable)

**Estimated Effort:** 1-2 days

**Risk:** Medium (timing sensitive, must complete fast)

---

## Task Dependencies Graph

```
Phase 1: Foundation
  T1.1 (Directory) ──┬──> T1.2 (Config)
                     │
                     └──> T1.3 (Migration)

Phase 2: YAML Handoffs
  T2.1 (Schema) ──> T2.2 (Serializer) ──> T2.3 (Skill Update)
                                     └──> T2.4 (Indexing)

Phase 3: Confidence Markers
  T3.1 (Schema Update) ──> T3.2 (Explorer Integration)

Phase 4: Skill Activation
  T4.1 (Rules Gen) ──> T4.2 (Core two) ──> T4.3 (Hook)

Phase 5: Persistent Memory
  T5.1 (DB Schema) ──> T5.2 (Search) ──> T5.3 (Hook)

Cross-Phase Dependencies:
  T1.1 ──> T2.2, T4.1, T5.1  (All need ~/.ring/)
  T1.2 ──> T4.3, T5.3  (Hooks check config)
  T2.2 ──> T2.4  (Indexing needs serializer)
```

---

## Testing Strategy Summary

### Test Coverage Targets

| Component | Unit Test Coverage | Integration Test Coverage |
|-----------|-------------------|---------------------------|
| ring_home.py | 90% | 100% |
| config_loader.py | 95% | 100% |
| handoff_serializer.py | 95% | 100% |
| skill_matcher.py | 90% | 90% |
| memory_repository.py | 90% | 95% |
| Hooks | 70% (bash) | 100% |

### Test Data

**Location:** `tests/fixtures/`

**Test Artifacts:**
- Sample handoffs (YAML and Markdown)
- Sample skill-rules.json
- Sample memory.db with test learnings
- Sample config.yaml files (global and project)

### Continuous Integration

**On commit:**
```bash
# Lint
shellcheck default/hooks/*.sh
ruff check default/lib/
black --check default/lib/

# Test
pytest tests/ --cov=default/lib/ --cov-report=term-missing

# Coverage gate
coverage report --fail-under=85
```

---

## Deployment Strategy

### Rollout Plan

| Phase | Users | Deployment |
|-------|-------|------------|
| **Phase 1-2** | Early adopters | Alpha release, manual install |
| **Phase 3-4** | Ring users | Beta release, install script |
| **Phase 5** | All users | Stable release, auto-update |

### Feature Flags

**Location:** `~/.ring/config.yaml`

```yaml
features:
  yaml_handoffs: true      # Enable YAML handoff format
  skill_activation: true   # Enable auto-suggestion
  memory_system: true      # Enable persistent memory
  confidence_markers: true # Enable markers in agent outputs
```

**Allows:**
- Gradual feature rollout
- Users opt-out if issues
- A/B testing different configurations

---

## Risk Mitigation

### High-Risk Tasks

| Task | Risk | Mitigation |
|------|------|------------|
| T4.2 (Skill Core two) | False positives | Extensive test suite with edge cases, negative patterns |
| T4.3 (Activation Hook) | Timeout issues | Async matching, 1s timeout, fallback to no suggestions |
| T5.3 (Memory Hook) | Performance impact | Cache searches, limit to 5 memories, 2s timeout |

### Rollback Plan

**Per Phase:**
1. **Phase 1:** Delete ~/.ring/, revert to .ring/
2. **Phase 2:** Set `handoffs.format: markdown` in config
3. **Phase 3:** Agents output without markers (backward compatible)
4. **Phase 4:** Set `skill_activation.enabled: false` in config
5. **Phase 5:** Set `memory_system.enabled: false` in config

**All features are opt-out via config.**

---

## Gate 7 Validation Checklist

- [x] Every task delivers user value independently
- [x] No task larger than 2 weeks (max is 2 days)
- [x] Dependencies are clear (dependency graph)
- [x] Testing approach defined per task
- [x] 5 phases map to 5 feature domains
- [x] 15 total tasks with clear acceptance criteria
- [x] Risk mitigation for high-risk tasks
- [x] Rollout plan with feature flags

---

## Appendix: Task Summary

| Phase | Task | Value | Effort | Risk |
|-------|------|-------|--------|------|
| **1** | T1.1 Directory Creation | Foundation | 0.5d | Low |
| **1** | T1.2 Config Precedence | Global preferences | 1d | Low |
| **1** | T1.3 Migration Utilities | Preserve existing data | 0.5-1d | Low |
| **2** | T2.1 YAML Schema | Handoff validation | 0.5d | Low |
| **2** | T2.2 YAML Serialization | Core capability | 1d | Low |
| **2** | T2.3 Update Skill | 5x token savings | 1d | Low |
| **2** | T2.4 Dual-Format Indexing | Universal search | 0.5-1d | Low |
| **3** | T3.1 Update Schemas | Standardized confidence | 0.5d | Low |
| **3** | T3.2 Explorer Integration | Reduced false claims | 1d | Low |
| **4** | T4.1 Generate Rules | Initial rules | 1d | Medium |
| **4** | T4.2 Matching Engine | Core activation logic | 1-2d | Medium |
| **4** | T4.3 Activation Hook | Real-time suggestions | 1d | Medium |
| **5** | T5.1 Memory Database | Persistent storage | 1-2d | Low |
| **5** | T5.2 Memory Search | Learning retrieval | 1d | Low |
| **5** | T5.3 Memory Hook | Auto-injection | 1-2d | Medium |

**Total:** 12-18 days (2.5-3.5 weeks)
