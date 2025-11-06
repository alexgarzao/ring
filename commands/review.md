Use the review-orchestrator agent to run sequential code review (Gates 1→2→3).

**Usage:**
- `/ring:review` - Review all changed files
- `/ring:review <file-path>` - Review specific file
- `/ring:review <pattern>` - Review files matching pattern

**Example:**
```
User: /ring:review src/auth.ts
Assistant: Starting sequential review of src/auth.ts (Gates 1→2→3)...
[Invokes full-reviewer agent]
```

**The agent will:**
1. Run Gate 1 (code-reviewer)
2. Run Gate 2 (business-logic-reviewer)
3. Run Gate 3 (security-reviewer), all three gates in parallel
4. Return consolidated report

**After completion:**
- Show consolidated findings
- Highlight critical/high issues
- Provide clear next steps
