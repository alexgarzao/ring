import type { Plugin } from "@opencode-ai/plugin"
import {
  getMessageState,
  incrementMessageCount,
  updateAcknowledgedTier,
  resetMessageState,
} from "./utils/message-tracking"
import { getSessionId } from "./utils/state"

/**
 * Ring Context Usage Check Plugin
 * Estimates context usage and injects tiered warnings.
 *
 * Equivalent to: default/hooks/context-usage-check.sh
 * Event: message.updated (workaround for UserPromptSubmit)
 *
 * This plugin tracks message count and estimates context usage,
 * injecting warnings at different severity tiers:
 * - info (50%): Informational note
 * - warning (70%): Recommend handoff creation
 * - critical (85%): Mandatory handoff and clear
 *
 * IMPORTANT: Only counts user messages to avoid double-counting.
 *
 * NOTE: Real context usage detection requires OpenCode API support.
 * Currently using estimation only - this is a known limitation.
 * The formula is configurable but based on observed patterns.
 */

// Tiers and thresholds
type WarningTier = "none" | "info" | "warning" | "critical"

const TIER_THRESHOLDS = {
  info: 50,
  warning: 70,
  critical: 85,
}

// Configuration for context estimation
// Formula: BASE_CONTEXT_PCT + (messageCount * PCT_PER_MESSAGE)
// Based on observed patterns: ~23% base usage + ~1.25% per message exchange
const CONFIG = {
  BASE_CONTEXT_PCT: 23,
  PCT_PER_MESSAGE: 1.25,
}

// Debug: Track if we've logged event structure (for initial testing)
let _loggedEventStructure = false

/**
 * Estimate context usage from message count.
 * Approximation based on observed patterns.
 *
 * KNOWN LIMITATION: Real context usage detection not available in OpenCode API.
 * Using turn-count estimation instead - see README.md for details.
 */
function estimateContextPct(messageCount: number): number {
  // KNOWN LIMITATION: Real context usage detection not available in OpenCode API
  // Using turn-count estimation instead - see README.md for details
  const pct = CONFIG.BASE_CONTEXT_PCT + Math.floor(messageCount * CONFIG.PCT_PER_MESSAGE)
  return Math.min(pct, 100)
}

/**
 * Determine warning tier from percentage.
 */
function getWarningTier(pct: number): WarningTier {
  if (pct >= TIER_THRESHOLDS.critical) return "critical"
  if (pct >= TIER_THRESHOLDS.warning) return "warning"
  if (pct >= TIER_THRESHOLDS.info) return "info"
  return "none"
}

/**
 * Check if tier should be shown (escalation logic).
 */
function shouldShowTier(currentTier: WarningTier, acknowledgedTier: string): boolean {
  if (currentTier === "none") return false

  const tierPriority: Record<string, number> = {
    none: 0,
    info: 1,
    warning: 2,
    critical: 3,
  }

  // Always show critical
  if (currentTier === "critical") return true

  // Show if current tier is higher than acknowledged
  return tierPriority[currentTier] > tierPriority[acknowledgedTier]
}

/**
 * Format warning message for tier.
 */
function formatWarning(tier: WarningTier, pct: number): string {
  switch (tier) {
    case "critical":
      return `<MANDATORY-USER-MESSAGE>
[!!!] CONTEXT CRITICAL: ${pct}% usage (estimated).

**MANDATORY ACTIONS:**
1. STOP current task immediately
2. Run /create-handoff to save progress NOW
3. Create continuity-ledger with current state
4. Run /clear to reset context
5. Resume from handoff in new session

**Verify with /context if needed.**
</MANDATORY-USER-MESSAGE>`

    case "warning":
      return `<MANDATORY-USER-MESSAGE>
[!!] Context Warning: ${pct}% usage (estimated).

**RECOMMENDED ACTIONS:**
- Create a continuity-ledger to preserve session state
- Run: /create-handoff or manually create ledger

**Recommended:** Complete current task, then /clear before starting new work.
</MANDATORY-USER-MESSAGE>`

    case "info":
      return `[i] Context at ${pct}% (estimated). Consider creating a handoff if starting new work.`

    default:
      return ""
  }
}

export const RingContextUsageCheck: Plugin = async ({ client, directory }) => {
  const projectRoot = directory
  const sessionId = getSessionId()

  return {
    event: async ({ event }) => {
      // Reset state on session created
      if (event.type === "session.created") {
        resetMessageState(projectRoot, "context", sessionId)
        return
      }

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
      const message = (event as any).properties?.message || (event as any).data?.message
      if (message?.role !== "user") {
        return // Skip assistant messages
      }

      // Increment message count
      const state = incrementMessageCount(projectRoot, "context", sessionId)

      // Estimate context usage
      // KNOWN LIMITATION: Using turn-count estimation, not actual API context usage
      const estimatedPct = estimateContextPct(state.messageCount)
      const currentTier = getWarningTier(estimatedPct)

      // Check if we should show warning
      if (!shouldShowTier(currentTier, state.acknowledgedTier)) {
        return
      }

      // Format warning
      const warning = formatWarning(currentTier, estimatedPct)
      if (!warning) {
        return
      }

      // Update acknowledged tier
      updateAcknowledgedTier(projectRoot, "context", currentTier, sessionId)

      // Get current session and inject warning - SDK returns array directly
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
                text: warning,
              },
            ],
          },
        })

        console.log(`[Ring:INFO] Context warning injected: ${currentTier} (${estimatedPct}%)`)
      }
    },
  }
}

export default RingContextUsageCheck
