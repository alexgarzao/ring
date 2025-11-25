#!/usr/bin/env bash
# SessionStart hook for ring-developers plugin
# Provides overview of available developer agents

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Generate agents overview
agents_overview="# Ring Developers Plugin

## Available Developer Agents

Use these specialized agents via Task tool with \`subagent_type\`:

| Agent | Expertise | Use For |
|-------|-----------|---------|
| \`ring-developers:backend-engineer-golang\` | Go, APIs, microservices, databases | Backend development, API design, database optimization |
| \`ring-developers:frontend-engineer\` | React, Next.js, TypeScript | UI components, state management, frontend architecture |
| \`ring-developers:devops-engineer\` | CI/CD, Docker, Kubernetes, IaC | Pipeline setup, containerization, infrastructure |
| \`ring-developers:qa-analyst\` | Testing strategies, automation | Test planning, E2E testing, quality gates |
| \`ring-developers:sre\` | Monitoring, reliability, performance | Observability, incident response, SLOs |

## Agent Selection Guide

**Use \`ring-developers:writing-code\` skill** to help identify the right agent for your task.

### Quick Selection:
- **Building APIs/services?** → \`backend-engineer-golang\`
- **Building UI/dashboards?** → \`frontend-engineer\`
- **Setting up pipelines/infra?** → \`devops-engineer\`
- **Writing tests/QA strategy?** → \`qa-analyst\`
- **Monitoring/reliability?** → \`sre\`

### Example Usage:
\`\`\`
Task tool with subagent_type=\"ring-developers:backend-engineer-golang\"
Prompt: \"Design a REST API for user authentication with JWT\"
\`\`\`"

# Escape for JSON
overview_escaped=$(echo "$agents_overview" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-developers-plugin>\n${overview_escaped}\n</ring-developers-plugin>"
  }
}
EOF

exit 0
