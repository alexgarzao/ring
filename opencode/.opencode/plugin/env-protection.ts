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
  /\.env(\..+)?$/, // .env, .env.local, .env.production
  /credentials?\.?(json|yaml|yml)?$/i, // credentials.json, credential.yaml
  /secrets?\.?(json|yaml|yml)?$/i, // secrets.json, secret.yaml
  /\.(pem|key|p12|pfx|keystore|jks)$/i, // Private keys
  /id_(rsa|ed25519|ecdsa|dsa)$/, // SSH keys
  /aws_credentials$/i,
  /\.npmrc$/,
  /\.netrc$/,
  /kubeconfig$/i,
]

const READ_COMMANDS = ["cat", "less", "more", "head", "tail", "grep", "awk", "sed", "xxd", "od", "strings"]

// KNOWN LIMITATION: Does not detect symlink-based bypasses
// (e.g., ln -s .env safe-name && cat safe-name)
// This requires file system write access which indicates higher privilege compromise

// KNOWN LIMITATION: May not detect all shell invocation patterns
// (e.g., sh -c "cat .env" or bash with piped input)
// Current implementation covers common direct read attempts

export const RingEnvProtection: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash" && input.tool !== "Bash") return

      const command = String(output.args?.command || input.args?.command || "")

      // Decode potential hex escapes to prevent bypass
      const decoded = command.replace(/\\x([0-9a-f]{2})/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)))

      for (const pattern of PROTECTED_PATTERNS) {
        if (pattern.test(command) || pattern.test(decoded)) {
          // Use word boundary regex for more robust command detection
          const commandPattern = new RegExp(`\\b(${READ_COMMANDS.join("|")})\\s`, "i")
          const isReadAttempt = commandPattern.test(command) || commandPattern.test(decoded)
          if (isReadAttempt) {
            console.error(`[Ring:ERROR] BLOCKED: Attempted read of protected file pattern: ${pattern}`)
            throw new Error(`Security: Cannot read protected file matching ${pattern}`)
          }
        }
      }
    },
  }
}

export default RingEnvProtection
