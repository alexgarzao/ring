---
name: ring:regulatory-templates-gate1
description: |
  Gate 1 sub-skill - performs regulatory compliance analysis, field mapping,
  batch approval by confidence level, and auto-saves dictionary after approval.
  Supports both pre-defined templates (dictionary exists) and new templates (any spec).

trigger: |
  - regulatory-templates-setup completed
  - Need to analyze regulatory specification and map fields

skip_when: |
  - Setup not complete → run setup first
  - Gate 1 already passed → proceed to Gate 2

sequence:
  after: [regulatory-templates-setup]
  before: [regulatory-templates-gate2]
---

# Regulatory Templates — Gate 1: Placeholder Mapping

Maps placeholders from Gate 0 template to backend data sources. No structure creation, no logic addition — pure mapping.

**Parent skill:** `regulatory-templates`

**Input:** Context from `regulatory-templates-setup`, template base from Gate 0
**Output:** Mapping of placeholders to backend data sources, updated dictionary

## Technical Requirements

### Field Naming: snake_case (MANDATORY)

All database field names must follow Python/Django PEP 8 convention (snake_case). Mixed conventions cause maintenance debt and BACEN audit failures.

| API Field | DB Field (correct) | Wrong |
|-----------|-------------------|-------|
| userId | user_id | userId |
| createdAt | created_at | createdAt |
| taxAmount | tax_amount | taxAmount |

### Data Source Prefixes (MANDATORY)

Every mapped field must have a source prefix for BACEN audit traceability:

| Prefix | Source | Example |
|--------|--------|---------|
| `model.` | Database model field | `model.account.tax_id` |
| `calculated.` | Derived/computed value | `calculated.total_amount` |
| `constant.` | Fixed/hardcoded value | `constant.currency_code` |
| `context.` | Request/session context | `context.reporting_date` |
| `external.` | External API/service | `external.bcb.exchange_rate` |

### Confidence Levels

| Level | Criteria | Treatment |
|-------|----------|-----------|
| HIGH (≥95%) | Clear direct mapping, no transformation | Auto-approve in batch |
| MEDIUM (70-94%) | Conditional mapping or minor transformation | Present for user review |
| LOW (<70%) | Complex mapping, multiple candidates | Must resolve before Gate 2 |

**Threshold:** Average confidence ≥80% required for Gate 1 PASS. Any LOW-confidence mandatory field = FAIL.

## Workflow

### Phase 1: Load Template and Dictionary

1. Read template from Gate 0 output
2. Extract all placeholders: `{% raw %}{{ placeholder_name }}{% endraw %}` and `{% for item in collection %}`
3. Check dictionary: `docs/regulatory/{template_type}/field-dictionary.json`
   - If exists → load for auto-matching
   - If not exists → full interactive validation required

### Phase 2: Classify Placeholders

For each placeholder:

| Type | Criteria | Handling |
|------|----------|---------|
| Mandatory | Required by BACEN/RFB spec | Must map; failure = non-compliant submission |
| Optional | Conditionally present | Map if available; document if absent |
| Computed | Derived from multiple fields | Document transformation logic |
| Constant | Fixed value per submission | Document source of constant |

### Phase 3: Dictionary Auto-Match (if dictionary exists)

For all placeholders with dictionary entries:
- Apply mapping from dictionary
- Assign confidence HIGH if exact match
- Batch-present HIGH-confidence mappings for user approval

**Batch approval format:**
```
HIGH-CONFIDENCE MAPPINGS (auto-matched from dictionary):
[Table of placeholder → data source → confidence]

Review and type APPROVE ALL or flag specific ones to revise.
```

### Phase 4: Interactive Validation (new or unmatched placeholders)

For each unmatched placeholder, present:
```
Placeholder: {{ cnpj_declarante }}
Type: Mandatory
Description: CNPJ of the declaring institution

What is the data source? Options:
1. model.institution.tax_id (snake_case: institution.tax_id)
2. context.reporting.declarant_cnpj
3. Custom (type your own)
4. Mark as UNKNOWN (lowers confidence)
```

### Phase 5: Build Mapping File

Output `docs/regulatory/{template_type}/gate1-mappings.json`:

```json
{
  "template": "CADOC-4010",
  "spec_version": "2024-01",
  "mapped_at": "ISO-8601",
  "confidence_avg": 87.5,
  "mandatory_coverage": 100,
  "mappings": [
    {
      "placeholder": "cnpj_declarante",
      "data_source": "model.institution.tax_id",
      "prefix": "model",
      "confidence": 95,
      "type": "mandatory",
      "transformation": null
    }
  ]
}
```

### Phase 6: Update Dictionary

After user approves all mappings, auto-save approved entries to `field-dictionary.json` for future reuse.

## Gate 1 Pass Criteria

| Criterion | Requirement |
|-----------|-------------|
| Mandatory coverage | 100% of mandatory fields mapped |
| Confidence average | ≥80% |
| LOW-confidence mandatory | 0 |
| snake_case compliance | 100% of field names |
| Source prefixes | 100% of mappings have prefix |

**Gate 1 Result:** PASS → proceed to Gate 2 | FAIL → resolve failing criteria and re-run
