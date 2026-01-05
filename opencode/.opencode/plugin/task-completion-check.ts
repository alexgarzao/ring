import type { Plugin } from "@opencode-ai/plugin"
import { writeState, getSessionId, sanitizeForPrompt } from "./utils/state"
import { EVENTS } from "./utils/events"

/**
 * Ring Task Completion Check Plugin
 * Detects when all todos are complete and suggests handoff creation.
 *
 * Equivalent to: default/hooks/task-completion-check.sh
 * Event: todo.updated
 *
 * This plugin monitors todo list updates and:
 * 1. Persists todo state for outcome inference
 * 2. Injects handoff recommendation when all tasks complete
 */

interface Todo {
  content: string
  status: "pending" | "in_progress" | "completed"
  activeForm?: string
}

interface TodoEvent {
  type: "todo.updated"
  properties?: {
    todos?: Todo[]
  }
  data?: {
    todos?: Todo[]
  }
}

export const RingTaskCompletionCheck: Plugin = async ({ client, directory }) => {
  const projectRoot = directory

  return {
    event: async ({ event }) => {
      if (event.type !== EVENTS.TODO_UPDATED) {
        return
      }

      const todoEvent = event as TodoEvent
      // Defensive payload handling - support both property paths
      const todos = todoEvent.properties?.todos || todoEvent.data?.todos || []

      // Runtime validation
      if (!Array.isArray(todos)) {
        console.warn("[Ring:WARN] Unexpected todo.updated payload structure - todos is not an array")
        return
      }

      if (todos.length === 0) {
        return
      }

      // Persist todos state for outcome inference
      const sessionId = getSessionId()
      writeState(projectRoot, "todos-state", todos, sessionId)

      // Count todos by status
      const total = todos.length
      const completed = todos.filter((t) => t.status === "completed").length
      const inProgress = todos.filter((t) => t.status === "in_progress").length
      const pending = todos.filter((t) => t.status === "pending").length

      // Check if all todos are complete
      if (total > 0 && completed === total) {
        // Build task list for message (sanitized to prevent prompt injection)
        const taskList = todos.map((t) => `- ${sanitizeForPrompt(t.content, 200)}`).join("\n")

        // Get current session - SDK returns a RequestResult wrapper
        const sessionsResult = await client.session.list()
        if (sessionsResult.error) {
          console.warn(`[Ring:WARN] Failed to list sessions: ${sessionsResult.error}`)
          return
        }

        const sessions = sessionsResult.data ?? []
        const currentSession = sessions.sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))[0]

        if (!currentSession) {
          console.warn("[Ring:WARN] No sessions found, cannot inject task completion message")
          return
        }

        // Inject completion message
        await client.session.prompt({
          path: { id: currentSession.id },
          body: {
            noReply: true,
            parts: [
              {
                type: "text",
                text: `<MANDATORY-USER-MESSAGE>
TASK COMPLETION DETECTED - HANDOFF RECOMMENDED

All ${total} todos are marked complete.

**FIRST:** Run /context to check actual context usage.

**IF context is high (>70%):** Create handoff NOW:
1. Run /create-handoff to preserve this session's learnings
2. Document what worked and what failed in the handoff

**IF context is low (<70%):** Handoff is optional - you can continue with new tasks.

Completed tasks:
${taskList}
</MANDATORY-USER-MESSAGE>`,
              },
            ],
          },
        })

        console.log(`[Ring:INFO] All ${total} tasks complete - handoff recommended`)
      } else if (completed > 0) {
        // Progress update - just log, don't inject
        console.log(
          `[Ring:INFO] Task progress: ${completed}/${total} complete, ${inProgress} in progress, ${pending} pending`
        )
      }
    },
  }
}

export default RingTaskCompletionCheck
