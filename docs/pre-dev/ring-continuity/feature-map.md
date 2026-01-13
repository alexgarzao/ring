# Ring Continuity - Feature Map (Gate 2)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** PRD v1.0 (docs/pre-dev/ring-continuity/prd.md)

---

## Executive Summary

Ring Continuity consists of **5 interconnected feature domains** that work together to create an intelligent, learning assistant. The feature map reveals a **layered dependency structure**: Foundation layer (~/.ring/), Storage layer (Memory + Handoffs), Enhancement layer (Confidence + Activation), and Integration layer (Hooks + Skills).

---

## Feature Domain Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │   Hook Integration       │  │   Skill Enhancement      │    │
│  │  • SessionStart          │  │  • Agent outputs         │    │
│  │  • UserPromptSubmit      │  │  • Skill definitions     │    │
│  │  • PostToolUse           │  │  • Command wrappers      │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   ENHANCEMENT LAYER                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │  Confidence Markers      │  │  Skill Activation        │    │
│  │  • Verification status   │  │  • Rules engine          │    │
│  │  • Evidence chains       │  │  • Pattern matching      │    │
│  │  • Trust calibration     │  │  • Auto-suggestion       │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                                │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │  Persistent Memory       │  │   YAML Handoffs          │    │
│  │  • SQLite + FTS5         │  │  • Compact format        │    │
│  │  • Learning types        │  │  • Schema validation     │    │
│  │  • Decay mechanism       │  │  • Backward compat       │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    FOUNDATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Global Ring Directory (~/.ring/)           │    │
│  │  • Directory structure                                  │    │
│  │  • Configuration management                             │    │
│  │  • Migration utilities                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Domain Breakdown

### Domain 1: Foundation - Global Ring Directory

**Purpose:** Establish ~/.ring/ as the global home for Ring data and configuration.

**Features:**

| Feature | Description | Priority |
|---------|-------------|----------|
| F1.1 - Directory Creation | Create ~/.ring/ on first use | P0 |
| F1.2 - Config Management | Load/merge global and project configs | P0 |
| F1.3 - Migration Utilities | Move existing data to ~/.ring/ | P1 |
| F1.4 - Cleanup Utilities | Remove old/stale data | P2 |

**Scope:**
- IN: Global directory structure, config precedence, migration
- OUT: Cloud sync, multi-user support

**Dependencies:**
- None (foundation layer)

---

### Domain 2: Storage - Persistent Memory

**Purpose:** Store and retrieve learnings across sessions using SQLite FTS5.

**Features:**

| Feature | Description | Priority |
|---------|-------------|----------|
| F2.1 - Memory Database | SQLite with FTS5 schema | P0 |
| F2.2 - Memory Storage | Store learnings with type classification | P0 |
| F2.3 - Memory Retrieval | FTS5 search with BM25 ranking | P0 |
| F2.4 - Memory Awareness | Hook to inject relevant memories | P1 |
| F2.5 - Memory Decay | Reduce relevance over time | P2 |
| F2.6 - Memory Expiration | Auto-delete expired memories | P2 |

**Scope:**
- IN: 7 learning types, FTS5 search, decay mechanism
- OUT: Embeddings, semantic search, real-time updates

**Dependencies:**
- F1.1 (Directory Creation) - needs ~/.ring/memory.db location

---

### Domain 3: Storage - YAML Handoffs

**Purpose:** Replace Markdown handoffs with token-efficient YAML format.

**Features:**

| Feature | Description | Priority |
|---------|-------------|----------|
| F3.1 - YAML Schema | Define handoff YAML structure | P0 |
| F3.2 - YAML Writer | Create handoffs in YAML format | P0 |
| F3.3 - YAML Reader | Parse YAML handoffs | P0 |
| F3.4 - Schema Validation | Validate against JSON Schema | P0 |
| F3.5 - Backward Compatibility | Read legacy Markdown handoffs | P1 |
| F3.6 - Migration Tool | Convert Markdown to YAML | P1 |
| F3.7 - Auto-Indexing | Index YAML handoffs in FTS5 | P1 |

**Scope:**
- IN: YAML format, validation, migration, FTS5 indexing
- OUT: Markdown generation, HTML export

**Dependencies:**
- F1.1 (Directory Creation) - needs ~/.ring/handoffs/ location
- Existing handoff-tracking skill - extends, not replaces

---

### Domain 4: Enhancement - Confidence Markers

**Purpose:** Add verification status to agent outputs to reduce false claims.

**Features:**

| Feature | Description | Priority |
|---------|-------------|----------|
| F4.1 - Marker Vocabulary | Define ✓/?/✗ symbols and meanings | P0 |
| F4.2 - Agent Output Schema | Add confidence section to schemas | P0 |
| F4.3 - Explorer Integration | Add markers to codebase-explorer | P0 |
| F4.4 - Evidence Chains | Track how conclusions were reached | P1 |
| F4.5 - Trust Calibration | Display confidence visually | P2 |

**Scope:**
- IN: Structured markers, evidence chains, schema updates
- OUT: Natural language epistemic markers, confidence scores

**Dependencies:**
- Existing agent output schemas (docs/AGENT_DESIGN.md)

---

### Domain 5: Enhancement - Skill Activation

**Purpose:** Auto-suggest relevant skills based on user prompt patterns.

**Features:**

| Feature | Description | Priority |
|---------|-------------|----------|
| F5.1 - Rules Schema | Define skill-rules.json structure | P0 |
| F5.2 - Keyword Matching | Match prompt keywords to skills | P0 |
| F5.3 - Intent Matching | Regex pattern matching | P1 |
| F5.4 - Activation Hook | UserPromptSubmit hook integration | P0 |
| F5.5 - Enforcement Levels | Block/suggest/warn behaviors | P0 |
| F5.6 - Negative Patterns | Exclude false positives | P1 |
| F5.7 - Project Overrides | Project rules override global | P1 |

**Scope:**
- IN: JSON Schema rules, three-tier enforcement, pattern matching
- OUT: Machine learning, semantic embeddings, user training

**Dependencies:**
- F1.1 (Directory Creation) - needs ~/.ring/skill-rules.json location
- Existing skill frontmatter (trigger/skip_when fields)

---

## Feature Relationships

### Dependency Graph

```
F1.1 (Directory Creation)
  ├─> F2.1 (Memory Database)
  │     └─> F2.2 (Memory Storage)
  │           └─> F2.3 (Memory Retrieval)
  │                 └─> F2.4 (Memory Awareness Hook)
  │                       └─> F2.5 (Memory Decay)
  │                             └─> F2.6 (Memory Expiration)
  │
  ├─> F3.1 (YAML Schema)
  │     ├─> F3.2 (YAML Writer)
  │     └─> F3.3 (YAML Reader)
  │           ├─> F3.4 (Schema Validation)
  │           ├─> F3.5 (Backward Compatibility)
  │           └─> F3.6 (Migration Tool)
  │                 └─> F3.7 (Auto-Indexing)
  │
  └─> F5.1 (Rules Schema)
        ├─> F5.2 (Keyword Matching)
        ├─> F5.3 (Intent Matching)
        └─> F5.4 (Activation Hook)
              ├─> F5.5 (Enforcement Levels)
              ├─> F5.6 (Negative Patterns)
              └─> F5.7 (Project Overrides)

F4.1 (Marker Vocabulary)
  └─> F4.2 (Agent Output Schema)
        └─> F4.3 (Explorer Integration)
              ├─> F4.4 (Evidence Chains)
              └─> F4.5 (Trust Calibration)
```

### Critical Path

The minimum viable feature set for Ring Continuity:

1. **F1.1** - Directory Creation (foundation)
2. **F3.1** - YAML Schema (handoff format)
3. **F3.2** - YAML Writer (handoff creation)
4. **F4.1** - Marker Vocabulary (confidence markers)
5. **F4.2** - Agent Output Schema (apply markers)
6. **F5.1** - Rules Schema (skill activation)
7. **F5.2** - Keyword Matching (basic activation)

**Estimated:** 2-3 days for MVP

### Optional Extensions

Can be deferred without breaking core functionality:

- F2.4 (Memory Awareness Hook)
- F2.5 (Memory Decay)
- F3.5 (Backward Compatibility)
- F5.3 (Intent Matching - regex)
- F5.6 (Negative Patterns)

---

## Domain Boundaries

### Physical Boundaries

| Domain | Files/Directories | Responsibility |
|--------|-------------------|----------------|
| **Foundation** | `~/.ring/`, `~/.ring/config.yaml` | Directory structure, config |
| **Memory** | `~/.ring/memory.db` | Persistent learning storage |
| **Handoffs** | `~/.ring/handoffs/`, `docs/handoffs/` | Session continuity |
| **Activation** | `~/.ring/skill-rules.json` | Skill routing |
| **Confidence** | Agent schemas in `docs/AGENT_DESIGN.md` | Output verification |

### Logical Boundaries

| Domain | Concerns | NOT Responsible For |
|--------|----------|---------------------|
| **Foundation** | Directory creation, config loading | Data storage, processing |
| **Memory** | Storage, retrieval, decay | Hook integration, display |
| **Handoffs** | YAML serialization, validation | Handoff creation logic (in skill) |
| **Activation** | Pattern matching, suggestion | Skill execution |
| **Confidence** | Schema definition, markers | Agent implementation |

---

## Integration Points

### Hook Integration Points

| Hook Event | Features Integrated | Purpose |
|------------|---------------------|---------|
| **SessionStart** | F1.2 (Config), F2.4 (Memory Awareness) | Load config, inject memories |
| **UserPromptSubmit** | F5.4 (Activation Hook) | Suggest relevant skills |
| **PostToolUse (Write)** | F3.7 (Auto-Indexing) | Index new handoffs |
| **PreCompact** | (Future) Auto-handoff creation | Save state before compact |
| **Stop** | (Future) Learning extraction | Extract session learnings |

### Skill Integration Points

| Skill | Features Integrated | Changes Required |
|-------|---------------------|------------------|
| **handoff-tracking** | F3.2 (YAML Writer), F3.4 (Validation) | Output YAML instead of Markdown |
| **continuity-ledger** | F3.2 (YAML Writer) | Optional YAML format |
| **artifact-query** | F2.3 (Memory Retrieval) | Query both artifacts and memories |
| **codebase-explorer** | F4.3 (Explorer Integration) | Add confidence markers to output |

### Agent Integration Points

| Agent | Features Integrated | Changes Required |
|-------|---------------------|------------------|
| **All exploration agents** | F4.2 (Agent Output Schema) | Add "Verification" section |
| **codebase-explorer** | F4.3, F4.4 (Markers + Evidence) | Include evidence chain |

---

## Feature Interactions

### Positive Interactions (Synergies)

| Feature A | Feature B | Synergy |
|-----------|-----------|---------|
| F2.3 (Memory Retrieval) | F5.4 (Activation Hook) | Memory informs which skills to suggest |
| F3.7 (Auto-Indexing) | F2.3 (Memory Retrieval) | Handoffs become searchable memories |
| F4.3 (Explorer Integration) | F2.2 (Memory Storage) | Verified findings stored as high-confidence memories |
| F5.5 (Enforcement Levels) | F4.1 (Marker Vocabulary) | Block-level skills can require verification |

### Negative Interactions (Conflicts)

| Feature A | Feature B | Conflict | Resolution |
|-----------|-----------|----------|------------|
| F3.5 (Backward Compat) | F3.2 (YAML Writer) | Dual format support | Indexer supports both |
| F2.5 (Memory Decay) | F2.2 (Memory Storage) | When to apply decay? | Apply on retrieval, not storage |
| F5.7 (Project Overrides) | F1.2 (Config Management) | Precedence rules | Document: project > global > default |

---

## Scope Visualization

### Feature Distribution by Phase

```
Phase 1 (Foundation):
├─ F1.1 ■■■■■■■■■■ Directory Creation
├─ F1.2 ■■■■■■■□□□ Config Management (partial)
└─ F1.3 ■■■■■□□□□□ Migration Utilities (basic)

Phase 2 (YAML Handoffs):
├─ F3.1 ■■■■■■■■■■ YAML Schema
├─ F3.2 ■■■■■■■■■■ YAML Writer
├─ F3.3 ■■■■■■■■■■ YAML Reader
├─ F3.4 ■■■■■■■■■■ Schema Validation
└─ F3.5 ■■■■■■■□□□ Backward Compatibility (partial)

Phase 3 (Confidence Markers):
├─ F4.1 ■■■■■■■■■■ Marker Vocabulary
├─ F4.2 ■■■■■■■■■■ Agent Output Schema
└─ F4.3 ■■■■■■■■■■ Explorer Integration

Phase 4 (Skill Activation):
├─ F5.1 ■■■■■■■■■■ Rules Schema
├─ F5.2 ■■■■■■■■■■ Keyword Matching
├─ F5.4 ■■■■■■■■■■ Activation Hook
├─ F5.5 ■■■■■■■■■■ Enforcement Levels
└─ F5.3 ■■■■■□□□□□ Intent Matching (defer)

Phase 5 (Persistent Memory):
├─ F2.1 ■■■■■■■■■■ Memory Database
├─ F2.2 ■■■■■■■■■■ Memory Storage
├─ F2.3 ■■■■■■■■■■ Memory Retrieval
├─ F2.4 ■■■■■■■□□□ Memory Awareness Hook
└─ F2.5 ■■■■■□□□□□ Memory Decay (defer)
```

### Risk by Feature

| Feature | Complexity | Risk Level | Mitigation |
|---------|------------|------------|------------|
| F1.1 | Low | Low | Straightforward directory creation |
| F2.1 | Medium | Medium | Use existing FTS5 patterns |
| F3.2 | Low | Low | YAML serialization is stdlib |
| F4.2 | Low | Low | Schema addition only |
| F5.4 | High | High | Complex hook timing, false positives |

---

## Gate 2 Validation Checklist

- [x] All features from PRD mapped to domains
- [x] Feature relationships documented (dependency graph)
- [x] Domain boundaries defined (physical and logical)
- [x] Feature interactions identified (synergies and conflicts)
- [x] Integration points specified (hooks, skills, agents)
- [x] Scope visualization provided (phase distribution)
- [x] Critical path identified for MVP
- [x] Risk assessment per feature

---

## Appendix: Feature Catalog

### Complete Feature List

| ID | Feature Name | Domain | Priority | Dependencies |
|----|--------------|--------|----------|--------------|
| F1.1 | Directory Creation | Foundation | P0 | None |
| F1.2 | Config Management | Foundation | P0 | F1.1 |
| F1.3 | Migration Utilities | Foundation | P1 | F1.1 |
| F1.4 | Cleanup Utilities | Foundation | P2 | F1.1 |
| F2.1 | Memory Database | Memory | P0 | F1.1 |
| F2.2 | Memory Storage | Memory | P0 | F2.1 |
| F2.3 | Memory Retrieval | Memory | P0 | F2.2 |
| F2.4 | Memory Awareness | Memory | P1 | F2.3 |
| F2.5 | Memory Decay | Memory | P2 | F2.3 |
| F2.6 | Memory Expiration | Memory | P2 | F2.5 |
| F3.1 | YAML Schema | Handoffs | P0 | F1.1 |
| F3.2 | YAML Writer | Handoffs | P0 | F3.1 |
| F3.3 | YAML Reader | Handoffs | P0 | F3.1 |
| F3.4 | Schema Validation | Handoffs | P0 | F3.3 |
| F3.5 | Backward Compatibility | Handoffs | P1 | F3.3 |
| F3.6 | Migration Tool | Handoffs | P1 | F3.5 |
| F3.7 | Auto-Indexing | Handoffs | P1 | F3.6 |
| F4.1 | Marker Vocabulary | Confidence | P0 | None |
| F4.2 | Agent Output Schema | Confidence | P0 | F4.1 |
| F4.3 | Explorer Integration | Confidence | P0 | F4.2 |
| F4.4 | Evidence Chains | Confidence | P1 | F4.3 |
| F4.5 | Trust Calibration | Confidence | P2 | F4.4 |
| F5.1 | Rules Schema | Activation | P0 | F1.1 |
| F5.2 | Keyword Matching | Activation | P0 | F5.1 |
| F5.3 | Intent Matching | Activation | P1 | F5.2 |
| F5.4 | Activation Hook | Activation | P0 | F5.2 |
| F5.5 | Enforcement Levels | Activation | P0 | F5.4 |
| F5.6 | Negative Patterns | Activation | P1 | F5.5 |
| F5.7 | Project Overrides | Activation | P1 | F1.2 |

**Total:** 27 features across 5 domains
