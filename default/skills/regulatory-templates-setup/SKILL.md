---
name: regulatory-templates-setup
description: Initial setup for regulatory templates - handles template selection and context initialization
---

# Regulatory Templates - Initial Setup

## Overview

**This sub-skill handles the initial setup phase for regulatory template creation, including template selection and context initialization.**

**Parent skill:** `regulatory-templates`

**Output:** Complete initial context object with all selections and configurations

---

## When to Use

**Called by:** `regulatory-templates` skill at the beginning of the workflow

**Purpose:** Gather all user selections and initialize the context object that will flow through all gates

---

## Setup Steps

### Step 1: Template Selection

Use `AskUserQuestion` tool to present template selection:

```javascript
AskUserQuestion({
  questions: [
    {
      question: "Which regulatory template do you want to create?",
      header: "Template",
      multiSelect: false,
      options: [
        {
          label: "CADOC 4010",
          description: "BACEN - Informações de Cadastro (Cadastral Information)"
        },
        {
          label: "CADOC 4016",
          description: "BACEN - Informações de Operações de Crédito (Credit Operations)"
        },
        {
          label: "CADOC 4111",
          description: "BACEN - Operações de Câmbio (Foreign Exchange Operations)"
        },
        {
          label: "e-Financeira - Movement",
          description: "RFB - Movimento de Operações Financeiras (Financial Movement)"
        },
        {
          label: "e-Financeira - Private Pension",
          description: "RFB - Eventos de Previdência Privada (Private Pension Events)"
        },
        {
          label: "DIMP",
          description: "RFB - Declaração de Informações sobre Movimentação Patrimonial"
        },
        {
          label: "APIX 001",
          description: "BACEN - Open Banking - Dados Cadastrais (Registration Data)"
        },
        {
          label: "APIX 002",
          description: "BACEN - Open Banking - Contas e Transações (Accounts & Transactions)"
        }
      ]
    }
  ]
})
```

**Capture and extract:**
- Template name (e.g., "CADOC 4010")
- Template code (e.g., "4010")
- Regulatory authority (BACEN, RFB)
- Template type for context

### Step 2: Optional Deadline Input

If not provided by user, use standard deadline for the template type.

### Step 3: Initialize Context Object

Create and return the complete initial context:

```javascript
let context = {
  // From template selection
  template_selected: "CADOC 4010",
  template_code: "4010",
  authority: "BACEN",
  template_type: "cadastral_information",

  // Optional user input
  deadline: "2025-12-31", // or ask if needed

  // Gates (to be populated by subsequent sub-skills)
  gate1: null,
  gate2: null,
  gate3: null
};
```

---

## State Tracking Output

After completing setup, output:

```
SKILL: regulatory-templates-setup
STATUS: COMPLETE
TEMPLATE: {context.template_selected}
DEADLINE: {context.deadline}
NEXT: → Gate 1: Regulatory Compliance Analysis
```

---

## Success Criteria

Setup is complete when:
- ✅ Template selected and validated
- ✅ Deadline established (input or default)
- ✅ Context object initialized with all values
- ✅ Documentation URL identified for selected template

---

## Output

Return the complete `context` object to the parent skill for use in subsequent gates.