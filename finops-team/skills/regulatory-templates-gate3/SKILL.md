---
name: ring:regulatory-templates-gate3
description: |
  Gate 3 sub-skill - generates complete .tpl template file with all validated
  mappings from Gates 1-2.

trigger: |
  - Gate 2 PASSED
  - Ready to generate production template file

skip_when: |
  - Gate 2 not passed → complete Gate 2 first
  - Template already generated → verify or regenerate

sequence:
  after: [regulatory-templates-gate2]
---

# Regulatory Templates — Gate 3: Template File Generation

Generates the complete .tpl template file with all validated mappings and transformations from Gates 1-2.

**Parent skill:** `regulatory-templates`
**Input:** Gate 1 mappings + Gate 2 validation, context object
**Output:** Production .tpl file + documentation .tpl.docs file

## Two-File Output Pattern

Production artifacts must be clean. Documentation bloats .tpl files and creates maintenance problems.

| File | Content | Used In |
|------|---------|---------|
| `{type}.tpl` | Pure Django/Jinja2 template with mappings + validation logic | Reporter platform (production) |
| `{type}.tpl.docs` | Field descriptions, transformation rationale, audit notes | Team documentation only |

## Workflow

### Phase 1: Dispatch finops-automation Agent

Pass complete context to `ring:finops-automation`:

```json
{
  "template_type": "CADOC-4010",
  "spec_version": "2024-01",
  "mappings": "[from gate1-mappings.json]",
  "validation_rules": "[from gate2-validation.json]",
  "output_files": {
    "template": "output/CADOC-4010.tpl",
    "docs": "output/CADOC-4010.tpl.docs"
  }
}
```

Agent applies:
- All validated mappings from Gate 1
- Transformation functions as validated in Gate 2
- Field validation logic from Gate 2 validation rules
- Django/Jinja2 template syntax throughout

### Phase 2: Syntax Validation

After agent returns, validate template:

```bash
# Django template syntax check
python manage.py shell -c "from django.template import Template; Template(open('CADOC-4010.tpl').read())"
```

Expected: no errors. Any syntax error → fix and regenerate.

### Phase 3: Mandatory Field Coverage Verification

Count mandatory fields from spec vs fields in generated template:

```bash
grep -c "{{ " CADOC-4010.tpl  # placeholder count
# Compare with mandatory field count from Gate 1
```

Required: 100% mandatory field coverage. Any missing field → fix mappings and regenerate.

### Phase 4: Output Summary

```markdown
## Gate 3 Generation Summary

| Metric | Value | Required |
|--------|-------|---------|
| Template syntax | Valid | Valid |
| Mandatory fields | 47/47 | 100% |
| Optional fields | 12/15 | — |
| Transformation functions | 8/8 | 100% |
| Validation rules applied | 47/47 | 100% |

## Files Generated
- `output/CADOC-4010.tpl` — Production template (Reporter platform)
- `output/CADOC-4010.tpl.docs` — Documentation

Status: PASS | FAIL
```

## Gate 3 Pass Criteria

| Criterion | Requirement |
|-----------|-------------|
| Template syntax | Valid — no errors |
| Mandatory field coverage | 100% |
| All validations applied | 100% of Gate 2 validation rules present |
| Two-file separation | .tpl clean; .tpl.docs separate |

**Gate 3 Result:** PASS → Template ready for deployment | FAIL → fix and regenerate

## Post-Generation (Optional)

**Test Gate:** Run template against BACEN/RFB sandbox API with test data. Verify submission accepted.

**Contribution Gate:** Submit validated template to ring FinOps registry for team reuse.
