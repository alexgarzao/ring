# Semantic Block Tags Refactoring Plan

## Objective

Update all dev-team skills (9) and agents (9) to use semantic block tags for improved AI recognition of critical instruction blocks.

---

## Tag Mapping Strategy

| Tag | Current Pattern to Replace | Where to Apply |
|-----|---------------------------|----------------|
| `<fetch_required>` | "WebFetch:", "Standards Loading" URLs | All agents, skills with standards loading |
| `<block_condition>` | "Blocker Criteria", "STOP and Report" lists | All skills and agents |
| `<forbidden>` | "FORBIDDEN Patterns", "Anti-Patterns" lists | All agents, some skills |
| `<dispatch_required>` | "Task tool:" YAML blocks | Skills that dispatch agents |
| `<verify_before_proceed>` | "Prerequisites", "Validate Input" sections | All skills |
| `<output_required>` | "Required Output Format", "Standards Coverage Table" | All agents |
| `<cannot_skip>` | "Cannot Be Overridden", "NON-NEGOTIABLE" lists | All skills and agents |
| `<user_decision>` | "APPROVED/REJECTED", "User Decision Required" | dev-validation, dev-cycle |

---

## Phase 1: Skills (9 files)

### 1.1 dev-cycle/SKILL.md (HIGH PRIORITY - Orchestrator)

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | CLAUDE.md URL |
| Orchestrator CANNOT Do | `<forbidden>` | Read/Write/Edit source code |
| SUB-SKILL LOADING IS MANDATORY | `<cannot_skip>` | Gate-to-skill mapping |
| Blocker Criteria | `<block_condition>` | Gate failure, missing standards |
| Cannot Be Overridden | `<cannot_skip>` | 6 gates, 3 reviewers, 85% coverage |
| Gate dispatch blocks | `<dispatch_required>` | Each gate's agent dispatch |
| Step 7.1/7.2 checkpoints | `<user_decision>` | Approval checkpoints |

### 1.2 dev-refactor/SKILL.md (HIGH PRIORITY - Orchestrator)

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| MANDATORY GAP PRINCIPLE | `<cannot_skip>` | All divergences are gaps |
| Orchestrator CANNOT Do | `<forbidden>` | Bash find/ls for analysis |
| Step 3 codebase-explorer | `<dispatch_required>` | Must use Task tool |
| Step 4 specialist agents | `<dispatch_required>` | Parallel agent dispatch |
| Step 0 PROJECT_RULES check | `<block_condition>` | File must exist |
| Step 8 user approval | `<user_decision>` | Approve/Cancel options |

### 1.3 dev-implementation/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Validate Input | `<verify_before_proceed>` | Required inputs check |
| Validate Prerequisites | `<block_condition>` | PROJECT_RULES.md exists |
| Gate 0.1 TDD-RED | `<dispatch_required>` | Agent dispatch with prompt |
| Gate 0.2 TDD-GREEN | `<dispatch_required>` | Agent dispatch with prompt |
| Validate TDD-RED Output | `<block_condition>` | Must contain "FAIL" |
| MANDATORY Instrumentation | `<cannot_skip>` | 90%+ coverage required |

### 1.4 dev-devops/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Validate Input | `<verify_before_proceed>` | Required inputs check |
| Step 4 DevOps Agent | `<dispatch_required>` | devops-engineer dispatch |
| Standards Reference | `<fetch_required>` | devops.md URL |
| Verification Commands | `<verify_before_proceed>` | docker-compose build/up |

### 1.5 dev-sre/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Validate Input | `<verify_before_proceed>` | Required inputs check |
| Step 3 SRE Agent | `<dispatch_required>` | sre agent dispatch |
| Step 6 Fix dispatch | `<dispatch_required>` | Implementation agent fix |
| FORBIDDEN Logging Patterns | `<forbidden>` | fmt.Println, console.log |
| Blocker Criteria | `<block_condition>` | Coverage < 50%, max iterations |
| Cannot Be Overridden | `<cannot_skip>` | 90% instrumentation |

### 1.6 dev-testing/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Validate Input | `<verify_before_proceed>` | Required inputs check |
| Step 3 QA Analyst | `<dispatch_required>` | qa-analyst dispatch |
| Coverage threshold | `<block_condition>` | < 85% = FAIL |
| Edge Cases Required | `<cannot_skip>` | Minimum edge cases per AC type |

### 1.7 dev-validation/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Self-Approval Prohibition | `<forbidden>` | Same agent cannot approve |
| Ambiguous Response Handling | `<block_condition>` | Invalid approval responses |
| Approval Format | `<user_decision>` | APPROVED/REJECTED only |
| Awaiting Approval | `<cannot_skip>` | STOP all work while waiting |

### 1.8 dev-feedback-loop/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| TodoWrite Tracking | `<cannot_skip>` | Must add to todo list first |
| Threshold Alerts | `<block_condition>` | Score < 70, iterations > 3 |
| Mandatory Feedback Collection | `<cannot_skip>` | Every task, no exceptions |
| Step 3.2 Dispatch | `<dispatch_required>` | prompt-quality-reviewer |

### 1.9 using-dev-team/SKILL.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Blocker Criteria | `<block_condition>` | Technology decisions |
| Cannot Be Overridden | `<cannot_skip>` | Dispatch, 6-gate, TDD |
| 7 Developer Specialists | `<dispatch_required>` | Agent dispatch template |

---

## Phase 2: Agents (9 files)

### 2.1 backend-engineer-golang.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | golang.md URL |
| FORBIDDEN Patterns Check | `<forbidden>` | fmt.Println, log.Fatal, panic |
| MANDATORY Instrumentation | `<cannot_skip>` | 90%+ coverage |
| Bootstrap Pattern Check | `<cannot_skip>` | For new projects |
| Blocker Criteria | `<block_condition>` | Architecture decisions, missing context |
| Standards Compliance Output | `<output_required>` | Standards Coverage Table |

### 2.2 backend-engineer-typescript.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | typescript.md URL |
| FORBIDDEN Patterns Check | `<forbidden>` | console.log, any type |
| MANDATORY Instrumentation | `<cannot_skip>` | 90%+ coverage |
| Bootstrap Pattern Check | `<cannot_skip>` | For new projects |
| Blocker Criteria | `<block_condition>` | Architecture decisions |
| Standards Compliance Output | `<output_required>` | Standards Coverage Table |

### 2.3 devops-engineer.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | devops.md URL |
| FORBIDDEN Patterns Check | `<forbidden>` | :latest tags, root user |
| Security Checklist | `<cannot_skip>` | All security checks |
| Blocker Criteria | `<block_condition>` | Missing context, security issues |
| Standards Compliance Output | `<output_required>` | Standards Coverage Table |

### 2.4 frontend-bff-engineer-typescript.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | typescript.md URL |
| FORBIDDEN Patterns Check | `<forbidden>` | console.log, any type |
| Clean Architecture | `<cannot_skip>` | Layer separation |
| Blocker Criteria | `<block_condition>` | Architecture decisions |
| Standards Compliance Output | `<output_required>` | Standards Coverage Table |

### 2.5 frontend-engineer.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | frontend.md URL |
| FORBIDDEN Patterns Check | `<forbidden>` | console.log, inline styles |
| Blocker Criteria | `<block_condition>` | Design system conflicts |
| Standards Compliance Output | `<output_required>` | Standards Coverage Table |

### 2.6 frontend-designer.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Scope Boundary Enforcement | `<forbidden>` | No code implementation |
| Project Context Discovery | `<cannot_skip>` | Must check for design system |
| Blocker Criteria | `<block_condition>` | Unclear requirements |
| Pre-Dev Integration | `<output_required>` | Design specs format |

### 2.7 sre.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | sre.md URL |
| FORBIDDEN Logging Patterns | `<forbidden>` | fmt.Println, console.log |
| Scope Boundaries | `<cannot_skip>` | Validate only, not implement |
| Blocker Criteria | `<block_condition>` | Missing observability |
| Standards Compliance Output | `<output_required>` | Instrumentation Coverage Table |

### 2.8 qa-analyst.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | golang.md or typescript.md |
| FORBIDDEN Test Patterns | `<forbidden>` | Mocking production, skipped tests |
| Test Quality Gate | `<cannot_skip>` | Gate 3 exit criteria |
| Blocker Criteria | `<block_condition>` | Coverage below threshold |
| Standards Compliance Output | `<output_required>` | Standards Coverage Table |

### 2.9 prompt-quality-reviewer.md

| Section | Tag to Apply | Notes |
|---------|--------------|-------|
| Standards Loading | `<fetch_required>` | Agent definition URLs |
| Blocker Criteria | `<block_condition>` | No agent outputs to analyze |
| Standards Compliance Report | `<forbidden>` | Not applicable for this agent |
| Analysis Output | `<output_required>` | Required output format |

---

## Phase 3: Execution Order

### Batch 1: Orchestrators (Critical Path)
1. `dev-cycle/SKILL.md` - Main orchestrator
2. `dev-refactor/SKILL.md` - Refactor orchestrator

### Batch 2: Gate Skills
3. `dev-implementation/SKILL.md` - Gate 0
4. `dev-devops/SKILL.md` - Gate 1
5. `dev-sre/SKILL.md` - Gate 2
6. `dev-testing/SKILL.md` - Gate 3
7. `dev-validation/SKILL.md` - Gate 5

### Batch 3: Support Skills
8. `dev-feedback-loop/SKILL.md` - Metrics
9. `using-dev-team/SKILL.md` - Plugin intro

### Batch 4: Implementation Agents
10. `backend-engineer-golang.md`
11. `backend-engineer-typescript.md`
12. `frontend-bff-engineer-typescript.md`
13. `frontend-engineer.md`

### Batch 5: Specialist Agents
14. `devops-engineer.md`
15. `sre.md`
16. `qa-analyst.md`
17. `frontend-designer.md`
18. `prompt-quality-reviewer.md`

---

## Estimated Effort

| Phase | Files | Estimated Time | Priority |
|-------|-------|----------------|----------|
| Phase 1: Skills | 9 | 2-3 hours | HIGH |
| Phase 2: Agents | 9 | 2-3 hours | HIGH |
| **Total** | **18** | **4-6 hours** | - |

---

## Validation Checklist

After each file update:
- [ ] All `<fetch_required>` tags have valid URLs
- [ ] All `<block_condition>` tags list specific conditions
- [ ] All `<forbidden>` tags list specific patterns
- [ ] All `<dispatch_required>` tags specify agent and model
- [ ] All `<cannot_skip>` tags explain why non-negotiable
- [ ] All `<output_required>` tags define exact format
- [ ] Strategic spacing (`---`) between tag blocks
- [ ] File still renders correctly in markdown

---

## Rollback Strategy

If issues found:
1. Each batch is a separate commit
2. Can revert individual batches
3. Tags are additive (don't break existing functionality)

---

## Success Criteria

1. All 18 files updated with semantic tags
2. No broken markdown rendering
3. Tags follow consistent format across all files
4. Documentation in CLAUDE.md matches implementation
