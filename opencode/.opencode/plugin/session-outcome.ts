import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readdirSync, statSync } from "fs"
import { join } from "path"
import { readState, writeState, deleteState, getSessionId, sanitizeForPrompt } from "./utils/state"

/**
 * Ring Session Outcome Plugin
 * Prompts for previous session outcome grade after session clear/compact.
 *
 * Equivalent to: default/hooks/session-outcome.sh
 * Events:
 *   - session.compacted (after compact)
 *   - session.created (detect new session after compact)
 *
 * This plugin detects when a session has been compacted and prompts
 * the user to grade the previous session's outcome for learning extraction.
 *
 * NOTE: OpenCode doesn't have session.compacted event with matcher support,
 * so we use a state-based workaround to distinguish startup vs clear/compact.
 */

interface Todo {
  content: string
  status: "pending" | "in_progress" | "completed"
}

interface PendingOutcomePrompt {
  timestamp: number
}

// Maximum time between session.compacted and session.created to show outcome prompt
const OUTCOME_PROMPT_WINDOW_MS = 5000

export const RingSessionOutcome: Plugin = async ({ client, directory, $ }) => {
  const projectRoot = directory
  const sessionId = getSessionId()

  /**
   * Check for recent session work indicators.
   */
  const detectSessionWork = (): { hasWork: boolean; context: string[] } => {
    const context: string[] = []
    let hasWork = false

    // Check for todos state
    const todos = readState<Todo[]>(projectRoot, "todos-state", sessionId)
    if (todos && todos.length > 0) {
      hasWork = true
      const completed = todos.filter((t) => t.status === "completed").length
      context.push(`Task progress: ${completed}/${todos.length} completed`)
    }

    // Check for active ledger (modified in last 2 hours)
    const ledgerDir = join(projectRoot, ".ring/ledgers")
    if (existsSync(ledgerDir)) {
      const twoHoursAgo = Date.now() - 2 * 60 * 60 * 1000

      const ledgers = readdirSync(ledgerDir)
        .filter((f) => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map((f) => ({ name: f, path: join(ledgerDir, f) }))
        .filter((f) => statSync(f.path).mtimeMs > twoHoursAgo)

      if (ledgers.length > 0) {
        hasWork = true
        context.push(`Ledger: ${ledgers[0].name.replace(".md", "")}`)
      }
    }

    // Check for recent handoffs
    const handoffDirs = [join(projectRoot, "docs/handoffs"), join(projectRoot, ".ring/handoffs")]

    for (const dir of handoffDirs) {
      if (existsSync(dir)) {
        const twoHoursAgo = Date.now() - 2 * 60 * 60 * 1000

        try {
          const handoffs = readdirSync(dir, { recursive: true })
            .filter((f) => String(f).endsWith(".md"))
            .map((f) => join(dir, String(f)))
            .filter((f) => existsSync(f) && statSync(f).mtimeMs > twoHoursAgo)

          if (handoffs.length > 0) {
            hasWork = true
            const name = handoffs[0].split("/").pop()
            context.push(`Handoff: ${name}`)
            break
          }
        } catch (err) {
          console.debug(`[Ring:DEBUG] Failed to read handoffs: ${err}`)
        }
      }
    }

    return { hasWork, context }
  }

  /**
   * Find artifact marker script for saving outcome.
   */
  const findArtifactMarker = (): string | null => {
    const candidates = [
      join(projectRoot, ".opencode/lib/artifact-index/artifact_mark.py"),
      join(projectRoot, "default/lib/artifact-index/artifact_mark.py"),
    ]

    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        return candidate
      }
    }
    return null
  }

  /**
   * Inject the outcome prompt.
   */
  const injectOutcomePrompt = async (contextStr: string): Promise<void> => {
    const artifactMarker = findArtifactMarker()

    let markerInstruction = ""
    if (artifactMarker) {
      markerInstruction = `

After user responds, save the grade using:
\`python3 ${artifactMarker} --outcome <GRADE>\``
    }

    // Get current session - SDK returns array directly
    const sessions = await client.session.list()
    const currentSession = sessions
      // Note: Using any due to SDK type availability - replace with Session type when available
      .sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))[0]

    if (currentSession) {
      await client.session.prompt({
        path: { id: currentSession.id },
        body: {
          noReply: true,
          parts: [
            {
              type: "text",
              text: `<MANDATORY-USER-MESSAGE>
PREVIOUS SESSION OUTCOME GRADE REQUESTED

You just cleared/compacted the previous session. Please ask the user to rate the PREVIOUS session's outcome.

**Previous Session Context:** ${sanitizeForPrompt(contextStr, 300)}

**MANDATORY ACTION:** Ask the user:
"How would you rate the previous session's outcome?"

Options:
- SUCCEEDED: All goals achieved, high quality output
- PARTIAL_PLUS: Most goals achieved (>=80%), minor issues
- PARTIAL_MINUS: Some progress (50-79%), significant gaps
- FAILED: Goals not achieved (<50%), major issues
${markerInstruction}

Then continue with the new session.
</MANDATORY-USER-MESSAGE>`,
            },
          ],
        },
      })

      console.log(`[Ring:INFO] Session outcome prompt injected (context: ${contextStr})`)
    }
  }

  return {
    // When session is compacted, set a flag for the next session.created
    "session.compacted": async () => {
      writeState(projectRoot, "pending-outcome-prompt", { timestamp: Date.now() } as PendingOutcomePrompt)
    },
    event: async ({ event }) => {
      // Handle session.created to check for pending outcome prompt
      if (event.type === "session.created") {
        const pending = readState<PendingOutcomePrompt>(projectRoot, "pending-outcome-prompt")
        if (pending && Date.now() - pending.timestamp < OUTCOME_PROMPT_WINDOW_MS) {
          // Clear the flag
          deleteState(projectRoot, "pending-outcome-prompt")

          // Check for session work
          const { hasWork, context } = detectSessionWork()

          if (hasWork) {
            const contextStr = context.join(", ")
            await injectOutcomePrompt(contextStr)
          } else {
            console.log("[Ring:INFO] No session work detected, skipping outcome prompt")
          }
        }
        return
      }

      // Also handle session.compacted directly if it fires
      if (event.type === "session.compacted") {
        const { hasWork, context } = detectSessionWork()

        if (!hasWork) {
          console.log("[Ring:INFO] No session work detected, skipping outcome prompt")
          return
        }

        const contextStr = context.join(", ")
        await injectOutcomePrompt(contextStr)
      }
    },
  }
}

export default RingSessionOutcome
