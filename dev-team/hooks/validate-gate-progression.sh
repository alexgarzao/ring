#!/usr/bin/env bash
# validate-gate-progression.sh
# PreToolUse hook for the lean backend ring:dev-cycle.
# Active backend gates:
#   Gate 0: implementation-owned TDD, coverage, local runtime, delivery verification
#   Gate 8: task-level review
#   Gate 9: user validation (not programmatically checked)

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

if [[ "$FILE_PATH" != *"current-cycle.json" ]] || [[ -z "$CONTENT" ]]; then
  exit 0
fi

if ! echo "$CONTENT" | jq empty 2>/dev/null; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Invalid JSON in current-cycle.json write"
    }
  }'
  exit 0
fi

STATE="$CONTENT"
CURRENT_TASK_INDEX=$(echo "$STATE" | jq -r '.current_task_index // 0')
TARGET_GATE=$(echo "$STATE" | jq -r '.current_gate // 0')
TASK_GATES=$(echo "$STATE" | jq -c ".tasks[$CURRENT_TASK_INDEX].gate_progress // {}")

errors=()

gate_to_num() {
  case "$1" in
    0) echo 0 ;;
    8) echo 8 ;;
    9) echo 9 ;;
    *) echo -1 ;;
  esac
}

validate_gate_0_for_subtask() {
  local idx="$1"
  local subtask_id current_gate tdd_red tdd_green delivery coverage threshold runtime_verified

  subtask_id=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].id // \"S-???\"")
  current_gate=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].current_gate // 0")

  if ! [[ "$current_gate" =~ ^[0-9]+$ ]] || [[ "$current_gate" -lt 1 ]]; then
    return
  fi

  tdd_red=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].gate_progress.implementation.tdd_red.status // \"pending\"")
  tdd_green=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].gate_progress.implementation.tdd_green.status // \"pending\"")
  delivery=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].gate_progress.implementation.delivery_verified // false")
  coverage=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].gate_progress.implementation.coverage_actual // 0")
  threshold=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].gate_progress.implementation.coverage_threshold // 85")
  runtime_verified=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks[$idx].gate_progress.implementation.local_runtime_verified // false")

  [[ "$tdd_red" == "completed" ]] || errors+=("Gate 0 ($subtask_id): TDD-RED not completed")
  [[ "$tdd_green" == "completed" ]] || errors+=("Gate 0 ($subtask_id): TDD-GREEN not completed")
  [[ "$delivery" == "true" ]] || errors+=("Gate 0 ($subtask_id): delivery verification missing")

  if ! [[ "$coverage" =~ ^[0-9]+\.?[0-9]*$ ]] || ! [[ "$threshold" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    errors+=("Gate 0 ($subtask_id): invalid coverage data")
  elif awk "BEGIN {exit !($coverage < $threshold)}"; then
    errors+=("Gate 0 ($subtask_id): coverage $coverage% < threshold $threshold%")
  fi

  if [[ "$runtime_verified" != "true" ]]; then
    errors+=("Gate 0 ($subtask_id): local runtime verification missing or explicitly false")
  fi
}

validate_gate_0() {
  local subtask_count
  subtask_count=$(echo "$STATE" | jq -r ".tasks[$CURRENT_TASK_INDEX].subtasks | length // 0")

  if [[ "$subtask_count" -eq 0 ]]; then
    local tdd_red tdd_green delivery coverage threshold runtime_verified
    tdd_red=$(echo "$TASK_GATES" | jq -r '.implementation.tdd_red.status // "pending"')
    tdd_green=$(echo "$TASK_GATES" | jq -r '.implementation.tdd_green.status // "pending"')
    delivery=$(echo "$TASK_GATES" | jq -r '.implementation.delivery_verified // false')
    coverage=$(echo "$TASK_GATES" | jq -r '.implementation.coverage_actual // 0')
    threshold=$(echo "$TASK_GATES" | jq -r '.implementation.coverage_threshold // 85')
    runtime_verified=$(echo "$TASK_GATES" | jq -r '.implementation.local_runtime_verified // false')

    [[ "$tdd_red" == "completed" ]] || errors+=("Gate 0: TDD-RED not completed")
    [[ "$tdd_green" == "completed" ]] || errors+=("Gate 0: TDD-GREEN not completed")
    [[ "$delivery" == "true" ]] || errors+=("Gate 0: delivery verification missing")
    if awk "BEGIN {exit !($coverage < $threshold)}"; then
      errors+=("Gate 0: coverage $coverage% < threshold $threshold%")
    fi
    [[ "$runtime_verified" == "true" ]] || errors+=("Gate 0: local runtime verification missing or explicitly false")
    return
  fi

  for ((i=0; i<subtask_count; i++)); do
    validate_gate_0_for_subtask "$i"
  done
}

validate_gate_8() {
  local status reviewer_count
  status=$(echo "$TASK_GATES" | jq -r '.review.status // "pending"')
  [[ "$status" == "completed" ]] || errors+=("Gate 8 (Review): not completed")

  reviewer_count=$(echo "$TASK_GATES" | jq -r '
    [.review.code_reviewer.verdict,
     .review.business_logic_reviewer.verdict,
     .review.security_reviewer.verdict,
     .review.nil_safety_reviewer.verdict,
     .review.test_reviewer.verdict,
     .review.consequences_reviewer.verdict,
     .review.dead_code_reviewer.verdict,
     .review.performance_reviewer.verdict,
     .review.multi_tenant_reviewer.verdict,
     .review.lib_commons_reviewer.verdict]
    | map(select(. != null and . != "")) | length
  ')

  if [[ "$status" == "completed" && "$reviewer_count" -lt 10 ]]; then
    errors+=("Gate 8 (Review): only $reviewer_count/10 reviewers have verdicts")
  fi
}

TARGET_NUM=$(gate_to_num "$TARGET_GATE")
if [[ "$TARGET_NUM" -eq -1 ]]; then
  jq -n --arg gate "$TARGET_GATE" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ("Invalid backend dev-cycle gate value: " + $gate + ". Expected active gates: 0, 8, 9.")
    }
  }'
  exit 0
fi

if [[ "$TARGET_NUM" -ge 8 ]]; then
  validate_gate_0
fi

if [[ "$TARGET_NUM" -ge 9 ]]; then
  validate_gate_8
fi

if [[ ${#errors[@]} -gt 0 ]]; then
  ERROR_JSON_ARRAY=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -sc .)
  jq -n --argjson errors "$ERROR_JSON_ARRAY" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ("Lean backend dev-cycle progression blocked:\n" + ($errors | map("- " + .) | join("\n")) + "\n\nRecovery: fix Gate 0 via ring:dev-implementation, then run Gate 8 via ring:codereview before Gate 9 validation.")
    }
  }'
  exit 0
fi

exit 0
