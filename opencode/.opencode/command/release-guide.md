---
description: Generate an Ops Update Guide from git diff between two refs
agent: build
subtask: false
---

Generate an internal Operations-facing update/migration guide based on git diff analysis.

## Process

This command interactively collects all required information:

1. **Base ref** - Starting point (tag, branch, or commit)
2. **Target ref** - Ending point (tag, branch, or commit)
3. **Version** - Optional, auto-detected from tags if not provided
4. **Language** - en, pt-br, or both
5. **Execution mode** - Preview or generate

## Output

The command generates:

1. **Preview summary** - Shows configuration and change counts
2. **User confirmation** - Waits for approval before writing
3. **Release guide file(s)** - Written to `notes/releases/`

## Guide Contents

- Breaking changes and migration steps
- New features and capabilities
- Configuration changes required
- Database migrations (if applicable)
- API changes
- Deprecations
- Known issues
- Rollback procedures

## Quality Checklist

Before finalizing:
- All breaking changes documented
- Migration steps are actionable
- Rollback procedures tested
- Version numbers correct
- Language appropriate for ops team

$ARGUMENTS

Run without arguments for interactive mode, or provide base and target refs.
