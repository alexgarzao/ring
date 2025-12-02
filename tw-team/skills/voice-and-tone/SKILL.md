---
name: voice-and-tone
description: |
  Voice and tone guidelines for technical documentation. Ensures consistent,
  clear, and human writing across all documentation.

trigger: |
  - Need to check voice and tone compliance
  - Writing new documentation
  - Reviewing existing documentation for style

skip_when: |
  - Only checking structure → use documentation-structure
  - Only checking technical accuracy → use ring-tw-team:docs-reviewer agent

related:
  complementary: [writing-functional-docs, writing-api-docs, documentation-review]
---

# Voice and Tone Guidelines

Write the way you work: with confidence, clarity, and care. Good documentation sounds like a knowledgeable colleague helping you solve a problem.

---

## Core Tone Principles

### Assertive, But Never Arrogant
Say what needs to be said, clearly and without overexplaining. Be confident in your statements.

**Good:**
> Core one uses a microservices architecture, which allows each component to be self-sufficient and easily scalable.

**Avoid:**
> Core one might use what some people call a microservices architecture, which could potentially allow components to be somewhat self-sufficient.

---

### Encouraging and Empowering
Guide users to make progress, especially when things get complex. Acknowledge difficulty but show the path forward.

**Good:**
> This setup isn't just technically solid; it's built for real-world use. You can add new components as needed without disrupting what's already in place.

**Avoid:**
> This complex setup requires careful understanding of multiple systems before you can safely make changes.

---

### Tech-Savvy, But Human
Talk to developers, not at them. Use technical terms when needed, but always aim for clarity over jargon.

**Good:**
> Each Account is linked to exactly one Asset type.

**Avoid:**
> The Account entity maintains a mandatory one-to-one cardinality with the Asset entity.

---

### Humble and Open
Be confident in your solutions but always assume there's more to learn.

**Good:**
> As Core one evolves, new fields and tables may be added.

**Avoid:**
> The system is complete and requires no further development.

---

## The Golden Rule

> When in doubt, write like you're helping a smart colleague who just joined the team.

This colleague is:
- Technical and can handle complexity
- New to this specific system
- Busy and appreciates efficiency
- Capable of learning quickly with good guidance

---

## Writing Mechanics

### Use Second Person ("You")
Address the reader directly. This creates connection and clarity.

| Use | Avoid |
|-----|-------|
| You can create as many accounts... | Users can create as many accounts... |
| Your configuration should look like... | The configuration should look like... |
| If you're working with an earlier release... | If one is working with an earlier release... |

---

### Use Present Tense
Describe current behavior, not hypothetical futures.

| Use | Avoid |
|-----|-------|
| Core one uses Helm Charts | Core one will use Helm Charts |
| The system returns an error | The system would return an error |
| Each Account holds one Asset type | Each Account will hold one Asset type |

---

### Use Active Voice
Put the subject first. Active voice is clearer and more direct.

| Use | Avoid |
|-----|-------|
| The API returns a JSON response | A JSON response is returned by the API |
| Create an account before... | An account should be created before... |
| Core one enforces financial discipline | Financial discipline is enforced by Core one |

---

### Keep Sentences Short
One idea per sentence. Break complex thoughts into multiple sentences.

**Good:**
> External accounts represent accounts outside your organization. They're used to track money coming in or going out.

**Avoid:**
> External accounts in Core one represent accounts outside your organization's structure, and they're used to track money that's coming in or going out, typically tied to users, partners, or financial providers beyond your internal ledger.

---

## Capitalization Rules

### Sentence Case for Headings
Only capitalize the first letter and proper nouns.

| Correct | Avoid |
|---------|-------|
| Getting started with the API | Getting Started With The API |
| Using the transaction builder | Using The Transaction Builder |
| Managing account types | Managing Account Types |

### Applies to:
- Page titles
- Section headings
- Card titles
- Navigation labels
- Table headers

---

## Terminology Consistency

### Product Names
Always capitalize product names as proper nouns:
- Core one (not "midaz" or "MIDAZ")
- Console (when referring to the product)
- Reporter, Core two, Core four

### Entity Names
Capitalize entity names when referring to the specific concept:
- Account, Ledger, Asset, Portfolio, Segment
- Transaction, Operation, Balance

**Example:**
> Each Account is linked to a single Asset.

But use lowercase for general references:
> You can create multiple accounts within a ledger.

---

## Contractions

Use contractions naturally. They make writing feel more conversational.

| Natural | Stiff |
|---------|-------|
| You'll find... | You will find... |
| It's important... | It is important... |
| Don't delete... | Do not delete... |
| That's because... | That is because... |

---

## Emphasis

### Bold for UI Elements and Key Terms
> Click **Create Account** to open the form.
>
> The **metadata** field accepts key-value pairs.

### Code Formatting for Technical Terms
> Use the `POST /accounts` endpoint.
>
> Set `allowSending` to `true`.

### Avoid Overusing Emphasis
If everything is bold or emphasized, nothing stands out.

---

## Info Boxes and Warnings

### Tips (Helpful Information)
> **Tip:** You can use account aliases to make transactions more readable.

### Notes (Important Context)
> **Note:** You're viewing documentation for the current version.

### Warnings (Potential Issues)
> **Warning:** External accounts cannot be deleted or changed.

### Deprecated Notices
> **Deprecated:** This field will be removed in v4. Use `route` instead.

---

## Quality Checklist

Before publishing, verify your writing:

- [ ] Uses second person ("you") consistently
- [ ] Uses present tense for current behavior
- [ ] Uses active voice (subject does the action)
- [ ] Sentences are short (one idea each)
- [ ] Headings use sentence case
- [ ] Technical terms are used appropriately
- [ ] Contractions are used naturally
- [ ] Emphasis is used sparingly
- [ ] Sounds like helping a colleague, not lecturing
