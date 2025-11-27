---
name: documentation-review
description: |
  Comprehensive checklist and process for reviewing documentation quality
  including voice, tone, structure, completeness, and technical accuracy.

trigger: |
  - Reviewing draft documentation
  - Pre-publication quality check
  - Documentation audit
  - Ensuring style guide compliance

skip_when: |
  - Writing new documentation → use writing-functional-docs or writing-api-docs
  - Only checking voice → use voice-and-tone

sequence:
  after: [writing-functional-docs, writing-api-docs]

related:
  complementary: [voice-and-tone, documentation-structure]
---

# Documentation Review Process

Review documentation systematically across multiple dimensions. A thorough review catches issues before they reach users.

---

## Review Dimensions

Documentation review covers five key areas:

1. **Voice and Tone** – Does it sound right?
2. **Structure** – Is it organized effectively?
3. **Completeness** – Is everything covered?
4. **Clarity** – Is it easy to understand?
5. **Technical Accuracy** – Is it correct?

---

## Voice and Tone Review

### Check Second Person Usage
- [ ] Uses "you" instead of "users" or "one"
- [ ] Addresses reader directly
- [ ] Creates connection with the audience

**Flag:**
> ❌ "Users can create accounts..."
>
> ✅ "You can create accounts..."

### Check Tense
- [ ] Uses present tense for current behavior
- [ ] Uses future tense only for planned features
- [ ] Avoids conditional ("would", "could") when stating facts

**Flag:**
> ❌ "The API will return a response..."
>
> ✅ "The API returns a response..."

### Check Active Voice
- [ ] Subject performs the action
- [ ] Avoids passive constructions
- [ ] Clear who/what is doing what

**Flag:**
> ❌ "An error is returned by the API..."
>
> ✅ "The API returns an error..."

### Check Tone
- [ ] Assertive but not arrogant
- [ ] Encouraging, not condescending
- [ ] Technical but human
- [ ] Sounds like helping a colleague

---

## Structure Review

### Check Hierarchy
- [ ] Logical content organization
- [ ] Clear parent-child relationships
- [ ] Appropriate nesting depth (max 3 levels)

### Check Headings
- [ ] Uses sentence case (not Title Case)
- [ ] Action-oriented where appropriate
- [ ] Descriptive and specific
- [ ] Creates scannable structure

**Flag:**
> ❌ "Account Creation Process Overview"
>
> ✅ "Creating your first account"

### Check Section Dividers
- [ ] Major sections separated with `---`
- [ ] Not overused (not every heading)
- [ ] Creates visual breathing room

### Check Navigation
- [ ] Links to related content
- [ ] Previous/Next links where appropriate
- [ ] On-this-page navigation for long content

---

## Completeness Review

### For Conceptual Documentation
- [ ] Definition/overview paragraph present
- [ ] Key characteristics listed
- [ ] "How it works" explained
- [ ] Related concepts linked
- [ ] Next steps provided

### For How-To Guides
- [ ] Prerequisites listed
- [ ] All steps included
- [ ] Verification step present
- [ ] Troubleshooting covered (if common issues exist)
- [ ] Next steps provided

### For API Documentation
- [ ] HTTP method and path documented
- [ ] All path parameters documented
- [ ] All query parameters documented
- [ ] All request body fields documented
- [ ] All response fields documented
- [ ] Required vs optional clear
- [ ] Request example provided
- [ ] Response example provided
- [ ] Error codes documented
- [ ] Deprecated fields marked

---

## Clarity Review

### Check Sentence Length
- [ ] One idea per sentence
- [ ] Sentences under 25 words (ideally)
- [ ] Complex ideas broken into multiple sentences

### Check Paragraph Length
- [ ] 2-3 sentences per paragraph
- [ ] One topic per paragraph
- [ ] White space between paragraphs

### Check Jargon
- [ ] Technical terms explained on first use
- [ ] Acronyms expanded on first use
- [ ] Common language preferred over jargon

### Check Examples
- [ ] Examples use realistic data
- [ ] Examples are complete (can be copied/used)
- [ ] Examples follow explanations immediately

---

## Technical Accuracy Review

### For Conceptual Content
- [ ] Facts are correct
- [ ] Behavior descriptions match actual behavior
- [ ] Version information is current
- [ ] Links work and go to correct destinations

### For API Documentation
- [ ] Endpoint paths are correct
- [ ] HTTP methods are correct
- [ ] Field names match actual API
- [ ] Data types are accurate
- [ ] Required/optional status is correct
- [ ] Examples are valid JSON/code
- [ ] Error codes match actual responses

### For Code Examples
- [ ] Code compiles/runs
- [ ] Output matches description
- [ ] No syntax errors
- [ ] Uses current API version

---

## Common Issues to Flag

### Voice Issues
| Issue | Example | Fix |
|-------|---------|-----|
| Third person | "Users can..." | "You can..." |
| Passive voice | "...is returned" | "...returns" |
| Future tense | "will provide" | "provides" |
| Conditional | "would receive" | "receives" |
| Arrogant tone | "Obviously..." | Remove |

### Structure Issues
| Issue | Example | Fix |
|-------|---------|-----|
| Title case | "Getting Started" | "Getting started" |
| Missing dividers | Wall of text | Add `---` |
| Deep nesting | H4, H5, H6 | Flatten or split |
| Vague headings | "Overview" | "Account overview" |

### Completeness Issues
| Issue | Example | Fix |
|-------|---------|-----|
| Missing prereqs | Steps without context | Add prerequisites |
| No examples | API without code | Add examples |
| Dead links | 404 errors | Fix or remove |
| Outdated info | Old version refs | Update |

### Clarity Issues
| Issue | Example | Fix |
|-------|---------|-----|
| Long sentences | 40+ words | Split |
| Wall of text | No bullets | Add structure |
| Undefined jargon | "DSL" unexplained | Define or link |
| Abstract examples | "foo", "bar" | Use realistic data |

---

## Review Output Format

When reviewing documentation, provide structured feedback.

> **Note:** Documentation reviews use `PASS/NEEDS_REVISION/MAJOR_ISSUES` verdicts, which differ from code review verdicts (`PASS/FAIL/NEEDS_DISCUSSION`). Documentation verdicts are graduated—most docs can be improved but may still be publishable with `NEEDS_REVISION`.

```markdown
## Review Summary

**Overall Assessment:** [PASS | NEEDS_REVISION | MAJOR_ISSUES]

### Voice and Tone
- [x] Second person usage ✓
- [ ] Active voice – Found 3 passive constructions
- [x] Appropriate tone ✓

### Issues Found

#### High Priority
1. **Line 45:** Passive voice "is created by" → "creates"
2. **Line 78:** Missing required field documentation

#### Medium Priority
1. **Line 23:** Title case in heading → sentence case
2. **Line 56:** Long sentence (42 words) → split

#### Low Priority
1. **Line 12:** Could add example for clarity

### Recommendations
1. Fix passive voice instances (3 found)
2. Add missing API field documentation
3. Convert headings to sentence case
```

---

## Quick Review Checklist

For rapid reviews, check these essentials:

**Voice (30 seconds)**
- [ ] "You" not "users"
- [ ] Present tense
- [ ] Active voice

**Structure (30 seconds)**
- [ ] Sentence case headings
- [ ] Section dividers present
- [ ] Scannable (bullets, tables)

**Completeness (1 minute)**
- [ ] Examples present
- [ ] Links work
- [ ] Next steps included

**Accuracy (varies)**
- [ ] Technical facts correct
- [ ] Code examples work
- [ ] Version info current
