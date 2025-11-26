#!/bin/bash
# Session start hook for ring-finops-team plugin
# Injects quick reference for FinOps regulatory agents

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-finops-team-system>\n**FinOps & Regulatory Compliance**\n\n2 specialist agents for Brazilian financial compliance:\n\n| Agent | Purpose |\n|-------|----------|\n| `ring-finops-team:finops-analyzer` | Field mapping & compliance analysis (Gates 1-2) |\n| `ring-finops-team:finops-automation` | Template generation in .tpl format (Gate 3) |\n\nWorkflow: Setup → Analyzer (compliance) → Automation (templates)\nSupported: BACEN, RFB, Open Banking, DIMP, APIX\n\nFor full details: Skill tool with \"ring-finops-team:using-finops-team\"\n</ring-finops-team-system>"
  }
}
EOF
