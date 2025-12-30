---
name: release-guide
description: Generate an Ops Update Guide from git diff between two refs
argument-hint: "<base-ref> <target-ref> [--version <version>] [--lang <en|pt-br|both>]"
---

Generate an internal Operations-facing update/migration guide based on git diff analysis between two refs.

## Usage

```
/release-guide <base-ref> <target-ref> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<base-ref>` | Yes | Starting point (branch, tag, or SHA) |
| `<target-ref>` | Yes | Ending point (branch, tag, or SHA) |
| `--version <version>` | No | Explicit version number (auto-detected from tags if not provided) |
| `--lang <en\|pt-br\|both>` | No | Output language(s), default: `en` |
| `--mode <strict\|clone>` | No | Execution mode, default: `strict` (STRICT_NO_TOUCH) |

## Examples

### Basic usage (main to HEAD)

```
/release-guide main HEAD
```

### Between tags (version auto-detected)

```
/release-guide <previous-tag> <current-tag>
```

### With explicit version

```
/release-guide main HEAD --version <version>
```

### Both languages

```
/release-guide <base-ref> <target-ref> --lang both
```

### Portuguese only

```
/release-guide <base-ref> <target-ref> --lang pt-br
```

## Output

The command generates:
1. **Preview summary** - Shows configuration and change counts
2. **User confirmation** - Waits for approval before writing
3. **Release guide file(s)** - Written to `notes/releases/`

**File naming:**
- With version: `{DATE}_{REPO}-{VERSION}.md`
- Without version: `{DATE}_{REPO}-{BASE}-to-{TARGET}.md`
- Portuguese suffix: `_pt-br.md`

## Process

The command follows the `version-release-info` skill workflow:

1. **Resolve refs** - Verify both refs exist
2. **Tag detection** - Auto-extract version from tags
3. **Commit analysis** - Parse commit messages for context
4. **Diff analysis** - Analyze changes between refs
5. **Build inventory** - Categorize changes
6. **Preview** - Show summary for confirmation
7. **Generate guide** - Write file(s) to disk

## Related

| Command/Skill | Relationship |
|---------------|--------------|
| `version-release-info` skill | Underlying skill with full workflow |
| `/commit` | Use after release guide to commit changes |
| `finishing-a-development-branch` | Complementary workflow for branch completion |

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: version-release-info
```

The skill contains the complete workflow with:
- Tag auto-detection and version resolution
- Commit log analysis for context
- Dual language support (English/Portuguese)
- Preview step before saving
- Anti-rationalization table
- Quality checklist
