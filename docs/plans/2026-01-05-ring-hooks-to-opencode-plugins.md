# Ring Hooks to OpenCode TypeScript Plugins Conversion Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Convert all 9 Ring hook scripts to TypeScript plugins for OpenCode, maintaining full feature parity with the original bash/Python implementations.

**Architecture:** Event-driven TypeScript plugins using OpenCode's plugin API (`@opencode-ai/plugin`). Context injection via SDK `client.session.prompt({ noReply: true })`. State persistence in `.opencode/state/` directory. Python logic ported to TypeScript for consistency.

**Tech Stack:**
- TypeScript (`.ts` files)
- OpenCode Plugin API (`@opencode-ai/plugin`)
- Bun shell API (`$`) for subprocess execution with shescape for argument escaping
- Node.js fs/path for file operations
- better-sqlite3 for database queries (no shell SQL injection)

**Global Prerequisites:**
- Environment: macOS/Linux, Node.js 18+, Bun runtime
- Tools: OpenCode installed and configured
- Access: Project directory with write access to `.opencode/`
- State: Working from `opencode/` subdirectory within Ring repo

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
cd /Users/fredamaral/repos/lerianstudio/ring/opencode
ls -la .opencode/plugin/  # Expected: existing plugin files (index.ts, session-start.ts, etc.)
which bun || echo "Bun not found"  # Expected: path to bun
node --version  # Expected: v18+ or v20+
```

---

## Historical Precedent

**Query:** "opencode plugin typescript hooks conversion"
**Index Status:** Populated

### Successful Patterns to Reference
- **ring-to-opencode (5f4ab0bac1a8)**: Successfully executed 49-task conversion plan across 8 phases with code review checkpoints. Skills, agents, and commands converted. Pattern: phased approach with CR checkpoints works well.

### Failure Patterns to AVOID
- None found in index for this topic.

### Related Past Plans
- `docs/plans/2026-01-04-ring-to-opencode-conversion.md`: Main conversion plan for skills/agents/commands.
- `docs/plans/2025-12-29-automatic-context-management.md`: Context management patterns.
- `docs/plans/2025-12-27-context-usage-warnings.md`: Context warning implementation.

---

## Event Mapping Reference

| Ring Event | OpenCode Event | Mapping Quality | Notes |
|------------|----------------|-----------------|-------|
| `SessionStart` | `session.created` | PARTIAL | No matcher support; must handle all cases |
| `UserPromptSubmit` | `message.updated` (workaround) | GAP | Track message count for throttling; filter user messages only |
| `PostToolUse` | `tool.execute.after` | GOOD | Direct mapping with tool name filter (case-insensitive) |
| `PreCompact` | `experimental.session.compacting` | GOOD | Direct mapping |
| `Stop` | `session.idle` | PARTIAL | Fires when AI stops responding |

---

## Phase 1: Foundation and Easy Wins (4 tasks)

### Task 1.1: Create package.json for Plugin Dependencies

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/package.json`

**Prerequisites:**
- OpenCode directory exists at `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/`

**Step 1: Create package.json with dependencies**

```json
{
  "name": "ring-opencode-plugins",
  "version": "1.0.0",
  "description": "Ring plugins for OpenCode - context injection, state management, and workflow automation",
  "type": "module",
  "dependencies": {
    "@opencode-ai/plugin": "0.1.0",
    "better-sqlite3": "9.0.0",
    "shescape": "2.1.0"
  },
  "devDependencies": {
    "@types/better-sqlite3": "7.6.8",
    "@types/node": "20.0.0",
    "typescript": "5.0.0"
  }
}
```

**Step 2: Verify file created**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/package.json`

**Expected output:**
```json
{
  "name": "ring-opencode-plugins",
  ...
}
```

**If Task Fails:**
1. Check directory exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/package.json`

---

### Task 1.2: Create State Directory and Utilities Module

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/state.ts`
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/state/.gitkeep`

**Prerequisites:**
- Task 1.1 complete (package.json exists)

**Step 1: Create state directory**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/state`

**Step 2: Create .gitkeep**

Run: `touch /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/state/.gitkeep`

**Step 3: Create state utility module**

```typescript
/**
 * State management utilities for Ring OpenCode plugins.
 * Provides session-isolated state persistence in .opencode/state/
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync, readdirSync, statSync, renameSync } from "fs"
import { join, dirname, resolve, relative, isAbsolute } from "path"
import { randomBytes } from "crypto"

// State directories - support both new and legacy locations
const STATE_DIRS = [".opencode/state", ".ring/state"]
// Primary state directory for writes
const STATE_DIR = ".opencode/state"

/**
 * Generate a cryptographically secure session ID.
 * Used as fallback when OPENCODE_SESSION_ID is not available.
 */
export function generateSecureSessionId(): string {
  return randomBytes(16).toString('hex')
}

// Global session ID cache to maintain consistency within a process
declare global {
  var _ringSecureSessionId: string | undefined
}

/**
 * Get the current session ID from environment or generate a secure one.
 * Supports both OPENCODE_SESSION_ID and CLAUDE_SESSION_ID for compatibility.
 */
export function getSessionId(): string {
  return process.env.OPENCODE_SESSION_ID ||
    process.env.CLAUDE_SESSION_ID ||
    (globalThis._ringSecureSessionId ??= generateSecureSessionId())
}

/**
 * Validate that a path is within the allowed root directory.
 * Prevents path traversal attacks.
 */
export function isPathWithinRoot(filePath: string, rootPath: string): boolean {
  const resolvedPath = resolve(filePath)
  const resolvedRoot = resolve(rootPath)
  const rel = relative(resolvedRoot, resolvedPath)
  return !rel.startsWith('..') && !isAbsolute(rel)
}

/**
 * Sanitize session ID for safe use in filenames.
 * Prevents path traversal attacks.
 */
export function sanitizeSessionId(sessionId: string): string {
  const sanitized = sessionId.replace(/[^a-zA-Z0-9_-]/g, "")
  if (!sanitized) return "unknown"
  return sanitized.slice(0, 64)
}

/**
 * Get the state directory path, creating it if needed.
 */
export function getStateDir(projectRoot: string): string {
  const stateDir = join(projectRoot, STATE_DIR)
  if (!existsSync(stateDir)) {
    mkdirSync(stateDir, { recursive: true })
  }
  return stateDir
}

/**
 * Sanitize state key for safe use in filenames.
 * Prevents path traversal attacks via key parameter.
 */
export function sanitizeKey(key: string): string {
  return key.replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 64) || "default"
}

/**
 * Get a state file path for a specific key and session.
 */
export function getStatePath(projectRoot: string, key: string, sessionId?: string): string {
  const stateDir = getStateDir(projectRoot)
  const safeKey = sanitizeKey(key)
  const safeSession = sessionId ? sanitizeSessionId(sessionId) : "global"
  return join(stateDir, `${safeKey}-${safeSession}.json`)
}

/**
 * Find a state file across all supported state directories.
 * Reads from either location for backward compatibility.
 */
function findStatePath(projectRoot: string, key: string, sessionId?: string): string | null {
  const safeSession = sessionId ? sanitizeSessionId(sessionId) : "global"
  const filename = `${key}-${safeSession}.json`

  for (const dir of STATE_DIRS) {
    const statePath = join(projectRoot, dir, filename)
    if (existsSync(statePath)) {
      return statePath
    }
  }
  return null
}

/**
 * Read state from file, returning null if not found.
 */
export function readState<T>(projectRoot: string, key: string, sessionId?: string): T | null {
  // First try to find existing file in any supported location
  const existingPath = findStatePath(projectRoot, key, sessionId)
  const statePath = existingPath || getStatePath(projectRoot, key, sessionId)

  try {
    if (!existsSync(statePath)) return null
    const content = readFileSync(statePath, "utf-8")
    return JSON.parse(content) as T
  } catch (err) {
    console.debug(`[Ring:DEBUG] Failed to read state ${key}: ${err}`)
    return null
  }
}

/**
 * Write state to file atomically with secure temp file.
 * Uses restrictive permissions (0o600) for sensitive data.
 */
export function writeState<T>(projectRoot: string, key: string, data: T, sessionId?: string): void {
  const statePath = getStatePath(projectRoot, key, sessionId)
  const randomSuffix = randomBytes(8).toString('hex')
  const tempPath = `${statePath}.tmp.${randomSuffix}`

  try {
    mkdirSync(dirname(statePath), { recursive: true })
    writeFileSync(tempPath, JSON.stringify(data, null, 2), { encoding: "utf-8", mode: 0o600 })
    // Atomic rename
    renameSync(tempPath, statePath)
  } catch (err) {
    // Clean up temp file on error
    try { unlinkSync(tempPath) } catch {}
    throw err
  }
}

/**
 * Delete state file.
 */
export function deleteState(projectRoot: string, key: string, sessionId?: string): void {
  const statePath = getStatePath(projectRoot, key, sessionId)
  try {
    if (existsSync(statePath)) {
      unlinkSync(statePath)
    }
  } catch (err) {
    console.debug(`[Ring:DEBUG] Failed to delete state ${key}: ${err}`)
  }
}

/**
 * Clean up old state files (older than specified days).
 */
export function cleanupOldState(projectRoot: string, maxAgeDays: number = 7): void {
  const stateDir = getStateDir(projectRoot)
  const maxAgeMs = maxAgeDays * 24 * 60 * 60 * 1000
  const now = Date.now()

  try {
    const files = readdirSync(stateDir)
    for (const file of files) {
      if (!file.endsWith(".json")) continue
      const filePath = join(stateDir, file)
      const stats = statSync(filePath)
      if (now - stats.mtimeMs > maxAgeMs) {
        unlinkSync(filePath)
      }
    }
  } catch (err) {
    console.debug(`[Ring:DEBUG] Failed to cleanup old state: ${err}`)
  }
}

/**
 * JSON escape utility for safe string embedding.
 */
export function jsonEscape(str: string): string {
  return str
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r")
    .replace(/\t/g, "\\t")
}

/**
 * Sanitize content for safe inclusion in prompts.
 * Prevents prompt injection attacks.
 */
export function sanitizeForPrompt(content: string, maxLength: number = 500): string {
  return content
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .slice(0, maxLength)
}

/**
 * Escapes XML-like tags in content to prevent prompt injection.
 * Combined with sanitizeForPrompt() which escapes < and >,
 * this provides layered protection against malformed tag injection.
 *
 * The regex matches XML-like tags (e.g., <tag>, </tag>, <tag attr="val">)
 * and replaces < and > with HTML entities to neutralize them.
 */
export function escapeXmlTags(content: string): string {
  return content.replace(/<\/?[a-z][^>]*>/gi,
    m => `&#60;${m.slice(1,-1)}&#62;`)
}
```

**Step 4: Verify files created**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/`

**Expected output:**
```
state.ts
```

**If Task Fails:**
1. Check parent directory: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Create utils directory: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils`
3. Rollback: `rm -rf /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils`

---

### Task 1.3: Implement Artifact Index Write Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/artifact-index-write.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create the artifact index write plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync } from "fs"
import { join, resolve, dirname } from "path"
import { escape } from "shescape"
import { isPathWithinRoot } from "./utils/state"

/**
 * Ring Artifact Index Write Plugin
 * Indexes handoffs and plans immediately after Write tool execution.
 *
 * Equivalent to: default/hooks/artifact-index-write.sh
 * Event: tool.execute.after (matcher: Write)
 *
 * This plugin intercepts Write tool completions and indexes any files
 * written to docs/handoffs/ or docs/plans/ directories for searchability.
 */
export const RingArtifactIndexWrite: Plugin = async ({ $, directory }) => {
  const projectRoot = directory

  /**
   * Check if file should be indexed (handoff or plan).
   */
  const shouldIndex = (filePath: string): boolean => {
    return filePath.includes("/handoffs/") || filePath.includes("/plans/")
  }

  /**
   * Find the artifact indexer script.
   */
  const findIndexer = (): string | null => {
    const candidates = [
      join(projectRoot, ".opencode/lib/artifact-index/artifact_index.py"),
      join(projectRoot, ".ring/lib/artifact-index/artifact_index.py"),
      join(projectRoot, "default/lib/artifact-index/artifact_index.py"),
    ]

    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        return candidate
      }
    }
    return null
  }

  /**
   * Ensure Python dependencies are available.
   */
  const ensurePythonDeps = async (): Promise<boolean> => {
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

  return {
    "tool.execute.after": async (input, output) => {
      // Only process Write tool (case-insensitive)
      const toolName = input.tool?.toLowerCase() || ""
      if (!["write", "file.write"].includes(toolName)) {
        return
      }

      // Extract file path from tool arguments
      const filePath = String(
        output.args?.file_path ||
        output.args?.filePath ||
        output.args?.path ||
        ""
      )

      if (!filePath) {
        return
      }

      // Security: Validate path is within project
      if (!isPathWithinRoot(filePath, projectRoot)) {
        console.error(`[Ring:ERROR] BLOCKED: Path traversal attempt: ${filePath}`)
        return
      }

      // Check if this is a handoff or plan file
      if (!shouldIndex(filePath)) {
        return
      }

      // Find indexer
      const indexer = findIndexer()
      if (!indexer) {
        console.log("[Ring:INFO] Artifact indexer not found, skipping index")
        return
      }

      // Ensure Python dependencies
      const hasDeps = await ensurePythonDeps()
      if (!hasDeps) {
        console.log("[Ring:INFO] Python dependencies unavailable, skipping index")
        return
      }

      // Index the file using escaped arguments to prevent command injection
      try {
        const escapedIndexer = escape(indexer)
        const escapedFile = escape(filePath)
        const escapedProject = escape(projectRoot)
        await $`python3 ${[escapedIndexer]} --file ${[escapedFile]} --project ${[escapedProject]}`
        console.log(`[Ring:INFO] Indexed artifact: ${filePath}`)
      } catch (err) {
        // Non-fatal - indexing is best-effort
        console.log(`[Ring:WARN] Failed to index ${filePath}: ${err}`)
      }
    }
  }
}

export default RingArtifactIndexWrite
```

**Step 2: Verify file created**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/artifact-index-write.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync } from "fs"
...
```

**If Task Fails:**
1. Check plugin directory exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/artifact-index-write.ts`

---

### Task 1.4: Implement Task Completion Check Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/task-completion-check.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create the task completion check plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { writeState, getSessionId, sanitizeForPrompt } from "./utils/state"

/**
 * Ring Task Completion Check Plugin
 * Detects when all todos are complete and suggests handoff creation.
 *
 * Equivalent to: default/hooks/task-completion-check.sh
 * Event: todo.updated
 *
 * This plugin monitors todo list updates and:
 * 1. Persists todo state for outcome inference
 * 2. Injects handoff recommendation when all tasks complete
 */

interface Todo {
  content: string
  status: "pending" | "in_progress" | "completed"
  activeForm?: string
}

interface TodoEvent {
  type: "todo.updated"
  properties?: {
    todos?: Todo[]
  }
  data?: {
    todos?: Todo[]
  }
}

export const RingTaskCompletionCheck: Plugin = async ({ client, directory }) => {
  const projectRoot = directory

  return {
    event: async ({ event }) => {
      if (event.type !== "todo.updated") {
        return
      }

      const todoEvent = event as TodoEvent
      // Defensive payload handling - support both property paths
      const todos = todoEvent.properties?.todos || todoEvent.data?.todos || []

      // Runtime validation
      if (!Array.isArray(todos)) {
        console.warn("[Ring:WARN] Unexpected todo.updated payload structure - todos is not an array")
        return
      }

      if (todos.length === 0) {
        return
      }

      // Persist todos state for outcome inference
      const sessionId = getSessionId()
      writeState(projectRoot, "todos-state", todos, sessionId)

      // Count todos by status
      const total = todos.length
      const completed = todos.filter(t => t.status === "completed").length
      const inProgress = todos.filter(t => t.status === "in_progress").length
      const pending = todos.filter(t => t.status === "pending").length

      // Check if all todos are complete
      if (total > 0 && completed === total) {
        // Build task list for message (sanitized to prevent prompt injection)
        const taskList = todos.map(t => `- ${sanitizeForPrompt(t.content, 200)}`).join("\n")

        // Get current session - SDK returns array directly, not { data: [] }
        const sessions = await client.session.list()
        const currentSession = sessions
          // Note: Using any due to SDK type availability - replace with Session type when available
        .sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))
          [0]

        if (currentSession) {
          // Inject completion message
          await client.session.prompt({
            path: { id: currentSession.id },
            body: {
              noReply: true,
              parts: [{
                type: "text",
                text: `<MANDATORY-USER-MESSAGE>
TASK COMPLETION DETECTED - HANDOFF RECOMMENDED

All ${total} todos are marked complete.

**FIRST:** Run /context to check actual context usage.

**IF context is high (>70%):** Create handoff NOW:
1. Run /create-handoff to preserve this session's learnings
2. Document what worked and what failed in the handoff

**IF context is low (<70%):** Handoff is optional - you can continue with new tasks.

Completed tasks:
${taskList}
</MANDATORY-USER-MESSAGE>`
              }]
            }
          })

          console.log(`[Ring:INFO] All ${total} tasks complete - handoff recommended`)
        }
      } else if (completed > 0) {
        // Progress update - just log, don't inject
        console.log(`[Ring:INFO] Task progress: ${completed}/${total} complete, ${inProgress} in progress, ${pending} pending`)
      }
    }
  }
}

export default RingTaskCompletionCheck
```

**Step 2: Verify file created**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/task-completion-check.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { writeState, getSessionId, sanitizeForPrompt } from "./utils/state"
...
```

**If Task Fails:**
1. Verify state utilities exist: `ls /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/state.ts`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/task-completion-check.ts`

---

### Task 1.5: Implement Environment Protection Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/env-protection.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create the environment protection plugin**

```typescript
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
  /\.env(\..+)?$/,                    // .env, .env.local, .env.production
  /credentials?\.?(json|yaml|yml)?$/i, // credentials.json, credential.yaml
  /secrets?\.?(json|yaml|yml)?$/i,     // secrets.json, secret.yaml
  /\.(pem|key|p12|pfx|keystore|jks)$/i, // Private keys
  /id_(rsa|ed25519|ecdsa|dsa)$/,       // SSH keys
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
      const decoded = command.replace(/\\x([0-9a-f]{2})/gi, (_, hex) =>
        String.fromCharCode(parseInt(hex, 16))
      )

      for (const pattern of PROTECTED_PATTERNS) {
        if (pattern.test(command) || pattern.test(decoded)) {
          // Use word boundary regex for more robust command detection
          const commandPattern = new RegExp(`\\b(${READ_COMMANDS.join('|')})\\s`, 'i')
          const isReadAttempt = commandPattern.test(command) || commandPattern.test(decoded)
          if (isReadAttempt) {
            console.error(`[Ring:ERROR] BLOCKED: Attempted read of protected file pattern: ${pattern}`)
            throw new Error(`Security: Cannot read protected file matching ${pattern}`)
          }
        }
      }
    }
  }
}

export default RingEnvProtection
```

**Step 2: Verify file created**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/env-protection.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Environment Protection Plugin
...
```

**If Task Fails:**
1. Check plugin directory exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/env-protection.ts`

---

### Code Review Checkpoint 1

**Dispatch all 3 reviewers in parallel:**
- REQUIRED SUB-SKILL: Use requesting-code-review
- Review files created in Phase 1:
  - `.opencode/package.json`
  - `.opencode/plugin/utils/state.ts`
  - `.opencode/plugin/artifact-index-write.ts`
  - `.opencode/plugin/task-completion-check.ts`
  - `.opencode/plugin/env-protection.ts`

**Fix Critical/High/Medium issues before proceeding.**

---

## Phase 2: Core Hooks (5 tasks)

### Task 2.1: Enhance Session Start Plugin with Full Context Injection

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-start.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Replace session-start.ts with enhanced version**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync, statSync } from "fs"
import { join, dirname } from "path"
import { escape } from "shescape"
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
        .filter(f => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map(f => ({
          name: f,
          path: join(ledgerDir, f),
          mtime: statSync(join(ledgerDir, f)).mtimeMs
        }))
        .sort((a, b) => b.mtime - a.mtime)

      if (files.length === 0) return null

      const newest = files[0]
      const content = readFileSync(newest.path, "utf-8")

      // Extract current phase (line with [->] marker)
      const phaseMatch = content.match(/\[->/m)
      const currentPhase = phaseMatch
        ? content.split("\n").find(line => line.includes("[->"))?.trim() || ""
        : ""

      return {
        name: newest.name.replace(".md", ""),
        content,
        currentPhase
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
          const escapedGenerator = escape(generator)
          const result = await $`python3 ${[escapedGenerator]}`.text()
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
        .filter(d => statSync(join(skillDir, d)).isDirectory())
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
        .sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))
        [0]

      if (currentSession) {
        await client.session.prompt({
          path: { id: currentSession.id },
          body: {
            noReply: true,
            parts: [{
              type: "text",
              text: context
            }]
          }
        })

        console.log("[Ring:INFO] Context injected successfully")
        if (ledger) {
          console.log(`[Ring:INFO] Active ledger: ${ledger.name}`)
        }
      }
    }
  }
}

export default RingSessionStart
```

**Step 2: Verify file updated**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-start.ts`

**Expected output:**
```
~230 session-start.ts
```

**If Task Fails:**
1. Check file exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-start.ts`
2. Rollback: Restore from git `git checkout opencode/.opencode/plugin/session-start.ts`

---

### Task 2.2: Implement Ledger Save Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/ledger-save.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create the ledger save plugin**

```typescript
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
        .filter(f => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map(f => ({
          path: join(ledgerDir, f),
          mtime: statSync(join(ledgerDir, f)).mtimeMs
        }))
        .filter(f => !statSync(f.path).isSymbolicLink())
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
    const phaseMatch = content.split("\n").find(line => line.includes("[->"))
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
    }
  }
}

export default RingLedgerSave
```

**Step 2: Verify file created**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/ledger-save.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync, writeFileSync, readdirSync, statSync } from "fs"
...
```

**If Task Fails:**
1. Check plugin directory: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/ledger-save.ts`

---

### Task 2.3: Implement Session Outcome Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-outcome.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create the session outcome plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readdirSync, statSync } from "fs"
import { join } from "path"
import { escape } from "shescape"
import { readState, writeState, deleteState, getSessionId, sanitizeForPrompt } from "./utils/state"

/**
 * Ring Session Outcome Plugin
 * Prompts for previous session outcome grade after session clear/compact.
 *
 * Equivalent to: default/hooks/session-outcome.sh
 * Events:
 *   - session.compacted (after compact)
 *   - session.created (detect new session after compact)
 *
 * This plugin detects when a session has been compacted and prompts
 * the user to grade the previous session's outcome for learning extraction.
 *
 * NOTE: OpenCode doesn't have session.compacted event with matcher support,
 * so we use a state-based workaround to distinguish startup vs clear/compact.
 */

interface Todo {
  content: string
  status: "pending" | "in_progress" | "completed"
}

interface PendingOutcomePrompt {
  timestamp: number
}

// Maximum time between session.compacted and session.created to show outcome prompt
const OUTCOME_PROMPT_WINDOW_MS = 5000

export const RingSessionOutcome: Plugin = async ({ client, directory, $ }) => {
  const projectRoot = directory
  const sessionId = getSessionId()

  /**
   * Check for recent session work indicators.
   */
  const detectSessionWork = (): { hasWork: boolean; context: string[] } => {
    const context: string[] = []
    let hasWork = false

    // Check for todos state
    const todos = readState<Todo[]>(projectRoot, "todos-state", sessionId)
    if (todos && todos.length > 0) {
      hasWork = true
      const completed = todos.filter(t => t.status === "completed").length
      context.push(`Task progress: ${completed}/${todos.length} completed`)
    }

    // Check for active ledger (modified in last 2 hours)
    const ledgerDir = join(projectRoot, ".ring/ledgers")
    if (existsSync(ledgerDir)) {
      const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000)

      const ledgers = readdirSync(ledgerDir)
        .filter(f => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map(f => ({ name: f, path: join(ledgerDir, f) }))
        .filter(f => statSync(f.path).mtimeMs > twoHoursAgo)

      if (ledgers.length > 0) {
        hasWork = true
        context.push(`Ledger: ${ledgers[0].name.replace(".md", "")}`)
      }
    }

    // Check for recent handoffs
    const handoffDirs = [
      join(projectRoot, "docs/handoffs"),
      join(projectRoot, ".ring/handoffs")
    ]

    for (const dir of handoffDirs) {
      if (existsSync(dir)) {
        const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000)

        try {
          const handoffs = readdirSync(dir, { recursive: true })
            .filter(f => String(f).endsWith(".md"))
            .map(f => join(dir, String(f)))
            .filter(f => existsSync(f) && statSync(f).mtimeMs > twoHoursAgo)

          if (handoffs.length > 0) {
            hasWork = true
            const name = handoffs[0].split("/").pop()
            context.push(`Handoff: ${name}`)
            break
          }
        } catch (err) {
          console.debug(`[Ring:DEBUG] Failed to read handoffs: ${err}`)
        }
      }
    }

    return { hasWork, context }
  }

  /**
   * Find artifact marker script for saving outcome.
   */
  const findArtifactMarker = (): string | null => {
    const candidates = [
      join(projectRoot, ".opencode/lib/artifact-index/artifact_mark.py"),
      join(projectRoot, "default/lib/artifact-index/artifact_mark.py"),
    ]

    for (const candidate of candidates) {
      if (existsSync(candidate)) {
        return candidate
      }
    }
    return null
  }

  /**
   * Inject the outcome prompt.
   */
  const injectOutcomePrompt = async (contextStr: string): Promise<void> => {
    const artifactMarker = findArtifactMarker()

    let markerInstruction = ""
    if (artifactMarker) {
      const escapedMarker = escape(artifactMarker)
      markerInstruction = `

After user responds, save the grade using:
\`python3 ${escapedMarker} --outcome <GRADE>\``
    }

    // Get current session - SDK returns array directly
    const sessions = await client.session.list()
    const currentSession = sessions
      // Note: Using any due to SDK type availability - replace with Session type when available
        .sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))
      [0]

    if (currentSession) {
      await client.session.prompt({
        path: { id: currentSession.id },
        body: {
          noReply: true,
          parts: [{
            type: "text",
            text: `<MANDATORY-USER-MESSAGE>
PREVIOUS SESSION OUTCOME GRADE REQUESTED

You just cleared/compacted the previous session. Please ask the user to rate the PREVIOUS session's outcome.

**Previous Session Context:** ${sanitizeForPrompt(contextStr, 300)}

**MANDATORY ACTION:** Ask the user:
"How would you rate the previous session's outcome?"

Options:
- SUCCEEDED: All goals achieved, high quality output
- PARTIAL_PLUS: Most goals achieved (>=80%), minor issues
- PARTIAL_MINUS: Some progress (50-79%), significant gaps
- FAILED: Goals not achieved (<50%), major issues
${markerInstruction}

Then continue with the new session.
</MANDATORY-USER-MESSAGE>`
          }]
        }
      })

      console.log(`[Ring:INFO] Session outcome prompt injected (context: ${contextStr})`)
    }
  }

  return {
    // When session is compacted, set a flag for the next session.created
    "session.compacted": async () => {
      writeState(projectRoot, "pending-outcome-prompt", { timestamp: Date.now() } as PendingOutcomePrompt)
    },
    event: async ({ event }) => {
      // Handle session.created to check for pending outcome prompt
      if (event.type === "session.created") {
        const pending = readState<PendingOutcomePrompt>(projectRoot, "pending-outcome-prompt")
        if (pending && Date.now() - pending.timestamp < OUTCOME_PROMPT_WINDOW_MS) {
          // Clear the flag
          deleteState(projectRoot, "pending-outcome-prompt")

          // Check for session work
          const { hasWork, context } = detectSessionWork()

          if (hasWork) {
            const contextStr = context.join(", ")
            await injectOutcomePrompt(contextStr)
          } else {
            console.log("[Ring:INFO] No session work detected, skipping outcome prompt")
          }
        }
        return
      }

      // Also handle session.compacted directly if it fires
      if (event.type === "session.compacted") {
        const { hasWork, context } = detectSessionWork()

        if (!hasWork) {
          console.log("[Ring:INFO] No session work detected, skipping outcome prompt")
          return
        }

        const contextStr = context.join(", ")
        await injectOutcomePrompt(contextStr)
      }
    }
  }
}

export default RingSessionOutcome
```

**Step 2: Verify file created**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-outcome.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readdirSync, statSync } from "fs"
...
```

**If Task Fails:**
1. Check plugin directory: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-outcome.ts`

---

### Task 2.4: Enhance Context Injection Plugin

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-injection.ts`

**Prerequisites:**
- Existing context-injection.ts file

**Step 1: Replace with enhanced version that includes ledger**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync, readdirSync, statSync } from "fs"
import { join } from "path"

/**
 * Ring Context Injection Plugin (Enhanced)
 * Injects comprehensive Ring context during session compaction.
 *
 * Equivalent to: default/hooks/session-start.sh (compaction portion)
 * Event: experimental.session.compacting
 *
 * When OpenCode compacts session history for context management,
 * this plugin ensures critical Ring rules, skill information,
 * and continuity ledger state are preserved and re-injected.
 */

// Critical rules - abbreviated for compaction context
const CRITICAL_RULES_COMPACT = `**3-FILE RULE: HARD GATE** - >3 files = dispatch agent, no exceptions.
**AUTO-TRIGGER:** "fix issues" -> agent, "find where" -> Explore agent.
**TDD:** Test must fail (RED) before implementation.
**REVIEW:** All 3 reviewers must pass before merge.
**COMMIT:** Use /commit command for intelligent grouping.`

export const RingContextInjection: Plugin = async ({ directory }) => {
  const projectRoot = directory

  /**
   * Find and summarize active continuity ledger.
   */
  const getLedgerSummary = (): string | null => {
    const ledgerDir = join(projectRoot, ".ring/ledgers")

    if (!existsSync(ledgerDir)) {
      return null
    }

    try {
      const files = readdirSync(ledgerDir)
        .filter(f => f.startsWith("CONTINUITY-") && f.endsWith(".md"))
        .map(f => ({
          name: f.replace(".md", ""),
          path: join(ledgerDir, f),
          mtime: statSync(join(ledgerDir, f)).mtimeMs
        }))
        .sort((a, b) => b.mtime - a.mtime)

      if (files.length === 0) return null

      const ledger = files[0]
      const content = readFileSync(ledger.path, "utf-8")

      // Extract current phase
      const phaseLine = content.split("\n").find(line => line.includes("[->"))
      const currentPhase = phaseLine?.trim() || "No active phase"

      // Extract key sections for summary
      const sections: string[] = []

      // Get BRIEF_SUMMARY if present
      const briefMatch = content.match(/## BRIEF_SUMMARY\n([^#]+)/s)
      if (briefMatch) {
        sections.push(briefMatch[1].trim().slice(0, 200))
      }

      // Get UNCONFIRMED items from open questions
      const openQMatch = content.match(/## Open Questions \(UNCONFIRMED\)\n([^#]+)/s)
      if (openQMatch && openQMatch[1].includes("[ ]")) {
        const unconfirmed = openQMatch[1]
          .split("\n")
          .filter(line => line.includes("[ ]"))
          .slice(0, 3)
          .join("\n")
        if (unconfirmed) {
          sections.push(`**Open Questions:**\n${unconfirmed}`)
        }
      }

      return `## Active Ledger: ${ledger.name}
**Current Phase:** ${currentPhase}
${sections.join("\n\n")}

**Full ledger at:** .ring/ledgers/${ledger.name}.md`
    } catch (err) {
      console.debug(`[Ring:DEBUG] Failed to read ledger: ${err}`)
      return null
    }
  }

  return {
    "experimental.session.compacting": async (input, output) => {
      // Defensive check for output.context
      if (!output?.context || !Array.isArray(output.context)) {
        console.warn("[Ring:WARN] output.context not available or not an array, skipping injection")
        return
      }

      // Inject critical rules (compact version)
      output.context.push(`## Ring Critical Rules (Compact)
${CRITICAL_RULES_COMPACT}`)

      // Inject skills reference
      output.context.push(`## Ring Skills System

Key skills for common tasks:
- **test-driven-development**: TDD methodology (RED -> GREEN -> REFACTOR)
- **requesting-code-review**: Parallel review with 3 specialized reviewers
- **systematic-debugging**: 4-phase debugging methodology
- **writing-plans**: Create detailed implementation plans
- **executing-plans**: Execute plans in batches with review checkpoints
- **dispatching-parallel-agents**: Run multiple agents concurrently
- **verification-before-completion**: Ensure work complete before done

## Ring Commands

- /commit - Intelligent commit grouping
- /codereview - Dispatch 3 parallel reviewers
- /brainstorm - Socratic design refinement
- /execute-plan - Batch execution with checkpoints
- /worktree - Create isolated development branch
- /lint - Run and fix lint issues
- /create-handoff - Create session handoff document

## Ring Agents

- code-reviewer - Technical code quality review
- security-reviewer - Security vulnerability analysis
- business-logic-reviewer - Business requirements alignment
- codebase-explorer - Autonomous codebase exploration
- write-plan - Implementation planning agent`)

      // Inject ledger summary if present
      const ledgerSummary = getLedgerSummary()
      if (ledgerSummary) {
        output.context.push(ledgerSummary)
      }

      console.log("[Ring:INFO] Compaction context injected")
    }
  }
}

export default RingContextInjection
```

**Step 2: Verify file updated**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-injection.ts`

**Expected output:**
```
~130 context-injection.ts
```

**If Task Fails:**
1. Check file exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-injection.ts`
2. Rollback: `git checkout opencode/.opencode/plugin/context-injection.ts`

---

### Task 2.5: Update Plugin Index with New Exports

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`

**Prerequisites:**
- All Phase 1 and Phase 2 plugins created

**Step 1: Update index.ts with all plugin exports**

```typescript
/**
 * Ring OpenCode Plugins
 *
 * This module exports all Ring plugins for OpenCode.
 * Plugins provide session management, context injection,
 * notifications, security features, and workflow automation.
 */

// Core plugins
export { RingSessionStart } from "./session-start"
export { RingContextInjection } from "./context-injection"
export { RingNotification } from "./notification"
export { RingEnvProtection } from "./env-protection"

// Workflow plugins
export { RingArtifactIndexWrite } from "./artifact-index-write"
export { RingTaskCompletionCheck } from "./task-completion-check"
export { RingLedgerSave } from "./ledger-save"
export { RingSessionOutcome } from "./session-outcome"

// Default export for convenience
export { RingSessionStart as default } from "./session-start"
```

**Step 2: Verify file updated**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`

**Expected output:**
```typescript
/**
 * Ring OpenCode Plugins
 ...
export { RingArtifactIndexWrite } from "./artifact-index-write"
...
```

**If Task Fails:**
1. Check file exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`
2. Rollback: `git checkout opencode/.opencode/plugin/index.ts`

---

### Code Review Checkpoint 2

**Dispatch all 3 reviewers in parallel:**
- REQUIRED SUB-SKILL: Use requesting-code-review
- Review files created/modified in Phase 2:
  - `.opencode/plugin/session-start.ts` (enhanced)
  - `.opencode/plugin/ledger-save.ts`
  - `.opencode/plugin/session-outcome.ts`
  - `.opencode/plugin/context-injection.ts` (enhanced)
  - `.opencode/plugin/index.ts` (updated)

**Fix Critical/High/Medium issues before proceeding.**

---

## Phase 3: UserPromptSubmit Workarounds (4 tasks)

### Task 3.1: Create Message Tracking Utilities

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/message-tracking.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create message tracking utility module**

```typescript
/**
 * Message tracking utilities for Ring OpenCode plugins.
 *
 * OpenCode doesn't have a UserPromptSubmit equivalent, so we track
 * message counts via message.updated events to throttle periodic
 * context injection (like claude-md-reminder and context-usage-check).
 *
 * IMPORTANT: message.updated fires for both user and assistant messages.
 * Plugins should filter to only count user messages where appropriate.
 */

import { readState, writeState } from "./state"

interface MessageTrackingState {
  messageCount: number
  lastInjectionAt: number
  acknowledgedTier: string
}

const DEFAULT_STATE: MessageTrackingState = {
  messageCount: 0,
  lastInjectionAt: 0,
  acknowledgedTier: "none"
}

/**
 * Get the current message tracking state.
 */
export function getMessageState(
  projectRoot: string,
  key: string,
  sessionId?: string
): MessageTrackingState {
  const state = readState<MessageTrackingState>(projectRoot, `msg-${key}`, sessionId)
  return state || { ...DEFAULT_STATE }
}

/**
 * Increment message count and optionally update last injection time.
 */
export function incrementMessageCount(
  projectRoot: string,
  key: string,
  sessionId?: string,
  markInjection: boolean = false
): MessageTrackingState {
  const state = getMessageState(projectRoot, key, sessionId)
  state.messageCount++

  if (markInjection) {
    state.lastInjectionAt = state.messageCount
  }

  writeState(projectRoot, `msg-${key}`, state, sessionId)
  return state
}

/**
 * Check if we should inject based on throttle interval.
 */
export function shouldInject(
  projectRoot: string,
  key: string,
  throttleInterval: number,
  sessionId?: string
): boolean {
  const state = getMessageState(projectRoot, key, sessionId)
  const messagesSinceInjection = state.messageCount - state.lastInjectionAt
  return messagesSinceInjection >= throttleInterval
}

/**
 * Update acknowledged tier for tiered warnings.
 */
export function updateAcknowledgedTier(
  projectRoot: string,
  key: string,
  tier: string,
  sessionId?: string
): void {
  const state = getMessageState(projectRoot, key, sessionId)
  state.acknowledgedTier = tier
  writeState(projectRoot, `msg-${key}`, state, sessionId)
}

/**
 * Reset message tracking state.
 */
export function resetMessageState(
  projectRoot: string,
  key: string,
  sessionId?: string
): void {
  writeState(projectRoot, `msg-${key}`, { ...DEFAULT_STATE }, sessionId)
}
```

**Step 2: Verify file created**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/message-tracking.ts`

**Expected output:**
```typescript
/**
 * Message tracking utilities for Ring OpenCode plugins.
...
```

**If Task Fails:**
1. Check utils directory: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/message-tracking.ts`

---

### Task 3.2: Implement CLAUDE.md Reminder Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/instruction-reminder.ts`

**Prerequisites:**
- Task 3.1 complete (message tracking utilities exist)

**Step 1: Create the instruction reminder plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync } from "fs"
import { join, basename } from "path"
import { incrementMessageCount, shouldInject, getMessageState } from "./utils/message-tracking"
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
  REMINDER_THROTTLE_MESSAGES: 2
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
  lastInjectionTimes: [] as number[]
}

/**
 * Check if we're within rate limits.
 */
function isWithinRateLimit(): boolean {
  const now = Date.now()
  const oneMinuteAgo = now - 60000

  // Clean up old timestamps
  RATE_LIMIT.lastInjectionTimes = RATE_LIMIT.lastInjectionTimes.filter(t => t > oneMinuteAgo)

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
    return files.filter(f => {
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
        console.debug(`[Ring:DEBUG] message.updated structure: ${JSON.stringify({
          hasProperties: !!(event as any).properties,
          hasData: !!(event as any).data,
          keys: Object.keys(event),
          propertiesKeys: (event as any).properties ? Object.keys((event as any).properties) : [],
          dataKeys: (event as any).data ? Object.keys((event as any).data) : []
        })}`)
        _loggedEventStructure = true
      }

      // Filter to only count user messages to avoid double-counting
      // Note: This requires verification of OpenCode's event payload structure
      const message = (event as any).properties?.message || (event as any).data?.message
      if (message?.role !== "user") {
        return  // Skip assistant messages
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
        .sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))
        [0]

      if (currentSession) {
        await client.session.prompt({
          path: { id: currentSession.id },
          body: {
            noReply: true,
            parts: [{
              type: "text",
              text: reminder
            }]
          }
        })

        console.log(`[Ring:INFO] Instruction files reminder injected (message ${state.messageCount})`)
      }
    }
  }
}

export default RingInstructionReminder
```

**Step 2: Verify file created**

Run: `head -30 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/instruction-reminder.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, readFileSync } from "fs"
...
```

**If Task Fails:**
1. Check message tracking exists: `ls /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/message-tracking.ts`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/instruction-reminder.ts`

---

### Task 3.3: Implement Context Usage Check Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-usage-check.ts`

**Prerequisites:**
- Task 3.1 complete (message tracking utilities exist)

**Step 1: Create the context usage check plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import {
  getMessageState,
  incrementMessageCount,
  updateAcknowledgedTier,
  resetMessageState
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
  critical: 85
}

// Configuration for context estimation
// Formula: BASE_CONTEXT_PCT + (messageCount * PCT_PER_MESSAGE)
// Based on observed patterns: ~23% base usage + ~1.25% per message exchange
const CONFIG = {
  BASE_CONTEXT_PCT: 23,
  PCT_PER_MESSAGE: 1.25
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
    critical: 3
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
        console.debug(`[Ring:DEBUG] message.updated structure: ${JSON.stringify({
          hasProperties: !!(event as any).properties,
          hasData: !!(event as any).data,
          keys: Object.keys(event),
          propertiesKeys: (event as any).properties ? Object.keys((event as any).properties) : [],
          dataKeys: (event as any).data ? Object.keys((event as any).data) : []
        })}`)
        _loggedEventStructure = true
      }

      // Filter to only count user messages to avoid double-counting
      const message = (event as any).properties?.message || (event as any).data?.message
      if (message?.role !== "user") {
        return  // Skip assistant messages
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
        .sort((a: any, b: any) => (b.updatedAt || 0) - (a.updatedAt || 0))
        [0]

      if (currentSession) {
        await client.session.prompt({
          path: { id: currentSession.id },
          body: {
            noReply: true,
            parts: [{
              type: "text",
              text: warning
            }]
          }
        })

        console.log(`[Ring:INFO] Context warning injected: ${currentTier} (${estimatedPct}%)`)
      }
    }
  }
}

export default RingContextUsageCheck
```

**Step 2: Verify file created**

Run: `head -30 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-usage-check.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import {
  getMessageState,
...
```

**If Task Fails:**
1. Check message tracking exists: `ls /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/message-tracking.ts`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-usage-check.ts`

---

### Task 3.4: Update Plugin Index with Phase 3 Exports

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`

**Prerequisites:**
- All Phase 3 plugins created

**Step 1: Update index.ts with Phase 3 exports**

```typescript
/**
 * Ring OpenCode Plugins
 *
 * This module exports all Ring plugins for OpenCode.
 * Plugins provide session management, context injection,
 * notifications, security features, and workflow automation.
 */

// Core plugins
export { RingSessionStart } from "./session-start"
export { RingContextInjection } from "./context-injection"
export { RingNotification } from "./notification"
export { RingEnvProtection } from "./env-protection"

// Workflow plugins
export { RingArtifactIndexWrite } from "./artifact-index-write"
export { RingTaskCompletionCheck } from "./task-completion-check"
export { RingLedgerSave } from "./ledger-save"
export { RingSessionOutcome } from "./session-outcome"

// Context management plugins
export { RingInstructionReminder } from "./instruction-reminder"
export { RingContextUsageCheck } from "./context-usage-check"

// Default export for convenience
export { RingSessionStart as default } from "./session-start"
```

**Step 2: Verify file updated**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`

**Expected output:**
```typescript
...
export { RingInstructionReminder } from "./instruction-reminder"
export { RingContextUsageCheck } from "./context-usage-check"
...
```

**If Task Fails:**
1. Check file exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`
2. Rollback: `git checkout opencode/.opencode/plugin/index.ts`

---

### Code Review Checkpoint 3

**Dispatch all 3 reviewers in parallel:**
- REQUIRED SUB-SKILL: Use requesting-code-review
- Review files created/modified in Phase 3:
  - `.opencode/plugin/utils/message-tracking.ts`
  - `.opencode/plugin/instruction-reminder.ts`
  - `.opencode/plugin/context-usage-check.ts`
  - `.opencode/plugin/index.ts` (updated)

**Fix Critical/High/Medium issues before proceeding.**

---

## Phase 4: Python Logic Ports (4 tasks)

### Task 4.1: Implement Outcome Inference Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/outcome-inference.ts`

**Prerequisites:**
- Task 1.2 complete (state utilities exist)

**Step 1: Create the outcome inference plugin (TypeScript port)**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { readState, writeState, getSessionId } from "./utils/state"

/**
 * Ring Outcome Inference Plugin
 * Infers session outcome from todo state.
 *
 * Equivalent to: default/lib/outcome-inference/outcome_inference.py
 * Event: session.idle
 *
 * This plugin runs when a session goes idle and infers the outcome
 * based on todo completion status. The outcome is saved for
 * learning extraction to pick up.
 *
 * NOTE: outcome-inference and learning-extract both use session.idle.
 * learning-extract should run after outcome-inference completes.
 */

// Outcome constants
const OUTCOME = {
  SUCCEEDED: "SUCCEEDED",
  PARTIAL_PLUS: "PARTIAL_PLUS",
  PARTIAL_MINUS: "PARTIAL_MINUS",
  FAILED: "FAILED",
  UNKNOWN: "UNKNOWN"
} as const

type OutcomeType = typeof OUTCOME[keyof typeof OUTCOME]

interface Todo {
  content: string
  status: "pending" | "in_progress" | "completed"
}

interface OutcomeResult {
  outcome: OutcomeType
  reason: string
  confidence: "low" | "medium" | "high"
  sources: string[]
}

interface SessionOutcome {
  status: OutcomeType
  summary: string
  confidence: string
  inferred_at: string
  key_decisions: string[]
}

/**
 * Analyze todos and return counts.
 */
function analyzeTodos(todos: Todo[]): { total: number; completed: number; inProgress: number; pending: number } {
  if (!todos || todos.length === 0) {
    return { total: 0, completed: 0, inProgress: 0, pending: 0 }
  }

  return {
    total: todos.length,
    completed: todos.filter(t => t.status === "completed").length,
    inProgress: todos.filter(t => t.status === "in_progress").length,
    pending: todos.filter(t => t.status === "pending").length
  }
}

/**
 * Infer outcome from todo counts.
 */
function inferOutcomeFromTodos(
  total: number,
  completed: number,
  inProgress: number,
  pending: number
): { outcome: OutcomeType; reason: string } {
  if (total === 0) {
    return { outcome: OUTCOME.FAILED, reason: "No todos tracked - unable to measure completion" }
  }

  const completionRatio = completed / total

  if (completed === total) {
    return { outcome: OUTCOME.SUCCEEDED, reason: `All ${total} tasks completed` }
  }

  if (completionRatio >= 0.8) {
    const remaining = total - completed
    return { outcome: OUTCOME.PARTIAL_PLUS, reason: `${completed}/${total} tasks done, ${remaining} minor items remain` }
  }

  if (completionRatio >= 0.5) {
    return { outcome: OUTCOME.PARTIAL_MINUS, reason: `${completed}/${total} tasks done, significant work remains` }
  }

  // <50% completion is FAILED
  return {
    outcome: OUTCOME.FAILED,
    reason: `Insufficient progress: only ${completed}/${total} tasks completed (${Math.floor(completionRatio * 100)}%)`
  }
}

/**
 * Infer outcome from available state.
 */
function inferOutcome(todos: Todo[] | null): OutcomeResult {
  const result: OutcomeResult = {
    outcome: OUTCOME.UNKNOWN,
    reason: "Unable to determine outcome",
    confidence: "low",
    sources: []
  }

  if (todos !== null) {
    const { total, completed, inProgress, pending } = analyzeTodos(todos)
    const inferred = inferOutcomeFromTodos(total, completed, inProgress, pending)

    result.outcome = inferred.outcome
    result.reason = inferred.reason
    result.sources.push("todos")

    // Confidence based on completion clarity
    if (total === 0) {
      result.confidence = "high"  // Empty todos = high confidence it's a failure
    } else if (completed === total || completed === 0) {
      result.confidence = "high"
    } else if (completed / total >= 0.8 || completed / total <= 0.2) {
      result.confidence = "medium"
    } else {
      result.confidence = "low"
    }
  }

  return result
}

export const RingOutcomeInference: Plugin = async ({ directory }) => {
  const projectRoot = directory
  const sessionId = getSessionId()

  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") {
        return
      }

      console.log("[Ring:INFO] Session idle - inferring outcome...")

      // Read todos state
      const todos = readState<Todo[]>(projectRoot, "todos-state", sessionId)

      // Infer outcome
      const result = inferOutcome(todos)

      // Save outcome for learning extraction
      const outcome: SessionOutcome = {
        status: result.outcome,
        summary: result.reason,
        confidence: result.confidence,
        inferred_at: new Date().toISOString(),
        key_decisions: []
      }

      writeState(projectRoot, "session-outcome", outcome, sessionId)

      console.log(`[Ring:INFO] Outcome inferred: ${result.outcome} (${result.confidence} confidence) - ${result.reason}`)
    }
  }
}

export default RingOutcomeInference
```

**Step 2: Verify file created**

Run: `head -30 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/outcome-inference.ts`

**Expected output:**
```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { readState, writeState, getSessionId } from "./utils/state"
...
```

**If Task Fails:**
1. Check state utilities exist: `ls /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/state.ts`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/outcome-inference.ts`

---

### Task 4.2: Implement Learning Extract Plugin

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/learning-extract.ts`

**Prerequisites:**
- Task 4.1 complete (outcome inference exists)

**Step 1: Create the learning extract plugin (TypeScript port)**

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, writeFileSync, mkdirSync } from "fs"
import { join, dirname } from "path"
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
      await new Promise(r => setTimeout(r, delay))
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
      patterns: []
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
      patterns: []
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
      return arr.filter(item => {
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
      patterns: dedupe([...a.patterns, ...b.patterns])
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
    }
  }
}

export default RingLearningExtract
```

**Step 2: Verify file created**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/learning-extract.ts`

**Expected output:**
```
~230 learning-extract.ts
```

**If Task Fails:**
1. Check state utilities exist: `ls /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/state.ts`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/learning-extract.ts`

---

### Task 4.3: Update Plugin Index with Phase 4 Exports

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`

**Prerequisites:**
- All Phase 4 plugins created

**Step 1: Update index.ts with Phase 4 exports**

```typescript
/**
 * Ring OpenCode Plugins
 *
 * This module exports all Ring plugins for OpenCode.
 * Plugins provide session management, context injection,
 * notifications, security features, and workflow automation.
 */

// Core plugins
export { RingSessionStart } from "./session-start"
export { RingContextInjection } from "./context-injection"
export { RingNotification } from "./notification"
export { RingEnvProtection } from "./env-protection"

// Workflow plugins
export { RingArtifactIndexWrite } from "./artifact-index-write"
export { RingTaskCompletionCheck } from "./task-completion-check"
export { RingLedgerSave } from "./ledger-save"
export { RingSessionOutcome } from "./session-outcome"

// Context management plugins
export { RingInstructionReminder } from "./instruction-reminder"
export { RingContextUsageCheck } from "./context-usage-check"

// Session analytics plugins
export { RingOutcomeInference } from "./outcome-inference"
export { RingLearningExtract } from "./learning-extract"

// Default export for convenience
export { RingSessionStart as default } from "./session-start"
```

**Step 2: Verify file updated**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`

**Expected output:**
```typescript
...
export { RingOutcomeInference } from "./outcome-inference"
export { RingLearningExtract } from "./learning-extract"
...
```

**If Task Fails:**
1. Check file exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts`
2. Rollback: Restore previous version manually

---

### Task 4.4: Create Utils Index for Clean Imports

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/index.ts`

**Prerequisites:**
- All utility modules created

**Step 1: Create utils index**

```typescript
/**
 * Ring OpenCode Plugin Utilities
 *
 * Centralized exports for utility modules.
 */

export * from "./state"
export * from "./message-tracking"
```

**Step 2: Verify file created**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/index.ts`

**Expected output:**
```typescript
/**
 * Ring OpenCode Plugin Utilities
...
export * from "./state"
export * from "./message-tracking"
```

**If Task Fails:**
1. Check utils directory: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/index.ts`

---

### Code Review Checkpoint 4

**Dispatch all 3 reviewers in parallel:**
- REQUIRED SUB-SKILL: Use requesting-code-review
- Review files created in Phase 4:
  - `.opencode/plugin/outcome-inference.ts`
  - `.opencode/plugin/learning-extract.ts`
  - `.opencode/plugin/utils/index.ts`
  - `.opencode/plugin/index.ts` (final version)

**Fix Critical/High/Medium issues before proceeding.**

---

## Phase 5: Integration and Testing (3 tasks)

### Task 5.1: Create Plugin Test Script

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/test-plugins.ts`

**Prerequisites:**
- All plugins created

**Step 1: Create test script for plugin validation**

```typescript
#!/usr/bin/env bun
/**
 * Ring OpenCode Plugin Test Script
 *
 * Validates that all plugins:
 * 1. Export correctly
 * 2. Have proper type signatures
 * 3. Return valid hook objects
 *
 * Run with: bun .opencode/plugin/test-plugins.ts
 */

import * as plugins from "./index"

interface TestResult {
  name: string
  passed: boolean
  error?: string
}

const results: TestResult[] = []

// Mock context for plugin initialization
// SDK returns array directly, not { data: [] }
const mockContext = {
  project: { name: "test-project", path: "/tmp/test-project" },
  client: {
    session: {
      // Returns array with realistic session structure
      list: async () => [
        { id: "test-session-1", updatedAt: Date.now(), name: "Test Session" }
      ],
      prompt: async () => ({ success: true })
    }
  },
  // Mock Bun shell ($) with realistic structure
  $: Object.assign(
    async (strings: TemplateStringsArray, ...values: unknown[]) => ({
      text: async () => "",
      quiet: () => Promise.resolve({ text: async () => "" }),
      exitCode: 0
    }),
    { quiet: () => Promise.resolve({ text: async () => "" }) }
  ),
  directory: "/tmp/test-project",
  worktree: "/tmp/test-project"
}

async function testPlugin(name: string, plugin: any): Promise<TestResult> {
  try {
    // Check it's a function
    if (typeof plugin !== "function") {
      return { name, passed: false, error: "Not a function" }
    }

    // Initialize plugin
    const hooks = await plugin(mockContext)

    // Check it returns an object
    if (typeof hooks !== "object") {
      return { name, passed: false, error: "Does not return hooks object" }
    }

    // Check for valid hooks
    const validHooks = [
      "event",
      "tool.execute.before",
      "tool.execute.after",
      "experimental.session.compacting",
      "session.compacted"
    ]

    const hookKeys = Object.keys(hooks)
    for (const key of hookKeys) {
      if (!validHooks.includes(key) && key !== "tool") {
        return { name, passed: false, error: `Invalid hook: ${key}` }
      }
    }

    return { name, passed: true }
  } catch (err) {
    return { name, passed: false, error: String(err) }
  }
}

async function runTests() {
  console.log("Testing Ring OpenCode Plugins\n")
  console.log("=".repeat(50))

  const pluginEntries = Object.entries(plugins).filter(
    ([name]) => name !== "default" && name.startsWith("Ring")
  )

  for (const [name, plugin] of pluginEntries) {
    const result = await testPlugin(name, plugin)
    results.push(result)

    const status = result.passed ? "PASS" : "FAIL"
    console.log(`${status}: ${name}`)
    if (result.error) {
      console.log(`       Error: ${result.error}`)
    }
  }

  console.log("\n" + "=".repeat(50))

  const passed = results.filter(r => r.passed).length
  const failed = results.filter(r => !r.passed).length

  console.log(`\nResults: ${passed} passed, ${failed} failed`)

  if (failed > 0) {
    process.exit(1)
  }
}

runTests().catch(console.error)
```

**Step 2: Make script executable and test**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/test-plugins.ts`

**Expected output:**
```
(no output - chmod is silent on success)
```

**If Task Fails:**
1. Check file created: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/test-plugins.ts`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/test-plugins.ts`

---

### Task 5.2: Verify All Files Created

**Files:**
- None (verification only)

**Prerequisites:**
- All phases complete

**Step 1: Verify plugin directory structure**

Run: `find /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin -name "*.ts" | sort`

**Expected output:**
```
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/artifact-index-write.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-injection.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/context-usage-check.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/env-protection.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/index.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/instruction-reminder.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/learning-extract.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/ledger-save.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/notification.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/outcome-inference.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-outcome.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/session-start.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/task-completion-check.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/test-plugins.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/index.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/message-tracking.ts
/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/utils/state.ts
```

**Step 2: Count total plugins (should be 13 main + 3 utils + 1 test = 17)**

Run: `find /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin -name "*.ts" | wc -l`

**Expected output:**
```
17
```

**If Task Fails:**
1. List what's missing: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Review earlier tasks for failed file creations

---

### Task 5.3: Create Hook Mapping Documentation

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/README.md`

**Prerequisites:**
- All plugins created

**Step 1: Create README documenting the plugin system**

```markdown
# Ring OpenCode Plugins

This directory contains TypeScript plugins that port Ring's hook system to OpenCode.

## Plugins Overview

| Plugin | Ring Equivalent | OpenCode Event | Description |
|--------|-----------------|----------------|-------------|
| `session-start.ts` | `session-start.sh` | `session.created` | Context injection at session start |
| `context-injection.ts` | `session-start.sh` (compact) | `experimental.session.compacting` | Preserve context during compaction |
| `ledger-save.ts` | `ledger-save.sh` | `experimental.session.compacting`, `session.idle` | Save continuity ledger before compact/end |
| `session-outcome.ts` | `session-outcome.sh` | `session.compacted`, `session.created` | Prompt for session outcome grade |
| `artifact-index-write.ts` | `artifact-index-write.sh` | `tool.execute.after` | Index handoffs/plans on write |
| `task-completion-check.ts` | `task-completion-check.sh` | `todo.updated` | Detect all todos complete |
| `instruction-reminder.ts` | `claude-md-reminder.sh` | `message.updated` | Re-inject instruction files |
| `context-usage-check.ts` | `context-usage-check.sh` | `message.updated` | Context usage warnings |
| `outcome-inference.ts` | `outcome_inference.py` | `session.idle` | Infer session outcome |
| `learning-extract.ts` | `learning-extract.py` | `session.idle` | Extract session learnings |
| `notification.ts` | N/A | `session.idle` | Desktop notifications |
| `env-protection.ts` | N/A | `tool.execute.before` | Protect sensitive files |

## Event Mapping

| Ring Event | OpenCode Event | Notes |
|------------|----------------|-------|
| `SessionStart` | `session.created` | No matcher support |
| `UserPromptSubmit` | `message.updated` | Workaround via message count tracking; filter user messages only |
| `PostToolUse` | `tool.execute.after` | Filter by `input.tool` (case-insensitive) |
| `PreCompact` | `experimental.session.compacting` | Direct mapping |
| `Stop` | `session.idle` | Fires when AI stops |
| N/A | `session.compacted` | After compaction complete (state-based workaround) |
| N/A | `todo.updated` | Todo list changes |

## State Management

State is persisted in `.opencode/state/` (with backward compat for `.ring/state/`):
- `{key}-{sessionId}.json` format
- Automatic cleanup of files >7 days old
- Atomic writes via temp file + rename with crypto random suffix
- Restrictive permissions (0o600) for sensitive data

## Session ID Handling

Session IDs are obtained from environment variables with secure fallback:
- Primary: `OPENCODE_SESSION_ID`
- Fallback: `CLAUDE_SESSION_ID`
- Secure fallback: Cryptographically random 16-byte hex (no process.ppid)

## Utilities

- `utils/state.ts` - State persistence helpers with path traversal protection
- `utils/message-tracking.ts` - Message count tracking for throttling

## Security Features

- **Path traversal protection**: All file paths validated against project root
- **Command injection prevention**: Uses `shescape` for shell argument escaping
- **SQL injection prevention**: Uses `better-sqlite3` with parameterized queries
- **Prompt injection prevention**: Content sanitization before injection
- **Secure temp files**: Crypto random suffix for atomic writes
- **Rate limiting**: Global limit on injections per minute

## Dependencies

Defined in `.opencode/package.json`:
- `@opencode-ai/plugin` - OpenCode plugin API (exact version: 0.1.0)
- `better-sqlite3` - Safe SQL queries (exact version: 9.0.0)
- `shescape` - Shell argument escaping (exact version: 2.1.0)
- `@types/better-sqlite3` - Type definitions
- `@types/node` - Node.js type definitions
- `typescript` - TypeScript compiler

## Testing

Run plugin tests:
```bash
cd opencode/.opencode/plugin
bun test-plugins.ts
```

## Known Limitations

1. **Real context usage**: Context estimation is based on message count, not actual API usage
2. **Event payload structure**: Some payload assumptions require verification against OpenCode's actual events
3. **message.updated double-counting**: Filters to user messages only but payload structure needs verification
```

**Step 2: Verify README created**

Run: `head -30 /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/README.md`

**Expected output:**
```markdown
# Ring OpenCode Plugins

This directory contains TypeScript plugins that port Ring's hook system to OpenCode.
...
```

**If Task Fails:**
1. Check directory exists: `ls -la /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/`
2. Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/opencode/.opencode/plugin/README.md`

---

### Final Code Review Checkpoint

**Dispatch all 3 reviewers in parallel:**
- REQUIRED SUB-SKILL: Use requesting-code-review
- Review all files in Phase 5:
  - `.opencode/plugin/test-plugins.ts`
  - `.opencode/plugin/README.md`
  - `.opencode/package.json`

**Fix Critical/High/Medium issues before completing.**

---

## Summary

This plan converts all 9 Ring hooks to OpenCode TypeScript plugins across 5 phases:

| Phase | Tasks | Key Deliverables |
|-------|-------|------------------|
| 1: Foundation | 5 | package.json, state utilities, artifact-index, task-completion, env-protection |
| 2: Core Hooks | 5 | session-start, ledger-save, session-outcome, context-injection |
| 3: Workarounds | 4 | message-tracking, instruction-reminder, context-usage-check |
| 4: Python Ports | 4 | outcome-inference, learning-extract |
| 5: Integration | 3 | test script, verification, documentation |

**Total: 21 tasks + 5 code review checkpoints**

**Files Created/Modified:**
- 13 plugin files (`.ts`) - includes env-protection.ts
- 3 utility files (`utils/*.ts`)
- 1 test file (`test-plugins.ts`)
- 1 configuration file (`package.json`)
- 1 documentation file (`README.md`)
- 1 state directory placeholder (`.gitkeep`)

**Feature Parity:**
- All 9 Ring hooks ported
- Context injection via SDK
- State persistence in `.opencode/state/`
- Python logic ported to TypeScript

### Known Behavioral Differences
- **Context usage warnings are estimated** from message count, not actual API context usage (OpenCode API doesn't expose context metrics)
- **Event payload structures** may need verification against actual OpenCode runtime

---

## Review Fixes Applied

This plan was updated to address all issues identified by the Code Quality, Security, and Business Logic reviewers:

### CRITICAL Issues Fixed (7)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| C1 | Wrong API Access Pattern | Changed `sessions.data?.[0]` to `sessions[0]` with sort by `updatedAt` throughout all plugins |
| C2 | SQL Injection in learning-extract.ts | Replaced shell sqlite3 with `better-sqlite3` library using parameterized queries |
| C3 | Command Injection via Bun Shell | Added `shescape` dependency and `escape()` calls for all shell arguments |
| C4 | Session ID Spoofing | Replaced `process.ppid` with `randomBytes(16).toString('hex')` via `getSessionId()` helper |
| C5 | SessionStart Core two Lost | Added state-based workaround in session-outcome.ts using pending-outcome-prompt state |
| C6 | message.updated Double-Counting | Added user message filtering (`message?.role !== "user"`) with payload verification note |
| C7 | ledger-save Missing Stop Handler | Added `session.idle` event handler alongside compacting handler |

### HIGH Issues Fixed (16)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| H1 | Undocumented Event Payload Assumptions | Added runtime validation and defensive handling for all event payloads |
| H2 | No "Current Session" API | Added sorting by `updatedAt` before taking first session |
| H3 | Wrong Instruction Paths | Changed `~/.claude/` to `~/.config/opencode/` |
| H4 | Unused Imports | Removed `readdirSync, statSync` from instruction-reminder.ts |
| H5 | OPENCODE_SESSION_ID Env Var | Support both `OPENCODE_SESSION_ID` and `CLAUDE_SESSION_ID` |
| H6 | Path Traversal Protection | Added `isPathWithinRoot()` function to all file operations |
| H7 | env-protection Bypass Vectors | Enhanced with regex patterns note in README |
| H8 | Prompt Injection Sanitization | Added `sanitizeForPrompt()` function and applied to injected content |
| H9 | Insecure Temp Files | Changed to `randomBytes(8).toString('hex')` suffix |
| H10 | Rate Limiting | Added global rate limiting in instruction-reminder.ts |
| H11 | Real Context Usage Missing | Added comment documenting limitation in context-usage-check.ts |
| H12 | State Directory Backward Compatibility | Added support for both `.opencode/state` and `.ring/state` |
| H13 | SQLite CLI to better-sqlite3 | Added to package.json and updated learning-extract.ts |
| H14 | PyYAML Auto-Install | Added `ensurePythonDeps()` function in session-start.ts and artifact-index-write.ts |
| H15 | Tool Name Matching | Changed to case-insensitive matching with array check |
| H16 | Prompt Injection in Task Content | Applied `sanitizeForPrompt()` to todo content |

### MEDIUM Issues Fixed (18)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| M1 | Inline require() in state.ts | Moved `renameSync` to top-level import |
| M2 | Empty .gitkeep Step | Added explicit command: `touch .../.gitkeep` |
| M3 | Test Mock Context | Fixed mock to return array directly |
| M4 | Context Estimation Formula | Added `CONFIG` object with documented constants |
| M5 | Multiple Plugins Same Event | Added coordination comment and 100ms delay in learning-extract |
| M6 | Silent Error Handling | Added logging with `console.debug()` for errors |
| M7 | Wrong Instruction Paths | Removed `~/.claude/` checks |
| M8 | Sensitive Data in State Files | Added `mode: 0o600` to writeFileSync calls |
| M9 | Insufficient Security Logging | Added `[Ring:ERROR]` prefix for security events |
| M10 | XML Tag Injection | Added `escapeXmlTags()` function |
| M11 | Dependency Pinning | Changed to exact versions (no `^` prefix) |
| M12 | todo.updated Payload Verification | Added defensive handling for both property paths |
| M13 | Session ID Both Env Vars | Added support in `getSessionId()` |
| M14 | Atomic Write Consistency | Using imported renameSync |
| M15 | Subdirectory Search Missing | Search pattern documented in instruction-reminder |
| M16 | env-protection.ts Implementation Not Shown | Added Task 1.5 with full env-protection.ts implementation |
| M17 | Event Payload Structure Assumptions | Added debug logging with `_loggedEventStructure` in instruction-reminder.ts and context-usage-check.ts |
| M18 | session.idle Ordering Between Plugins | Changed learning-extract.ts to use `getSessionOutcomeWithRetry()` with state-based coordination and retry logic (100ms + 200ms retries) |

### LOW Issues Fixed (14)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| L1 | Console Log Prefixes | Standardized to `[Ring:INFO]`, `[Ring:WARN]`, `[Ring:ERROR]`, `[Ring:DEBUG]` |
| L2 | Magic Numbers | Extracted to CONFIG objects |
| L3 | README Code Blocks | Fixed markdown formatting |
| L4 | Throttle Interval Mismatch | Changed to 2 to match original bash |
| L5-L8 | Minor improvements | Various logging and validation improvements |
| L9 | Type Casting in Sort | Added type comment for `(a: any, b: any)` - "Note: Using any due to SDK type availability - replace with Session type when available" |
| L10 | 5-Second Window Magic Number | Extracted to named constant `OUTCOME_PROMPT_WINDOW_MS = 5000` in session-outcome.ts |
| L11 | Test Mock Incomplete | Updated test-plugins.ts mock with realistic session response structure and proper `$` function with `quiet()` method |
| L12 | Standardize Log Prefix Format | Verified all console.* calls use consistent `[Ring:LEVEL]` format |
| L13 | Throttle Interval Constant | Added `CONFIG.REMINDER_THROTTLE_MESSAGES` in instruction-reminder.ts |
| L14 | Add Comment for Known Limitations | Added inline comments in context-usage-check.ts: "KNOWN LIMITATION: Real context usage detection not available in OpenCode API" |

### Package.json Changes

```json
{
  "dependencies": {
    "@opencode-ai/plugin": "0.1.0",      // Exact version (was ^0.1.0)
    "better-sqlite3": "9.0.0",            // NEW: Safe SQL queries
    "shescape": "2.1.0"                   // NEW: Shell escaping
  },
  "devDependencies": {
    "@types/better-sqlite3": "7.6.8",     // NEW: Type definitions
    "@types/node": "20.0.0",              // Exact version
    "typescript": "5.0.0"                 // Exact version
  }
}
```

### Final Review Fixes Applied (Round 2)

Additional issues identified and fixed in the final review round:

#### HIGH Issues Fixed (2)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| NEW-H1 | Missing Defensive Check for output.context | Added null/array check in `ledger-save.ts` and `context-injection.ts` before using `output.context.push()` |
| NEW-H2 | Database Connection Leak on Error | Moved `db.close()` to finally block in `learning-extract.ts` with `let db: Database | null = null` pattern |

#### MEDIUM Issues Fixed (3)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| NEW-M1 | env-protection Command Detection Bypass | Replaced string includes check with word boundary regex: `new RegExp(\`\\b(${READ_COMMANDS.join('|')})\\s\`, 'i')` |
| NEW-M2 | State Key Path Traversal | Added `sanitizeKey()` function to validate key parameter and applied in `getStatePath()` |
| NEW-M3 | Context Estimation Limitation Not in Summary | Added "Known Behavioral Differences" section to Summary documenting estimation limitations |

#### LOW Issues Fixed (5)

| ID | Issue | Fix Applied |
|----|-------|-------------|
| NEW-L1 | env-protection Symlink Bypass | Added documentation comment explaining symlink bypass limitation and why it's not critical |
| NEW-L2 | Shell Invocation Pattern Coverage | Added documentation comment explaining shell invocation pattern limitations |
| NEW-L3 | Retry Timing Assumes Fast I/O | Increased retry delays in `learning-extract.ts` to total 400ms using `RETRY_DELAYS_MS = [100, 300]` array |
| NEW-L4 | Debug Logging Environment Gate | Added `process.env.RING_DEBUG` check before debug logging in `instruction-reminder.ts` and `context-usage-check.ts` |
| NEW-L5 | XML Tag Escape Regex Comment | Added explanatory JSDoc comment to `escapeXmlTags()` function describing layered protection approach |
