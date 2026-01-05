import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"
import { cleanupOldState, deleteState, getSessionId } from "./utils/state"

/**
 * Ring Session Start Plugin (Enhanced)
 * Comprehensive context injection at session start.
 *
 * Equivalent to: default/hooks/session-start.sh
 * Event: session.created
 *
 * Features:
 * 1. Injects critical rules (3-file rule, agent triggers)
 * 2. Injects doubt-triggered questions pattern
 * 3. Loads and injects active continuity ledger
 * 4. Generates skills quick reference
 * 5. Resets context usage state
 * 6. Cleans up old state files
 */

// Critical rules that MUST survive compact
const CRITICAL_RULES = `## ORCHESTRATOR CRITICAL RULES (SURVIVE COMPACT)

**3-FILE RULE: HARD GATE**
DO NOT read/edit >3 files directly. This is a PROHIBITION.
- >3 files -> STOP. Launch specialist agent. DO NOT proceed manually.
- Already touched 3 files? -> At gate. Dispatch agent NOW.

**AUTO-TRIGGER PHRASES -> MANDATORY AGENT:**
- "fix issues/remaining/findings" -> Launch specialist agent
- "apply fixes", "fix the X issues" -> Launch specialist agent
- "find where", "search for", "understand how" -> Launch Explore agent

**If you think "this task is small" or "I can handle 5 files":**
WRONG. Count > 3 = agent. No exceptions. Task size is irrelevant.

**Full rules:** Use skill tool with "ring-default:using-ring" if needed.`

// Doubt-triggered questions pattern
const DOUBT_QUESTIONS = `## DOUBT-TRIGGERED QUESTIONS (WHEN TO ASK)

**Resolution hierarchy (check BEFORE asking):**
1. User dispatch context -> Did they already specify?
2. CLAUDE.md / repo conventions -> Is there a standard?
3. Codebase patterns -> What does existing code do?
4. Best practice -> Is one approach clearly superior?
5. **-> ASK** -> Only if ALL above fail AND affects correctness

**Genuine doubt criteria (ALL must be true):**
- Cannot resolve from hierarchy above
- Multiple approaches genuinely viable
- Choice significantly impacts correctness
- Getting it wrong wastes substantial effort

**Question quality - show your work:**
- GOOD: "Found PostgreSQL in docker-compose but MongoDB in docs.
    This feature needs time-series. Which should I extend?"
- BAD: "Which database should I use?"

**If proceeding without asking:**
State assumption -> Explain why -> Note what would change it`

/**
 * Ensure Python dependencies are available.
 */
const ensurePythonDeps = async ($: any): Promise<boolean> => {
  try {
    await $`python3 -c "import yaml"`.quiet()
    return true
  } catch {
    try {
      await $`pip3 install --quiet --user 'PyYAML>=6.0'`
      return true
    } catch (err) {
      console.warn(`[Ring:WARN] Failed to install PyYAML: ${err}`)
      return false
    }
  }
}

export const RingSessionStart: Plugin = async ({ client, directory, $ }) => {
  const projectRoot = directory
  const sessionId = getSessionId()

  /**
   * Find and read the active continuity ledger.
   */
  const findActiveLedger = (): { name: string; content: string; currentPhase: string } | null => {
    const ledgerDir = join(projectRoot, ".ring/ledgers")

    if (!existsSync(ledgerDir)) {
      return null
    }

    try {
      const files = readdirSync(ledgerDir)
        .filter((f) => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map((f) => ({
          name: f,
          path: join(ledgerDir, f),
          mtime: statSync(join(ledgerDir, f)).mtimeMs,
        }))
        .sort((a, b) => b.mtime - a.mtime)

      if (files.length === 0) return null

      const newest = files[0]
      const content = readFileSync(newest.path, "utf-8")

      // Extract current phase (line with [->] marker)
      const phaseMatch = content.match(/\[->/m)
      const currentPhase = phaseMatch ? content.split("\n").find((line) => line.includes("[->"))?.trim() || "" : ""

      return {
        name: newest.name.replace(".md", ""),
        content,
        currentPhase,
      }
    } catch (err) {
      console.debug(`[Ring:DEBUG] Failed to read ledger: ${err}`)
      return null
    }
  }

  /**
   * Generate skills quick reference.
   * Tries Python script first, then TypeScript fallback.
   */
  const generateSkillsOverview = async (): Promise<string> => {
    // Ensure Python dependencies first
    await ensurePythonDeps($)

    // Try to find and run the Python generator
    const pythonGenerators = [
      join(projectRoot, "default/hooks/generate-skills-ref.py"),
      join(projectRoot, ".ring/hooks/generate-skills-ref.py"),
    ]

    for (const generator of pythonGenerators) {
      if (existsSync(generator)) {
        try {
          const result = await $`python3 ${[generator]}`.text()
          return result
        } catch (err) {
          console.debug(`[Ring:DEBUG] Python generator failed: ${err}`)
          continue
        }
      }
    }

    // Fallback: Generate minimal reference from .opencode/skill/
    const skillDir = join(projectRoot, ".opencode/skill")
    if (!existsSync(skillDir)) {
      return `# Ring Skills Quick Reference

**Note:** Skills directory not found.
Skills are available via the skill() tool.

Run: \`skill: "using-ring"\` to see available workflows.`
    }

    try {
      const skills = readdirSync(skillDir)
        .filter((d) => statSync(join(skillDir, d)).isDirectory())
        .sort()

      let overview = "# Ring Skills Quick Reference\n\n"
      overview += `**${skills.length} skills available**\n\n`

      for (const skill of skills.slice(0, 20)) {
        overview += `- **${skill}**\n`
      }

      if (skills.length > 20) {
        overview += `\n...and ${skills.length - 20} more\n`
      }

      overview += "\n## Usage\n"
      overview += "To use a skill: Use the skill() tool with skill name\n"
      overview += 'Example: `skill: "using-ring"`\n'

      return overview
    } catch (err) {
      console.debug(`[Ring:DEBUG] Failed to read skills: ${err}`)
      return "# Ring Skills Quick Reference\n\n**Error loading skills.**\n"
    }
  }

  return {
    event: async ({ event }) => {
      if (event.type !== "session.created") {
        return
      }

      console.log("[Ring:INFO] Session starting - injecting context...")

      // Reset context usage state for new session
      deleteState(projectRoot, "context-usage", sessionId)

      // Clean up old state files (> 7 days)
      cleanupOldState(projectRoot, 7)

      // Generate skills overview
      const skillsOverview = await generateSkillsOverview()

      // Find active ledger
      const ledger = findActiveLedger()

      // Build context to inject
      let context = `<ring-critical-rules>
${CRITICAL_RULES}
</ring-critical-rules>

<ring-doubt-questions>
${DOUBT_QUESTIONS}
</ring-doubt-questions>

<ring-skills-system>
${skillsOverview}
</ring-skills-system>`

      // Add ledger context if present
      if (ledger) {
        context += `

<ring-continuity-ledger>
## Active Continuity Ledger: ${ledger.name}

**Current Phase:** ${ledger.currentPhase || "No active phase marked"}

<continuity-ledger-content>
${ledger.content}
</continuity-ledger-content>

**Instructions:**
1. Review the State section - find [->] for current work
2. Check Open Questions for UNCONFIRMED items
3. Continue from where you left off
</ring-continuity-ledger>`
      }

      // Get current session and inject context
      // SDK returns array directly, not { data: [] }
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
                text: context,
              },
            ],
          },
        })

        console.log("[Ring:INFO] Context injected successfully")
        if (ledger) {
          console.log(`[Ring:INFO] Active ledger: ${ledger.name}`)
        }
      }
    },
  }
}

export default RingSessionStart
