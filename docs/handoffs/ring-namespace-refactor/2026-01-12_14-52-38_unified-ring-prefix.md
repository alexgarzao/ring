---
date: 2026-01-12T17:52:38Z
session_name: ring-namespace-refactor
git_commit: 945718fb3f23a713572911c28394dbab57da01cd
branch: main
repository: LerianStudio/ring
topic: "Unified ring: Namespace Refactoring"
tags: [refactoring, naming-convention, namespace, ring-prefix]
status: in_progress
outcome: UNKNOWN
root_span_id:
turn_span_id:
---

# Handoff: Unified ring: Namespace Refactoring

## Task Summary

Comprehensive refactoring to standardize all Ring components (skills, agents, commands) to use a unified `ring:` namespace prefix instead of plugin-specific prefixes (`ring-default:`, `ring-dev-team:`, etc.).

**Status:** IN_PROGRESS - All renaming complete, commit pending

**Completed:**
1. ✅ Renamed all frontmatter `name:` fields across 109 files to use `ring:[name]` format
2. ✅ Updated all internal references (Skill tool, subagent_type, etc.) to use `ring:` prefix
3. ✅ Updated CLAUDE.md Section 4 from "Fully Qualified Names" to "Unified Ring Namespace"
4. ✅ Added finops-team plugin components (8 files renamed)

**Pending:**
- Create git commit for all changes
- User was reviewing changes before commit

## Critical References

- `CLAUDE.md:33-38` - New unified namespace rules (Section 4)
- `CLAUDE.md:521-528` - Updated naming conventions for invocation

## Recent Changes

### Phase 1: Frontmatter Renames (101 files)
All skills, agents, and commands across 4 plugins renamed:
- `default/` - 28 skills, 7 agents, 14 commands
- `dev-team/` - 9 skills, 9 agents, 5 commands
- `pm-team/` - 10 skills, 3 agents, 2 commands
- `tw-team/` - 7 skills, 3 agents, 3 commands

### Phase 2: Internal Reference Updates (54 files modified)
- Skill tool references: `Use Skill tool: X` → `Use Skill tool: ring:X`
- Agent references: `subagent_type="X"` → `subagent_type="ring:X"`
- Old plugin prefixes: `ring-default:X` → `ring:X`

### Phase 3: finops-team Plugin (8 files)
- 2 agents: finops-analyzer, finops-automation
- 6 skills: regulatory-templates, regulatory-templates-setup, regulatory-templates-gate1/2/3, using-finops-team

## Learnings

### What Worked
- **Parallel agent dispatch**: Using 4 agents simultaneously (one per plugin) reduced rename time by ~75%
- **Bash with perl for bulk updates**: `perl -pi -e 's/pattern/replacement/'` was efficient for mass renames
- **Verification grep patterns**: Quick verification with `grep -r "^name: ring:" | wc -l` confirmed changes

### What Failed
- **Initial exploration agent timeout**: First agent exploration hit token limits; solved by splitting into focused queries
- **Skill invocation with new prefix**: `ring:handoff-tracking` didn't work yet as skill registry not updated; fallback to bare name worked

### Key Decisions
- **Decision:** Use unified `ring:` prefix for ALL components (no plugin differentiation)
  - Alternatives: Keep `ring-{plugin}:` format, use no prefix
  - Reason: Simplifies invocation, plugin routing handled internally, cleaner UX

- **Decision:** Update CLAUDE.md rules to mark old format as deprecated
  - Reason: Documentation must reflect new standard; old examples marked with ❌

## Files Modified

### Documentation (5 files)
- `CLAUDE.md` - MODIFIED: Section 4 renamed, examples updated throughout
- `ARCHITECTURE.md` - MODIFIED: Updated invocation examples
- `MANUAL.md` - MODIFIED: Updated invocation format
- `docs/PROMPT_ENGINEERING.md` - MODIFIED: Updated examples
- `docs/WORKFLOWS.md` - MODIFIED: Updated skill references

### Default Plugin (21 files)
- `default/agents/*.md` (2) - MODIFIED: name field
- `default/commands/*.md` (12) - MODIFIED: name field + skill references
- `default/skills/*/SKILL.md` (4) - MODIFIED: name field + internal references
- `default/skills/shared-patterns/*.md` (1) - MODIFIED: agent references

### Dev-team Plugin (18 files)
- `dev-team/agents/*.md` (9) - MODIFIED: name field + self-references
- `dev-team/commands/*.md` (3) - MODIFIED: name field + skill references
- `dev-team/skills/*/SKILL.md` (7) - MODIFIED: name field + internal references

### PM-team Plugin (4 files)
- `pm-team/agents/*.md` (3) - MODIFIED: name field
- `pm-team/skills/using-pm-team/SKILL.md` - MODIFIED: name field + references

### TW-team Plugin (6 files)
- `tw-team/agents/*.md` (3) - MODIFIED: name field
- `tw-team/commands/*.md` (3) - MODIFIED: name field + skill references

### Finops-team Plugin (8 files - NEW PLUGIN ADDED)
- `finops-team/agents/*.md` (2) - MODIFIED: name field
- `finops-team/skills/*/SKILL.md` (6) - MODIFIED: name field

### Infrastructure
- `.claude-plugin/marketplace.json` - MODIFIED: finops-team plugin added
- `install-ring.sh` - MODIFIED: Updated for new plugin
- `README.md` - MODIFIED: Updated plugin list

## Action Items & Next Steps

1. **IMMEDIATE: Create commit** - All changes ready, user was reviewing before commit
   ```bash
   git add -A
   git commit -S -m "refactor(naming): standardize all references to unified ring: namespace" \
     -m "Updates all skills, agents, and commands to use ring: prefix. Deprecates plugin-specific prefixes (ring-default:, ring-dev-team:, etc.)." \
     --trailer "X-Lerian-Ref: 0x1"
   ```

2. **Handle untracked directories:**
   - `finops-team/` - New plugin, needs to be added
   - `.archive/` - Archived plugins, decide whether to include

3. **Update skill registry** - Skills currently invoked by bare name; may need registry update for `ring:` prefix invocation

4. **Test skill invocation** - Verify `/commit`, `/codereview`, etc. work with new naming

## Other Notes

### Git Status at Handoff
- 56 modified files (staged changes pending)
- `finops-team/` untracked (new plugin)
- `.archive/` untracked (archived plugins)

### Verification Commands
```bash
# Count files with ring: prefix
grep -r "^name: ring:" --include="*.md" default/ dev-team/ pm-team/ tw-team/ finops-team/ | wc -l
# Expected: 109

# Check for old plugin prefixes (should be 0 outside deprecated examples)
grep -r "ring-default:\|ring-dev-team:" --include="*.md" | grep -v "deprecated\|❌" | wc -l
# Expected: 0
```

### Commit Proposal
The user was presented with commit options when handoff was requested:
- Single commit (recommended) - All namespace changes in one refactor
- Two commits - 1) Namespace refactor, 2) Add finops-team
- Include .archive/ option
