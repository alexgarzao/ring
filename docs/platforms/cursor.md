# Ring for Cursor

Cursor uses **rules** and **workflows** instead of skills and agents. Ring transforms content to Cursor's format during installation.

## Installation

```bash
# Interactive installer
./installer/install-ring.sh

# Direct install
./installer/install-ring.sh install --platforms cursor

# Multiple platforms
./installer/install-ring.sh install --platforms claude,cursor
```

## Installation Path

Ring installs to: `~/.cursor/`

```
~/.cursor/
├── .cursorrules                 # Generated rules file
├── workflows/                   # Transformed agents/commands
│   ├── code-review.md
│   ├── tdd-workflow.md
│   ├── debugging-workflow.md
│   └── ... (consolidated workflows)
└── .ring-manifest.json          # Installation tracking
```

## Transformations

### Skills → Rules

Ring consolidates skills into Cursor's `.cursorrules` format:

**Claude Code (multiple skill files):**
```
skills/
├── test-driven-development/SKILL.md
├── systematic-debugging/SKILL.md
└── verification-before-completion/SKILL.md
```

**Cursor (single rules file):**
```
.cursorrules
├── # Test-Driven Development
│   RED → GREEN → REFACTOR cycle...
├── # Systematic Debugging
│   4-phase root cause analysis...
└── # Verification Before Completion
    Evidence before claims...
```

### Agents → Workflows

Agents become workflow definitions:

| Claude Code | Cursor |
|-------------|--------|
| `agents/code-reviewer.md` | `workflows/code-review.md` |
| `agents/write-plan.md` | `workflows/implementation-planning.md` |
| `subagent_type="..."` | Follow workflow guide |

### Commands → Workflow Triggers

Slash commands become workflow entry points documented in the workflows directory.

## The .cursorrules File

Ring generates a comprehensive `.cursorrules` file containing:

1. **Core Principles** - Using-ring mandatory discovery
2. **Development Rules** - TDD, debugging, verification
3. **Code Quality Rules** - Anti-patterns, best practices
4. **Workflow References** - Links to workflow files

**Example .cursorrules excerpt:**
```markdown
# Ring Skills for Cursor

## Mandatory: Skill Discovery
Before any task, check if a skill applies.
If a skill applies, you MUST use it.

## Test-Driven Development
1. Write test first (RED)
2. Run test - must fail
3. Write minimal code (GREEN)
4. Run test - must pass
5. Refactor if needed

## Systematic Debugging
Phase 1: Investigate (gather ALL evidence)
Phase 2: Analyze patterns
Phase 3: Test hypothesis (one at a time)
Phase 4: Implement fix (with test)

...
```

## Workflows Directory

Each workflow is a standalone guide:

**workflows/code-review.md:**
```markdown
# Code Review Workflow

## Overview
Parallel 3-reviewer code review process.

## Reviewers
1. Foundation Review - Architecture, patterns, quality
2. Correctness Review - Business logic, requirements, edge cases
3. Safety Review - Security, OWASP, authentication

## Process
1. Identify files to review
2. Run all 3 reviews in parallel
3. Aggregate findings by severity
4. Address Critical/High issues first
5. Re-review after fixes

## Severity Guide
- CRITICAL: Security vulnerabilities, data loss risk
- HIGH: Business logic errors, missing requirements
- MEDIUM: Code quality, maintainability
- LOW: Style, minor improvements
```

## Usage in Cursor

### Following Rules

Cursor automatically loads `.cursorrules`. The AI will:
1. Check applicable rules before tasks
2. Follow TDD when writing code
3. Use debugging phases for issues
4. Require verification before completion

### Using Workflows

Reference workflows when needed:
```
"Follow the code-review workflow for this PR"
"Use the debugging-workflow to investigate this issue"
```

## Feature Mapping

| Ring Feature | Cursor Equivalent |
|--------------|-------------------|
| Skills | Rules in .cursorrules |
| Agents | Workflow guides |
| Commands | Workflow entry points |
| Hooks | Not supported |

**Limitations:**
- No automatic hook execution
- No dynamic skill loading
- Workflows are guidance, not enforced

## Updating

```bash
# Check for updates
./installer/install-ring.sh check

# Update Cursor installation
./installer/install-ring.sh update --platforms cursor

# Regenerate rules file
./installer/install-ring.sh install --platforms cursor --force
```

## Uninstalling

```bash
./installer/install-ring.sh uninstall --platforms cursor
```

This removes:
- `.cursorrules` file
- `workflows/` directory
- `.ring-manifest.json`

## Troubleshooting

### Rules not loading
1. Verify `.cursorrules` exists in `~/.cursor/`
2. Restart Cursor to reload rules
3. Check Cursor settings for rules enablement

### Workflow not found
1. Check `~/.cursor/workflows/` directory
2. Re-run installer: `./installer/install-ring.sh install --platforms cursor`

## Best Practices for Cursor

1. **Reference workflows explicitly**: "Use the TDD workflow"
2. **Remind about rules**: If AI skips rules, reference them
3. **Combine with manual checks**: Rules are guidance, verify compliance
4. **Update regularly**: Re-run installer to get latest skills
