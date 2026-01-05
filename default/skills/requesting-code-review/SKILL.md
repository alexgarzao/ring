---
name: requesting-code-review
description: |
  Gate 4 of development cycle - dispatches 3 specialized reviewers (code, business-logic,
  security) in parallel for comprehensive code review feedback.

trigger: |
  - Gate 4 of development cycle
  - After completing major feature implementation
  - Before merge to main branch
  - After fixing complex bug

NOT_skip_when: |
  - "Code is simple" → Simple code can have security issues. Review required.
  - "Just refactoring" → Refactoring may expose vulnerabilities. Review required.
  - "Already reviewed similar code" → Each change needs fresh review.

sequence:
  after: [dev-testing]
  before: [dev-validation]

related:
  complementary: [dev-cycle, dev-implementation, dev-testing]

input_schema:
  required: []  # All inputs optional for standalone usage
  optional:
    - name: unit_id
      type: string
      description: "Task or subtask identifier (auto-generated if not provided)"
    - name: base_sha
      type: string
      description: "Git SHA before implementation (auto-detected via git merge-base HEAD main)"
    - name: head_sha
      type: string
      description: "Git SHA after implementation (auto-detected via git rev-parse HEAD)"
    - name: implementation_summary
      type: string
      description: "Summary of what was implemented (auto-generated from git log if not provided)"
    - name: requirements
      type: string
      description: "Requirements or acceptance criteria (reviewers will infer from code if not provided)"
    - name: implementation_files
      type: array
      items: string
      description: "List of files changed (auto-detected via git diff if not provided)"
    - name: gate0_handoff
      type: object
      description: "Full handoff from Gate 0 (only when called from dev-cycle)"
    - name: skip_reviewers
      type: array
      items: string
      enum: [code-reviewer, business-logic-reviewer, security-reviewer]
      description: "Reviewers to skip (use sparingly)"

output_schema:
  format: markdown
  required_sections:
    - name: "Review Summary"
      pattern: "^## Review Summary"
      required: true
    - name: "Issues by Severity"
      pattern: "^## Issues by Severity"
      required: true
    - name: "Reviewer Verdicts"
      pattern: "^## Reviewer Verdicts"
      required: true
    - name: "CodeRabbit External Review"
      pattern: "^## CodeRabbit External Review"
      required: false
    - name: "Handoff to Next Gate"
      pattern: "^## Handoff to Next Gate"
      required: true
  metrics:
    - name: result
      type: enum
      values: [PASS, FAIL, NEEDS_FIXES]
    - name: reviewers_passed
      type: string
      description: "X/3 format"
    - name: issues_critical
      type: integer
    - name: issues_high
      type: integer
    - name: issues_medium
      type: integer
    - name: issues_low
      type: integer
    - name: iterations
      type: integer
    - name: coderabbit_status
      type: enum
      values: [PASS, ISSUES_FOUND, SKIPPED, NOT_INSTALLED]
    - name: coderabbit_issues
      type: integer
      description: "Number of issues found by CodeRabbit (0 if skipped)"

examples:
  - name: "Feature review"
    input:
      unit_id: "task-001"
      base_sha: "abc123"
      head_sha: "def456"
      implementation_summary: "Added user authentication with JWT"
      requirements: "AC-1: User can login, AC-2: Invalid password returns error"
    expected_output: |
      ## Review Summary
      **Status:** PASS
      **Reviewers:** 3/3 PASS
      
      ## Issues by Severity
      | Severity | Count |
      |----------|-------|
      | Critical | 0 |
      | High | 0 |
      | Medium | 0 |
      | Low | 2 |
      
      ## Reviewer Verdicts
      | Reviewer | Verdict |
      |----------|---------|
      | code-reviewer | ✅ PASS |
      | business-logic-reviewer | ✅ PASS |
      | security-reviewer | ✅ PASS |
      
      ## Handoff to Next Gate
      - Ready for Gate 5: YES
---

# Code Review (Gate 4)

## Overview

Dispatch all three reviewer subagents in **parallel** for fast, comprehensive feedback:

1. **code-reviewer** - Architecture, design patterns, code quality
2. **business-logic-reviewer** - Domain correctness, business rules, edge cases
3. **security-reviewer** - Vulnerabilities, authentication, OWASP risks

**Core principle:** All 3 reviewers run simultaneously in a single message with 3 Task tool calls.

## CRITICAL: Role Clarification

**This skill ORCHESTRATES. Reviewer Agents REVIEW.**

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Dispatch reviewers, aggregate findings, track iterations |
| **Reviewer Agents** | Analyze code, report issues with severity |
| **Implementation Agent** | Fix issues found by reviewers |

---

## Step 1: Gather Context (Auto-Detect if Not Provided)

```text
This skill supports TWO modes:
1. WITH INPUTS: Called by any skill/user that provides structured inputs (unit_id, base_sha, etc.)
2. STANDALONE: Called directly without inputs - auto-detects everything from git

FOR EACH INPUT, check if provided OR auto-detect:

1. unit_id:
   IF provided → use it
   ELSE → generate: "review-" + timestamp (e.g., "review-20241222-143052")

2. base_sha:
   IF provided → use it
   ELSE → Execute: git merge-base HEAD main
   IF git fails → Execute: git rev-parse HEAD~10 (fallback to last 10 commits)

3. head_sha:
   IF provided → use it
   ELSE → Execute: git rev-parse HEAD

4. implementation_files:
   IF provided → use it
   ELSE → Execute: git diff --name-only [base_sha] [head_sha]

5. implementation_summary:
   IF provided → use it
   ELSE → Execute: git log --oneline [base_sha]..[head_sha]
   Format as: "Changes: [list of commit messages]"

6. requirements:
   IF provided → use it
   ELSE → Set to: "Infer requirements from code changes and commit messages"
   (Reviewers will analyze code to understand intent)

AFTER AUTO-DETECTION, display context:
┌─────────────────────────────────────────────────────────────────┐
│ 📋 CODE REVIEW CONTEXT                                          │
├─────────────────────────────────────────────────────────────────┤
│ Unit ID: [unit_id]                                              │
│ Base SHA: [base_sha]                                            │
│ Head SHA: [head_sha]                                            │
│ Files Changed: [count] files                                    │
│ Commits: [count] commits                                        │
│                                                                 │
│ Dispatching 3 reviewers in parallel...                          │
└─────────────────────────────────────────────────────────────────┘
```

## Step 2: Initialize Review State

```text
review_state = {
  unit_id: [from input],
  base_sha: [from input],
  head_sha: [from input],
  reviewers: {
    code_reviewer: {verdict: null, issues: []},
    business_logic_reviewer: {verdict: null, issues: []},
    security_reviewer: {verdict: null, issues: []}
  },
  aggregated_issues: {
    critical: [],
    high: [],
    medium: [],
    low: [],
    cosmetic: []
  },
  iterations: 0,
  max_iterations: 3
}
```

## Step 3: Dispatch All 3 Reviewers in Parallel

**⛔ CRITICAL: All 3 reviewers MUST be dispatched in a SINGLE message with 3 Task calls.**

```yaml
# Task 1: Code Reviewer
Task:
  subagent_type: "code-reviewer"
  model: "opus"
  description: "Code review for [unit_id]"
  prompt: |
    ## Code Review Request
    
    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha]
    **Head SHA:** [head_sha]
    
    ## What Was Implemented
    [implementation_summary]
    
    ## Requirements
    [requirements]
    
    ## Files Changed
    [implementation_files or "Use git diff"]
    
    ## Your Focus
    - Architecture and design patterns
    - Code quality and maintainability
    - Naming conventions
    - Error handling patterns
    - Performance concerns
    
    ## Required Output
    ### VERDICT: PASS / FAIL
    
    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW/COSMETIC] | [issue] | [location] | [fix] |
    
    ### What Was Done Well
    [positive observations]

# Task 2: Business Logic Reviewer
Task:
  subagent_type: "business-logic-reviewer"
  model: "opus"
  description: "Business logic review for [unit_id]"
  prompt: |
    ## Business Logic Review Request
    
    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha]
    **Head SHA:** [head_sha]
    
    ## What Was Implemented
    [implementation_summary]
    
    ## Requirements
    [requirements]
    
    ## Your Focus
    - Domain correctness
    - Business rules implementation
    - Edge cases handling
    - Requirements coverage
    - Data validation
    
    ## Required Output
    ### VERDICT: PASS / FAIL
    
    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW/COSMETIC] | [issue] | [location] | [fix] |
    
    ### Requirements Traceability
    | Requirement | Status | Evidence |
    |-------------|--------|----------|
    | [req] | ✅/❌ | [file:line] |

# Task 3: Security Reviewer
Task:
  subagent_type: "security-reviewer"
  model: "opus"
  description: "Security review for [unit_id]"
  prompt: |
    ## Security Review Request
    
    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha]
    **Head SHA:** [head_sha]
    
    ## What Was Implemented
    [implementation_summary]
    
    ## Requirements
    [requirements]
    
    ## Your Focus
    - Authentication and authorization
    - Input validation
    - SQL injection, XSS, CSRF
    - Sensitive data handling
    - OWASP Top 10 risks
    
    ## Required Output
    ### VERDICT: PASS / FAIL
    
    ### Issues Found
    | Severity | Description | File:Line | OWASP Category | Recommendation |
    |----------|-------------|-----------|----------------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [issue] | [location] | [A01-A10] | [fix] |
    
    ### Security Checklist
    | Check | Status |
    |-------|--------|
    | Input validation | ✅/❌ |
    | Auth checks | ✅/❌ |
    | No hardcoded secrets | ✅/❌ |
```

## Step 4: Wait for All Reviewers and Parse Output

```text
Wait for all 3 Task calls to complete.

For each reviewer:
1. Extract VERDICT (PASS/FAIL)
2. Extract Issues Found table
3. Categorize issues by severity

review_state.reviewers.code_reviewer = {
  verdict: [PASS/FAIL],
  issues: [parsed issues]
}
// ... same for other reviewers

Aggregate all issues by severity:
review_state.aggregated_issues.critical = [all critical from all reviewers]
review_state.aggregated_issues.high = [all high from all reviewers]
// ... etc
```

## Step 5: Handle Results by Severity

```text
Count blocking issues:
blocking_count = critical.length + high.length + medium.length

IF blocking_count == 0:
  → All reviewers PASS
  → Proceed to Step 8 (Success)

IF blocking_count > 0:
  → review_state.iterations += 1
  → IF iterations >= max_iterations: Go to Step 9 (Escalate)
  → Go to Step 6 (Dispatch Fixes)
```

## Step 6: Dispatch Fixes to Implementation Agent

**⛔ CRITICAL: You are an ORCHESTRATOR. You CANNOT edit source files directly.**
**You MUST dispatch the implementation agent to fix ALL review issues.**

### Orchestrator Boundaries (HARD GATE)

| Action | Permitted? | Required Action |
|--------|------------|-----------------|
| Read review findings | ✅ YES | Parse reviewer output |
| Edit source code files | ❌ NO | Dispatch agent |
| Add TODO comments | ❌ NO | Dispatch agent |
| Run tests | ❌ NO | Agent runs tests |
| Commit changes | ❌ NO | Agent commits |

**If you catch yourself about to use Edit/Write/Create on source files → STOP. Dispatch agent.**

### Dispatch Implementation Agent

```yaml
Task:
  subagent_type: "[implementation_agent from Gate 0]"
  model: "opus"
  description: "Fix review issues for [unit_id]"
  prompt: |
    ⛔ FIX REQUIRED - Code Review Issues Found

    ## Context
    - **Unit ID:** [unit_id]
    - **Iteration:** [iterations] of [max_iterations]

    ## Critical Issues (MUST FIX)
    [list critical issues with file:line and recommendation]

    ## High Issues (MUST FIX)
    [list high issues]

    ## Medium Issues (MUST FIX)
    [list medium issues]

    ## Requirements
    1. Fix ALL Critical, High, and Medium issues
    2. Run tests to verify fixes
    3. Commit fixes with descriptive message
    4. Return list of fixed issues with evidence

    ## For Low/Cosmetic Issues
    Add TODO/FIXME comments:
    - Low: `// TODO(review): [Issue] - [reviewer] on [date]`
    - Cosmetic: `// FIXME(nitpick): [Issue] - [reviewer] on [date]`
```

### Anti-Rationalization for Direct Editing

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "It's a one-line fix" | Size is irrelevant. Orchestrators don't edit code. | **Dispatch agent** |
| "I already know how to fix it" | Knowing ≠ permission. Orchestrators orchestrate. | **Dispatch agent** |
| "Agent dispatch takes too long" | Consistency > speed. Always dispatch. | **Dispatch agent** |
| "Just adding a TODO comment" | TODO comments are code changes. Agents write code. | **Dispatch agent** |
| "The reviewer told me exactly what to change" | Instructions are for the agent, not you. | **Dispatch agent** |
| "I'll fix it faster myself" | Fast + wrong > slow + right. Dispatch agent. | **Dispatch agent** |

## Step 7: Re-Run All Reviewers After Fixes

```text
After fixes committed:
1. Get new HEAD_SHA
2. Go back to Step 3 (dispatch all 3 reviewers again)

⛔ CRITICAL: Always re-run ALL 3 reviewers after fixes.
Do NOT cherry-pick reviewers.
```

## Step 7.5: Optional CodeRabbit CLI Review (AFTER Ring Reviewers Pass)

### ⚠️ PREREQUISITES & ENVIRONMENT REQUIREMENTS

**Before attempting Step 7.5, verify your environment supports the required operations:**

| Requirement | Local Dev | CI/CD | Containerized | Remote/SSH |
|-------------|-----------|-------|---------------|------------|
| `curl \| sh` install | ✅ Yes | ⚠️ May require elevated permissions | ❌ Often blocked | ⚠️ Depends on config |
| Browser auth (`coderabbit auth login`) | ✅ Yes | ❌ No browser | ❌ No browser | ❌ No browser |
| Write to `$HOME/.coderabbit/` | ✅ Yes | ⚠️ Ephemeral | ⚠️ Ephemeral | ✅ Usually |
| Internet access to `cli.coderabbit.ai` | ✅ Yes | ⚠️ Check firewall | ⚠️ Check firewall | ⚠️ Check firewall |

**⛔ HARD STOP CONDITIONS - Skip Step 7.5 if ANY apply:**
- Running in containerized environment without persistent storage
- CI/CD pipeline without pre-installed CodeRabbit CLI
- Non-interactive environment (no TTY for browser auth)
- Network restrictions blocking `cli.coderabbit.ai`
- Read-only filesystem

### Environment-Specific Guidance

#### Local Development (RECOMMENDED)
Standard flow works: `curl | sh` install + browser authentication.

#### CI/CD Pipelines
**Option A: Pre-install in CI image**
```dockerfile
# Add to your CI Dockerfile
RUN curl -fsSL https://cli.coderabbit.ai/install.sh | sh
```

**Option B: Use API token authentication (headless)**
```bash
# Set token via environment variable (add to CI secrets)
export CODERABBIT_API_TOKEN="your-api-token"
coderabbit auth login --token "$CODERABBIT_API_TOKEN"
```

**Option C: Skip CodeRabbit in CI, run locally**
```bash
# In CI config, set env var to auto-skip
export SKIP_CODERABBIT_REVIEW=true
```

#### Containerized/Docker Environments
```bash
# Option 1: Mount credentials from host
docker run -v ~/.coderabbit:/root/.coderabbit ...

# Option 2: Pass token as env var
docker run -e CODERABBIT_API_TOKEN="..." ...

# Option 3: Pre-bake into image (not recommended for tokens)
```

#### Non-Interactive/Headless Authentication
```bash
# Generate API token at: https://app.coderabbit.ai/settings/api-tokens
# Then authenticate without browser:
coderabbit auth login --token "cr_xxxxxxxxxxxxx"
```

---

```text
┌─────────────────────────────────────────────────────────────────┐
│ ✅ ALL 3 RING REVIEWERS PASSED                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Would you like to run CodeRabbit CLI for additional external    │
│ AI-powered code review before proceeding to validation?         │
│                                                                 │
│ CodeRabbit catches race conditions, memory leaks, security      │
│ vulnerabilities, and edge cases that may complement Ring        │
│ reviewers.                                                      │
│                                                                 │
│ ⚠️  ENVIRONMENT CHECK:                                          │
│     • Interactive terminal with browser access? → Standard flow │
│     • CI/headless? → Requires API token or pre-installed CLI    │
│     • Container? → Mount credentials or use token auth          │
│                                                                 │
│ ⚠️  Requires: CodeRabbit CLI installed and authenticated        │
│     Install: curl -fsSL https://cli.coderabbit.ai/install.sh | sh│
│     Auth: coderabbit auth login (or --token for headless)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Ask user:** "Do you want to run CodeRabbit CLI review before proceeding? (a) Yes (b) No, skip (c) Skip - environment doesn't support it"

### If User Selects YES:

#### Step 7.5.1: Check CodeRabbit Installation

```bash
# Verify CodeRabbit CLI is installed
which coderabbit || which cr
```

**If NOT installed:**
```text
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  CodeRabbit CLI not found                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ CodeRabbit CLI is not installed on your system.                 │
│                                                                 │
│ Would you like to:                                              │
│   (a) Skip CodeRabbit review and proceed to Gate 5              │
│   (b) Install CodeRabbit CLI now (I'll guide you)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**If user selects (b) Install:**

```text
┌─────────────────────────────────────────────────────────────────┐
│ 📦 INSTALLING CODERABBIT CLI                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ⚠️  ENVIRONMENT CHECK FIRST:                                    │
│                                                                 │
│ This installation requires:                                     │
│   • curl command available                                      │
│   • Write access to $HOME or /usr/local/bin                     │
│   • Internet access to cli.coderabbit.ai                        │
│   • Non-containerized environment (or persistent storage)       │
│                                                                 │
│ If in CI/container, see "Environment-Specific Guidance" above.  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Check environment before proceeding:**
```bash
# Verify prerequisites
curl --version && echo "curl: OK" || echo "curl: MISSING"
test -w "$HOME" && echo "HOME writable: OK" || echo "HOME writable: NO"
curl -sI https://cli.coderabbit.ai | head -1 | grep -q "200\|301\|302" && echo "Network: OK" || echo "Network: BLOCKED"
```

**If prerequisites pass, install:**
```text
┌─────────────────────────────────────────────────────────────────┐
│ 📦 Step 1: Installing CodeRabbit CLI...                         │
└─────────────────────────────────────────────────────────────────┘
```

```bash
# Step 1: Download and install CodeRabbit CLI
curl -fsSL https://cli.coderabbit.ai/install.sh | sh
```

**After installation, verify:**
```bash
# Verify installation
which coderabbit || which cr
```

**If installation successful:**
```text
┌─────────────────────────────────────────────────────────────────┐
│ ✅ CodeRabbit CLI installed successfully!                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Step 2: Authentication required                                 │
│                                                                 │
│ Choose your authentication method:                              │
│                                                                 │
│   (a) Browser login (interactive - opens browser)               │
│       → Best for: Local development with GUI                    │
│       → Command: coderabbit auth login                          │
│                                                                 │
│   (b) API token (headless - no browser needed)                  │
│       → Best for: CI/CD, containers, SSH sessions               │
│       → Get token: https://app.coderabbit.ai/settings/api-tokens│
│       → Command: coderabbit auth login --token "cr_xxx"         │
│                                                                 │
│   (c) Skip authentication and CodeRabbit review                 │
│                                                                 │
│ Note: Free tier allows 1 review/hour.                           │
│       Paid plans get enhanced reviews + higher limits.          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**If user selects (a) Browser login:**
```bash
# Step 2a: Authenticate with CodeRabbit (opens browser)
# ⚠️ Requires: GUI environment with default browser
coderabbit auth login
```

**If user selects (b) API token:**
```bash
# Step 2b: Authenticate with API token (headless)
# Get your token from: https://app.coderabbit.ai/settings/api-tokens
coderabbit auth login --token "cr_xxxxxxxxxxxxx"
```

**After authentication:**
```text
┌─────────────────────────────────────────────────────────────────┐
│ ✅ CodeRabbit CLI ready!                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Installation: Complete                                          │
│ Authentication: Complete                                        │
│                                                                 │
│ Proceeding to CodeRabbit review...                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

→ Proceed to Step 7.5.2 (Run CodeRabbit Review)

**If installation failed:**
```text
┌─────────────────────────────────────────────────────────────────┐
│ ❌ CodeRabbit CLI installation failed                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Error: [error message from curl/sh]                             │
│                                                                 │
│ Troubleshooting:                                                │
│   • Check internet connection                                   │
│   • Try manual install: https://docs.coderabbit.ai/cli/overview │
│   • macOS/Linux only (Windows not supported yet)                │
│                                                                 │
│ Would you like to:                                              │
│   (a) Retry installation                                        │
│   (b) Skip CodeRabbit and proceed to Gate 5                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 7.5.2: Run CodeRabbit Review

```bash
# Run CodeRabbit in prompt-only mode (optimized for AI agents)
coderabbit --prompt-only --type uncommitted --base [base_branch]
```

**Parse CodeRabbit output for:**
- Critical issues
- High severity issues
- Security vulnerabilities
- Performance concerns

#### Step 7.5.3: Handle CodeRabbit Findings

**⛔ CRITICAL: You are an ORCHESTRATOR. You CANNOT edit source files directly.**
**You MUST dispatch the implementation agent to fix issues.**

```text
IF CodeRabbit found CRITICAL or HIGH issues:
  → Display findings to user
  → Ask: "CodeRabbit found [N] critical/high issues. Fix now or proceed anyway?"
    (a) Fix issues - dispatch to implementation agent
    (b) Proceed to Gate 5 (acknowledge risk)
    (c) Review findings in detail

  IF user selects (a) Fix issues:
    → ⛔ DO NOT edit files directly
    → DISPATCH implementation agent with CodeRabbit findings:
    
    Task:
      subagent_type: "[same agent used in Gate 0]"
      model: "opus"
      description: "Fix CodeRabbit issues for [unit_id]"
      prompt: |
        ## CodeRabbit Issues to Fix
        
        The following issues were found by CodeRabbit CLI external review.
        Fix ALL Critical and High severity issues.
        
        ### Critical Issues
        [list from CodeRabbit output]
        
        ### High Issues
        [list from CodeRabbit output]
        
        ## Requirements
        1. Fix each issue following Ring Standards
        2. Run tests to verify fixes don't break functionality
        3. Commit fixes with descriptive message
    
    → After agent completes, re-run CodeRabbit: `coderabbit --prompt-only`
    → If CodeRabbit issues remain, repeat fix cycle (max 2 iterations for CodeRabbit)
    
    → ⛔ AFTER CodeRabbit passes, MUST re-run Ring reviewers:
    
    ┌─────────────────────────────────────────────────────────────────┐
    │ 🔄 RE-RUNNING RING REVIEWERS AFTER CODERABBIT FIXES             │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │ CodeRabbit fixes may have introduced new issues detectable by   │
    │ Ring reviewers. Re-validation is MANDATORY before Gate 5.       │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    
    Step 7.5.3a: Re-Run All 3 Ring Reviewers
    ─────────────────────────────────────────
    1. Get new HEAD_SHA after CodeRabbit fixes
    2. Dispatch all 3 reviewers in parallel (per Step 3):
       - code-reviewer
       - business-logic-reviewer  
       - security-reviewer
    3. Wait for all 3 to complete
    
    Step 7.5.3b: Handle Ring Reviewer Results
    ─────────────────────────────────────────
    IF all 3 Ring reviewers PASS:
      → Proceed to Step 8 (Success Output)
    
    IF any Ring reviewer finds CRITICAL/HIGH/MEDIUM issues:
      → Increment coderabbit_ring_iteration counter
      → IF coderabbit_ring_iteration >= 2:
          → ESCALATE: "Max iterations reached after CodeRabbit fixes"
          → Go to Step 9 (Escalate)
      → DISPATCH implementation agent to fix Ring reviewer issues
      → After fixes committed:
          → Re-run CodeRabbit: `coderabbit --prompt-only`
          → IF CodeRabbit passes:
              → Re-run all 3 Ring reviewers (loop back to Step 7.5.3a)
          → IF CodeRabbit finds issues:
              → Fix CodeRabbit issues first, then re-run Ring reviewers
    
    State tracking for CodeRabbit fix cycle:
    ```
    coderabbit_fix_state = {
      coderabbit_iterations: 0,      // max 2 for CodeRabbit-only fixes
      ring_revalidation_iterations: 0,  // max 2 for Ring reviewer re-runs
      total_max_iterations: 4        // absolute cap: 2 CR + 2 Ring
    }
    ```

IF CodeRabbit found only MEDIUM/LOW issues:
  → Display summary
  → ⛔ DO NOT edit files directly to add TODOs
  → DISPATCH implementation agent to add TODO comments:
  
  Task:
    subagent_type: "[same agent used in Gate 0]"
    description: "Add TODO comments for CodeRabbit findings"
    prompt: |
      Add TODO comments for these CodeRabbit findings:
      [list MEDIUM/LOW issues with file:line]
      
      Format: // TODO(coderabbit): [issue description]
  
  → After TODO comments added (code changed):
      → Re-run all 3 Ring reviewers (per Step 7.5.3a above)
      → IF Ring reviewers PASS: Proceed to Step 8
      → IF Ring reviewers find issues: Fix and re-run (max 2 iterations)

IF CodeRabbit found no issues:
  → Display: "✅ CodeRabbit review passed - no additional issues found"
  → No code changes made by CodeRabbit flow
  → Proceed directly to Step 8 (no Ring re-run needed)
```

### Anti-Rationalization for Direct Editing

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "It's just a small fix" | Size is irrelevant. Orchestrators don't edit code. | **Dispatch agent** |
| "I can add TODO comments quickly" | Orchestrators don't write to source files. Period. | **Dispatch agent** |
| "Agent dispatch is overkill for this" | Consistency > convenience. Always dispatch. | **Dispatch agent** |
| "CodeRabbit already told me what to fix" | Knowing the fix ≠ permission to implement. | **Dispatch agent** |

#### Step 7.5.4: CodeRabbit Results Summary

```markdown
## CodeRabbit External Review
**Status:** [PASS|ISSUES_FOUND|SKIPPED]
**Issues Found:** [N]

| Severity | Count | Action |
|----------|-------|--------|
| Critical | [N] | [Fixed/Acknowledged] |
| High | [N] | [Fixed/Acknowledged] |
| Medium | [N] | [TODO added] |
| Low | [N] | [TODO added] |
```

### If User Selects NO (Skip):

```text
→ Record: "CodeRabbit review: SKIPPED (user choice)"
→ Proceed directly to Step 8 (Success Output)
```

---

## Step 8: Prepare Success Output

```text
Generate skill output:

## Review Summary
**Status:** PASS
**Unit ID:** [unit_id]
**Iterations:** [review_state.iterations]

## Issues by Severity
| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | [count] |
| Cosmetic | [count] |

## Reviewer Verdicts
| Reviewer | Verdict | Issues |
|----------|---------|--------|
| code-reviewer | ✅ PASS | [count] |
| business-logic-reviewer | ✅ PASS | [count] |
| security-reviewer | ✅ PASS | [count] |

## Low/Cosmetic Issues (TODO/FIXME added)
[list with file locations]

## Handoff to Next Gate
- Review status: COMPLETE
- All blocking issues: RESOLVED
- Reviewers passed: 3/3
- Ready for Gate 5 (Validation): YES
```

## Step 9: Escalate - Max Iterations Reached

```text
Generate skill output:

## Review Summary
**Status:** FAIL
**Unit ID:** [unit_id]
**Iterations:** [max_iterations] (MAX REACHED)

## Issues by Severity
| Severity | Count |
|----------|-------|
| Critical | [count] |
| High | [count] |
| Medium | [count] |

## Unresolved Issues
[list all Critical/High/Medium still open]

## Reviewer Verdicts
| Reviewer | Verdict |
|----------|---------|
| code-reviewer | [PASS/FAIL] |
| business-logic-reviewer | [PASS/FAIL] |
| security-reviewer | [PASS/FAIL] |

## Handoff to Next Gate
- Review status: FAILED
- Unresolved blocking issues: [count]
- Ready for Gate 5: NO
- **Action Required:** User must manually resolve issues

⛔ ESCALATION: Max iterations (3) reached. Blocking issues remain.
```

---

## Pressure Resistance

See [dev-team/skills/shared-patterns/shared-pressure-resistance.md](../../dev-team/skills/shared-patterns/shared-pressure-resistance.md) for universal pressure scenarios.

| User Says | Your Response |
|-----------|---------------|
| "Skip review, code is simple" | "Simple code can have security issues. Dispatching all 3 reviewers." |
| "Just run code-reviewer" | "All 3 reviewers run in parallel. No time saved by skipping." |
| "Fix later, merge now" | "Blocking issues (Critical/High/Medium) MUST be fixed before Gate 5." |

## Anti-Rationalization Table

See [dev-team/skills/shared-patterns/shared-anti-rationalization.md](../../dev-team/skills/shared-patterns/shared-anti-rationalization.md) for universal anti-rationalizations.

### Gate 4-Specific Anti-Rationalizations

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Run reviewers one at a time" | Sequential = slow. Parallel = 3x faster. | **Dispatch all 3 in single message** |
| "Skip security for internal code" | Internal code can have vulnerabilities. | **Include security-reviewer** |
| "Critical issue is false positive" | Prove it with evidence, don't assume. | **Fix or provide evidence** |
| "Low issues don't need TODO" | TODOs ensure issues aren't forgotten. | **Add TODO comments** |
| "2 of 3 reviewers passed" | Gate 4 requires ALL 3. 2/3 = 0/3. | **Re-run ALL 3 reviewers** |
| "MEDIUM is not blocking" | MEDIUM = MUST FIX. Same as CRITICAL/HIGH. | **Fix MEDIUM issues NOW** |

---

## Execution Report Format

```markdown
## Review Summary
**Status:** [PASS|FAIL|NEEDS_FIXES]
**Unit ID:** [unit_id]
**Duration:** [Xm Ys]
**Iterations:** [N]

## Issues by Severity
| Severity | Count |
|----------|-------|
| Critical | [N] |
| High | [N] |
| Medium | [N] |
| Low | [N] |

## Reviewer Verdicts
| Reviewer | Verdict |
|----------|---------|
| code-reviewer | ✅/❌ |
| business-logic-reviewer | ✅/❌ |
| security-reviewer | ✅/❌ |

## CodeRabbit External Review (Optional)
**Status:** [PASS|ISSUES_FOUND|SKIPPED|NOT_INSTALLED]
**Issues Found:** [N or N/A]

## Handoff to Next Gate
- Review status: [COMPLETE|FAILED]
- Blocking issues: [resolved|N remaining]
- CodeRabbit: [PASS|SKIPPED|N issues acknowledged]
- Ready for Gate 5: [YES|NO]
```
