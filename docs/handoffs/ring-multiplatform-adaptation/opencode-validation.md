# Handoff: OpenCode Adapter Validation

**Created:** 2026-01-04
**Session:** `opencode-validation`
**Status:** READY_TO_START
**Parallel Session:** `droid-validation` (separate handoff)

---

## Goal

Validate and improve the OpenCode adapter by comparing the existing implementation against crawled OpenCode documentation. Ensure skills, agents, commands, and hooks work correctly when installed to OpenCode.

**Done when:**
- All OpenCode docs reviewed for adapter accuracy
- Missing transformations identified and fixed
- Test installation verified (if OpenCode available)
- Gaps documented for future work

---

## Context

### Existing Implementation
- **Adapter:** `installer/ring_installer/adapters/opencode.py`
- **Platform config:** `installer/ring_installer/manifests/platforms.json` (opencode section)
- **Crawled docs:** `.references/opencode/` (34 markdown files)
- **Index:** `.references/opencode/INDEX.md`

### Key OpenCode Characteristics (from adapter)
- Install path: `~/.config/opencode/`
- Directory names: **singular** (`agent/`, `command/`, `skill/`, `hook/`)
- Tool names: **lowercase** (`bash`, `read`, `write`, `edit`, `glob`, `grep`)
- Model format: `provider/model-id` (e.g., `anthropic/claude-sonnet-4-5`)
- Config file: `opencode.json` or `opencode.jsonc`
- Native format: **Yes** (minimal transformation needed)

---

## Phase 1: Documentation Review

### Files to Read and Compare

| Doc File | What to Validate | Adapter Location |
|----------|------------------|------------------|
| `.references/opencode/skills.md` | Skill frontmatter fields | `transform_skill()` |
| `.references/opencode/agents.md` | Agent frontmatter fields, modes | `transform_agent()`, `_transform_agent_frontmatter()` |
| `.references/opencode/slash-commands.md` | Command format, argument-hint | `transform_command()` |
| `.references/opencode/hooks.md` | Hook events, format | `transform_hook()` |
| `.references/opencode/tools.md` | Tool names, availability | `_OPENCODE_TOOL_NAME_MAP` |
| `.references/opencode/configuration.md` | Config file structure | `get_config_path()` |

### Validation Checklist

```
[ ] Skills
    [ ] Frontmatter fields match OpenCode expectations
    [ ] Skill discovery path correct (skill/<name>/SKILL.md)
    [ ] No unsupported fields being passed through

[ ] Agents
    [ ] mode field (primary, subagent, all) handled correctly
    [ ] model format transformation accurate
    [ ] tools object format (not array) conversion working
    [ ] Agent discovery path correct (agent/*.md)

[ ] Commands
    [ ] argument-hint field mapped correctly
    [ ] Command discovery path correct (command/*.md)
    [ ] $ARGUMENTS placeholder if needed

[ ] Hooks
    [ ] Hook events match OpenCode's supported events
    [ ] Path transformations correct
    [ ] Integration with opencode.json if needed

[ ] Tools
    [ ] All Claude Code tool names mapped to OpenCode equivalents
    [ ] No invalid tool references in transformed content
```

---

## Phase 2: Gap Analysis

### Questions to Answer

1. **Hook Support:** Does OpenCode support the same hook events as Claude Code?
   - SessionStart, Stop, PreCompact, UserPromptSubmit?
   - Check `.references/opencode/hooks.md`

2. **Skill Discovery:** Does OpenCode auto-discover skills or require registration?
   - Check `.references/opencode/skills.md`

3. **Agent Modes:** What agent modes does OpenCode support?
   - Check `.references/opencode/agents.md`

4. **MCP Integration:** Does OpenCode support MCP servers?
   - Check `.references/opencode/mcp*.md` files

5. **Tool Permissions:** How does OpenCode handle tool permissions?
   - Check `.references/opencode/tools.md`

---

## Phase 3: Implementation Fixes

If gaps found, update:

1. `installer/ring_installer/adapters/opencode.py` - Adapter logic
2. `installer/ring_installer/manifests/platforms.json` - Platform config
3. `installer/ring_installer/transformers/skill.py` - If OpenCode needs special skill transform

### Testing Approach

```bash
# Dry-run installation to OpenCode
cd /Users/fredamaral/repos/lerianstudio/ring
python -m ring_installer.cli install --platform opencode --dry-run --verbose

# If OpenCode is installed, actual test:
python -m ring_installer.cli install --platform opencode --plugins ring-default
```

---

## Key Files

| Purpose | Path |
|---------|------|
| OpenCode adapter | `installer/ring_installer/adapters/opencode.py` |
| Platform manifest | `installer/ring_installer/manifests/platforms.json` |
| Crawled docs | `.references/opencode/` |
| Skill transformer | `installer/ring_installer/transformers/skill.py` |
| Base adapter | `installer/ring_installer/adapters/base.py` |

---

## Constraints

- Do NOT modify Claude Code behavior
- Preserve backward compatibility with existing installations
- Document any OpenCode limitations that affect Ring features
- Follow existing adapter patterns

---

## Output Expected

1. **Validation Report:** Table of what matches vs what differs
2. **Code Changes:** PRs or commits fixing any issues
3. **Documentation:** Update adapter docstrings if behavior changes
4. **Known Limitations:** List of Ring features that won't work on OpenCode

---

## Notes

- OpenCode is marked as `native_format: true` in platforms.json
- The `_strip_model_requirement_section()` method removes Claude-specific model checks
- Tool names use lowercase in OpenCode vs capitalized in Claude Code
