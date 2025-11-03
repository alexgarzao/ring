View skill and agent usage metrics.

**Usage:**
- `/ring:metrics` - Show all metrics
- `/ring:metrics <skill-name>` - Show metrics for specific skill
- `/ring:metrics agents` - Show agent metrics only

**Example:**
```
User: /ring:metrics test-driven-development
Assistant: Showing metrics for test-driven-development...

[Reads .ring/metrics.json]

test-driven-development:
  Usage count: 127
  Last used: 2025-11-02 15:30:00
  Compliance rate: 73% (92 compliant, 35 violations)

  Top violations:
    1. test_before_code: 23 times
    2. watch_test_fail: 12 times

  Last violation: 2025-11-02 14:00:00
```

**Metrics tracked:**
- Skill usage counts
- Compliance violations
- Agent verdicts (PASS/FAIL)
- Last used timestamps

**Helpful for:**
- Identifying frequently violated rules
- Understanding skill effectiveness
- Improving skill compliance
