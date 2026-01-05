# Standards Boundary Enforcement

Canonical source for preventing agents from hallucinating requirements beyond what exists in Ring standards files.

---

## ⛔ CRITICAL: Check ONLY What Standards Define

**This is NON-NEGOTIABLE. Agents MUST NOT invent, assume, or hallucinate requirements.**

| Rule | Enforcement |
|------|-------------|
| **ONLY check items explicitly listed in standards** | If not in WebFetch result → NOT a requirement |
| **NEVER invent "should have" items** | Standards define WHAT exists, not what you think should exist |
| **NEVER add industry best practices not in standards** | Ring standards ARE the best practices for this org |
| **NEVER assume common patterns are required** | If not listed → NOT required |

**If you flag something not in standards → Your output is INVALID. Remove the hallucinated finding.**

---

## Why This Pattern Exists

**Problem:** AI agents "helpfully" invent requirements based on:
- General industry knowledge
- Common patterns seen in training data
- Assumptions about what "should" exist
- Extrapolation from partial information

**Example Failures:**
| Agent Said | Reality | Problem |
|------------|---------|---------|
| "Missing `make proto`" | NOT in devops.md Makefile Standards | Hallucinated requirement |
| "Missing `make mocks`" | NOT in devops.md Makefile Standards | Hallucinated requirement |
| "Missing `make migrate-up/down`" | NOT in devops.md Makefile Standards | Hallucinated requirement |
| "Should use gRPC" | NOT in golang.md Frameworks | Hallucinated requirement |
| "Needs GraphQL schema" | NOT in typescript.md | Hallucinated requirement |

**Solution:** Agents MUST extract requirements ONLY from WebFetch result, never from general knowledge.

---

## ⛔ MANDATORY: Standards Extraction Process

**Before checking compliance, you MUST:**

### Step 1: WebFetch the Standards File

```text
WebFetch:
  url: [agent-specific URL from standards-workflow.md]
  prompt: "Extract ALL requirements, patterns, and expected items"
```

### Step 2: Extract and LIST the Requirements

**For EACH section you will check, you MUST output what you found:**

```markdown
## Standards Extracted from WebFetch

### Section: [Name]

**Requirements found in standards file:**
1. [Exact requirement from WebFetch]
2. [Exact requirement from WebFetch]
3. [Exact requirement from WebFetch]

**I will check ONLY these items. Nothing else.**
```

### Step 3: Check ONLY Extracted Requirements

**Your findings MUST reference the extracted list:**

```markdown
### Finding: [Issue]

**Standard Reference:** [Section Name] → Requirement #2 from extracted list
**Evidence:** [file:line showing violation]
```

---

## Agent-Specific Boundaries

**⛔ CRITICAL: Do NOT duplicate standards content here. Reference the standards files.**

### How to Use This Pattern

Each agent MUST:
1. **WebFetch** the appropriate standards file
2. **Extract** requirements from the fetched content
3. **Check ONLY** what the standards explicitly list
4. **Verify** before flagging - if not in WebFetch result, do NOT flag

### Common Hallucinations by Agent Type

**These are items agents commonly invent that are NOT typically in standards. Always verify in WebFetch result before flagging.**

#### devops-engineer → devops.md

| Common Hallucination | Action |
|---------------------|--------|
| `make proto` | Verify in devops.md "Makefile Standards" section |
| `make mocks` | Verify in devops.md "Makefile Standards" section |
| `make migrate-*` | Verify in devops.md "Makefile Standards" section |
| `make install` | Verify in devops.md "Makefile Standards" section |
| `make clean` | Verify in devops.md "Makefile Standards" section |

#### backend-engineer-golang → golang.md

| Common Hallucination | Action |
|---------------------|--------|
| gRPC requirement | Verify in golang.md "Frameworks & Libraries" section |
| GraphQL requirement | Verify in golang.md "Frameworks & Libraries" section |
| Gin instead of Fiber | Check actual HTTP framework in golang.md |
| GORM instead of pgx | Check actual ORM/driver in golang.md |

#### backend-engineer-typescript → typescript.md

| Common Hallucination | Action |
|---------------------|--------|
| class-validator | Verify validation library in typescript.md |
| TypeORM | Verify ORM in typescript.md |
| Jest | Verify testing framework in typescript.md |
| InversifyJS | Verify DI framework in typescript.md |

#### sre → sre.md

| Common Hallucination | Action |
|---------------------|--------|
| Prometheus metrics endpoint | Verify in sre.md if explicitly required |
| Jaeger UI | Verify in sre.md if explicitly required |
| Custom dashboards | Verify in sre.md if explicitly required |
| Alert rules | Verify in sre.md if explicitly required |

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Industry standard to have make proto" | Industry ≠ Ring standards. Ring defines requirements. | **Do NOT flag** |
| "Most Go projects need gRPC" | Most ≠ this project. Standards define this project. | **Do NOT flag** |
| "It's a best practice to have X" | Best practices are IN the standards. If not there, not required. | **Do NOT flag** |
| "This would improve the codebase" | Improvement suggestions ≠ compliance findings. | **Do NOT flag as non-compliant** |
| "I've seen this in similar projects" | Similar ≠ this. Standards are project-specific. | **Do NOT flag** |
| "Common sense says this is needed" | Common sense ≠ explicit requirement. Standards are explicit. | **Do NOT flag** |
| "The team probably wants this" | Probably ≠ definitely. Standards define definitely. | **Do NOT flag** |
| "It's implied by the architecture" | Implied ≠ explicit. Only explicit requirements count. | **Do NOT flag** |

---

## Self-Verification Checklist

**Before submitting findings, verify:**

```text
For EACH finding:
1. Is this item EXPLICITLY listed in the WebFetch result?       [ ]
2. Can I quote the EXACT line from standards defining this?     [ ]
3. Am I flagging absence of something NOT in standards?         [ ]
4. Am I inventing requirements from general knowledge?          [ ]
5. Am I assuming "should have" vs "standards say must have"?    [ ]

If #1 or #2 is NO → REMOVE the finding
If #3, #4, or #5 is YES → REMOVE the finding
```

---

## How Agents Reference This Pattern

Add to agent's Standards Compliance section:

```markdown
## Standards Boundary (MANDATORY)

See [shared-patterns/standards-boundary-enforcement.md](../skills/shared-patterns/standards-boundary-enforcement.md) for:
- ONLY check what standards explicitly define
- Agent-specific requirement boundaries
- Forbidden hallucinations list
- Self-verification checklist

**⛔ HARD GATE:** Before flagging ANY item as non-compliant:
1. Verify the requirement EXISTS in WebFetch result
2. Quote the exact standard that requires it
3. If you cannot quote it → Do NOT flag it
```
