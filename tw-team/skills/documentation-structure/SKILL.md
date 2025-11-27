---
name: documentation-structure
description: |
  Patterns for organizing and structuring documentation including hierarchy,
  navigation, and information architecture.

trigger: |
  - Planning documentation structure
  - Organizing content hierarchy
  - Deciding how to split content across pages
  - Creating navigation patterns

skip_when: |
  - Writing content → use writing-functional-docs or writing-api-docs
  - Checking voice → use voice-and-tone

related:
  complementary: [writing-functional-docs, writing-api-docs]
---

# Documentation Structure

Good structure helps users find what they need quickly. Organize content by user tasks and mental models, not by internal system organization.

---

## Content Hierarchy

### Top-Level Organization

Structure documentation around user needs:

```
Documentation/
├── Welcome/              # Entry point, product overview
├── Getting Started/      # First steps, quick wins
├── Guides/              # Task-oriented documentation
│   ├── Understanding X   # Conceptual documentation
│   ├── Installing X     # Setup and deployment
│   ├── Use Cases        # Real-world scenarios
│   ├── Core Entities    # Domain concepts
│   └── Best Practices   # Recommendations
├── API Reference/       # Technical reference
│   ├── Introduction     # API overview
│   ├── Getting Started  # Quick start
│   └── Endpoints/       # Per-resource documentation
└── Updates/             # Changelog, versioning
```

---

## Page Structure Patterns

### Overview Pages
Introduce a section and link to child pages.

```markdown
# Section Name

Brief description of what this section covers and who it's for.

---

## Content

In this section, you will find:

- [**Topic A**](link): Brief description
- [**Topic B**](link): Brief description
- [**Topic C**](link): Brief description
```

---

### Conceptual Pages
Explain a single concept thoroughly.

```markdown
# Concept Name

Lead paragraph defining the concept and its importance.

## Key characteristics

- Point 1
- Point 2
- Point 3

## How it works

Detailed explanation with diagrams.

---

## Subtopic A

Content about subtopic A.

---

## Subtopic B

Content about subtopic B.

---

## Related concepts

- [Related A](link) – Connection explanation
- [Related B](link) – Connection explanation
```

---

### Task-Oriented Pages
Guide users through a specific workflow.

```markdown
# How to [accomplish task]

Brief context on when and why.

## Prerequisites

- Requirement 1
- Requirement 2

---

## Step 1: Action name

Explanation of what to do.

## Step 2: Action name

Continue the workflow.

---

## Verification

How to confirm success.

## Next steps

- [Follow-up task](link)
- [Related task](link)
```

---

## Section Dividers

Use horizontal rules (`---`) to create visual separation between major sections.

```markdown
## Section One

Content here.

---

## Section Two

New topic content here.
```

**When to use dividers:**
- Between major topic changes
- Before "Related" or "Next steps" sections
- After introductory content
- Before prerequisites in guides

**Don't overuse:** Not every heading needs a divider. Use them for significant transitions.

---

## Navigation Patterns

### Breadcrumb Context
Always show where users are in the hierarchy:

```
Guides > Core Entities > Accounts
```

### Previous/Next Links
Connect sequential content:

```markdown
[Previous: Assets](link) | [Next: Portfolios](link)
```

### On-This-Page Navigation
For long pages, show section links:

```markdown
On this page:
- [Key characteristics](#key-characteristics)
- [How it works](#how-it-works)
- [Managing via API](#managing-via-api)
```

---

## Information Density

### Scannable Content
Users scan before they read. Make content scannable:

1. **Lead with the key point** in each section
2. **Use bullet points** for lists of 3+ items
3. **Use tables** for comparing options
4. **Use headings** every 2-3 paragraphs
5. **Use bold** for key terms on first use

---

### Progressive Disclosure

Start with essentials, then add depth:

```markdown
# Feature Overview

Essential information that 80% of users need.

---

## Advanced Configuration

Deeper details for users who need them.

### Rare Scenarios

Edge cases and special situations.
```

---

## Tables vs Lists

### Use Tables When:
- Comparing multiple items across same attributes
- Showing structured data (API fields, parameters)
- Displaying options with consistent properties

```markdown
| Model | Best For | Support Level |
|-------|----------|---------------|
| Community | Experimentation | Community |
| Enterprise | Production | Dedicated |
```

### Use Lists When:
- Items don't have comparable attributes
- Sequence matters (steps)
- Items have varying levels of detail

```markdown
## Key features

- **Central Ledger**: Real-time account and transaction management
- **Modularity**: Flexible architecture for customization
- **Scalability**: Handles large transaction volumes
```

---

## Code Examples Placement

### Inline Code
For short references within text:

> Set the `assetCode` field to your currency code.

### Code Blocks
For complete, runnable examples:

```json
{
  "name": "Customer Account",
  "assetCode": "BRL"
}
```

### Placement Rules:
1. Show the example immediately after explaining it
2. Keep examples minimal but complete
3. Use realistic data (not "foo", "bar")
4. Show both request and response for API docs

---

## Cross-Linking Strategy

### Link to First Mention
Link concepts when first mentioned in a section:

> Each [Account](link) is linked to a single [Asset](link).

### Don't Over-Link
Don't link every mention of a term. Once per section is enough.

### Link Destinations

| Link Type | Destination |
|-----------|-------------|
| Concept name | Conceptual documentation |
| API action | API reference endpoint |
| "Learn more" | Deeper dive documentation |
| "See also" | Related but different topics |

---

## Page Length Guidelines

| Page Type | Target Length | Reasoning |
|-----------|---------------|-----------|
| Overview | 1-2 screens | Quick orientation |
| Concept | 2-4 screens | Thorough explanation |
| How-to | 1-3 screens | Task completion |
| API endpoint | 2-3 screens | Complete reference |
| Best practices | 3-5 screens | Multiple recommendations |

If a page exceeds 5 screens, consider splitting into multiple pages.

---

## Quality Checklist

Before finalizing structure:

- [ ] Content is organized by user task, not system structure
- [ ] Overview pages link to all child content
- [ ] Section dividers separate major topics
- [ ] Headings create scannable structure
- [ ] Tables are used for comparable items
- [ ] Code examples follow explanations
- [ ] Cross-links connect related content
- [ ] Page length is appropriate for content type
- [ ] Navigation (prev/next) connects sequential content
