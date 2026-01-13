# Ring Continuity - Product Requirements Document (Gate 1)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Stakeholder:** Ring Plugin Users & Maintainers

---

## Problem Statement

### The Problem

AI coding assistants like Claude Code suffer from **session amnesia** - they cannot remember learnings, preferences, or context across sessions. This leads to:

1. **Repeated explanations:** Users re-explain the same patterns, preferences, and project context every session
2. **Repeated mistakes:** AI makes the same errors it learned to avoid in previous sessions
3. **Wasted tokens:** Handoff documents consume ~2000 tokens in Markdown format when ~400 would suffice
4. **Manual skill invocation:** Users must remember and manually invoke relevant skills instead of automatic suggestion
5. **Unverified claims:** AI makes assertions without clear indication of verification status, leading to hallucination-based errors

### Who Is Affected

| User Type | Pain Point | Frequency |
|-----------|------------|-----------|
| **Daily Ring users** | Re-explaining preferences every session | Daily |
| **Long-running project teams** | Lost context between work sessions | Weekly |
| **Multi-project developers** | No cross-project learning transfer | Ongoing |
| **New Ring adopters** | Discovering which skills to use | Every task |

### Business Value

| Metric | Current State | Target State | Value |
|--------|---------------|--------------|-------|
| **Session startup time** | 5-10 min context rebuild | <1 min auto-load | 80% reduction |
| **Handoff token cost** | ~2000 tokens | ~400 tokens | 5x efficiency |
| **Skill discovery** | Manual lookup | Auto-suggest | Better adoption |
| **False claim rate** | ~80% (unverified grep) | <20% (with markers) | 4x improvement |

---

## Vision

**Ring Continuity** transforms Ring from a stateless skill library into an **intelligent, learning assistant** that:

- **Remembers** user preferences, project patterns, and successful approaches
- **Learns** from failures and avoids repeating mistakes
- **Suggests** relevant skills based on user intent
- **Verifies** claims with explicit confidence markers
- **Persists** state efficiently across sessions and projects

All while maintaining Ring's core principle: **lightweight, accessible, no heavy infrastructure**.

---

## User Stories

### Epic 1: Global Ring Directory (~/.ring/)

**US-1.1: As a Ring user, I want a global ~/.ring/ directory so that my preferences and learnings persist across all projects.**

- Acceptance Criteria:
  - [ ] `~/.ring/` directory is created on first Ring use
  - [ ] Directory contains `config.yaml`, `memory.db`, `skill-rules.json`
  - [ ] Works alongside project-local `.ring/` directory
  - [ ] Migration path from existing `.ring/` artifacts

**US-1.2: As a Ring user, I want my global settings to be separate from project-specific settings so that I can have different behaviors per project.**

- Acceptance Criteria:
  - [ ] Global `~/.ring/config.yaml` for user preferences
  - [ ] Project `.ring/config.yaml` overrides global settings
  - [ ] Clear precedence: project > global > defaults

### Epic 2: YAML Handoff Format

**US-2.1: As a Ring user, I want handoffs in YAML format so that they consume fewer tokens and can be machine-parsed.**

- Acceptance Criteria:
  - [ ] New `/create-handoff` produces YAML format
  - [ ] YAML handoffs are ~400 tokens (vs ~2000 markdown)
  - [ ] Schema validation ensures required fields present
  - [ ] `/resume-handoff` reads both YAML and legacy Markdown

**US-2.2: As a Ring user, I want handoffs to be auto-indexed so that I can search past sessions.**

- Acceptance Criteria:
  - [ ] PostToolUse hook indexes YAML handoffs
  - [ ] FTS5 search via `/query-artifacts`
  - [ ] BM25 ranking for relevance

### Epic 3: Confidence Markers

**US-3.1: As a Ring user, I want agent outputs to include confidence markers so that I know which claims are verified vs assumed.**

- Acceptance Criteria:
  - [ ] Agents output `✓ VERIFIED` for claims backed by file reads
  - [ ] Agents output `? INFERRED` for claims based on grep/search
  - [ ] Agents output `✗ UNCERTAIN` for unverified assumptions
  - [ ] Confidence markers appear in Findings/Claims sections

**US-3.2: As a Ring user, I want the codebase-explorer to distinguish verified facts from inferences so that I can trust its findings.**

- Acceptance Criteria:
  - [ ] Explorer agent marks each finding with confidence level
  - [ ] Evidence chain shows how conclusion was reached
  - [ ] Human review flag for low-confidence claims

### Epic 4: Skill Activation Rules

**US-4.1: As a Ring user, I want skills to be automatically suggested based on my prompt so that I don't have to remember all skill names.**

- Acceptance Criteria:
  - [ ] `~/.ring/skill-rules.json` defines activation patterns
  - [ ] UserPromptSubmit hook matches prompt against rules
  - [ ] Matching skills appear as suggestions in response
  - [ ] Three enforcement levels: block, suggest, warn

**US-4.2: As a Ring user, I want to customize which skills are suggested for which patterns so that I can tune the system to my workflow.**

- Acceptance Criteria:
  - [ ] User can edit `skill-rules.json` directly
  - [ ] Project-level rules override global rules
  - [ ] Schema validation prevents invalid rules

### Epic 5: Persistent Memory System

**US-5.1: As a Ring user, I want the AI to remember what worked and what failed so that it doesn't repeat mistakes.**

- Acceptance Criteria:
  - [ ] Learnings stored in `~/.ring/memory.db` (SQLite + FTS5)
  - [ ] 7 learning types: WORKING_SOLUTION, FAILED_APPROACH, etc.
  - [ ] Memory recalled at session start via hook
  - [ ] Relevant memories injected into context

**US-5.2: As a Ring user, I want to store user preferences that persist across sessions so that the AI adapts to my style.**

- Acceptance Criteria:
  - [ ] USER_PREFERENCE learning type for style/preferences
  - [ ] Preferences searchable and retrievable
  - [ ] Explicit `/remember` command to store preferences
  - [ ] Automatic preference extraction from sessions

**US-5.3: As a Ring user, I want memories to have expiration and relevance decay so that the system doesn't get cluttered with stale information.**

- Acceptance Criteria:
  - [ ] Memories have `created_at` and `accessed_at` timestamps
  - [ ] Unused memories decay in relevance over time
  - [ ] Optional `expires_at` for temporary learnings
  - [ ] Maintenance task to prune old, low-relevance memories

---

## Acceptance Criteria Summary

### Must Have (P0)

| ID | Requirement | Validation |
|----|-------------|------------|
| P0-1 | `~/.ring/` directory created on first use | Directory exists with config.yaml |
| P0-2 | YAML handoff format produces <500 tokens | Token count measured |
| P0-3 | Confidence markers in explorer agent output | Markers visible in output |
| P0-4 | skill-rules.json with keyword matching | Skills suggested on matching prompts |
| P0-5 | SQLite FTS5 memory storage | Memories searchable via FTS5 |

### Should Have (P1)

| ID | Requirement | Validation |
|----|-------------|------------|
| P1-1 | Memory awareness hook at session start | Relevant memories injected |
| P1-2 | Intent pattern matching (regex) in skill rules | Patterns match fuzzy intents |
| P1-3 | Legacy Markdown handoff migration | Old handoffs still readable |
| P1-4 | Project-level config overrides | Project settings take precedence |

### Nice to Have (P2)

| ID | Requirement | Validation |
|----|-------------|------------|
| P2-1 | Memory relevance decay over time | Old unused memories deprioritized |
| P2-2 | `/remember` command for explicit storage | Command stores user preference |
| P2-3 | Automatic preference extraction | Preferences detected from behavior |
| P2-4 | Cross-project memory queries | Memories from other projects searchable |

---

## Success Metrics

### Quantitative Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Handoff token count** | ~2000 | <500 | Token counter on handoff |
| **Session startup context** | Manual rebuild | Auto-injected | User feedback |
| **Skill discovery rate** | Manual lookup | 80% auto-suggested | Usage analytics |
| **False claim rate** | ~80% unverified | <20% | Sample audit |

### Qualitative Metrics

| Metric | Measurement Method |
|--------|-------------------|
| **User satisfaction** | Feedback in GitHub issues |
| **Adoption rate** | ~/.ring/ directory creation stats |
| **Workflow improvement** | Before/after user testimonials |

---

## Out of Scope

### Explicitly NOT Included

| Item | Reason |
|------|--------|
| **PostgreSQL/pgvector** | Conflicts with "lightweight, no dependencies" principle |
| **Cloud sync** | Privacy concerns, complexity |
| **Multi-user collaboration** | Ring is single-user tool |
| **Real-time memory updates** | Batch updates at session boundaries sufficient |
| **Embedding-based semantic search** | FTS5 with BM25 sufficient for MVP |
| **GUI configuration** | CLI/file-based config is sufficient |

### Future Considerations (Post-MVP)

| Item | Potential Value |
|------|-----------------|
| **Optional embedding support** | Better semantic search for power users |
| **Memory export/import** | Backup and portability |
| **Memory visualization** | Understanding what Ring remembers |
| **Collaborative memory** | Team-shared learnings |

---

## Constraints

### Technical Constraints

| Constraint | Impact |
|------------|--------|
| **No new runtime dependencies** | Must use Python stdlib (sqlite3, json, yaml via PyYAML) |
| **Bash hooks** | Performance-sensitive hooks stay in bash |
| **Backward compatibility** | Existing handoffs must remain readable |
| **Cross-platform** | macOS and Linux support required |

### Business Constraints

| Constraint | Impact |
|------------|--------|
| **Open source** | All code MIT licensed |
| **Self-contained** | No external services required |
| **Privacy-first** | All data stays local |

---

## Dependencies

### Internal Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Existing handoff tracking skill | Stable | Must extend, not replace |
| Existing FTS5 infrastructure | Stable | Reuse patterns |
| Hook system | Stable | Add new hooks |
| Agent output schema | Stable | Add confidence section |

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Memory scripts |
| SQLite | 3.35+ | FTS5 support |
| PyYAML | >=6.0 | YAML parsing |
| Bash | 4.0+ | Hook scripts |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **FTS5 insufficient for semantic search** | Medium | Medium | Design for optional embedding layer |
| **Memory bloat over time** | Medium | Low | Decay mechanism, expiration |
| **Skill activation false positives** | High | Low | Negative patterns, confidence thresholds |
| **Breaking existing handoffs** | Low | High | Dual-format support, migration tool |
| **Performance impact from hooks** | Medium | Medium | Timeout limits, async processing |

---

## Gate 1 Validation Checklist

- [x] Problem is clearly defined (session amnesia, repeated context, wasted tokens)
- [x] User value is measurable (80% startup time reduction, 5x token efficiency)
- [x] Acceptance criteria are testable (specific validation per requirement)
- [x] Scope is explicitly bounded (out of scope section)
- [x] Success metrics defined (quantitative and qualitative)
- [x] Risks identified with mitigations
- [x] Dependencies documented

---

## Appendix: Glossary

| Term | Definition |
|------|------------|
| **Handoff** | Document capturing session state for resume |
| **Ledger** | In-session state that survives /clear |
| **Memory** | Persistent learning stored in SQLite |
| **Skill activation** | Automatic suggestion of relevant skills |
| **Confidence marker** | Indicator of verification status (✓/?/✗) |
| **FTS5** | SQLite Full-Text Search version 5 |
| **BM25** | Best Match 25 ranking algorithm |
