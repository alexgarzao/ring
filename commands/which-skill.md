Find relevant skills for your task using the skill matcher.

**Usage:**
- `/ring:which-skill <task description>` - Get skill suggestions

**Example:**
```
User: /ring:which-skill debug authentication failing randomly
Assistant: Finding skills for your task...

[Runs lib/skill-matcher.sh "debug authentication failing randomly"]

Relevant skills:
1. systematic-debugging (HIGH confidence)
   - Use for bugs, test failures, unexpected behavior
2. test-driven-development (MEDIUM confidence)
   - Use when implementing bugfix
3. condition-based-waiting (LOW confidence)
   - Use for race conditions, timing issues

Recommended: Start with systematic-debugging
```

**The matcher uses:**
- Keyword extraction from task description
- Matching against skill descriptions
- Confidence scoring (HIGH/MEDIUM/LOW)
- Top 5 ranked results

**Helpful for:**
- Discovering relevant skills (28 skills available)
- Reducing cognitive load in skill selection
- Ensuring right skill for the job
