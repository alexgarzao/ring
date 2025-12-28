---
name: compound-learnings
description: Analyze session learnings and propose new rules/skills
argument-hint: "[--approve <id>] [--reject <id>] [--list]"
---

Analyze accumulated session learnings to detect recurring patterns and propose new rules, skills, or hooks. Requires user approval before creating any permanent artifacts.

## Usage

```
/compound-learnings [options]
```

## Options

| Option | Description |
|--------|-------------|
| (none) | Analyze learnings and generate new proposals |
| `--list` | List pending proposals without analyzing |
| `--approve <id>` | Approve a specific proposal (e.g., `--approve proposal-1`) |
| `--reject <id>` | Reject a specific proposal with optional reason |
| `--history` | Show history of approved/rejected proposals |

## Examples

### Analyze Learnings (Default)
```
/compound-learnings
```
Analyzes all session learnings, detects patterns appearing 3+ times, and presents proposals.

### List Pending Proposals
```
/compound-learnings --list
```
Shows proposals waiting for approval without re-analyzing.

### Approve a Proposal
```
/compound-learnings --approve proposal-1
```
Creates the rule/skill from the approved proposal.

### Reject a Proposal
```
/compound-learnings --reject proposal-2 "Too project-specific"
```
Marks proposal as rejected with reason.

### View History
```
/compound-learnings --history
```
Shows all past approvals and rejections.

## Process

The command follows this workflow:

### 1. Gather (Automatic)
- Reads `.ring/cache/learnings/*.md` files
- Counts total sessions available

### 2. Analyze (Automatic)
- Extracts patterns from What Worked, What Failed, Key Decisions
- Consolidates similar patterns using fuzzy matching
- Detects patterns appearing in 3+ sessions

### 3. Categorize (Automatic)
- Classifies patterns as rule, skill, or hook candidates
- Generates preview content for each

### 4. Propose (Interactive)
- Presents each qualifying pattern
- Shows draft content
- Waits for your decision

### 5. Create (On Approval)
- Creates rule/skill/hook in appropriate location
- Updates proposal history
- Archives processed learnings

## Output Example

```markdown
## Compound Learnings Analysis

**Sessions Analyzed:** 12
**Patterns Detected:** 8
**Qualifying (3+ sessions):** 3

---

### Proposal 1: Always use explicit file paths

**Signal:** 5 sessions (abc, def, ghi, jkl, mno)
**Category:** Rule
**Sources:** patterns, what_worked

**Preview:**
# Always use explicit file paths
## Pattern
Never use relative paths like "./file" - always use absolute paths.
...

**Action Required:** Type `approve`, `reject`, or `modify`

---
```

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `compound-learnings` skill | Underlying skill with full process details |
| `handoff-tracking` | Provides source data (what_worked, what_failed) |
| `artifact-query` | Search past handoffs for context |

## Troubleshooting

### "No learnings found"
No `.ring/cache/learnings/*.md` files exist. Complete some sessions with outcome tracking enabled.

### "Insufficient data for patterns"
Fewer than 3 learning files. Continue working - patterns emerge after multiple sessions.

### "Pattern already exists"
Check `.ring/generated/rules/` and `.ring/generated/skills/` in your project, or `default/rules/` and `default/skills/` in the plugin - a similar rule or skill may already exist.

### "Proposal not found"
The proposal ID doesn't exist in pending.json. Run `/compound-learnings --list` to see current proposals.
