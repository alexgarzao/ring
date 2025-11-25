---
name: regulatory-templates-gate3
description: Gate 3 of regulatory templates - generates the complete .tpl template file with all validated mappings
---

# Regulatory Templates - Gate 3: Template File Generation

## Overview

**This sub-skill executes Gate 3 of the regulatory template workflow: generating the complete .tpl template file with all validated mappings and transformations from Gates 1-2.**

**Parent skill:** `regulatory-templates`

**Prerequisites:**
- Gate 1 PASSED (field mappings complete)
- Gate 2 PASSED (validations confirmed)
- Context object with Gates 1-2 results

**Output:** Generated .tpl template file ready for use

---

## When to Use

**Called by:** `regulatory-templates` skill after Gate 2 passes

**Purpose:** Create the final Django/Jinja2 template file with all field mappings, transformations, and validation logic

---

## Gate 3 Process

### Agent Dispatch

**Use the Task tool to dispatch the finops-automation agent for template generation:**

1. **Invoke the Task tool with these parameters:**
   - `subagent_type`: "finops-automation"
   - `model`: "sonnet"
   - `description`: "Gate 3: Generate template file"
   - `prompt`: Use the prompt template below with accumulated context from Gates 1-2

2. **Prompt Template for Gate 3:**

```
GATE 3: TEMPLATE FILE GENERATION

CONTEXT FROM GATES 1-2:
- Template: [insert context.template_name]
- Template Code: [insert context.template_code]
- Authority: [insert context.authority]
- Fields Mapped: [insert context.field_mappings.length]
- Validation Rules: [insert context.validation_rules.length]

FIELD MAPPINGS FROM GATE 1:
[For each field in context.field_mappings, list:]
Field [field_code]: [field_name]
- Source: [selected_mapping]
- Transformation: [transformation or 'none']
- Confidence: [confidence_score]%
- Required: [required]

VALIDATION RULES FROM GATE 2:
[For each rule in context.validation_rules, list:]
Rule [rule_id]: [description]
- Formula: [formula]

TASKS:
1. Generate CLEAN .tpl file with ONLY Django/Jinja2 template code
2. Include all field mappings with transformations
3. Apply correct template syntax for Reporter
4. Structure according to regulatory format requirements
5. Include conditional logic where needed
6. Use MINIMAL inline comments (max 1-2 lines critical notes only)

CRITICAL - NAMING CONVENTION:
⚠️ ALL field names are in SNAKE_CASE standard
- Gate 1 has already converted all fields to snake_case
- Examples:
  * Use {{ legal_document }} (converted from legalDocument)
  * Use {{ operation_route }} (already snake_case)
  * Use {{ opening_date }} (converted from openingDate)
  * Use {{ natural_person }} (converted from naturalPerson)
- ALL fields follow snake_case convention consistently
- No conversion needed - fields arrive already standardized

CRITICAL - DATA SOURCES:
⚠️ ALWAYS prefix fields with the correct data source!
Reference: /docs/regulatory/DATA_SOURCES.md

Available Data Sources:
- midaz_onboarding: organization, account (cadastral data)
- midaz_transaction: operation_route, balance, operation (transactional data)

Field Path Format: {data_source}.{entity}.{index?}.{field}

Examples:
- CNPJ: {{ midaz_onboarding.organization.0.legal_document|slice:':8' }}
- COSIF: {{ midaz_transaction.operation_route.code }}
- Saldo: {{ midaz_transaction.balance.available }}
- Data: {% date_time "YYYY/MM" %}

WRONG: {{ organization.legal_document }}
CORRECT: {{ midaz_onboarding.organization.0.legal_document }}

TEMPLATE STRUCTURE:
- Use proper hierarchy per regulatory spec
- Include loops for repeating elements (accounts, transactions)
- Apply transformations using Django filters
- NO DOCUMENTATION BLOCKS - only functional template code

OUTPUT FILES (Generate TWO separate files):

FILE 1 - TEMPLATE (CLEAN):
- Filename: [template_code]_preview.tpl
- Content: ONLY the Django/Jinja2 template code
- NO extensive comments or documentation blocks
- Maximum 1-2 critical inline comments if absolutely necessary
- Ready for DIRECT use in Reporter without editing

FILE 2 - DOCUMENTATION:
- Filename: [template_code]_preview.tpl.docs
- Content: Full documentation including:
  * Field mappings table
  * Transformation rules
  * Validation checklist
  * Troubleshooting guide
  * Maintenance notes
  * All the helpful documentation

CRITICAL: The .tpl file must be production-ready and contain ONLY
the functional template code. All documentation goes in .docs file.

COMPLETION STATUS must be COMPLETE or INCOMPLETE.
```

3. **Example Task tool invocation:**
```
When executing Gate 3, call the Task tool with:
- subagent_type: "finops-automation"
- model: "sonnet"
- description: "Gate 3: Generate template file"
- prompt: [The full prompt above with context from Gates 1-2 substituted]
```
```

---

## Agent Execution

The agent `finops-automation` will handle all technical aspects:

- Analyze template requirements based on authority type
- Generate appropriate template structure (XML, JSON, etc.)
- Apply all necessary transformations using Django/Jinja2 filters
- Include conditional logic for business rules
- Ensure compliance with regulatory format specifications

---

## Expected Output

The agent will generate two files:

1. **Template File**: `{template_code}_{timestamp}_preview.tpl`
   - Contains the functional Django/Jinja2 template code
   - Ready for direct use in Reporter
   - Minimal inline comments only if necessary

2. **Documentation File**: `{template_code}_{timestamp}_preview.tpl.docs`
   - Contains full documentation
   - Field mapping details
   - Maintenance notes

---

## Pass/Fail Criteria

### PASS Criteria
- ✅ Template file generated successfully
- ✅ All mandatory fields included
- ✅ Transformations correctly applied
- ✅ Django/Jinja2 syntax valid
- ✅ Output format matches specification
- ✅ File saved with correct extension

### FAIL Criteria
- ❌ Missing mandatory fields
- ❌ Invalid template syntax
- ❌ Transformation errors
- ❌ File generation failed

---

## State Tracking

### After PASS:

```
SKILL: regulatory-templates-gate3
GATE: 3 - Template File Generation
STATUS: PASSED ✅
TEMPLATE: {context.template_selected}
FILE: {filename}
FIELDS: {fields_included}/{total_fields}
NEXT: Template ready for use
EVIDENCE: File generated successfully
BLOCKERS: None
```

### After FAIL:

```
SKILL: regulatory-templates-gate3
GATE: 3 - Template File Generation
STATUS: FAILED ❌
TEMPLATE: {context.template_selected}
ERROR: {error_message}
NEXT: Fix generation issues
EVIDENCE: {specific_failure}
BLOCKERS: {blocker_description}
```

---

## Output to Parent Skill

Return to `regulatory-templates` main skill:

```javascript
{
  "gate3_passed": true/false,
  "template_file": {
    "filename": "cadoc4010_20251119_preview.tpl",
    "path": "/path/to/file",
    "size_bytes": 2048,
    "fields_included": 9
  },
  "ready_for_use": true/false,
  "next_action": "template_complete" | "fix_and_regenerate"
}
```

---

## Common Template Patterns

### SNAKE_CASE Field Names (STANDARD)
```django
CORRECT - All fields in snake_case (as provided by Gate 1):
{{ organization.legal_document }}  # Converted from legalDocument
{{ holder.natural_person }}        # Already snake_case
{{ account.opening_date }}          # Converted from openingDate
{{ banking_details.account_number }} # Converted from accountNumber

WRONG - Using other naming conventions:
{{ organization.legalDocument }}   # ❌ Should be legal_document
{{ holder.naturalPerson }}         # ❌ Should be natural_person
{{ account.openingDate }}          # ❌ Should be opening_date
{{ bankingDetails.accountNumber }} # ❌ Should be banking_details.account_number
```

### Iterating Collections
```django
{% for item in collection %}
    {{ item.field }}
{% endfor %}
```

### Conditional Fields
```django
{% if condition %}
    <field>{{ value }}</field>
{% endif %}
```

### Nested Objects
```django
{{ parent.child.grandchild }}
```

### Filters Chain
```django
{{ value|slice:':8'|upper }}
```

---

## Remember

1. **Use exact field paths** from Gate 1 mappings
2. **ALL FIELDS IN SNAKE_CASE** - Gate 1 provides all fields already converted to snake_case
3. **Apply all transformations** validated in Gate 2
4. **Include comments** for maintainability
5. **Follow regulatory format** exactly
6. **Test syntax validity** before saving
7. **Document assumptions** made during generation
8. **Fields are standardized** - All fields follow snake_case convention consistently