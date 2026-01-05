import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Environment Protection Plugin
 * Blocks read attempts of sensitive files containing credentials.
 *
 * Event: tool.execute.before
 *
 * This plugin intercepts Bash tool execution and blocks any attempts
 * to read files matching protected patterns (credentials, keys, etc.).
 */

const PROTECTED_PATTERNS = [
  /\.env(?:\.[^/\\]+)?$/, // .env, .env.local, .env.production
  /credentials?\.(?:json|ya?ml)$/i, // credentials.json, credentials.yaml
  /secrets?\.(?:json|ya?ml)$/i, // secrets.json, secret.yml
  /\.(?:pem|key|p12|pfx|keystore|jks)$/i, // Private keys
  /id_(?:rsa|ed25519|ecdsa|dsa)$/, // SSH keys
  /aws_credentials$/i,
  /\.npmrc$/,
  /\.netrc$/,
  /kubeconfig$/i,
]

const READ_COMMANDS = [
  "cat",
  "less",
  "more",
  "head",
  "tail",
  "grep",
  "awk",
  "sed",
  "xxd",
  "od",
  "strings",
  "python",
  "python3",
  "node",
  "ruby",
]

// Patterns that commonly enable bypassing naive read detection
const BYPASS_PATTERNS = [
  /\bbase64\b\s+(-d|--decode)\b/i,
  /\beval\b/i,
  /\bsource\b/i,
  /\b\.\s+[^\s]/, // `. file` source shorthand
  /\$\([^)]*\)/, // $(...)
  /`[^`]+`/, // backticks
  /\b(sh|bash|zsh)\b\s+-c\b/i,
]

export const RingEnvProtection: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash" && input.tool !== "Bash") return

      const command = String(output.args?.command || input.args?.command || "")

      // Decode potential hex escapes to prevent bypass
      const decoded = command.replace(/\\x([0-9a-f]{2})/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)))

      const combined = `${command}\n${decoded}`

      for (const pattern of PROTECTED_PATTERNS) {
        if (pattern.test(command) || pattern.test(decoded)) {
          // Use word boundary regex for more robust command detection
          const commandPattern = new RegExp(`\\b(${READ_COMMANDS.join("|")})\\b`, "i")
          const isReadAttempt = commandPattern.test(command) || commandPattern.test(decoded)

          // If a protected file is referenced AND the command contains a bypass-enabler,
          // block it even if we can't prove a direct read.
          const hasBypassPattern = BYPASS_PATTERNS.some((p) => p.test(combined))

          if (isReadAttempt || hasBypassPattern) {
            console.error(`[Ring:ERROR] BLOCKED: Attempted access of protected file pattern: ${pattern}`)
            throw new Error(`Security: Cannot access protected file matching ${pattern}`)
          }
        }
      }
    },
  }
}

export default RingEnvProtection
