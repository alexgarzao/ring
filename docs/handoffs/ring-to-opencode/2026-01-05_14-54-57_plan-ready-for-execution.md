# Handoff: Ring to OpenCode Conversion

## Metadata
- **Created:** 2026-01-05T14:54:57Z
- **Branch:** main
- **Commit:** d2e3d3681d689b60fd359a1fca37e661fdb9d391
- **Status:** READY_FOR_EXECUTION
- **Session Type:** Planning + Review

---

## Task Summary

### What Was Done
1. **Explored OpenCode documentation** (`.references/opencode/`) to understand:
   - Skills: `.opencode/skill/<name>/SKILL.md` with limited frontmatter (5 fields only)
   - Agents: `.opencode/agent/<name>.md` with mode/model/tools/permission fields
   - Commands: `.opencode/command/<name>.md` with $ARGUMENTS for user input
   - Plugins: TypeScript event-driven (replaces bash hooks)

2. **Analyzed existing installer** (`installer/`) to understand:
   - Python adapter pattern with 6 platforms
   - OpenCode adapter exists but incomplete
   - Transformation rules for frontmatter/model/tools

3. **Created comprehensive implementation plan** with 49 tasks across 8 phases

4. **Ran 3-reviewer code review** on the plan:
   - Code Quality: Found 4 High issues (task granularity, missing examples)
   - Business Logic: Found 2 Critical + 3 High (metadata type mismatch, shared-patterns missing)
   - Security: Found 3 High (overly permissive bash, missing .env protection)

5. **Fixed all Critical and High issues** in the plan

### Current Status
- Plan is **COMPLETE and REVIEWED**
- Ready for execution (49 tasks, ~5-7 hours)
- No code has been written yet - only the plan document

---

## Critical References

### MUST READ to continue:
1. **`docs/plans/2026-01-04-ring-to-opencode-conversion.md`** - The complete implementation plan (1800+ lines)
2. **`.references/opencode/skills.md`** - OpenCode skills documentation
3. **`.references/opencode/agents.md`** - OpenCode agents documentation
4. **`.references/opencode/plugins.md`** - OpenCode plugins (replaces hooks)

### Key Transformation Rules (from plan):
| Ring Field | OpenCode Field | Action |
|------------|----------------|--------|
| Complex fields (compliance_rules, prerequisites) | Body sections | Move to markdown |
| `model: opus` | `model: anthropic/claude-opus-4-5` | Convert shorthand |
| `type: specialist` | `mode: subagent` | Convert type to mode |
| Model Requirement section | N/A | **STRIP entirely** |
| Hooks (bash) | Plugins (TypeScript) | Rewrite in TS |

---

## Recent Changes

### Files Modified This Session:
1. **`docs/plans/2026-01-04-ring-to-opencode-conversion.md`** - Created and refined
   - Lines 50-72: Updated Skills Transformation table with metadata limitation note
   - Lines 169-220: Updated opencode.json with secure bash whitelist
   - Lines 296-340: Added Task 2.0 (shared-patterns directory)
   - Lines 594-721: Split Task 2.8 into 4 batches (2.8-2.11)
   - Lines 725-766: Added Task 2.12 (path reference updates)
   - Lines 773-836: Added bash whitelist to codebase-explorer
   - Lines 1183-1253: Added Task 5.5 (.env protection plugin)
   - Lines 1431-1556: Split Task 6.4 into 4 batches (6.4a-d)
   - Lines 1809-1836: Updated summary table

### Files Created:
- `docs/plans/2026-01-04-ring-to-opencode-conversion.md` (new)
- `docs/handoffs/ring-to-opencode/` (this directory)

---

## Key Learnings

### What Worked Well
1. **3-phase exploration** - Understanding OpenCode, then installer, then mapping strategy
2. **Parallel reviewer dispatch** - All 3 reviewers found different issues
3. **Immediate plan fixes** - Addressing issues before execution saves rework

### What Failed / Needed Iteration
1. **Initial plan had oversized batch tasks** - Task 2.8 with 21 skills was too large
2. **Security review caught permission gaps** - Global `bash: allow` is dangerous
3. **Business logic found metadata limitation** - OpenCode metadata is string-only, not object

### Decisions Made
1. **Separate folder approach** - `opencode/` directory, not real-time transformation
2. **Manual conversion (Option A)** - High quality over automation
3. **Complex fields to body** - compliance_rules, prerequisites go to markdown sections
4. **Security-first permissions** - Bash whitelist, .env protection plugin

---

## Action Items for Next Session

### Immediate (Start Here)
1. **Read the plan thoroughly**: `docs/plans/2026-01-04-ring-to-opencode-conversion.md`
2. **Execute Phase 1** (3 tasks): Create directory structure
3. **Execute Phase 2** (13 tasks): Convert core skills

### Execution Command
```
/execute-plan docs/plans/2026-01-04-ring-to-opencode-conversion.md
```

Or manually follow the plan task-by-task.

### Phase Overview
| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| 1 | 3 | 15 min |
| 2 | 13 | 90 min |
| CR1 | 1 | 20 min |
| 3 | 5 | 45 min |
| 4 | 6 | 45 min |
| CR2 | 1 | 20 min |
| 5 | 5 | 45 min |
| 6 | 8 | 60 min |
| CR3 | 1 | 20 min |
| 7 | 2 | (optional) |
| 8 | 4 | 30 min |

---

## Open Questions

1. **Plugin package name** - Plan uses `@opencode-ai/plugin` but verify this exists
2. **PM-team and TW-team** - Phase 7 is optional, decide if needed
3. **Testing strategy** - How to verify OpenCode components work (need OpenCode installed)

---

## Resume Command

```
/resume-handoff docs/handoffs/ring-to-opencode/2026-01-05_14-54-57_plan-ready-for-execution.md
```
