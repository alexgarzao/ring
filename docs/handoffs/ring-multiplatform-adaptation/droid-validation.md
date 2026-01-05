# Handoff: Factory/Droid Adapter Validation

**Created:** 2026-01-04
**Session:** `droid-validation`
**Status:** READY_TO_START
**Parallel Session:** `opencode-validation` (separate handoff)

---

## Goal

Validate and improve the Factory AI (Droid) adapter by comparing the existing implementation against crawled Droid documentation. Ensure skills, agents (droids), commands, and hooks work correctly when installed to Factory.

**Done when:**
- All Droid docs reviewed for adapter accuracy
- Missing transformations identified and fixed
- Test installation verified (if Factory available)
- Gaps documented for future work

---

## Context

### Existing Implementation
- **Adapter:** `installer/ring_installer/adapters/factory.py`
- **Platform config:** `installer/ring_installer/manifests/platforms.json` (factory section)
- **Crawled docs:** `.references/droid/` (79 markdown files)
- **Index:** `.references/droid/INDEX.md`

### Key Factory/Droid Characteristics (from adapter)
- Install path: `~/.factory/`
- Terminology: `agents → droids`
- Directory structure: **flat** for droids (`~/.factory/droids/*.md`)
- Droid names: **lowercase, digits, `-`, `_` only** (NO colons!)
- Model format: full ID like `claude-opus-4-5-20251101` or `inherit`
- Hooks: Merged into `settings.json` (not separate hooks.json)
- Native format: **No** (requires transformation)

### Critical Transformation Rules
1. `ring-plugin:agent-name` → `ring-plugin-agent-name` (colons to hyphens)
2. Tool names: `WebFetch→FetchUrl`, `Bash→Execute`, `Write→Create`
3. Droids cannot spawn other droids (Task tool invalid)
4. Hooks go into settings.json, not hooks.json

---

## Phase 1: Documentation Review

### Files to Read and Compare

| Doc File | What to Validate | Adapter Location |
|----------|------------------|------------------|
| `.references/droid/cli-configuration-skills.md` | Skill format, discovery | `transform_skill()` |
| `.references/droid/cli-configuration-droids.md` | Droid frontmatter, tools | `transform_agent()`, `_transform_agent_frontmatter()` |
| `.references/droid/cli-configuration-commands.md` | Command format | `transform_command()` |
| `.references/droid/cli-configuration-hooks.md` | Hook events, settings.json | `transform_hook()`, `merge_hooks_to_settings()` |
| `.references/droid/cli-tools-*.md` | Tool names, capabilities | `_FACTORY_TOOL_NAME_MAP` |
| `.references/droid/cli-configuration-settings.md` | settings.json structure | `get_settings_path()` |

### Validation Checklist

```
[ ] Skills
    [ ] Skill path: ~/.factory/skills/<name>/SKILL.md
    [ ] Frontmatter fields match Factory expectations
    [ ] Tool references transformed (WebFetch→FetchUrl, etc.)
    [ ] Agent terminology replaced with droid

[ ] Droids (Agents)
    [ ] Flat directory structure: ~/.factory/droids/*.md
    [ ] Name format: ring-{plugin}-{name} (no colons)
    [ ] Model shorthand→full ID transformation accurate
    [ ] Tools list transformation (remove Task, map names)
    [ ] Description ≤500 chars enforced
    [ ] subagent_type preserved (Factory Task tool uses it)

[ ] Commands
    [ ] Command path: ~/.factory/commands/*.md
    [ ] argument-hint field mapped from args
    [ ] $ARGUMENTS placeholder usage
    [ ] Flat structure (no subdirectories)

[ ] Hooks
    [ ] hooks.json NOT installed as file
    [ ] Hooks merged into settings.json
    [ ] Hook script paths transformed
    [ ] enableHooks: true set in settings.json

[ ] Tools
    [ ] WebFetch → FetchUrl
    [ ] Bash → Execute
    [ ] Write → Create
    [ ] Task removed (droids can't spawn droids)
    [ ] MCP tool names: mcp__ → context7___
```

---

## Phase 2: Gap Analysis

### Questions to Answer

1. **Hook Events:** What events does Factory support?
   - Check `.references/droid/cli-configuration-hooks.md`
   - Compare to: SessionStart, Stop, PreCompact, UserPromptSubmit

2. **Droid Tools:** Complete list of valid Factory tools?
   - Check `.references/droid/cli-tools-*.md` files
   - Verify `_FACTORY_TOOL_NAME_MAP` is complete

3. **Model IDs:** Current valid model IDs for Factory?
   - Check `.references/droid/cli-configuration-droids.md`
   - Update `_FACTORY_MODEL_MAP` if needed

4. **Skill Discovery:** How does Factory discover skills?
   - Check `.references/droid/cli-configuration-skills.md`

5. **reasoningEffort:** Is this field supported? Values?
   - Check droid configuration docs

---

## Phase 3: Implementation Fixes

If gaps found, update:

1. `installer/ring_installer/adapters/factory.py` - Adapter logic
2. `installer/ring_installer/manifests/platforms.json` - Platform config
3. `installer/ring_installer/transformers/skill.py` - If Factory needs changes

### Testing Approach

```bash
# Dry-run installation to Factory
cd /Users/fredamaral/repos/lerianstudio/ring
python -m ring_installer.cli install --platform factory --dry-run --verbose

# If Factory is installed, actual test:
python -m ring_installer.cli install --platform factory --plugins ring-default

# Verify droid names are valid (no colons)
ls ~/.factory/droids/

# Check settings.json has hooks
cat ~/.factory/settings.json | jq '.hooks'
```

---

## Key Files

| Purpose | Path |
|---------|------|
| Factory adapter | `installer/ring_installer/adapters/factory.py` |
| Platform manifest | `installer/ring_installer/manifests/platforms.json` |
| Crawled docs | `.references/droid/` |
| Skill transformer | `installer/ring_installer/transformers/skill.py` |
| Base adapter | `installer/ring_installer/adapters/base.py` |

---

## Constraints

- Droid names MUST NOT contain colons (Factory uses colons for custom: prefix)
- Droids CANNOT use Task tool (can't spawn other droids)
- Hooks MUST go into settings.json, not hooks.json
- Preserve subagent_type field (Factory Task tool uses it)
- Description max 500 characters

---

## Output Expected

1. **Validation Report:** Table of what matches vs what differs
2. **Code Changes:** PRs or commits fixing any issues
3. **Tool Map Update:** Complete mapping of Claude→Factory tools
4. **Model Map Update:** Current valid model IDs
5. **Known Limitations:** List of Ring features that won't work on Factory

---

## Critical Transformations Reference

### Terminology
| Ring | Factory |
|------|---------|
| agent | droid |
| agents | droids |
| hook | trigger |

### Tool Names
| Claude Code | Factory |
|-------------|---------|
| WebFetch | FetchUrl |
| Bash | Execute |
| Write | Create |
| MultiEdit | Edit |
| Task | ❌ (invalid) |

### Model IDs
| Shorthand | Factory Full ID |
|-----------|-----------------|
| opus | claude-opus-4-5-20251101 |
| sonnet | claude-sonnet-4-5-20250929 |
| haiku | claude-haiku-4-5-20250929 |
| inherit | inherit |

---

## Notes

- Factory adapter is the most complex due to extensive transformations
- The `_replace_agent_references()` method handles terminology throughout content
- Protected regions (code blocks, URLs) are preserved during replacement
- `requires_flat_components()` returns True for agents, commands, skills
