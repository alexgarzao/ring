# Ring Full Prompt Quality Audit

**Date:** 2026-02-27
**Scope:** 35 agents + 82 skills across 6 plugins
**Standard:** CLAUDE.md (Ring prompt engineering requirements)

---

## Executive Summary

| Plugin | Files | Avg Score | Critical | High | Medium | Low | Total Gaps |
|--------|-------|-----------|----------|------|--------|-----|------------|
| **default** | 34 | 96% | 0 | 2 | 2 | 0 | 4 |
| **dev-team** | 30 | 91% | 0 | 3 | 8 | 12 | 23 |
| **pm-team** | 17 | 76% | 13 | 37 | 7 | 1 | 58 |
| **pmo-team** | 15 | 77% | 8 | 14 | 16 | 0 | 38 |
| **finops-team** | 10 | 77% | 5 | 12 | 11 | 4 | 32 |
| **tw-team** | 10 | 87% | 0 | 3 | 7 | 2 | 12 |
| **TOTAL** | **116** | **84%** | **26** | **71** | **51** | **19** | **167** |

---

## Plugin-Level Findings

### default (96%) - Excellent

- All 8 agents fully compliant with CLAUDE.md required sections
- 26 skills with 100% YAML frontmatter compliance
- **HIGH**: `production-readiness-audit` (6632+ lines) and `release-guide-info` (2256 lines) should be modularized
- **MEDIUM**: 2 skills missing anti-pattern sections

### dev-team (91%) - Strong

- All 11 agents compliant (92.5% agents, 89.5% skills)
- Strong enforcement language (MUST, CANNOT, FORBIDDEN, STOP)
- Excellent semantic block tags (`<cannot_skip>`, `<block_condition>`, `<dispatch_required>`)
- **HIGH**: 2 agents missing "When Not Needed" sections; 1 skill has heavy shared-patterns reliance
- **MEDIUM**: Missing severity calibration tables in some skills

### pm-team (76%) - Needs Attention

- 4 agents fully compliant (92-95%)
- **Skills are the problem**: 11 of 13 skills lack formal required sections
- **CRITICAL**: `ring:using-pm-team` missing ALL 7 required sections (entry point skill)
- **CRITICAL**: `ring:pre-dev-research` missing 5 required sections (Gate 0 skill)
- Most skills have rationalization content but not in CLAUDE.md required format
- Weak language ("should" instead of "MUST") in several skills

### pmo-team (77%) - Needs Attention

- Best performers: `executive-reporter` (92%), `delivery-reporter` (88%)
- **CRITICAL**: Missing Severity Calibration in 5 skills
- **CRITICAL**: Missing "Cannot Be Overridden" in 7 skills
- **HIGH**: Missing Standards Loading in 2 agents
- Weakest: `pmo-retrospective` (65%), `dependency-mapping` (68%)

### finops-team (77%) - Needs Attention

- Best performer: `infrastructure-cost-estimator` (92%)
- **CRITICAL**: 5 gaps including missing Severity Calibration in 5 files
- **HIGH**: Missing Blocker Criteria in 2 skills
- Weakest: `regulatory-templates-gate2` and `gate3` (68%)
- Inconsistent terminology in rationalization tables

### tw-team (87%) - Good

- All 3 agents excellent (90-92%) with complete CLAUDE.md compliance
- Skills provide great reference documentation but lack behavioral enforcement
- **HIGH**: All 7 skills missing Blocker Criteria, Pressure Resistance, Anti-Rationalization tables
- No critical gaps

---

## Systemic Issues (Cross-Plugin)

### 1. Skills vs Agents Gap

Agents are consistently better than skills at CLAUDE.md compliance. Pattern across ALL plugins:

| Component | Avg Compliance | Typical Missing Sections |
|-----------|---------------|--------------------------|
| Agents | ~92% | Minor: When Not Needed, Standards Loading |
| Skills | ~76% | Major: Blocker Criteria, Severity Calibration, Pressure Resistance, Anti-Rationalization |

### 2. Most Common Missing Sections (in skills)

| Missing Section | Occurrences | Impact |
|----------------|-------------|--------|
| Severity Calibration | ~20 skills | Agents can't properly triage issues |
| Cannot Be Overridden | ~18 skills | Agents may waive non-negotiable requirements |
| Pressure Resistance | ~17 skills | Agents cave to user pressure to skip gates |
| Blocker Criteria | ~15 skills | Agents don't know when to STOP |
| Standards Loading | ~10 skills | Agents proceed without current standards |

### 3. Language Weakness Pattern

Several pm-team and pmo-team skills use weak language:
- "should" instead of "MUST"
- "recommended" instead of "REQUIRED"
- "consider" instead of "MANDATORY"
- Enforcement words in middle/end of sentences instead of beginning

---

## Priority Remediation Plan

### P0 - Critical (fix immediately)

1. **pm-team: `ring:using-pm-team`** — Missing ALL 7 required sections. Entry point skill.
2. **pm-team: `ring:pre-dev-research`** — Missing 5 required sections. Gate 0 skill.
3. **pmo-team: 5 skills** — Missing Severity Calibration (agents can't triage)

### P1 - High (fix this sprint)

4. **pm-team: 9 skills** — Add formal Blocker Criteria, Cannot Be Overridden, Pressure Resistance
5. **pmo-team: 7 skills** — Add Cannot Be Overridden sections
6. **finops-team: 2 skills** — Add Blocker Criteria
7. **tw-team: 7 skills** — Add behavioral enforcement sections
8. **default: 2 skills** — Modularize oversized skills (6632+ lines)

### P2 - Medium (fix next sprint)

9. **All plugins** — Standardize rationalization tables to 3-column format
10. **pm-team + pmo-team** — Strengthen language (should → MUST)
11. **All plugins** — Ensure enforcement words at beginning of instructions

---

## Methodology

Each plugin was audited by `ring:prompt-quality-reviewer` which:
1. WebFetched CLAUDE.md as the primary standard
2. Read every agent and skill file in the plugin
3. Checked for 7 required sections per CLAUDE.md Agent Modification Verification
4. Evaluated language strength and enforcement word positioning
5. Generated per-file scores and gap lists

**Scoring:** 15 pts each for Standards Loading, Blocker Criteria, Cannot Be Overridden, Pressure Resistance, Anti-Rationalization + 10 pts each for Severity Calibration, When Not Needed + 5 pts for strong language. Max = 100.
