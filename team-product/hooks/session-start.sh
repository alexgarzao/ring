#!/usr/bin/env bash
# SessionStart hook for ring-team-product plugin
# Provides overview of pre-dev planning skills

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Generate plugin overview
plugin_overview="# Ring Team Product Plugin

## Pre-Development Planning Skills

Systematic 8-gate workflow for product feature planning:

### Gate Progression

| Gate | Skill | Output | Purpose |
|------|-------|--------|---------|
| 1 | \`ring-team-product:pre-dev-prd-creation\` | PRD.md | Business requirements (WHAT/WHY) |
| 2 | \`ring-team-product:pre-dev-feature-map\` | feature-map.md | Feature relationships and groupings |
| 3 | \`ring-team-product:pre-dev-trd-creation\` | TRD.md | Technical architecture (HOW) |
| 4 | \`ring-team-product:pre-dev-api-design\` | API.md | Component contracts and interfaces |
| 5 | \`ring-team-product:pre-dev-data-model\` | data-model.md | Entity relationships and schemas |
| 6 | \`ring-team-product:pre-dev-dependency-map\` | dependencies.md | Technology selection and dependencies |
| 7 | \`ring-team-product:pre-dev-task-breakdown\` | tasks.md | Work increments and estimates |
| 8 | \`ring-team-product:pre-dev-subtask-creation\` | subtasks.md | Atomic implementation units |

## Track Selection

### Small Features (<2 days)
Use 3-gate workflow: Gates 1, 3, 7
- Simple UI changes
- Bug fixes with clear scope
- Single-component features

### Large Features (≥2 days)
Use full 8-gate workflow: All gates
- New user flows
- Multi-service integration
- Database schema changes
- External API integration

## Quick Start

\`\`\`
# For small features:
/ring-default:pre-dev-feature [feature-name]

# For large features:
/ring-default:pre-dev-full [feature-name]
\`\`\`

## Output Location

All artifacts saved to: \`docs/pre-dev/{feature-name}/\`"

# Escape for JSON
overview_escaped=$(echo "$plugin_overview" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-team-product-plugin>\n${overview_escaped}\n</ring-team-product-plugin>"
  }
}
EOF

exit 0
