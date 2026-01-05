import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Environment Protection Plugin
 * Prevents reading sensitive files (.env, credentials, keys).
 *
 * SECURITY: This plugin intercepts file read operations and blocks
 * access to files that commonly contain secrets, credentials, or
 * private keys. This prevents accidental exposure of sensitive
 * information during AI-assisted development.
 *
 * Protected file patterns:
 * - Environment files: .env, .env.local, .env.production, etc.
 * - Credential files: credentials.json, secrets.yaml, etc.
 * - Key files: *.pem, *.key, id_rsa, id_ed25519, etc.
 * - Certificate stores: *.p12, *.pfx
 */
export const RingEnvProtection: Plugin = async (ctx) => {
  const PROTECTED_PATTERNS = [
    // Environment files
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.staging",
    ".env.test",

    // Credential files
    "credentials",
    "secrets",
    "secret",

    // Key files
    ".pem",
    ".key",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",

    // Certificate stores
    ".p12",
    ".pfx",
    ".keystore",
    ".jks",

    // Cloud provider credentials
    "gcloud",
    "aws_credentials",
    ".aws/credentials",
    ".azure/credentials",

    // API keys and tokens
    "api_key",
    "apikey",
    "api-key",
    "token.json",
    "tokens.json",
  ]

  const isProtectedFile = (filePath: string): string | null => {
    const lowerPath = filePath.toLowerCase()

    for (const pattern of PROTECTED_PATTERNS) {
      if (lowerPath.includes(pattern)) {
        return pattern
      }
    }

    return null
  }

  return {
    "tool.execute.before": async (input, output) => {
      // Check file read operations
      if (input.tool === "read" || input.tool === "file_read") {
        const filePath = String(output.args?.filePath || output.args?.path || "")
        const matchedPattern = isProtectedFile(filePath)

        if (matchedPattern) {
          throw new Error(
            `Security: Cannot read protected file type (${matchedPattern}). ` +
              `This file may contain secrets or credentials. ` +
              `If you need to access this file, please do so manually outside of the AI session.`
          )
        }
      }

      // Also check bash/shell commands that might read protected files
      if (input.tool === "bash" || input.tool === "shell" || input.tool === "exec") {
        const command = String(output.args?.command || output.args?.cmd || "")

        // Commands that can read or expose file contents
        // KNOWN LIMITATION: Does not detect symlink-based bypasses
        // (e.g., ln -s .env safe-name && cat safe-name)
        // KNOWN LIMITATION: May not detect all shell invocation patterns
        // (e.g., sh -c "cat .env" or bash with piped input)
        const READ_COMMANDS = [
          "cat",
          "less",
          "more",
          "head",
          "tail",
          "grep",
          "sed",
          "awk",
          "python",
          "python3",
          "node",
          "ruby",
          "perl",
          "xargs",
          "source",
          "eval",
          "base64",
          "xxd",
          "hexdump",
          "strings",
          "tee",
          "cp",
          "scp",
          "rsync",
          "curl",
          "wget",
        ]

        // SECURITY: Use word boundary regex for more robust command detection
        // This prevents bypasses like "notcat .env" while still catching "cat .env"
        const commandPattern = new RegExp(`\\b(${READ_COMMANDS.join("|")})\\s`, "i")

        // Decode potential hex escapes to detect obfuscation attempts
        const decodedCommand = command.replace(/\\x([0-9a-f]{2})/gi, (_, hex) =>
          String.fromCharCode(parseInt(hex, 16))
        )

        // Check if command references any protected file pattern
        for (const pattern of PROTECTED_PATTERNS) {
          if (command.includes(pattern) || decodedCommand.includes(pattern)) {
            // Check if any read command is used with the protected pattern
            const usesReadCommand = commandPattern.test(command) || commandPattern.test(decodedCommand)
            // Also block if redirecting protected files via < or piping
            const usesRedirect = command.includes("<") || command.includes("|")

            if (usesReadCommand || usesRedirect) {
              throw new Error(
                `Security: Cannot access protected file type (${pattern}) via shell command. ` +
                  `This file may contain secrets or credentials.`
              )
            }
          }
        }
      }
    }
  }
}

export default RingEnvProtection
