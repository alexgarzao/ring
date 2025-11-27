---
name: writing-functional-docs
description: |
  Patterns and structure for writing functional documentation including guides,
  conceptual explanations, tutorials, and best practices documentation.

trigger: |
  - Writing a new guide or tutorial
  - Creating conceptual documentation
  - Documenting best practices
  - Writing "how to" content

skip_when: |
  - Writing API reference → use writing-api-docs
  - Reviewing documentation → use documentation-review
  - Writing code → use dev-team agents

sequence:
  before: [documentation-review]

related:
  similar: [writing-api-docs]
  complementary: [voice-and-tone, documentation-structure]
---

# Writing Functional Documentation

Functional documentation explains concepts, guides users through workflows, and helps them understand "why" and "how" things work. This differs from API reference, which documents "what" each endpoint does.

---

## Document Types

### 1. Conceptual Documentation
Explains core concepts, architecture, and how things work together.

**Structure:**
```markdown
# Concept Name

Brief definition paragraph explaining what this concept is and why it matters.

## Key characteristics

- Characteristic 1: Brief explanation
- Characteristic 2: Brief explanation
- Characteristic 3: Brief explanation

## How it works

Detailed explanation of mechanics, with diagrams if helpful.

## Related concepts

- [Related Concept 1](link) – Brief connection explanation
- [Related Concept 2](link) – Brief connection explanation
```

**Example (from Accounts documentation):**
> In banking terms, an Account represents a financial product, such as a checking account, savings account, or loan account.

---

### 2. Getting Started Guides
Helps users accomplish their first task with the product.

**Structure:**
```markdown
# Getting started with [Feature]

Brief intro explaining what users will accomplish.

## Prerequisites

- Requirement 1
- Requirement 2

## Step 1: First action

Explanation of what to do and why.

[Code example or screenshot]

## Step 2: Second action

Continue the workflow.

## Next steps

- [Advanced topic 1](link)
- [Advanced topic 2](link)
```

---

### 3. How-To Guides
Task-focused documentation for specific goals.

**Structure:**
```markdown
# How to [accomplish task]

Brief context on when and why you'd do this.

## Before you begin

Prerequisites or context needed.

## Steps

1. **Action name**: Description of what to do
2. **Action name**: Description of what to do
3. **Action name**: Description of what to do

## Verification

How to confirm success.

## Troubleshooting

Common issues and solutions.
```

---

### 4. Best Practices
Guidance on optimal usage patterns.

**Structure:**
```markdown
# Best practices for [topic]

Brief intro on why these practices matter.

## Practice 1: Name

- **Mistake:** What users commonly do wrong
- **Best practice:** What to do instead and why

## Practice 2: Name

- **Mistake:** Common error pattern
- **Best practice:** Correct approach

## Summary

Key takeaways in bullet form.
```

---

## Writing Patterns

### Lead with Value
Start every document with a clear statement of what the reader will learn or accomplish.

**Good:**
> This guide shows you how to create your first transaction in under 5 minutes.

**Avoid:**
> In this document, we will discuss the various aspects of transaction creation.

---

### Use Second Person ("You")
Address the reader directly.

**Good:**
> You can create as many accounts as your structure demands.

**Avoid:**
> Users can create as many accounts as their structure demands.

---

### Present Tense
Use present tense for current behavior.

**Good:**
> Core one uses a microservices architecture.

**Avoid:**
> Core one will use a microservices architecture.

---

### Action-Oriented Headings
Headings should indicate what the section covers or what users will do.

**Good:**
> ## Creating your first account

**Avoid:**
> ## Account creation process overview

---

### Short Paragraphs
Keep paragraphs to 2-3 sentences maximum. Use bullet points for lists.

**Good:**
> Each Account is linked to exactly one Asset type. Accounts are uniquely identified within a Ledger.

**Avoid:**
> Each Account is linked to exactly one Asset type, and accounts are uniquely identified within a Ledger, which tracks and consolidates all balances and operations for the organization.

---

## Visual Elements

### Info Boxes
Use for helpful tips or additional context.

```markdown
> **Tip:** You can use account aliases to make transactions more readable.
```

### Warning Boxes
Use for important cautions.

```markdown
> **Warning:** External accounts cannot be deleted or changed.
```

### Code Examples
Always include working examples for technical concepts.

```markdown
```json
{
  "name": "Customer Account",
  "assetCode": "BRL",
  "type": "checking"
}
```
```

### Tables
Use for comparing options or showing structured data.

```markdown
| Option | When to Use |
|--------|-------------|
| Community | Developers, startups, experimentation |
| Enterprise | Production, compliance, dedicated support |
```

---

## Section Dividers

Use horizontal rules (`---`) to separate major sections. This improves scannability.

```markdown
## Section One

Content here.

---

## Section Two

Content here.
```

---

## Linking Patterns

### Internal Links
Link to related documentation when mentioning concepts.

**Good:**
> Each Account is linked to a single [Asset](link-to-assets), defining the type of value it holds.

### API Reference Links
Connect functional docs to API reference.

**Good:**
> You can manage your Accounts via [API](link) or through the [Console](link).

### Next Steps
End guides with clear next steps.

```markdown
## Next steps

- [Learn about Portfolios](link) – Group accounts for easier management
- [Create your first Transaction](link) – Move funds between accounts
```

---

## Quality Checklist

Before finishing functional documentation, verify:

- [ ] Leads with clear value statement
- [ ] Uses second person ("you")
- [ ] Uses present tense
- [ ] Headings are action-oriented (sentence case)
- [ ] Paragraphs are short (2-3 sentences)
- [ ] Includes working code examples
- [ ] Links to related documentation
- [ ] Ends with next steps
- [ ] Follows voice and tone guidelines
