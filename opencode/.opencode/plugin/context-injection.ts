import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Context Injection Plugin
 * Injects Ring context during session compaction.
 *
 * When OpenCode compacts session history for context management,
 * this plugin ensures critical Ring rules and skill information
 * are preserved and re-injected into the context.
 */
export const RingContextInjection: Plugin = async (ctx) => {
  return {
    "experimental.session.compacting": async (input, output) => {
      output.context.push(`
## Ring Skills System

Ring skills are available via the skill() tool. Key skills:
- test-driven-development: TDD methodology (RED -> GREEN -> REFACTOR)
- requesting-code-review: Parallel code review with 3 specialized reviewers
- systematic-debugging: 4-phase debugging methodology
- writing-plans: Create detailed implementation plans
- executing-plans: Execute plans in batches with review checkpoints
- dispatching-parallel-agents: Run multiple agents concurrently
- verification-before-completion: Ensure work is complete before declaring done

## Ring Critical Rules

- **3-FILE RULE**: Do not edit >3 files directly, dispatch agent instead
- **TDD**: Test must fail before implementation (RED phase required)
- **REVIEW**: All 3 reviewers must pass (code, security, business-logic)
- **COMMIT**: Use /commit command for intelligent change grouping
- **VERIFY**: Always verify work before marking complete

## Available Agents

- code-reviewer: Technical code quality review
- security-reviewer: Security vulnerability analysis
- business-logic-reviewer: Business requirements alignment
- codebase-explorer: Autonomous codebase exploration
- write-plan: Implementation planning agent

## Available Commands

- /commit - Intelligent commit grouping
- /codereview - Dispatch 3 parallel reviewers
- /brainstorm - Socratic design refinement
- /execute-plan - Batch execution with checkpoints
- /worktree - Create isolated development branch
- /lint - Run and fix lint issues
`)
    }
  }
}

export default RingContextInjection
