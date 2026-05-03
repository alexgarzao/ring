---
name: ring:regulatory-templates
description: |
  5-stage regulatory template orchestrator - manages setup, Gate 1 (analysis + auto-save),
  Gate 2 (validation), Gate 3 (generation), optional Test Gate, optional Contribution Gate.
  Supports any regulatory template (BACEN, RFB, CVM, SUSEP, COAF, or other).

trigger: |
  - Creating BACEN CADOCs (4010, 4016, 4111, or any other)
  - Mapping e-Financeira, DIMP, APIX templates
  - Full automation from analysis to template creation
  - Creating any new regulatory template not yet in registry

skip_when: |
  - Non-Brazilian regulations → not applicable
  - Analysis-only without template → use finops-analyzer directly
  - Template already exists, just needs updates → modify directly

sequence:
  before: [regulatory-templates-setup]
---

# Regulatory Templates — Orchestrator

Orchestrates the regulatory template creation workflow through modular sub-skills, managing a 3-gate sequential validation process with dynamic context passing between gates.

## Architecture

```
regulatory-templates-setup     → Initial configuration and selection
regulatory-templates-gate1     → Regulatory compliance analysis and field mapping
regulatory-templates-gate2     → Technical validation of mappings
regulatory-templates-gate3     → Template file generation (.tpl)
```

**Required agents:**
- `finops-analyzer` — Gates 1-2 (regulatory analysis and validation)
- `finops-automation` — Gate 3 (template file generation)

## Supported Templates

**BACEN (Banco Central):**
- CADOC: 4010 (Cadastro), 4016 (Crédito), 4111 (Câmbio)
- APIX: 001 (Dados Cadastrais), 002 (Contas e Transações)

**RFB (Receita Federal):**
- e-Financeira: evtCadDeclarante, evtAberturaeFinanceira, evtFechamentoeFinanceira, evtMovOpFin, evtMovPP, evtMovOpFinAnual
- DIMP: v10 (Movimentação Patrimonial)

**Any other:** Open intake via official spec URL/XSD/PDF

## 5-Stage Workflow

| Stage | Sub-skill | Description |
|-------|-----------|-------------|
| 0 | ring:regulatory-templates-setup | Template selection, context initialization, dictionary check |
| 1 | ring:regulatory-templates-gate1 | Field mapping: placeholders → data sources, confidence scoring, dictionary update |
| 2 | ring:regulatory-templates-gate2 | Validation: resolve uncertainties, test transformations, confirm mapping rules |
| 3 | ring:regulatory-templates-gate3 | Generation: produce .tpl + .tpl.docs files via finops-automation agent |
| Test | (optional) | Run test submission against sandbox API |
| Contribute | (optional) | Submit new template to registry for team reuse |

Gates are sequential. Cannot skip or reorder.

## Context Object

Pass context between gates:

```json
{
  "authority": "BACEN | RFB | CVM | SUSEP | COAF | OTHER",
  "template_type": "CADOC-4010 | e-Financeira | ...",
  "spec_version": "2024-01",
  "dictionary_status": "exists | not_found",
  "gate1": {
    "status": "PENDING | PASS | FAIL",
    "mappings_file": "docs/regulatory/{type}/gate1-mappings.json",
    "confidence_avg": null,
    "mandatory_coverage": null
  },
  "gate2": {
    "status": "PENDING | PASS | FAIL",
    "validation_file": "docs/regulatory/{type}/gate2-validation.json"
  },
  "gate3": {
    "status": "PENDING | PASS | FAIL",
    "template_file": "output/{type}.tpl",
    "docs_file": "output/{type}.tpl.docs"
  }
}
```

## Stage Execution Protocol

For each stage:
1. Load sub-skill
2. Pass context object
3. Execute stage workflow
4. Update context with results
5. Check pass criteria → proceed or STOP

## Stop Criteria

| Condition | Action |
|-----------|--------|
| Gate 1 mandatory coverage < 100% | STOP: list uncovered mandatory fields |
| Gate 1 confidence avg < 80% | STOP: re-run interactive validation for LOW confidence fields |
| Gate 2 test pass rate < 90% | STOP: fix failing transformations |
| Gate 2 mandatory validation < 100% | STOP: add missing validation rules |
| Gate 3 template syntax error | STOP: fix and regenerate |
| Gate 3 mandatory fields < 100% | STOP: fix mappings and regenerate |

## Output Files

| File | Location | Description |
|------|----------|-------------|
| gate1-mappings.json | `docs/regulatory/{type}/` | Approved field mappings |
| gate2-validation.json | `docs/regulatory/{type}/` | Validation rules per field |
| {type}.tpl | `output/` | Production Django/Jinja2 template |
| {type}.tpl.docs | `output/` | Documentation for template (separate from production artifact) |
| field-dictionary.json | `docs/regulatory/{type}/` | Updated dictionary for future reuse |
