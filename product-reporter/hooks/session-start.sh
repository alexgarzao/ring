#!/usr/bin/env bash
# SessionStart hook for ring-product-reporter plugin
# Provides overview of FinOps agents and regulatory skills

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Generate plugin overview
plugin_overview="# Ring Product Reporter Plugin

## FinOps Agents

Use these specialized agents via Task tool with \`subagent_type\`:

| Agent | Purpose | Use For |
|-------|---------|---------|
| \`ring-product-reporter:finops-analyzer\` | Regulatory compliance analysis | Field mapping, compliance validation, regulatory analysis |
| \`ring-product-reporter:finops-automation\` | Template generation | Creating .tpl files, automating regulatory reports |

## Regulatory Template Skills

Brazilian financial regulatory compliance workflow:

| Skill | Gate | Purpose |
|-------|------|---------|
| \`ring-product-reporter:regulatory-templates\` | Orchestrator | Main workflow - guides through all gates |
| \`ring-product-reporter:regulatory-templates-setup\` | Setup | Template selection and context initialization |
| \`ring-product-reporter:regulatory-templates-gate1\` | Gate 1 | Compliance analysis and field mapping |
| \`ring-product-reporter:regulatory-templates-gate2\` | Gate 2 | Validate mappings and confirm specifications |
| \`ring-product-reporter:regulatory-templates-gate3\` | Gate 3 | Generate complete .tpl template file |

## Supported Regulations

- **BACEN** - Central Bank of Brazil (COSIF, CADOCs)
- **RFB** - Brazilian Federal Revenue (e-Financeira, SPED)
- **Open Banking** - Brazilian Open Banking specifications
- **DIMP** - Digital Payment Institutions Module
- **APIX** - API specifications for financial data

## Workflow Example

\`\`\`
1. Use Skill: ring-product-reporter:regulatory-templates
2. Follow gate progression: Setup → Gate 1 → Gate 2 → Gate 3
3. Output: Complete .tpl template file for Reporter platform
\`\`\`"

# Escape for JSON
overview_escaped=$(echo "$plugin_overview" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-product-reporter-plugin>\n${overview_escaped}\n</ring-product-reporter-plugin>"
  }
}
EOF

exit 0
