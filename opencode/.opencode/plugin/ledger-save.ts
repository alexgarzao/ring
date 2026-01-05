import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync, writeFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

/**
 * Ring Ledger Save Plugin
 * Auto-saves active ledger before compaction and on session end.
 *
 * Equivalent to: default/hooks/ledger-save.sh
 * Events:
 *   - experimental.session.compacting (save before compact)
 *   - session.idle (save on session end)
 *
 * This plugin ensures the continuity ledger is saved with updated
 * timestamp before session compaction or end, preserving state.
 */

export const RingLedgerSave: Plugin = async ({ directory }) => {
  const projectRoot = directory

  /**
   * Find the most recently modified continuity ledger.
   */
  const findActiveLedger = (): string | null => {
    const ledgerDir = join(projectRoot, ".ring/ledgers")

    if (!existsSync(ledgerDir)) {
      return null
    }

    try {
      const files = readdirSync(ledgerDir)
        .filter((f) => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map((f) => ({
          path: join(ledgerDir, f),
          mtime: statSync(join(ledgerDir, f)).mtimeMs,
        }))
        .filter((f) => !statSync(f.path).isSymbolicLink())
        .sort((a, b) => b.mtime - a.mtime)

      return files.length > 0 ? files[0].path : null
    } catch (err) {
      console.debug(`[Ring:DEBUG] Failed to find ledger: ${err}`)
      return null
    }
  }

  /**
   * Update the ledger's timestamp.
   */
  const updateLedgerTimestamp = (ledgerPath: string): void => {
    const timestamp = new Date().toISOString()

    let content = readFileSync(ledgerPath, "utf-8")

    if (content.includes("Updated:")) {
      // Update existing timestamp
      content = content.replace(/^Updated:.*$/m, `Updated: ${timestamp}`)
    } else {
      // Append if missing
      content += `\nUpdated: ${timestamp}\n`
    }

    writeFileSync(ledgerPath, content, { encoding: "utf-8", mode: 0o600 })
  }

  /**
   * Save the ledger and return context info.
   */
  const saveLedger = (): { saved: boolean; ledgerName: string; currentPhase: string } | null => {
    const activeLedger = findActiveLedger()

    if (!activeLedger) {
      console.log("[Ring:INFO] No active ledger to save")
      return null
    }

    // Update timestamp
    updateLedgerTimestamp(activeLedger)

    const ledgerName = activeLedger.split("/").pop()?.replace(".md", "") || "unknown"

    // Extract current phase for context
    const content = readFileSync(activeLedger, "utf-8")
    const phaseMatch = content.split("\n").find((line) => line.includes("[->"))
    const currentPhase = phaseMatch?.trim() || "No active phase"

    console.log(`[Ring:INFO] Ledger saved: ${ledgerName}`)
    console.log(`[Ring:INFO] Current phase: ${currentPhase}`)

    return { saved: true, ledgerName, currentPhase }
  }

  return {
    "experimental.session.compacting": async (input, output) => {
      const result = saveLedger()

      if (result && output?.context && Array.isArray(output.context)) {
        // Inject ledger preservation note into compaction context
        output.context.push(`
## Continuity Ledger Preserved

The continuity ledger **${result.ledgerName}** has been saved.
Current phase: ${result.currentPhase}

After compact, the ledger will auto-restore on session resume.
`)
      }
    },
    event: async ({ event }) => {
      // Also save on session idle (session end)
      if (event.type === "session.idle") {
        saveLedger()
      }
    },
  }
}

export default RingLedgerSave
