import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync, statSync } from "fs"
import { join } from "path"
import { incrementMessageCount, shouldInject } from "./utils/message-tracking"
import { getSessionId, escapeAngleBrackets } from "./utils/state"
import { EVENTS } from "./utils/events"

/**
 * Ring Instruction Reminder Plugin
 * Periodically re-injects instruction files to combat context drift.
 *
 * Equivalent to: default/hooks/claude-md-reminder.sh
 * Event: message.updated (workaround for UserPromptSubmit)
 *
 * This plugin tracks message count and periodically re-injects:
 * - CLAUDE.md / AGENTS.md / RULES.md files
 * - Agent usage reminder
 * - Duplication prevention guard
 *
 * IMPORTANT: Only counts user messages to avoid double-counting.
 */

// Configuration constants
const CONFIG = {
  // Throttle interval changed to 2 to match original bash implementation
  REMINDER_THROTTLE_MESSAGES: 2,
}
const INSTRUCTION_FILES = ["CLAUDE.md", "AGENTS.md", "RULES.md"]


// Agent usage reminder (compact version)
const AGENT_REMINDER = `<agent-usage-reminder>
CONTEXT CHECK: Before using Glob/Grep/Read chains, consider agents:

| Task | Agent |
|------|-------|
| Explore codebase | Explore |
| Multi-file search | Explore |
| Complex research | general-purpose |
| Code review | code-reviewer + business-logic-reviewer + security-reviewer (PARALLEL) |
| Implementation plan | write-plan |
| Deep architecture | codebase-explorer |

**3-File Rule:** If reading >3 files, use an agent instead. 15x more context-efficient.
</agent-usage-reminder>`

// Duplication prevention
const DUPLICATION_GUARD = `<duplication-prevention-guard>
**BEFORE ADDING CONTENT** to any file:
1. SEARCH FIRST: \`grep -r 'keyword' --include='*.md'\`
2. If exists -> REFERENCE it, don't copy
3. Canonical sources: CLAUDE.md (rules), docs/*.md (details)
4. NEVER duplicate - always link to single source of truth
</duplication-prevention-guard>`

// Global rate limiting for injections
const RATE_LIMIT = {
  maxInjectionsPerMinute: 10,
  lastInjectionTimes: [] as number[],
}

/**
 * Check if we're within rate limits.
 */
function isWithinRateLimit(): boolean {
  const now = Date.now()
  const oneMinuteAgo = now - 60000

  // Clean up old timestamps and keep the array bounded
  RATE_LIMIT.lastInjectionTimes = RATE_LIMIT.lastInjectionTimes
    .filter((t) => t > oneMinuteAgo)
    .slice(-RATE_LIMIT.maxInjectionsPerMinute)

  if (RATE_LIMIT.lastInjectionTimes.length >= RATE_LIMIT.maxInjectionsPerMinute) {
    console.warn(`[Ring:WARN] Rate limit reached (${RATE_LIMIT.maxInjectionsPerMinute}/min)`)
    return false
  }

  RATE_LIMIT.lastInjectionTimes.push(now)
  return true
}

export const RingInstructionReminder: Plugin = async ({ client, directory }) => {
  const projectRoot = directory
  const sessionId = getSessionId()
  const homeDir = process.env.HOME || ""

  const MAX_INSTRUCTION_FILE_SIZE_BYTES = 1024 * 1024

  /**
   * Find all instruction files, searching subdirectories.
   */
  const findInstructionFiles = (): Array<{ path: string; displayPath: string }> => {
    const files: Array<{ path: string; displayPath: string }> = []

    for (const fileName of INSTRUCTION_FILES) {
      // OpenCode config directory (preferred for OpenCode)
      const opencodeConfig = join(homeDir, ".config/opencode", fileName)
      if (existsSync(opencodeConfig)) {
        files.push({ path: opencodeConfig, displayPath: `~/.config/opencode/${fileName}` })
      }

      // Project root
      const projectPath = join(projectRoot, fileName)
      if (existsSync(projectPath)) {
        files.push({ path: projectPath, displayPath: fileName })
      }
    }

    // Deduplicate by path
    const seen = new Set<string>()
    return files.filter((f) => {
      if (seen.has(f.path)) return false
      seen.add(f.path)
      return true
    })
  }

  /**
   * Build reminder content from instruction files.
   */
  const buildReminder = (files: Array<{ path: string; displayPath: string }>, messageCount: number): string => {
    let reminder = `<instruction-files-reminder>
Re-reading instruction files to combat context drift (message ${messageCount}):

`

    for (const file of files) {
      // Avoid injecting extremely large files
      const st = statSync(file.path)
      if (st.size > MAX_INSTRUCTION_FILE_SIZE_BYTES) {
        console.warn(`[Ring:WARN] Skipping large instruction file: ${file.displayPath}`)
        continue
      }

      const content = readFileSync(file.path, "utf-8")
      // Escape content to prevent prompt injection
      const escapedContent = escapeAngleBrackets(content)

      reminder += `------------------------------------------------------------------------
${file.displayPath}
------------------------------------------------------------------------

${escapedContent}

`
    }

    reminder += `</instruction-files-reminder>

${AGENT_REMINDER}

${DUPLICATION_GUARD}`

    return reminder
  }

  return {
    event: async ({ event }) => {
      // Track messages via message.updated
      if (event.type !== EVENTS.MESSAGE_UPDATED) {
        return
      }

      // Filter to only count user messages to avoid double-counting.
      // If the message object isn't present (SDK mismatch), proceed rather than disabling the hook.
      const message = (event as any).properties?.message || (event as any).data?.message
      if (message && message.role !== "user") {
        return // Skip assistant messages
      }

      // Check rate limit
      if (!isWithinRateLimit()) {
        return
      }

      // Increment message count
      const state = incrementMessageCount(projectRoot, "reminder", sessionId)

      // Check if we should inject
      if (!shouldInject(projectRoot, "reminder", CONFIG.REMINDER_THROTTLE_MESSAGES, sessionId)) {
        return
      }

      // Find instruction files
      const files = findInstructionFiles()
      if (files.length === 0) {
        return
      }

      // Build reminder content
      const reminder = buildReminder(files, state.messageCount)

      // Mark that we're injecting
      incrementMessageCount(projectRoot, "reminder", sessionId, true)

      // Get current session and inject - SDK returns a RequestResult wrapper
      const sessionsResult = await client.session.list()
      if (sessionsResult.error) {
        console.warn(`[Ring:WARN] Failed to list sessions: ${sessionsResult.error}`)
        return
      }

      const sessions = sessionsResult.data ?? []
      const currentSession = sessions.sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))[0]

      if (!currentSession) {
        console.warn("[Ring:WARN] No sessions found, cannot inject instruction reminder")
        return
      }

      await client.session.prompt({
        path: { id: currentSession.id },
        body: {
          noReply: true,
          parts: [
            {
              type: "text",
              text: reminder,
            },
          ],
        },
      })

      console.log(`[Ring:INFO] Instruction files reminder injected (message ${state.messageCount})`)
    },
  }
}

export default RingInstructionReminder
