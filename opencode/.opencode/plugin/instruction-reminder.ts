import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync } from "fs"
import { join } from "path"
import { incrementMessageCount, shouldInject } from "./utils/message-tracking"
import { getSessionId, escapeXmlTags } from "./utils/state"

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

// Debug: Track if we've logged event structure (for initial testing)
let _loggedEventStructure = false

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

  // Clean up old timestamps
  RATE_LIMIT.lastInjectionTimes = RATE_LIMIT.lastInjectionTimes.filter((t) => t > oneMinuteAgo)

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
      const content = readFileSync(file.path, "utf-8")
      // Escape any XML-like tags to prevent prompt injection
      const escapedContent = escapeXmlTags(content)

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
      if (event.type !== "message.updated") {
        return
      }

      // Debug: Log event structure on first event to verify assumptions (only in debug mode)
      if (!_loggedEventStructure && process.env.RING_DEBUG) {
        console.debug(
          `[Ring:DEBUG] message.updated structure: ${JSON.stringify({
            hasProperties: !!(event as any).properties,
            hasData: !!(event as any).data,
            keys: Object.keys(event),
            propertiesKeys: (event as any).properties ? Object.keys((event as any).properties) : [],
            dataKeys: (event as any).data ? Object.keys((event as any).data) : [],
          })}`
        )
        _loggedEventStructure = true
      }

      // Filter to only count user messages to avoid double-counting
      // Note: This requires verification of OpenCode's event payload structure
      const message = (event as any).properties?.message || (event as any).data?.message
      if (message?.role !== "user") {
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

      // Get current session and inject - SDK returns array directly
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
                text: reminder,
              },
            ],
          },
        })

        console.log(`[Ring:INFO] Instruction files reminder injected (message ${state.messageCount})`)
      }
    },
  }
}

export default RingInstructionReminder
