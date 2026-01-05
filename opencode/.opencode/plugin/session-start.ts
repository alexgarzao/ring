import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Session Start Plugin
 * Logs Ring initialization at session start.
 *
 * This plugin provides visual feedback when Ring is active,
 * helping users understand that the Ring skills system is available.
 */
export const RingSessionStart: Plugin = async ({ project }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        console.log("[Ring] Session started - Ring skills system active")
        console.log("[Ring] Skills available in .opencode/skill/")
        console.log("[Ring] Commands available in .opencode/command/")
        console.log("[Ring] Agents available in .opencode/agent/")
      }
    }
  }
}

export default RingSessionStart
