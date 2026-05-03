---
name: ring:regulatory-templates-gate2
description: |
  Gate 2 sub-skill - validates uncertain mappings from Gate 1 and confirms
  all field specifications through testing.

trigger: |
  - Gate 1 PASSED
  - Need to validate mappings before template generation

skip_when: |
  - Gate 1 not passed → complete Gate 1 first
  - Gate 2 already passed → proceed to Gate 3

sequence:
  after: [regulatory-templates-gate1]
  before: [regulatory-templates-gate3]
---

# Regulatory Templates — Gate 2: Technical Validation

Validates Gate 1 mappings through testing and confirms all field specifications before template generation.

**Parent skill:** `regulatory-templates`
**Input:** Gate 1 mappings, context object
**Output:** Validated mappings with test results and validation rules

## Purpose

Gate 2 resolves uncertainties and validates that mappings produce correct output:
- All MEDIUM/LOW confidence mappings resolved
- Data transformations tested against real sample data
- Validation rules defined per field for Gate 3 template logic
- 100% mandatory field validation confirmed

## Workflow

### Phase 1: Uncertainty Resolution

Load `gate1-mappings.json`. For each MEDIUM or LOW confidence mapping:

1. Present to user with specific concern: "This mapping has {confidence}% confidence because {reason}"
2. Ask user to confirm or provide correct mapping
3. Retest if mapping changed
4. Upgrade confidence after confirmation

All uncertainties must be resolved before Gate 2 can pass.

### Phase 2: Transformation Testing

For each mapping with `transformation != null`, dispatch `finops-analyzer` to test:

```
Test payload: { sample data matching the data source field }
Expected output: { expected value after transformation }
Actual output: { result of applying transformation }
Pass/Fail
```

**Test pass rate required:** >90%. Failing transformations must be fixed and retested.

### Phase 3: Validation Rule Definition

For each mandatory field, define validation rules for Gate 3 template logic:

```json
{
  "placeholder": "cnpj_declarante",
  "validation_rules": [
    {"type": "not_null", "error": "CNPJ é obrigatório"},
    {"type": "format", "pattern": "^\\d{14}$", "error": "CNPJ deve ter 14 dígitos"},
    {"type": "check_digit", "algorithm": "cnpj", "error": "CNPJ inválido"}
  ]
}
```

### Phase 4: Validation Dashboard

Compile and present summary:

```markdown
## Gate 2 Validation Dashboard

| Metric | Value | Required |
|--------|-------|---------|
| Uncertainties resolved | N/N | 100% |
| Test pass rate | 94% | >90% |
| Mandatory validation | 47/47 | 100% |
| Optional validation | 12/15 | — |

Status: PASS | FAIL
```

### Phase 5: Output

Save `docs/regulatory/{type}/gate2-validation.json`:

```json
{
  "template": "CADOC-4010",
  "validated_at": "ISO-8601",
  "uncertainties_resolved": true,
  "test_pass_rate": 94.5,
  "mandatory_validation_coverage": 100,
  "validated_mappings": [...],
  "validation_rules": [...]
}
```

## Gate 2 Pass Criteria

| Criterion | Requirement |
|-----------|-------------|
| Uncertainties resolved | 100% (all MEDIUM/LOW resolved) |
| Test pass rate | >90% |
| Mandatory validation coverage | 100% |
| No workarounds for BACEN-rejected fields | Zero |

**Gate 2 Result:** PASS → proceed to Gate 3 | FAIL → fix failing criteria and re-run
