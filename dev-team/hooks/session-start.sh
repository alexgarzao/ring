#!/bin/bash
# Session start hook for ring-dev-team plugin
# Injects quick reference for developer specialist agents

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-dev-team-system>\n**Developer Specialists Available**\n\nUse via Task tool with `subagent_type`:\n\n| Agent | Expertise |\n|-------|----------|\n| `ring-dev-team:backend-engineer-golang` | Go, APIs, microservices, databases |\n| `ring-dev-team:frontend-engineer` | React, TypeScript, UI, state management |\n| `ring-dev-team:frontend-designer` | Visual design, typography, motion, aesthetics |\n| `ring-dev-team:devops-engineer` | CI/CD, Docker, Kubernetes, infrastructure |\n| `ring-dev-team:qa-analyst` | Testing, automation, quality gates |\n| `ring-dev-team:sre` | Monitoring, reliability, performance |\n\nFor full details: Skill tool with \"ring-dev-team:using-dev-team\"\n</ring-dev-team-system>"
  }
}
EOF
