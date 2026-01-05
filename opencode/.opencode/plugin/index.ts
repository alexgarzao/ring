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
