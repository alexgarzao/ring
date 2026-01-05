import type { Plugin } from "@opencode-ai/plugin"
import { existsSync, lstatSync } from "fs"
import { join } from "path"
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
type ShellExec = PromiseLike<unknown> & {
  quiet: () => Promise<unknown>
}

type Shell = (strings: TemplateStringsArray, ...values: unknown[]) => ShellExec

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
      if (!existsSync(candidate)) continue
      if (!isPathWithinRoot(candidate, projectRoot)) continue

      try {
        const st = lstatSync(candidate)
        if (st.isSymbolicLink()) continue
      } catch {
        continue
      }

      return candidate
    }
    return null
  }

  /**
   * Ensure Python dependencies are available.
   */
  const ensurePythonDeps = async (): Promise<boolean> => {
    const shell = $ as unknown as Shell
    try {
        await shell`python3 -c "import yaml"`.quiet()
      return true
    } catch {
      try {
        await shell`pip3 install --quiet --user 'PyYAML>=6.0'`
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

      // Extract file path from tool output metadata
      // NOTE: tool.execute.after output does not include args in the SDK typing.
      // Many tool implementations include args inside metadata.
      const metadata = output.metadata as any
      const rawPath =
        metadata?.args?.file_path ||
        metadata?.args?.filePath ||
        metadata?.args?.path ||
        metadata?.file_path ||
        metadata?.filePath ||
        metadata?.path

      if (typeof rawPath !== "string") {
        return
      }

      const filePath = rawPath.trim()
      if (!filePath || filePath.includes("\0")) {
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

      // Index the file using Bun's safe argument interpolation
      try {
        await $`python3 ${[indexer]} --file ${[filePath]} --project ${[projectRoot]}`
        console.log(`[Ring:INFO] Indexed artifact: ${filePath}`)
      } catch (err) {
        // Non-fatal - indexing is best-effort
        console.log(`[Ring:WARN] Failed to index ${filePath}: ${err}`)
      }
    },
  }
}

export default RingArtifactIndexWrite
