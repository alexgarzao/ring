#!/bin/bash
# Session start hook for ralph-wiggum plugin
# Injects quick reference for Ralph Wiggum commands

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ralph-wiggum-system>\n**Ralph Wiggum - Iterative AI Development Loops**\n\nAutonomous task refinement using Stop hooks. Claude works on a task until completion.\n\n**Commands:**\n| Command | Purpose |\n|---------|----------|\n| `/ralph-wiggum:ralph-loop PROMPT [--max-iterations N] [--completion-promise TEXT]` | Start iterative loop |\n| `/ralph-wiggum:cancel-ralph` | Cancel active loop |\n| `/ralph-wiggum:help` | Show Ralph technique guide |\n\n**How it works:**\n1. You provide a prompt with clear completion criteria\n2. Claude works on the task\n3. Stop hook intercepts exit, re-feeds prompt\n4. Loop continues until `<promise>TEXT</promise>` found or max iterations\n\n**Example:**\n```\n/ralph-wiggum:ralph-loop \"Build REST API. Output <promise>DONE</promise> when tests pass.\" --completion-promise \"DONE\" --max-iterations 20\n```\n\nFor details: `/ralph-wiggum:help`\n</ralph-wiggum-system>"
  }
}
EOF
