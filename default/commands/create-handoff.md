---
name: ring:create-handoff
description: Create a handoff document capturing current session state for future resumption
user_invocable: true
arguments:
  - name: session-name
    description: Short name for the session/feature (e.g., "auth-refactor")
    required: false
  - name: description
    description: Brief description of current work
    required: false
---

# /ring:create-handoff Command

Creates a comprehensive handoff document that captures the current session's context, progress, decisions, and next steps. Use this before running `/clear` to preserve session state for later resumption via `/ring:resume-handoff`.

## Usage

```
/ring:create-handoff [session-name] [description]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `session-name` | No | Short identifier for the session (defaults to feature/task name) |
| `description` | No | Brief description of current state |

## What Gets Captured

The handoff document includes:

1. **Session Summary** - What was being worked on in this entire session (organize per sub-topics)
2. **Current State** - Where things stand right now
3. **Completed Work** - What was accomplished
4. **In-Progress Work** - What's partially done
5. **Key Decisions** - Important choices made and why
6. **What Worked** - Successful approaches
7. **What Didn't Work** - Failed approaches to avoid
8. **Open Questions** - Unresolved items needing attention
9. **Next Steps** - Clear actions for resumption
10. **Relevant Files** - Key files touched or to be modified

## Output Location

Handoffs are saved to: `docs/handoffs/{session-name}/{timestamp}_{description}.md`

Example: `docs/handoffs/auth-refactor/2025-12-27_15-45-00_oauth-integration.md`

## Workflow

1. **Create handoff**: `/ring:create-handoff auth-refactor "OAuth integration complete"`
2. **Clear context**: Run `/clear` to reset conversation
3. **Resume later**: `/ring:resume-handoff docs/handoffs/auth-refactor/...`

## Handoff Template

When invoked, create a file with this structure:

```markdown
# Handoff: {Session Name}

**Created:** {timestamp}
**Status:** {In Progress | Blocked | Ready for Review | Complete}

## Summary

{1-2 sentence overview of what this session was about}

## Current State

{Where things stand right now - be specific about what's done vs pending}

## Completed Work

- {List of completed items with file references where relevant}

## In-Progress Work

- {Partially completed items - describe exactly where you stopped}

## Key Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| {decision} | {why} | {what else was considered} |

## What Worked

- {Successful approaches, patterns, or solutions worth reusing}

## What Didn't Work

- {Failed approaches - document to avoid repeating}

## Open Questions

- [ ] {Unresolved questions that need answers}
- [ ] {Blockers or dependencies}

## Next Steps

1. {First thing to do when resuming}
2. {Second priority}
3. {Third priority}

## Relevant Files

| File | Purpose | Status |
|------|---------|--------|
| `path/to/file` | {what it does} | {modified/created/to-modify} |

## Context for Resumption

{Any additional context the next session needs - gotchas, environment setup, etc.}
```

## Examples

### Basic Usage
```
User: /ring:create-handoffAssistant: I'll create a handoff document for the current session.
[Creates docs/handoffs/current-session/2025-12-27_15-45-00_session.md with filled template]
```

### With Session Name
```
User: /ring:create-handoff auth-refactor "OAuth provider integration"
Assistant: I'll create a handoff document for the auth-refactor session.
[Creates docs/handoffs/auth-refactor/2025-12-27_15-45-00_session.md with filled template]

Summary:
- Created: docs/handoffs/auth-refactor/2025-12-27_15-45-00_session.md
- Session ID: auth-refactor_2025-12-27_15-45-00
- Title: OAuth provider integration
```
