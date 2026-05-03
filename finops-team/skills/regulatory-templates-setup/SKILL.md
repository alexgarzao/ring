---
name: ring:regulatory-templates-setup
description: |
  Initial setup sub-skill - handles template selection and context initialization
  for the 5-stage regulatory workflow. Supports any regulatory template (pre-defined
  or new) via official spec intake (URL/XSD/PDF).

trigger: |
  - Called by regulatory-templates orchestrator at workflow start
  - Need to select template type and initialize context

skip_when: |
  - Not in regulatory-templates workflow
  - Setup already completed for current template

sequence:
  after: [regulatory-templates]
  before: [regulatory-templates-gate1]
---

# Regulatory Templates — Initial Setup

Handles template selection, context initialization, and dictionary status check for the 5-stage regulatory workflow.

**Parent skill:** `regulatory-templates`
**Output:** Complete initial context object for all subsequent gates

## Step 1: Template Selection

AskUserQuestion: "Which regulatory authority?"
- BACEN (Banco Central do Brasil)
- RFB (Receita Federal do Brasil)
- CVM (Comissão de Valores Mobiliários)
- SUSEP (Superintendência de Seguros Privados)
- COAF (Conselho de Controle de Atividades Financeiras)
- Other (provide spec)

**Conditional follow-up based on authority:**

| Authority | Templates |
|-----------|-----------|
| BACEN | CADOC 4010, CADOC 4016, CADOC 4111, APIX 001, APIX 002 |
| RFB | e-Financeira (6 types), DIMP v10 |
| CVM/SUSEP/COAF | Ask for spec URL or file |
| Other | Ask for spec URL, XSD, or PDF |

AskUserQuestion: "Which specific template?" (based on authority selection)

AskUserQuestion: "What spec version are you targeting?" (e.g., 2024-01)

## Step 2: Spec Loading (for pre-defined templates)

For BACEN/RFB templates, load the canonical spec from the ring FinOps registry:
- URL pattern: `https://registry.ring.lerian.studio/finops/{authority}/{template}/{version}/spec.json`
- If registry not available: ask user to provide spec URL or file

For new/custom templates: load spec from user-provided URL/XSD/PDF via WebFetch or read.

## Step 3: Dictionary Status Check

Check for existing field dictionary: `docs/regulatory/{authority}/{template}/field-dictionary.json`

| Status | Impact |
|--------|--------|
| Found (recent) | Gate 1 can auto-match; fewer interactive validations (~5 min faster) |
| Found (outdated) | Partial auto-match; validate changed fields |
| Not found | Full interactive validation required in Gate 1 (~40 min for complex templates) |

Alert user: "Dictionary {found/not found}. Gate 1 will require {X} interactive validations."

## Step 4: Initialize Context

Build and return context object:

```json
{
  "authority": "BACEN",
  "template_type": "CADOC-4010",
  "spec_version": "2024-01",
  "spec_loaded": true,
  "spec_source": "registry | url | file",
  "dictionary_status": "exists | not_found | outdated",
  "dictionary_path": "docs/regulatory/BACEN/CADOC-4010/field-dictionary.json",
  "setup_timestamp": "ISO-8601",
  "gate1": {"status": "PENDING"},
  "gate2": {"status": "PENDING"},
  "gate3": {"status": "PENDING"}
}
```

## Step 5: Gate 0 — Template Structure

Load base template for the selected spec. This is the skeleton .tpl file with all required sections and placeholder positions (no data mapping yet — Gate 1 handles mapping).

Output: `docs/regulatory/{authority}/{template}/gate0-template-base.tpl`

## Setup Complete

When all steps complete, pass context to `ring:regulatory-templates-gate1`.
