#!/bin/bash
# Session start hook for ring-team-product plugin
# Injects quick reference for pre-dev planning workflow

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-team-product-system>\n**Pre-Dev Planning Skills**\n\n8 skills for structured feature planning (use via Skill tool):\n\n| Skill | Gate | Output |\n|-------|------|--------|\n| `ring-team-product:pre-dev-prd-creation` | 1 | PRD.md |\n| `ring-team-product:pre-dev-feature-map` | 2 | feature-map.md |\n| `ring-team-product:pre-dev-trd-creation` | 3 | TRD.md |\n| `ring-team-product:pre-dev-api-design` | 4 | API.md |\n| `ring-team-product:pre-dev-data-model` | 5 | data-model.md |\n| `ring-team-product:pre-dev-dependency-map` | 6 | dependencies.md |\n| `ring-team-product:pre-dev-task-breakdown` | 7 | tasks.md |\n| `ring-team-product:pre-dev-subtask-creation` | 8 | subtasks.md |\n\nEntry points: `/ring-default:pre-dev-feature` (gates 1,3,7) or `/ring-default:pre-dev-full` (all 8)\n\nFor full details: Skill tool with \"ring-team-product:using-team-product\"\n</ring-team-product-system>"
  }
}
EOF
