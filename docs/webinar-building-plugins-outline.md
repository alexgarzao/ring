# Webinar: Building Plugins for AI Coding Assistants

> **Purpose:** Teaching developers how to build plugins like Ring for Claude Code, Droid, OpenCode, Amp, and similar AI coding harnesses.

---

## Slide 1: Title

**Building Plugins for AI Coding Assistants**

*Understanding Agents, Skills, Commands, Hooks, and Tools*

---

## Slide 2: What We'll Cover

1. What is a "harness" on top of an LLM?
2. The layered architecture of AI coding assistants
3. The five building blocks: Tools, Skills, Agents, Commands, Hooks
4. How these components relate to each other
5. Building your first plugin

---

## Slide 3: The Layered Architecture

**Key Message:** You're not just prompting an LLM — you're working with a stack

```
┌──────────────────────────────────────────────────────────────┐
│                     USER'S REQUEST                           │
├──────────────────────────────────────────────────────────────┤
│  PLUGINS         Skills │ Agents │ Commands │ Hooks          │  ← YOU BUILD THIS
├──────────────────────────────────────────────────────────────┤
│  HARNESS         Claude Code / Droid / Amp / OpenCode        │  ← Tooling + orchestration
├──────────────────────────────────────────────────────────────┤
│  TOOLS           Read │ Write │ Bash │ Task │ Glob │ Grep    │  ← Native capabilities
├──────────────────────────────────────────────────────────────┤
│  SYSTEM PROMPT   Anthropic's safety + behavior guidelines    │  ← Invisible to you
├──────────────────────────────────────────────────────────────┤
│  LLM TRAINING    Claude's base knowledge + reasoning         │  ← The foundation
└──────────────────────────────────────────────────────────────┘
```

---

## Slide 4: Why Layers Matter

Each layer has different "influence" over the LLM:

| Layer | Who Controls It | Can You Change It? |
|-------|-----------------|-------------------|
| LLM Training | Anthropic/OpenAI | No |
| System Prompt | Anthropic/OpenAI | No |
| Harness Prompt | Tool vendor (Claude Code) | No |
| Tools | Tool vendor | No (but you can compose them) |
| **Plugins** | **You** | **Yes — highest influence layer** |

**Plugins operate closest to the user's request = maximum influence**

---

## Slide 5: The Five Building Blocks

| Component | One-Line Definition |
|-----------|---------------------|
| **Tools** | Atomic operations the LLM can perform |
| **Skills** | Reusable methodologies and patterns |
| **Agents** | Specialized personas with structured output |
| **Commands** | User-facing workflow orchestrators |
| **Hooks** | Event-driven automation scripts |

---

## Slide 6: Tools — The Native Capabilities

**Definition:** Tools are the atomic operations provided by the harness. They're what the LLM can actually *do*.

| Tool | What It Does |
|------|--------------|
| `Read` | Read file contents |
| `Write` | Create/overwrite files |
| `Edit` | Surgical text replacement |
| `Bash` | Execute shell commands |
| `Glob` | Find files by pattern |
| `Grep` | Search file contents |
| `Task` | Dispatch a subagent |
| `Skill` | Load a skill into context |
| `WebFetch` | Fetch URL content |

---

## Slide 7: Tools — Key Point

**You don't create new tools.**

You *compose* existing tools through Skills, Agents, Commands, and Hooks.

Think of tools as the **primitive operations** — like assembly instructions for the AI.

---

## Slide 8: Skills — Reusable Methodologies

**Definition:** A skill teaches the LLM *how* to approach a type of problem. It's a methodology, not an actor.

**Mental Model:** Skills are like **recipes** — they teach a process but don't do the work themselves.

---

## Slide 9: Skills — Example Structure

```yaml
# File: skills/test-driven-development/SKILL.md
---
name: ring:test-driven-development
description: RED-GREEN-REFACTOR implementation methodology
trigger: |
  - Starting implementation of new feature
  - Starting bugfix
skip_when: |
  - Reviewing existing tests
  - Documentation-only changes
---

# Test-Driven Development

## The RED-GREEN-REFACTOR Cycle

1. **RED:** Write a failing test first
2. **GREEN:** Write minimal code to pass
3. **REFACTOR:** Clean up while tests pass

[Detailed procedural content...]
```

---

## Slide 10: Skills — Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Declarative triggers** | When should this skill apply? |
| **Procedural content** | Step-by-step guidance |
| **Composable** | Skills can reference other skills |
| **Invocation** | `Skill tool: "ring:skill-name"` |
| **No output schema** | Guidance, not structured reports |

---

## Slide 11: Agents — Specialized Personas

**Definition:** An agent is a specialized *role* with defined responsibilities and structured output.

**Mental Model:** Agents are like **specialists** — you dispatch them to analyze and report back.

---

## Slide 12: Agents — Example Structure

```yaml
# File: agents/code-reviewer.md
---
name: ring:code-reviewer
version: 4.0.0
description: "Reviews code quality, architecture, design patterns"
type: reviewer
model: opus  # Can require specific model!
output_schema:
  format: "markdown"
  required_sections:
    - name: "VERDICT"
      pattern: "^## VERDICT: (PASS|FAIL|NEEDS_DISCUSSION)$"
      required: true
    - name: "Issues Found"
      required: true
    - name: "What Was Done Well"
      required: true
---

# Code Reviewer

## Your Role
You are a senior engineer reviewing code for quality...

## Focus Areas
- Architecture and design patterns
- Code maintainability
- Error handling
[...]
```

---

## Slide 13: Agents — Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Defined output schema** | Structured, predictable results |
| **Model requirements** | Can demand opus vs sonnet vs haiku |
| **Domain focus** | Security, code quality, business logic, etc. |
| **Parallel execution** | Multiple agents run simultaneously |
| **Invocation** | `Task tool: subagent_type="ring:agent-name"` |

---

## Slide 14: Agents vs Skills — The Difference

| Aspect | Skill | Agent |
|--------|-------|-------|
| **Purpose** | Teach a methodology | Perform specialized analysis |
| **Output** | Procedural guidance | Structured report with verdict |
| **Runs as** | Context injection | Independent subprocess |
| **Parallelism** | Sequential (chained) | Parallel (concurrent) |
| **Has persona** | No | Yes (defined role) |
| **Example** | "How to do TDD" | "Review this code for security" |

---

## Slide 15: Commands — User-Facing Orchestrators

**Definition:** A command is a user-invocable workflow that orchestrates skills and agents.

**Mental Model:** Commands are like **conductors** — they coordinate the orchestra (skills + agents).

---

## Slide 16: Commands — Example Structure

```yaml
# File: commands/codereview.md
---
name: ring:codereview
description: Run parallel code review with 5 specialized reviewers
argument-hint: "[files-or-paths]"
---

# Code Review Command

## What This Does
1. Runs pre-analysis (static analysis tools)
2. Dispatches 5 reviewers in parallel
3. Consolidates findings into actionable report

## Step 1: Gather Context
- What was implemented?
- What are the requirements?

## Step 2: Dispatch Reviewers (PARALLEL)
Use a single message with 5 Task tool calls:
- ring:code-reviewer
- ring:security-reviewer
- ring:business-logic-reviewer
- ring:test-reviewer
- ring:nil-safety-reviewer

## Step 3: Consolidate Results
[...]
```

---

## Slide 17: Commands — Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **User-invocable** | `/commandname [args]` |
| **Orchestration logic** | Coordinates multiple components |
| **High-level workflows** | Not atomic operations |
| **Can run binaries** | Shell commands, analysis tools |
| **Aggregates results** | Collects outputs from agents |

---

## Slide 18: Hooks — Event-Driven Automation

**Definition:** Hooks are shell scripts triggered by lifecycle events — the user never invokes them directly.

**Mental Model:** Hooks are like **background services** — always running, injecting context.

---

## Slide 19: Hooks — Example Structure

```json
// File: hooks/hooks.json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Slide 20: Hooks — Available Events

| Event | When It Fires |
|-------|---------------|
| `SessionStart` | Session begins, resumes, or compacts |
| `UserPromptSubmit` | After each user message |
| `Stop` | Session ends |

**Hook scripts must output JSON:**
```json
{"success": true, "message": "Context loaded"}
```

---

## Slide 21: Hooks — Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Invisible to user** | Automatic execution |
| **Context injection** | Adds info without being asked |
| **Shell scripts** | Must output JSON response |
| **Can't be skipped** | Always runs on event |
| **Setup automation** | Install dependencies, validate env |

---

## Slide 22: The Relationship Map — Visual

```
                    USER
                      │
                      ▼
              ┌───────────────┐
              │   /command    │  User types /ring:codereview
              └───────┬───────┘
                      │ orchestrates
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │ Agent 1 │ │ Agent 2 │ │ Agent 3 │  Dispatched in parallel
     └────┬────┘ └────┬────┘ └────┬────┘
          │           │           │
          └───────────┼───────────┘
                      │ uses
                      ▼
              ┌───────────────┐
              │    Skills     │  Loaded as methodology
              └───────┬───────┘
                      │ via
                      ▼
              ┌───────────────┐
              │    Tools      │  Read, Write, Bash, etc.
              └───────────────┘

        ════════════════════════════════
        │         HOOKS                │  ← Running in background
        │  (SessionStart, PromptSubmit)│     injecting context
        ════════════════════════════════
```

---

## Slide 23: The Relationship Map — Table

| Component | What It Is | User Invokes? | Output | Mental Model |
|-----------|------------|---------------|--------|--------------|
| **Tool** | Atomic operation | No (LLM uses) | Action result | Hands |
| **Skill** | Methodology/pattern | Via `Skill tool` | Procedural guidance | Recipe |
| **Agent** | Specialized role | Via `Task tool` | Structured report | Specialist |
| **Command** | Workflow orchestrator | Yes: `/name` | Aggregated findings | Conductor |
| **Hook** | Event automation | No (auto-trigger) | Context injection | Background service |

---

## Slide 24: How They Work Together — Example

**Scenario:** User runs `/ring:codereview`

1. **Hook** (SessionStart) already loaded skill references at session start
2. **Command** (`/ring:codereview`) receives user request
3. **Command** runs pre-analysis binary via **Tool** (`Bash`)
4. **Command** dispatches 5 **Agents** in parallel via **Tool** (`Task`)
5. Each **Agent** loads relevant **Skills** for methodology
6. Each **Agent** uses **Tools** (`Read`, `Grep`) to analyze code
7. Each **Agent** returns structured verdict
8. **Command** consolidates all verdicts into final report

---

## Slide 25: Analogy for Non-Technical Audience

| Component | Restaurant Analogy |
|-----------|-------------------|
| **Tools** | Your hands (what you can physically do) |
| **Skills** | Recipes (how to cook a dish) |
| **Agents** | Specialists (the chef, the sommelier, the pastry chef) |
| **Commands** | Customer order ("dinner for two" — kitchen coordinates) |
| **Hooks** | The host greeting you when you walk in (automatic, contextual) |

---

## Slide 26: Why This Architecture Matters

| Component | Benefit |
|-----------|---------|
| **Skills** | Reusability across projects |
| **Agents** | Parallelism + specialization |
| **Commands** | User ergonomics (simple invocation) |
| **Hooks** | Zero-friction context (auto-setup) |

**Together:** Consistent, repeatable, high-quality AI-assisted development.

---

## Slide 27: Building Your First Plugin — Structure

```
my-plugin/
├── skills/
│   └── my-pattern/
│       └── SKILL.md          # Methodology
├── agents/
│   └── my-reviewer.md        # Specialized persona
├── commands/
│   └── my-workflow.md        # User-facing orchestration
└── hooks/
    ├── hooks.json            # Event registry
    └── session-start.sh      # Startup script
```

---

## Slide 28: Building Your First Plugin — Minimal Skill

```yaml
# File: skills/my-pattern/SKILL.md
---
name: my-plugin:my-pattern
description: A simple pattern for X
trigger: |
  - When user asks to do X
---

# My Pattern

## Overview
This pattern helps you do X effectively.

## Steps
1. First, do this
2. Then, do that
3. Finally, verify with this
```

---

## Slide 29: Building Your First Plugin — Minimal Agent

```yaml
# File: agents/my-reviewer.md
---
name: my-plugin:my-reviewer
description: Reviews code for X
type: reviewer
output_schema:
  required_sections:
    - name: "VERDICT"
      pattern: "^## VERDICT: (PASS|FAIL)$"
    - name: "Findings"
---

# My Reviewer

## Your Role
You review code for X quality.

## What to Check
- Check for A
- Check for B
- Check for C

## Output Format
Start with VERDICT, then list findings.
```

---

## Slide 30: Building Your First Plugin — Minimal Command

```yaml
# File: commands/my-workflow.md
---
name: my-plugin:my-workflow
description: Run my custom workflow
argument-hint: "[target]"
---

# My Workflow

## What This Does
1. Analyzes the target
2. Dispatches my-reviewer agent
3. Reports findings

## Steps
1. Use Glob to find relevant files
2. Use Task tool to dispatch my-plugin:my-reviewer
3. Summarize results for user
```

---

## Slide 31: Building Your First Plugin — Minimal Hook

```json
// File: hooks/hooks.json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/setup.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
# File: hooks/setup.sh
echo '{"success": true, "message": "My plugin loaded!"}'
```

---

## Slide 32: Key Takeaways

1. **AI coding assistants are layered systems** — plugins are your influence layer
2. **Tools are primitives** — you compose them, not create them
3. **Skills teach methodology** — reusable patterns across projects
4. **Agents are specialists** — parallel execution with structured output
5. **Commands orchestrate** — user-friendly workflow coordination
6. **Hooks automate** — zero-friction context injection

---

## Slide 33: Resources

- **Ring Repository:** github.com/LerianStudio/ring
- **Claude Code Documentation:** docs.anthropic.com
- **Plugin Examples:** See Ring's `default/`, `dev-team/`, `pm-team/` directories

---

## Slide 34: Q&A

**Questions?**

---

## Speaker Notes

### For Slide 3 (Layered Architecture)
- Emphasize that most developers think of AI as monolithic
- The stack mental model is crucial for understanding influence
- Plugins are powerful because they're closest to user intent

### For Slide 14 (Agents vs Skills)
- This is the most common confusion point
- Use the recipe vs chef analogy: recipe tells you how, chef does the work
- Skills are loaded into context; agents run as subprocesses

### For Slide 22 (Relationship Map)
- Walk through a real example step by step
- Show how a single user command triggers the whole cascade
- Highlight parallel execution of agents

### For Live Demo
- Run `/ring:codereview` on a small code change
- Show the 5 agents being dispatched in parallel
- Point out the structured output from each agent
