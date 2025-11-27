---
name: using-tw-team
description: |
  Technical writing specialists for functional and API documentation. Dispatch when
  you need to create guides, conceptual docs, or API references following established
  documentation standards.

trigger: |
  - Need to write functional documentation (guides, conceptual docs, tutorials)
  - Need to write API reference documentation
  - Need to review existing documentation quality
  - Writing or updating product documentation

skip_when: |
  - Writing code → use dev-team agents
  - Writing plans → use pm-team agents
  - General code review → use default plugin reviewers

related:
  similar: [using-ring, using-dev-team]
---

# Using Ring Technical Writing Specialists

The ring-tw-team plugin provides specialized agents for technical documentation. Use them via `Task tool with subagent_type:`.

**Remember:** Follow the **ORCHESTRATOR principle** from `using-ring`. Dispatch agents to handle documentation tasks; don't write complex documentation directly.

---

## 3 Documentation Specialists

### 1. Functional Writer
**`ring-tw-team:functional-writer`**

**Specializations:**
- Conceptual documentation and guides
- Getting started tutorials
- Feature explanations
- Best practices documentation
- Use case documentation
- Workflow and process guides

**Use When:**
- Writing new product guides
- Creating tutorials for features
- Documenting best practices
- Writing conceptual explanations
- Creating "how to" documentation

**Example dispatch:**
```
Task tool:
  subagent_type: "ring-tw-team:functional-writer"
  model: "opus"
  prompt: "Write a getting started guide for the authentication feature"
```

---

### 2. API Writer
**`ring-tw-team:api-writer`**

**Specializations:**
- REST API reference documentation
- Endpoint descriptions and examples
- Request/response schema documentation
- Error code documentation
- Field-level descriptions
- API integration guides

**Use When:**
- Documenting new API endpoints
- Writing request/response examples
- Documenting error codes
- Creating API field descriptions
- Writing integration guides

**Example dispatch:**
```
Task tool:
  subagent_type: "ring-tw-team:api-writer"
  model: "opus"
  prompt: "Document the POST /accounts endpoint with request/response examples"
```

---

### 3. Documentation Reviewer
**`ring-tw-team:docs-reviewer`**

**Specializations:**
- Voice and tone compliance
- Structure and hierarchy review
- Completeness assessment
- Clarity and readability analysis
- Consistency checking
- Technical accuracy verification

**Use When:**
- Reviewing draft documentation
- Checking documentation quality
- Ensuring style guide compliance
- Validating documentation completeness
- Pre-publication review

**Example dispatch:**
```
Task tool:
  subagent_type: "ring-tw-team:docs-reviewer"
  model: "opus"
  prompt: "Review this guide for voice, tone, structure, and completeness"
```

---

## Decision Matrix: Which Specialist?

| Need | Specialist | Use Case |
|------|-----------|----------|
| Guides, tutorials, concepts | Functional Writer | Product documentation |
| API endpoints, schemas, errors | API Writer | Technical API reference |
| Quality check, style compliance | Docs Reviewer | Pre-publication review |

---

## Documentation Standards Summary

These agents enforce the following standards:

### Voice and Tone
- **Assertive, but never arrogant** – Say what needs to be said, clearly
- **Encouraging and empowering** – Guide users through complexity
- **Tech-savvy, but human** – Use technical terms when needed, prioritize clarity
- **Humble and open** – Confident but always learning

### Capitalization
- **Sentence case** for all headings and titles
- Only first letter and proper nouns are capitalized
- ✅ "Getting started with the API"
- ❌ "Getting Started With The API"

### Structure Patterns
1. Lead with a clear definition paragraph
2. Use bullet points for key characteristics
3. Separate sections with `---` dividers
4. Include info boxes and warnings where needed
5. Link to related API reference
6. Add code examples for technical topics

---

## Dispatching Multiple Specialists

For comprehensive documentation, dispatch in **parallel** (single message, multiple Task calls):

```
✅ CORRECT:
Task #1: ring-tw-team:functional-writer (write the guide)
Task #2: ring-tw-team:api-writer (write API reference)
(Both run in parallel)

Then:
Task #3: ring-tw-team:docs-reviewer (review both)
```

---

## ORCHESTRATOR Principle

Remember:
- **You're the orchestrator** – Dispatch specialists, don't write directly
- **Let specialists apply standards** – They know voice, tone, and structure
- **Combine with other plugins** – API writers + backend engineers for accuracy

### Good Example (ORCHESTRATOR):
> "I need documentation for the new feature. Let me dispatch functional-writer to create the guide."

### Bad Example (OPERATOR):
> "I'll manually write all the documentation myself."

---

## Available in This Plugin

**Agents:**
- functional-writer
- api-writer
- docs-reviewer

**Skills:**
- using-tw-team: Plugin introduction and agent selection
- writing-functional-docs: Functional documentation patterns
- writing-api-docs: API reference documentation patterns
- documentation-structure: Document hierarchy and organization
- voice-and-tone: Voice and tone guidelines
- documentation-review: Documentation quality checklist
- api-field-descriptions: Field description patterns

**Commands:**
- /ring-tw-team:write-guide: Start writing a functional guide
- /ring-tw-team:write-api: Start writing API documentation
- /ring-tw-team:review-docs: Review existing documentation

---

## Integration with Other Plugins

- **using-ring** (default) – ORCHESTRATOR principle for ALL agents
- **using-dev-team** – Developer agents for technical accuracy
- **using-pm-team** – Pre-dev planning before documentation

Dispatch based on your need:
- Documentation writing → ring-tw-team agents
- Technical implementation → ring-dev-team agents
- Feature planning → ring-pm-team agents
