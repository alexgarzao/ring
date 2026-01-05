import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, writeFileSync, mkdirSync } from "fs"
import { join } from "path"
import Database from "better-sqlite3"
import { readState, sanitizeSessionId, getSessionId } from "./utils/state"

/**
 * Ring Learning Extract Plugin
 * Extracts learnings from session for future reference.
 *
 * Equivalent to: default/hooks/learning-extract.py
 * Event: session.idle
 *
 * This plugin extracts learnings from:
 * 1. Handoffs database (artifact index) using better-sqlite3 (no SQL injection)
 * 2. Session outcome state
 *
 * Learnings are saved to .ring/cache/learnings/ for future queries.
 *
 * NOTE: outcome-inference and learning-extract both use session.idle.
 * This plugin should run after outcome-inference completes.
 * A brief delay is used to allow outcome-inference to save its state.
 */

interface Learnings {
  what_worked: string[]
  what_failed: string[]
  key_decisions: string[]
  patterns: string[]
}

interface SessionOutcome {
  status: string
  summary: string
  confidence: string
  key_decisions: string[]
}

interface HandoffRow {
  outcome: string
  what_worked: string
  what_failed: string
  key_decisions: string
}

export const RingLearningExtract: Plugin = async ({ directory }) => {
  const projectRoot = directory
  const sessionId = getSessionId()

  // Retry with increasing delays (total 400ms wait)
  const RETRY_DELAYS_MS = [100, 300]

  /**
   * Get session outcome with retry logic for coordination with outcome-inference.
   * outcome-inference may take variable time to complete on session.idle.
   */
  const getSessionOutcomeWithRetry = async (): Promise<SessionOutcome | null> => {
    // Try immediately
    let outcome = readState<SessionOutcome>(projectRoot, "session-outcome", sessionId)
    if (outcome) return outcome

    for (const delay of RETRY_DELAYS_MS) {
      await new Promise((r) => setTimeout(r, delay))
      outcome = readState<SessionOutcome>(projectRoot, "session-outcome", sessionId)
      if (outcome) return outcome
    }
    return null
  }

  /**
   * Extract learnings from handoffs database using better-sqlite3.
   * Uses parameterized queries to prevent SQL injection.
   */
  const extractFromHandoffs = async (): Promise<Learnings> => {
    const learnings: Learnings = {
      what_worked: [],
      what_failed: [],
      key_decisions: [],
      patterns: [],
    }

    const dbPath = join(projectRoot, ".ring/cache/artifact-index/context.db")
    if (!existsSync(dbPath)) {
      return learnings
    }

    let db: Database | null = null
    try {
      // Use better-sqlite3 with parameterized queries to prevent SQL injection
      db = new Database(dbPath, { readonly: true })

      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split("T")[0]

      const stmt = db.prepare(`
        SELECT outcome, what_worked, what_failed, key_decisions
        FROM handoffs
        WHERE created_at >= ?
        ORDER BY created_at DESC
        LIMIT 10
      `)

      const rows = stmt.all(yesterday) as HandoffRow[]

      const seenWorked = new Set<string>()
      const seenFailed = new Set<string>()
      const seenDecisions = new Set<string>()

      for (const row of rows) {
        if ((row.outcome === "SUCCEEDED" || row.outcome === "PARTIAL_PLUS") && row.what_worked) {
          if (!seenWorked.has(row.what_worked)) {
            learnings.what_worked.push(row.what_worked)
            seenWorked.add(row.what_worked)
          }
        }

        if ((row.outcome === "FAILED" || row.outcome === "PARTIAL_MINUS") && row.what_failed) {
          if (!seenFailed.has(row.what_failed)) {
            learnings.what_failed.push(row.what_failed)
            seenFailed.add(row.what_failed)
          }
        }

        if (row.key_decisions && !seenDecisions.has(row.key_decisions)) {
          learnings.key_decisions.push(row.key_decisions)
          seenDecisions.add(row.key_decisions)
        }
      }
    } catch (err) {
      console.log(`[Ring:WARN] Could not query handoffs database: ${err}`)
    } finally {
      db?.close()
    }

    return learnings
  }

  /**
   * Extract learnings from session outcome state.
   * Uses retry-based coordination to wait for outcome-inference.
   */
  const extractFromOutcome = async (): Promise<Learnings> => {
    const learnings: Learnings = {
      what_worked: [],
      what_failed: [],
      key_decisions: [],
      patterns: [],
    }

    // Use retry-based coordination with outcome-inference plugin
    const outcome = await getSessionOutcomeWithRetry()
    if (!outcome) {
      return learnings
    }

    const status = outcome.status || "unknown"
    if ((status === "SUCCEEDED" || status === "PARTIAL_PLUS") && outcome.summary) {
      learnings.what_worked.push(outcome.summary)
    } else if ((status === "FAILED" || status === "PARTIAL_MINUS") && outcome.summary) {
      learnings.what_failed.push(outcome.summary)
    }

    if (outcome.key_decisions && Array.isArray(outcome.key_decisions)) {
      learnings.key_decisions.push(...outcome.key_decisions)
    }

    return learnings
  }

  /**
   * Merge and deduplicate learnings.
   */
  const mergeLearnings = (a: Learnings, b: Learnings): Learnings => {
    const dedupe = (arr: string[]): string[] => {
      const seen = new Set<string>()
      return arr.filter((item) => {
        const normalized = item.toLowerCase().trim()
        if (seen.has(normalized)) return false
        seen.add(normalized)
        return true
      })
    }

    return {
      what_worked: dedupe([...a.what_worked, ...b.what_worked]),
      what_failed: dedupe([...a.what_failed, ...b.what_failed]),
      key_decisions: dedupe([...a.key_decisions, ...b.key_decisions]),
      patterns: dedupe([...a.patterns, ...b.patterns]),
    }
  }

  /**
   * Save learnings to file.
   */
  const saveLearnings = (learnings: Learnings): string => {
    const learningsDir = join(projectRoot, ".ring/cache/learnings")
    mkdirSync(learningsDir, { recursive: true })

    const dateStr = new Date().toISOString().split("T")[0]
    const safeSession = sanitizeSessionId(sessionId)
    const filename = `${dateStr}-${safeSession}.md`
    const filePath = join(learningsDir, filename)

    const now = new Date().toISOString().replace("T", " ").split(".")[0]

    let content = `# Learnings from Session ${safeSession}

**Date:** ${now}

## What Worked

`
    for (const item of learnings.what_worked) {
      content += `- ${item}\n`
    }
    if (learnings.what_worked.length === 0) {
      content += "- (No successful patterns recorded)\n"
    }

    content += `
## What Failed

`
    for (const item of learnings.what_failed) {
      content += `- ${item}\n`
    }
    if (learnings.what_failed.length === 0) {
      content += "- (No failures recorded)\n"
    }

    content += `
## Key Decisions

`
    for (const item of learnings.key_decisions) {
      content += `- ${item}\n`
    }
    if (learnings.key_decisions.length === 0) {
      content += "- (No key decisions recorded)\n"
    }

    content += `
## Patterns

`
    for (const item of learnings.patterns) {
      content += `- ${item}\n`
    }
    if (learnings.patterns.length === 0) {
      content += "- (No patterns identified)\n"
    }

    writeFileSync(filePath, content, { encoding: "utf-8", mode: 0o600 })
    return filePath
  }

  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") {
        return
      }

      console.log("[Ring:INFO] Extracting session learnings...")

      // Extract from both sources
      // Note: extractFromOutcome uses retry-based coordination with outcome-inference
      const handoffLearnings = await extractFromHandoffs()
      const outcomeLearnings = await extractFromOutcome()

      // Merge and deduplicate
      const learnings = mergeLearnings(handoffLearnings, outcomeLearnings)

      // Check if we have any learnings
      const hasLearnings =
        learnings.what_worked.length > 0 ||
        learnings.what_failed.length > 0 ||
        learnings.key_decisions.length > 0 ||
        learnings.patterns.length > 0

      if (hasLearnings) {
        const filePath = saveLearnings(learnings)
        const relativePath = filePath.replace(projectRoot + "/", "")
        console.log(`[Ring:INFO] Session learnings saved to ${relativePath}`)
      } else {
        console.log("[Ring:INFO] No learnings extracted from this session")
      }
    },
  }
}

export default RingLearningExtract
