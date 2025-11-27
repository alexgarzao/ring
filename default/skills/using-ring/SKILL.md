---
name: using-ring
description: |
  Mandatory orchestrator protocol - establishes ORCHESTRATOR principle (dispatch agents,
  don't operate directly) and skill discovery workflow for every conversation.

trigger: |
  - Every conversation start (automatic via SessionStart hook)
  - Before ANY task (check for applicable skills)
  - When tempted to operate tools directly instead of delegating

skip_when: |
  - Never skip - this skill is always mandatory

sequence:
  before: [all-other-skills]
---

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST read the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## ⛔ 3-FILE RULE: HARD GATE (NON-NEGOTIABLE)

**DO NOT read more than 3 files directly. This is a PROHIBITION, not guidance.**

```
FILES YOU'RE ABOUT TO TOUCH: [count]

≤3 files → Direct operation permitted (if user explicitly requested)
>3 files → STOP. DO NOT PROCEED. Launch specialist agent.

VIOLATION = WASTING 15x CONTEXT. This is unacceptable.
```

**This gate applies to:**
- Reading files (Read tool)
- Searching files (Grep/Glob returning >3 matches to inspect)
- Editing files (Edit tool on >3 files)
- Any combination totaling >3 file operations

**If you've already read 3 files and need more:**
STOP. You are at the gate. Dispatch an agent NOW with what you've learned.

**Why this number?** 3 files ≈ 6-15k tokens. Beyond that, agent dispatch costs ~2k tokens and returns focused results. The math is clear: >3 files = agent is 5-15x more efficient.

## 🚨 AUTO-TRIGGER PHRASES: MANDATORY AGENT DISPATCH

**When user says ANY of these, DEFAULT to launching specialist agent:**

| User Phrase Pattern | Mandatory Action |
|---------------------|------------------|
| "fix issues", "fix remaining", "address findings" | Launch specialist agent (NOT manual edits) |
| "apply fixes", "fix the X issues" | Launch specialist agent |
| "fix errors", "fix warnings", "fix linting" | Launch specialist agent |
| "update across", "change all", "refactor" | Launch specialist agent |
| "find where", "search for", "locate" | Launch Explore agent |
| "understand how", "how does X work" | Launch Explore agent |

**Why?** These phrases imply multi-file operations. You WILL exceed 3 files. Pre-empt the violation.

## MANDATORY PRE-ACTION CHECKPOINT

**Before EVERY tool use, you MUST complete this checkpoint. No exceptions.**

```
┌─────────────────────────────────────────────────────────────┐
│  ⛔ STOP. COMPLETE BEFORE PROCEEDING.                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. FILES THIS TASK WILL TOUCH: ___                         │
│     □ >3 files? → STOP. Launch agent. DO NOT proceed.       │
│                                                             │
│  2. USER PHRASE CHECK:                                      │
│     □ Did user say "fix issues/remaining/findings"?         │
│     □ Did user say "apply fixes" or "fix the X issues"?     │
│     □ Did user say "find/search/locate/understand"?         │
│     → If ANY checked: Launch agent. DO NOT proceed manually.│
│                                                             │
│  3. OPERATION TYPE:                                         │
│     □ Investigation/exploration → Explore agent             │
│     □ Multi-file edit → Specialist agent                    │
│     □ Single explicit file (user named it) → Direct OK      │
│                                                             │
│  CHECKPOINT RESULT: [Agent dispatch / Direct operation]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**If you skip this checkpoint, you are in automatic violation.**

# Getting Started with Skills

## MANDATORY FIRST RESPONSE PROTOCOL

Before responding to ANY user message, you MUST complete this checklist IN ORDER:

1. ☐ **Check for MANDATORY-USER-MESSAGE** - If additionalContext contains `<MANDATORY-USER-MESSAGE>` tags, display the message FIRST, verbatim, at the start of your response
2. ☐ **ORCHESTRATION DECISION** - Determine which agent handles this task
   - Create TodoWrite: "Orchestration decision: [agent-name] with Opus"
   - Default model: **Opus** (use unless user specifies otherwise)
   - If considering direct tools, document why the exception applies (user explicitly requested specific file read)
   - Mark todo complete only after documenting decision
3. ☐ **Skill Check** - List available skills in your mind, ask: "Does ANY skill match this request?"
4. ☐ **If yes** → Use the Skill tool to read and run the skill file
5. ☐ **Announce** - State which skill/agent you're using (when non-obvious)
6. ☐ **Execute** - Dispatch agent OR follow skill exactly

**Responding WITHOUT completing this checklist = automatic failure.**

### MANDATORY-USER-MESSAGE Contract

If additionalContext contains `<MANDATORY-USER-MESSAGE>` tags:
- Display verbatim at message start, no exceptions
- No paraphrasing, no "will mention later" rationalizations

## Critical Rules

1. **Follow mandatory workflows.** Brainstorming before coding. Check for relevant skills before ANY task.

2. Execute skills with the Skill tool

## Common Rationalizations That Mean You're About To Fail

If you catch yourself thinking ANY of these thoughts, STOP. You are rationalizing. Check for and use the skill. Also check: are you being an OPERATOR instead of ORCHESTRATOR?

**Skill Checks:**
- "This is just a simple question" → WRONG. Questions are tasks. Check for skills.
- "This doesn't need a formal skill" → WRONG. If a skill exists for it, use it.
- "I remember this skill" → WRONG. Skills evolve. Run the current version.
- "This doesn't count as a task" → WRONG. If you're taking action, it's a task. Check for skills.
- "The skill is overkill for this" → WRONG. Skills exist because simple things become complex. Use it.
- "I'll just do this one thing first" → WRONG. Check for skills BEFORE doing anything.
- "I need context before checking skills" → WRONG. Gathering context IS a task. Check for skills first.

**Orchestrator Breaks (Direct Tool Usage):**
- "I can check git/files quickly" → WRONG. Use agents, stay ORCHESTRATOR.
- "Let me gather information first" → WRONG. Dispatch agent to gather it.
- "Just a quick look at files" → WRONG. That "quick" becomes 20k tokens. Use agent.
- "I'll scan the codebase manually" → WRONG. That's operator behavior. Use Explore.
- "This exploration is too simple for an agent" → WRONG. Simplicity makes agents more efficient.
- "I already started reading files" → WRONG. Stop. Dispatch agent instead.
- "It's faster to do it myself" → WRONG. You're burning context. Agents are 15x faster contextually.

**3-File Rule Rationalizations (YOU WILL TRY THESE):**
- "This task is small" → WRONG. Count files. >3 = agent. Task size is irrelevant.
- "It's only 5 fixes across 5 files, I can handle it" → WRONG. 5 files > 3 files. Agent mandatory.
- "User said 'here' so they want me to do it in this conversation" → WRONG. "Here" means get it done, not manually.
- "TodoWrite took priority so I'll execute sequentially" → WRONG. TodoWrite plans WHAT. Orchestrator decides HOW.
- "The 3-file rule is guidance, not a gate" → WRONG. It's a PROHIBITION. You DO NOT proceed past 3 files.
- "User didn't explicitly call an agent so I shouldn't" → WRONG. Agent dispatch is YOUR decision.
- "I'm confident I know where the files are" → WRONG. Confidence doesn't reduce context cost.
- "Let me finish these medium/low fixes here" → WRONG. "Fix issues" phrase = auto-trigger for agent.

**Why:** Skills document proven techniques. Agents preserve context. Not using them means repeating mistakes and wasting tokens.

**Both matter:** Skills check is mandatory. ORCHESTRATOR approach is mandatory.

If a skill exists or if you're about to use tools directly, you must use the proper approach or you will fail.

## The Cost of Skipping Skills

Every time you skip checking for skills:
- You fail your task (skills contain critical patterns)
- You waste time (rediscovering solved problems)
- You make known errors (skills prevent common mistakes)
- You lose trust (not following mandatory workflows)

**This is not optional. Check for skills or fail.**

## Mandatory Skill Check Points

**Before EVERY tool use**, ask yourself:
- About to use Read? → Is there a skill for reading this type of file?
- About to use Bash? → Is there a skill for this command type?
- About to use Grep? → Is there a skill for searching?
- About to use Task? → Which subagent_type matches?

**No tool use without skill check first.**

## MANDATORY PRE-TOOL-USE PROTOCOL

**Before EVERY tool call** (Read, Grep, Glob, Bash), complete this check:

```
┌─────────────────────────────────────────────────────────────┐
│  Tool I'm about to use: [tool-name]                         │
│  Purpose: [what I'm trying to learn/do]                     │
│  Files this will touch: [count] ← CHECK 3-FILE RULE         │
├─────────────────────────────────────────────────────────────┤
│  ⛔ 3-FILE GATE:                                             │
│  □ Will touch >3 files? → STOP. Launch agent. DO NOT proceed│
│  □ Already touched 3 files? → STOP. At gate. Dispatch now.  │
├─────────────────────────────────────────────────────────────┤
│  Orchestration Decision:                                    │
│  □ User explicitly requested specific file → Direct tool OK │
│  □ Investigation/exploration/search → MUST use agent        │
│  □ User said "fix issues/remaining/findings" → MUST use agent│
├─────────────────────────────────────────────────────────────┤
│  Agent I'm dispatching: [agent-name]                        │
│  Model: Opus (default, unless user specified otherwise)     │
│  OR                                                         │
│  Exception: [why user explicitly requested this file]       │
└─────────────────────────────────────────────────────────────┘
```

**CONSEQUENCES OF SKIPPING THIS CHECK:**
- You waste 15x context (agent returns ~2k, manual exploration ~30k)
- You deprive user of conversation headroom
- You violate ORCHESTRATOR principle
- **This is automatic failure**

**Examples:**

❌ **WRONG:**
```
User: "Where are errors handled?"
Me: [uses Grep to search for "error"]
```
**Why wrong:** No orchestration decision documented, direct tool usage for exploration.

✅ **CORRECT:**
```
User: "Where are errors handled?"
Me:
Tool I'm about to use: None (using agent)
Purpose: Find error handling code
Orchestration Decision: Investigation task → Explore agent
Agent I'm dispatching: Explore
Model: Opus
```

## ORCHESTRATOR Principle: Agent-First Always

**Your role is ORCHESTRATOR, not operator.**

You don't read files, run grep chains, or manually explore – you **dispatch agents** to do the work and return results. This is not optional. This is mandatory for context efficiency.

**The Problem with Direct Tool Usage:**
- Manual exploration chains: ~30-100k tokens in main context
- Each file read adds context bloat
- Grep/Glob chains multiply the problem
- User sees work happening but context explodes

**The Solution: Orchestration:**
- Dispatch agents to handle complexity
- Agents return only essential findings (~2-5k tokens)
- Main context stays lean for reasoning
- **15x more efficient** than direct file operations

### Your Role: ORCHESTRATOR (No Exceptions)

**You dispatch agents. You do not operate tools directly.**

**Default answer for ANY exploration/search/investigation:** Use one of the three built-in agents (Explore, Plan, or general-purpose) with Opus model.

**Which agent?**
- **Explore** - Fast codebase navigation, finding files/code, understanding architecture
- **Plan** - Implementation planning, breaking down features into tasks
- **general-purpose** - Multi-step research, complex investigations, anything not fitting Explore/Plan

**Model Selection:** Always use **Opus** for agent dispatching unless user explicitly specifies otherwise (e.g., "use Haiku", "use Sonnet").

**Only exception:** User explicitly provides a file path AND explicitly requests you read it (e.g., "read src/foo.ts").

**All these are STILL orchestration tasks:**
- ❌ "I need to understand the codebase structure first" → Explore agent
- ❌ "Let me check what files handle X" → Explore agent
- ❌ "I'll grep for the function definition" → Explore agent
- ❌ "User mentioned component Y, let me find it" → Explore agent
- ❌ "I'm confident it's in src/foo/" → Explore agent
- ❌ "Just checking one file to confirm" → Explore agent
- ❌ "This search premise seems invalid, won't find anything" → Explore agent (you're not the validator)

**You don't validate search premises.** Dispatch the agent, let the agent report back if search yields nothing.

**If you're about to use Read, Grep, Glob, or Bash for investigation:**
You are breaking ORCHESTRATOR. Use an agent instead.

### Available Agents

#### Built-in Agents (Claude Code)
| Agent | Purpose | When to Use | Model Default |
|-------|---------|-------------|---------------|
| **`Explore`** | Codebase navigation & discovery | Finding files/code, understanding architecture, searching patterns | **Opus** |
| **`Plan`** | Implementation planning | Breaking down features, creating task lists, architecting solutions | **Opus** |
| **`general-purpose`** | Multi-step research & investigation | Complex analysis, research requiring multiple steps, anything not fitting Explore/Plan | **Opus** |
| `claude-code-guide` | Claude Code documentation | Questions about Claude Code features, hooks, MCP, SDK | Opus |

#### Ring Agents (Specialized)
| Agent | Purpose |
|-------|---------|
| `ring-default:code-reviewer` | Architecture & patterns |
| `ring-default:business-logic-reviewer` | Correctness & requirements |
| `ring-default:security-reviewer` | Security & OWASP |
| `ring-default:write-plan` | Implementation planning |

### Decision: Which Agent?

**Don't ask "should I use an agent?" Ask "which agent?"**

```
START: I need to do something with the codebase

├─▶ Explore/find/understand code
│   └─▶ Use Explore agent with Opus
│       Examples: "Find where X is used", "Understand auth flow", "Locate config files"
│
├─▶ Search for something (grep, find function, locate file)
│   └─▶ Use Explore agent with Opus (YES, even "simple" searches)
│       Examples: "Search for handleError", "Find all API endpoints", "Locate middleware"
│
├─▶ Plan implementation or break down features
│   └─▶ Use Plan agent with Opus
│       Examples: "Plan how to add feature X", "Break down this task", "Design solution for Y"
│
├─▶ Multi-step research or complex investigation
│   └─▶ Use general-purpose agent with Opus
│       Examples: "Research and analyze X", "Investigate Y across multiple files", "Deep dive into Z"
│
├─▶ Review code quality
│   └─▶ Use ALL THREE in parallel:
│       • ring-default:code-reviewer (with Opus)
│       • ring-default:business-logic-reviewer (with Opus)
│       • ring-default:security-reviewer (with Opus)
│
├─▶ Create implementation plan document
│   └─▶ Use ring-default:write-plan agent with Opus
│
├─▶ Question about Claude Code
│   └─▶ Use claude-code-guide agent with Opus
│
└─▶ User explicitly said "read [specific-file]"
    └─▶ Read directly (ONLY if user explicitly requested specific file read)
```

### Quick Reference: WRONG → RIGHT

| Your Thought | Action |
|--------------|--------|
| "Let me read files to understand X" | Explore agent: "Understand X" |
| "I'll grep for Y" | Explore agent: "Find Y" |
| "User mentioned file Z" | Explore agent (unless user said "read Z") |
| "Need context for good agent instructions" | Dispatch agent with broad topic |
| "Already read 3 files, just 2 more" | STOP at gate. Dispatch now. |
| "This search won't find anything" | Dispatch anyway. You're not the validator. |

**Any of these thoughts = you're about to violate ORCHESTRATOR.**

### Ring Reviewers: ALWAYS Parallel

When dispatching code reviewers, **single message with 3 Task calls:**

```
✅ CORRECT: One message with 3 Task calls (all in parallel)
❌ WRONG: Three separate messages (sequential, 3x slower)
```

### Context Efficiency: Orchestrator Wins

| Approach | Context Cost | Your Role |
|----------|--------------|-----------|
| Manual file reading (5 files) | ~25k tokens | Operator |
| Manual grep chains (10 searches) | ~50k tokens | Operator |
| Explore agent dispatch | ~2-3k tokens | Orchestrator |
| **Savings** | **15-25x more efficient** | **Orchestrator always wins** |

## TodoWrite Requirements

**First two todos for ANY task:**
1. "Orchestration decision: [agent-name] with Opus" (or exception justification)
2. "Check for relevant skills"

**If skill has checklist:** Create TodoWrite todo for EACH item. No mental checklists.

## Announcing Skill Usage

- **Always announce meta-skills:** brainstorming, writing-plans, systematic-debugging (methodology change)
- **Skip when obvious:** User says "write tests first" → no need to announce TDD

## Required Patterns

This skill uses these universal patterns:
- **State Tracking:** See `skills/shared-patterns/state-tracking.md`
- **Failure Recovery:** See `skills/shared-patterns/failure-recovery.md`
- **Exit Criteria:** See `skills/shared-patterns/exit-criteria.md`
- **TodoWrite:** See `skills/shared-patterns/todowrite-integration.md`

Apply ALL patterns when using this skill.

# About these skills

**Many skills contain rigid rules (TDD, debugging, verification).** Follow them exactly. Don't adapt away the discipline.

**Some skills are flexible patterns (architecture, naming).** Adapt core principles to your context.

The skill itself tells you which type it is.

## Instructions ≠ Permission to Skip Workflows

Your human partner's specific instructions describe WHAT to do, not HOW.

"Add X", "Fix Y" = the goal, NOT permission to skip brainstorming, TDD, or RED-GREEN-REFACTOR.

**Red flags:** "Instruction was specific" • "Seems simple" • "Workflow is overkill"

**Why:** Specific instructions mean clear requirements, which is when workflows matter MOST. Skipping process on "simple" tasks is how simple tasks become complex problems.

## Summary

**Starting any task:**
1. **Orchestration decision** → Which agent handles this? Use **Opus** model by default (TodoWrite required)
2. **Skill check** → If relevant skill exists, use it
3. **Announce** → State which skill/agent you're using
4. **Execute** → Dispatch agent with Opus OR follow skill exactly

**Before ANY tool use (Read/Grep/Glob/Bash):** Complete PRE-TOOL-USE PROTOCOL checklist.

**Skill has checklist?** TodoWrite for every item.

**Default answer: Use an agent with Opus. Exception is rare (user explicitly requests specific file read).**

**Model default: Opus** (unless user specifies Haiku/Sonnet explicitly).

**Finding a relevant skill = mandatory to read and use it. Not optional.**
