#!/bin/bash
# Session start hook for ring-developers plugin
# Injects quick reference for developer specialist agents

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-developers-system>\n**Developer Specialists Available**\n\nUse via Task tool with `subagent_type`:\n\n| Agent | Expertise |\n|-------|----------|\n| `ring-developers:backend-engineer-golang` | Go, APIs, microservices, databases |\n| `ring-developers:frontend-engineer` | React, TypeScript, UI, state management |\n| `ring-developers:devops-engineer` | CI/CD, Docker, Kubernetes, infrastructure |\n| `ring-developers:qa-analyst` | Testing, automation, quality gates |\n| `ring-developers:sre` | Monitoring, reliability, performance |\n\nFor full details: Skill tool with \"ring-developers:using-developers\"\n</ring-developers-system>"
  }
}
EOF
