---
name: regulatory-templates-gate1
description: Gate 1 of regulatory templates - performs regulatory compliance analysis and field mapping
when_to_use: Use after regulatory-templates-setup completes to perform compliance analysis and field mapping
---

# Regulatory Templates - Gate 1: Placeholder Mapping (Post Gate 0)

## Overview

**UPDATED: Gate 1 now maps placeholders from Gate 0 template to data sources. NO structure creation, NO logic addition.**

**Parent skill:** `regulatory-templates`

**Prerequisites:**
- Context from `regulatory-templates-setup`
- Template base from `regulatory-templates-gate0`

**Output:** Mapping of placeholders to backend data sources

---

## Foundational Principle

**Field mapping errors compound through Gates 2-3 and into production.**

Gate 1 is the foundation of regulatory template accuracy:
- **snake_case conversion**: Python/Django ecosystem standard (PEP 8) - mixed conventions cause maintenance nightmares
- **Data source prefixes**: BACEN audits require data lineage traceability - "where did this value come from?"
- **Interactive validation**: No dictionary = no ground truth - user approval prevents assumption errors
- **Confidence thresholds**: Quality gates prevent low-confidence mappings from reaching production
- **Dictionary checks**: Consistency across team, audit trail for regulatory reviews

**Every "shortcut" in Gate 1 multiplies through downstream gates:**
- Skip snake_case → Gate 3 templates have mixed conventions → maintenance debt
- Skip prefixes → Gate 2 cannot trace data sources → debugging nightmares
- Auto-approve mappings → Gate 2 validates wrong assumptions → compliance violations
- Skip optional fields → Gate 1 fails confidence threshold → rework loops
- Lower thresholds → Low-confidence fields reach Gate 3 → production errors

**Technical correctness in Gate 1 = foundation for compliance in production.**

---

## When to Use

**Called by:** `regulatory-templates` skill after Gate 0 template structure copy

**Purpose:** Map each placeholder to its data source - structure already defined in Gate 0

---

## NO EXCEPTIONS - Technical Requirements Are Mandatory

**Gate 1 field mapping requirements have ZERO exceptions.** Every requirement exists to prevent specific failure modes.

### Common Pressures You Must Resist

| Pressure | Your Thought | Reality |
|----------|--------------|---------|
| **Speed** | "camelCase works, skip conversion" | PEP 8 violation creates maintenance debt. 30 min now vs 75+ min debugging later |
| **Simplicity** | "Prefix is verbose, omit it" | BACEN audits require data lineage. Implicit resolution = debugging nightmares |
| **Efficiency** | "AUTO-approve obvious mappings" | No dictionary = no ground truth. "Obvious" assumptions cause compliance violations |
| **Pragmatism** | "Skip optional fields" | Confidence calculated across ALL fields. 64% coverage = FAIL |
| **Authority** | "75% confidence is enough" | Threshold erosion: 75% → 70% → 60%. LOW confidence fields = high-risk mappings |
| **Experience** | "I memorized these, skip dictionary" | Memory is fallible. 1-min check prevents 20-40 min error correction |

### Technical Requirements (Non-Negotiable)

**snake_case Conversion:**
- ✅ REQUIRED: Convert ALL field names to snake_case
- ❌ FORBIDDEN: Use camelCase, PascalCase, or mixed conventions
- Why: Python/Django PEP 8 standard, grep-able patterns, maintenance

**Data Source Prefixes:**
- ✅ REQUIRED: `{{ midaz_onboarding.organization.0.legal_document }}`
- ❌ FORBIDDEN: `{{ organization.legal_document }}`
- Why: Data lineage traceability, multi-source disambiguation, audit compliance

**Interactive Validation:**
- ✅ REQUIRED: AskUserQuestion for EACH field mapping
- ❌ FORBIDDEN: Auto-approve HIGH confidence fields
- Why: No dictionary = no ground truth, user provides domain knowledge

**Confidence Threshold:**
- ✅ REQUIRED: Overall confidence ≥ 80%
- ❌ FORBIDDEN: Lower threshold or skip fields
- Why: Quality gate for Gate 2/3, prevents low-confidence mappings in production

**Dictionary Check:**
- ✅ REQUIRED: Check `~/.claude/docs/regulatory/dictionaries/` first
- ❌ FORBIDDEN: Skip check and use memory
- Why: Consistency, audit trail, error prevention

### The Bottom Line

**Shortcuts in field mapping = errors in production regulatory submissions.**

Gate 1 creates the foundation for Gates 2-3. Technical correctness here prevents compliance violations downstream.

**If you're tempted to skip ANY requirement, ask yourself: Am I willing to debug production BACEN submission failures caused by this shortcut?**

---

## Rationalization Table - Know the Excuses

Every rationalization below has been used to justify skipping requirements. **ALL are invalid.**

| Excuse | Why It's Wrong | Correct Response |
|--------|---------------|------------------|
| "camelCase works fine in Django" | PEP 8 violation, maintenance debt, inconsistent conventions | Convert ALL to snake_case |
| "Prefix is verbose and ugly" | Audit trail required, multi-source disambiguation critical | Prefix ALL fields |
| "HIGH confidence = obvious, no approval needed" | No dictionary = no ground truth, assumptions fail | Ask approval for EACH field |
| "Optional fields don't affect compliance" | Confidence calculated across ALL fields, 64% = FAIL | Map ALL fields |
| "75% is close to 80%, good enough" | Threshold erosion, LOW confidence = high risk | Research to ≥80% |
| "I know these mappings by heart" | Memory fallible, experience creates overconfidence | Check dictionary first |
| "Everyone knows where organization comes from" | Implicit tribal knowledge, new team members lost | Explicit beats implicit |
| "User approval wastes their time" | User provides domain knowledge we lack | Interactive validation mandatory |
| "Conversion is unnecessary busywork" | Dismissing requirements without understanding cost | Technical correctness prevents debt |
| "This is simple, process is overkill" | Simple tasks accumulate into complex problems | Follow workflow completely |

### If You Find Yourself Making These Excuses

**STOP. You are rationalizing.**

The requirements exist to prevent these exact thoughts from causing errors. If a requirement seems "unnecessary," that's evidence it's working - preventing shortcuts that seem reasonable but create risk.

---

## CRITICAL CHANGE

### ❌ OLD Gate 1 (Over-engineering)
- Created complex field mappings
- Added transformation logic
- Built nested structures
- Result: 90+ line templates

### ✅ NEW Gate 1 (Simple)
- Takes template from Gate 0
- Maps placeholders to single data source
- NO structural changes
- Result: <20 line templates

### 🔴 CRITICAL: NAMING CONVENTION - SNAKE_CASE STANDARD
**ALL field names MUST be converted to snake_case:**
- ✅ If API returns `legalDocument` → convert to `legal_document`
- ✅ If API returns `taxId` → convert to `tax_id`
- ✅ If API returns `openingDate` → convert to `opening_date`
- ✅ If API returns `naturalPerson` → convert to `natural_person`
- ✅ If API returns `tax_id` → keep as `tax_id` (already snake_case)

**ALWAYS convert camelCase, PascalCase, or any other convention to snake_case.**

### 🔴 CRITICAL: DATA SOURCES - ALWAYS USE CORRECT DOMAIN PREFIX

**REFERENCE:** See `/docs/regulatory/DATA_SOURCES.md` for complete documentation.

**Available Data Sources (Reporter Platform):**

| Data Source | Descrição | Entidades Principais |
|-------------|-----------|---------------------|
| `midaz_onboarding` | Dados cadastrais | organization, account |
| `midaz_transaction` | Dados transacionais | operation_route, balance, operation |
| `midaz_onboarding_metadata` | Metadados cadastro | custom fields |
| `midaz_transaction_metadata` | Metadados transações | custom fields |

**Field Path Format:**
```
{data_source}.{entity}.{index?}.{field}
```

**Examples:**
```django
# CNPJ da organização (primeiro item da lista)
{{ midaz_onboarding.organization.0.legal_document }}

# Código COSIF (iterando operation_routes)
{%- for route in midaz_transaction.operation_route %}
  {{ route.code }}
{% endfor %}

# Saldo (filtrado por operation_route)
{%- with balance = filter(midaz_transaction.balance, "operation_route_id", route.id)[0] %}
  {{ balance.available }}
{% endwith %}
```

**Common Regulatory Field Mappings:**

| Campo Regulatório | Data Source | Path |
|-------------------|-------------|------|
| CNPJ (8 dígitos) | `midaz_onboarding` | `organization.0.legal_document` |
| Código COSIF | `midaz_transaction` | `operation_route.code` |
| Saldo | `midaz_transaction` | `balance.available` |

**RULE:** Always prefix fields with the correct data source!
- ❌ WRONG: `{{ organization.legal_document }}`
- ✅ CORRECT: `{{ midaz_onboarding.organization.0.legal_document }}`

---

## Gate 1 Process

### STEP 1: Check for Data Dictionary (FROM/TO Mappings)

**HIERARCHICAL SEARCH - Data Dictionary first, Interactive Validation second:**

```javascript
// CRITICAL: Hierarchical search to avoid unnecessary MCP calls

// STANDARDIZED DICTIONARY PATH - ALWAYS USE THIS PATH
const DICTIONARY_BASE_PATH = "~/.claude/docs/regulatory/dictionaries";

const templateCode = context.template_selected.split(' ')[1]; // e.g., "4010"
const templateCategory = context.template_category.toLowerCase(); // e.g., "cadoc"
const dictionaryPath = `${DICTIONARY_BASE_PATH}/${templateCategory}-${templateCode}.yaml`;

// 1. FIRST: Check LOCAL data dictionary
if (fileExists(dictionaryPath)) {
  console.log(`✅ Data dictionary found: ${dictionaryPath}`);
  const dictionary = readYAML(dictionaryPath);

  // Dictionary contains:
  // - field_mappings: FROM (regulatory) → TO (systems)
  // - Validated transformations
  // - Known pitfalls
  // - Validation rules

  // Use existing mappings
  return useDictionary(dictionary);
}

// 2. IF NOT EXISTS: INTERACTIVE VALIDATION REQUIRED
console.log(`⚠️ Dictionary not found. Starting INTERACTIVE VALIDATION...`);
console.log(`📋 Template ${context.template_selected} requires USER APPROVAL for field mappings`);

// 2.1 Query schemas via MCP
console.log(`📡 Fetching system schemas via MCP...`);
const midazSchema = await mcp__apidog_midaz__read_project_oas();
const crmSchema = await mcp__apidog_crm__read_project_oas();

// 2.2 Analyze schemas and SUGGEST mappings (not decide)
// CRITICAL: Preserve exact field casing from schemas!
console.log(`🔍 Analyzing schemas and suggesting mappings...`);
console.log(`⚠️ PRESERVING EXACT FIELD CASING FROM API SCHEMAS`);
const suggestedMappings = analyzeSchemasAndSuggestMappings(
  regulatorySpec,
  midazSchema,  // Fields like: legalDocument, openingDate (camelCase)
  crmSchema     // Fields like: natural_person, tax_id (snake_case)
);

// 2.3 PRESENT suggestions to user for APPROVAL via AskUserQuestion
// CRITICAL: Use interactive validation with selection boxes AND typing option
console.log(`👤 Requesting INTERACTIVE user approval for suggested mappings...`);
const approvedMappings = await interactiveFieldValidation(suggestedMappings);

// 2.4 CREATE dictionary with APPROVED mappings only
const newDictionary = {
  metadata: {
    template_code: templateCode,
    template_name: context.template_selected,
    authority: context.authority,
    created_at: new Date().toISOString(),
    created_by: "interactive validation with user approval",
    version: "1.0"
  },
  field_mappings: approvedMappings, // Only approved mappings
  xml_structure: extractXMLStructure(regulatorySpec),
  validation_rules: extractValidationRules(regulatorySpec)
};

// 2.5 Save APPROVED dictionary for future use
writeYAML(dictionaryPath, newDictionary);
console.log(`✅ Dictionary created with approved mappings: ${dictionaryPath}`);

// 2.6 Use newly created dictionary
return useDictionary(newDictionary);
```

---

## 🔴 CRITICAL: INTERACTIVE VALIDATION FOR TEMPLATES WITHOUT DICTIONARY

### Data Dictionaries Location

**Dicionários de dados disponíveis em:** `~/.claude/docs/regulatory/dictionaries/`

Consulte os dicionários existentes antes de iniciar o mapeamento de campos.

---

### Interactive Validation Process (MANDATORY for templates without dictionary)

```
┌─────────────────────────────────────────────────────────────────┐
│              INTERACTIVE VALIDATION WORKFLOW                      │
│           (For templates WITHOUT data dictionary)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STEP A: Discover Fields from Regulatory Specification       │
    │ - Read regulatory spec (XSD, manual PDF, etc.)             │
    │ - Extract ALL required fields                               │
    │ - Identify field types, formats, validations                │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STEP B: Query API Schemas via MCP                           │
    │ - mcp__apidog-midaz__read_project_oas()                    │
    │ - mcp__apidog-crm__read_project_oas()                      │
    │ - Extract available fields from both systems                │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STEP C: INTERACTIVE VALIDATION FOR EACH FIELD               │
    │                                                              │
    │ For EACH regulatory field, use AskUserQuestion with:        │
    │                                                              │
    │ 1. SELECTION BOX: Show top 3-4 suggested mappings          │
    │ 2. TYPING OPTION: "Other" allows custom field path         │
    │ 3. SKIP OPTION: Mark field for later resolution            │
    │                                                              │
    │ Example AskUserQuestion for "CNPJ" field:                   │
    │ ┌────────────────────────────────────────────────────────┐ │
    │ │ Question: "Map regulatory field 'CNPJ (14 digits)'?"   │ │
    │ │                                                         │ │
    │ │ Options:                                                │ │
    │ │ ○ midaz_onboarding.organization.0.legal_document      │ │
    │ │   (HIGH confidence - exact match in Core one)             │ │
    │ │                                                         │ │
    │ │ ○ crm.holder.document                                  │ │
    │ │   (MEDIUM confidence - found in CRM)                   │ │
    │ │                                                         │ │
    │ │ ○ Skip for now                                         │ │
    │ │   (Mark as unmapped, resolve later)                    │ │
    │ │                                                         │ │
    │ │ ○ Other... [TEXT INPUT]                                │ │
    │ │   (Type custom field path)                             │ │
    │ └────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STEP D: Validate Transformations (for each approved field)  │
    │                                                              │
    │ If field needs transformation, ask user:                    │
    │ ┌────────────────────────────────────────────────────────┐ │
    │ │ Question: "Transformation for 'CNPJ Base (8 digits)'?" │ │
    │ │                                                         │ │
    │ │ Options:                                                │ │
    │ │ ○ slice:':8' (extract first 8 digits)                 │ │
    │ │ ○ No transformation (use raw value)                    │ │
    │ │ ○ Other... [TEXT INPUT]                                │ │
    │ └────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STEP E: Generate and Save Dictionary                        │
    │ - Create YAML with ALL approved mappings                    │
    │ - Save to: DICTIONARY_BASE_PATH/[template].yaml             │
    │ - Dictionary available for future use (no repeat questions) │
    └─────────────────────────────────────────────────────────────┘
```

---

### AskUserQuestion Implementation for Field Mapping

**CRITICAL: Use AskUserQuestion tool with these patterns:**

```javascript
// PATTERN 1: Field Source Selection (with suggestions + typing)
async function askFieldMapping(regulatoryField, suggestions) {
  // Build options from suggestions (max 3) + skip option
  // Note: "Other" option is AUTOMATICALLY added by AskUserQuestion
  const options = [
    ...suggestions.slice(0, 3).map(s => ({
      label: s.field_path,
      description: `${s.confidence_level} confidence (${s.confidence}%) - ${s.reasoning}`
    })),
    {
      label: "Skip for now",
      description: "Mark as unmapped and resolve in Gate 2"
    }
  ];

  return AskUserQuestion({
    questions: [{
      question: `Map regulatory field '${regulatoryField.name}' (${regulatoryField.type}, ${regulatoryField.required ? 'required' : 'optional'})?`,
      header: regulatoryField.code,
      multiSelect: false,
      options: options
      // Note: User can always select "Other" to type custom path
    }]
  });
}

// PATTERN 2: Transformation Selection (with options + typing)
async function askTransformation(field, suggestedTransforms) {
  const options = [
    ...suggestedTransforms.map(t => ({
      label: t.filter,
      description: `${t.description} - Example: '${t.example_input}' → '${t.example_output}'`
    })),
    {
      label: "No transformation",
      description: "Use raw value without modification"
    }
  ];

  return AskUserQuestion({
    questions: [{
      question: `Transformation needed for '${field.name}'?`,
      header: "Transform",
      multiSelect: false,
      options: options
      // Note: User can always select "Other" to type custom filter
    }]
  });
}

// PATTERN 3: Batch Approval (up to 4 fields at once)
async function askBatchApproval(fieldsToApprove) {
  // Group related fields (max 4 questions per batch)
  const questions = fieldsToApprove.slice(0, 4).map(field => ({
    question: `Approve mapping for '${field.regulatory_name}'?\nSuggested: ${field.suggested_path}\nConfidence: ${field.confidence}%`,
    header: field.code,
    multiSelect: false,
    options: [
      { label: "Approve ✓", description: "Accept suggested mapping" },
      { label: "Reject ✗", description: "I'll provide alternative" }
    ]
  }));

  return AskUserQuestion({ questions });
}
```

---

### Complete Interactive Validation Example

```javascript
// EXAMPLE: Interactive validation for e-Financeira evtMovOpFin (no dictionary)

async function interactiveFieldValidation(context) {
  const approvedMappings = [];
  const skippedFields = [];

  // 1. Read regulatory specification
  const regulatorySpec = await readRegulatorySpec(context.template_code);
  const requiredFields = extractRequiredFields(regulatorySpec);

  console.log(`📋 Found ${requiredFields.length} fields requiring validation`);

  // 2. Query API schemas
  const midazSchema = await mcp__apidog_midaz__read_project_oas();
  const crmSchema = await mcp__apidog_crm__read_project_oas();

  // 3. For EACH field, get user approval
  for (const field of requiredFields) {
    // Find suggestions from schemas
    const suggestions = findFieldSuggestions(field, midazSchema, crmSchema);

    // Ask user to select/type mapping
    const response = await AskUserQuestion({
      questions: [{
        question: `Map '${field.name}' (${field.format})?\n\nRegulatory requirement: ${field.description}\nData type: ${field.type}`,
        header: field.code || field.name.substring(0, 10),
        multiSelect: false,
        options: [
          ...suggestions.slice(0, 3).map(s => ({
            label: s.path,
            description: `${s.source} - ${s.confidence}% confidence`
          })),
          {
            label: "Skip",
            description: "Resolve later in Gate 2"
          }
        ]
      }]
    });

    // Process user response
    if (response.includes("Skip")) {
      skippedFields.push(field);
    } else if (response.isCustomInput) {
      // User typed custom path via "Other" option
      approvedMappings.push({
        regulatory_field: field.name,
        api_field: response.customValue,
        transformation: "direct",
        approved_by: "user_custom_input",
        confidence: 100
      });
    } else {
      // User selected suggested option
      const selectedSuggestion = suggestions.find(s => response.includes(s.path));

      // Ask about transformation if needed
      if (field.needsTransformation) {
        const transformResponse = await AskUserQuestion({
          questions: [{
            question: `Transformation for '${field.name}'?`,
            header: "Transform",
            multiSelect: false,
            options: [
              { label: "slice:':8'", description: "First 8 characters" },
              { label: "floatformat:2", description: "2 decimal places" },
              { label: "No transform", description: "Use raw value" }
            ]
          }]
        });

        approvedMappings.push({
          regulatory_field: field.name,
          api_field: selectedSuggestion.path,
          transformation: transformResponse.isCustomInput ? transformResponse.customValue : transformResponse,
          approved_by: "user_selection",
          confidence: selectedSuggestion.confidence
        });
      } else {
        approvedMappings.push({
          regulatory_field: field.name,
          api_field: selectedSuggestion.path,
          transformation: "direct",
          approved_by: "user_selection",
          confidence: selectedSuggestion.confidence
        });
      }
    }
  }

  // 4. Summary and confirmation
  console.log(`✅ Approved: ${approvedMappings.length} fields`);
  console.log(`⏭️ Skipped: ${skippedFields.length} fields (to resolve in Gate 2)`);

  return { approvedMappings, skippedFields };
}
```

---

### Validation Rules for User Input

```javascript
// When user selects "Other" and types custom field path:

const VALID_PATH_PATTERNS = {
  midaz_onboarding: /^midaz_onboarding\.(organization|account)\.\d+\.[a-z_]+$/,
  midaz_transaction: /^midaz_transaction\.(operation_route|balance|operation)\.[a-z_]+$/,
  crm: /^crm\.(holder|alias)\.[a-z_.]+$/,
  metadata: /^(midaz|crm)\.[a-z_]+\.metadata\.[a-z_]+$/
};

function validateUserInputPath(inputPath) {
  // Check against valid patterns
  for (const [source, pattern] of Object.entries(VALID_PATH_PATTERNS)) {
    if (pattern.test(inputPath)) {
      return { valid: true, source };
    }
  }

  // If no pattern matches, warn user but allow
  return {
    valid: false,
    warning: `Path '${inputPath}' doesn't match known patterns. Please verify.`
  };
}
```

### NAMING CONVENTION IN FIELD DISCOVERY

```javascript
CRITICAL: When discovering fields, ALWAYS CONVERT TO SNAKE_CASE!

Examples of CORRECT field mapping with snake_case conversion:
✅ API has "legalDocument" → Map as "organization.legal_document"
✅ API has "taxId" → Map as "organization.tax_id"
✅ API has "TaxID" → Map as "organization.tax_id"
✅ API has "openingDate" → Map as "organization.opening_date"
✅ API has "naturalPerson" → Map as "organization.natural_person"

Examples of INCORRECT field mapping (NEVER DO THIS):
❌ API has "legalDocument" → Mapping as "organization.legalDocument" (keep camelCase)
❌ API has "openingDate" → Mapping as "organization.openingDate" (keep camelCase)

The search patterns below help FIND fields. Once found, CONVERT TO SNAKE_CASE!
```

### Hierarchical Search Strategy

```javascript
DYNAMIC FIELD DISCOVERY ORDER:

⚠️ CRITICAL: When you find a field, CONVERT IT TO SNAKE_CASE!
ALWAYS convert camelCase, PascalCase to snake_case!

For EACH regulatory field required:

STEP 1: Query Available Schemas
----------------------------------------
// Get current schemas via MCP
// PRESERVE field names exactly as they appear in schemas!
const crmSchema = await mcp__apidog_crm__read_project_oas();
const midazSchema = await mcp__apidog_midaz__read_project_oas();

STEP 2: Search CRM First (Most Complete)
----------------------------------------
Priority paths in CRM:
1. holder.document → CPF/CNPJ
2. holder.name → Nome completo
3. holder.type → NATURAL_PERSON or LEGAL_PERSON
4. holder.addresses.primary.* → Endereço principal
5. holder.addresses.additional1.* → Endereço adicional
6. holder.contact.* → Email e telefones
7. holder.naturalPerson.* → Dados de pessoa física
8. holder.legalPerson.* → Dados de pessoa jurídica
9. alias.bankingDetails.* → TODOS dados bancários
10. alias.metadata.* → Campos customizados

STEP 3: Search Core one Second (Account/Transaction)
-------------------------------------------------
Priority paths in Core one:
1. account.name → Nome da conta
2. account.alias → Identificador alternativo
3. account.metadata.* → Dados extras da conta
4. account.status → Status da conta
5. transaction.metadata.* → Dados da transação
6. balance.amount → Saldos
7. organization.legalDocument → Documento da organização

STEP 4: Check Metadata Fields (Custom Data)
-------------------------------------------
Both systems support metadata for custom fields:
- crm.holder.metadata.*
- crm.alias.metadata.*
- midaz.account.metadata.*
- midaz.transaction.metadata.*

STEP 5: Mark as Uncertain
-------------------------
If not found in any system:
- Document all searched locations
- Suggest closest matches found
- Indicate confidence level
```

### Confidence Scoring System

```javascript
CONFIDENCE CALCULATION FOR FIELD MAPPINGS:

HIGH CONFIDENCE (90-100%):
-------------------------
✓ Exact field name match in schema
✓ Data type matches regulatory requirement
✓ Found in primary expected system (CRM for personal, Core one for transactions)
✓ Validation with sample data passes
✓ No transformation needed OR simple transformation

Example:
{
  "field": "CPF/CNPJ",
  "mapped_to": "crm.holder.document",
  "confidence": 95,
  "level": "HIGH",
  "reasoning": "Exact match, CRM is primary for identity, type matches"
}

MEDIUM CONFIDENCE (60-89%):
---------------------------
⚠ Partial field name match or pattern match
⚠ Data type compatible but needs transformation
⚠ Found in secondary system
⚠ Some validation uncertainty

Example:
{
  "field": "Data Abertura",
  "mapped_to": "midaz.account.created_at",
  "confidence": 75,
  "level": "MEDIUM",
  "reasoning": "Pattern match for date, needs timezone conversion"
}

LOW CONFIDENCE (30-59%):
------------------------
⚠ Only synonym or fuzzy match
⚠ Significant transformation required
⚠ Found only in metadata or unexpected location
⚠ Cannot validate with examples

Example:
{
  "field": "Codigo Agencia",
  "mapped_to": "midaz.account.metadata.branch",
  "confidence": 45,
  "level": "LOW",
  "reasoning": "Found in metadata only, cannot confirm format"
}

CONFIDENCE SCORING FORMULA:
Score = Base + NameMatch + SystemMatch + TypeMatch + ValidationMatch

Where:
- Base = 30 (if field exists)
- NameMatch = 0-25 (exact=25, partial=15, pattern=5)
- SystemMatch = 0-25 (primary=25, secondary=15, metadata=5)
- TypeMatch = 0-20 (exact=20, compatible=10, needs_transform=5)
- ValidationMatch = 0-20 (validated=20, partial=10, cannot_validate=0)
```

### Validation with Examples

```javascript
AUTOMATIC VALIDATION PROCESS:

For each mapped field:

1. FETCH SAMPLE DATA:
   // Get real record from API
   const sample = await fetch(`${api_base}/holders?limit=1`);
   const fieldValue = sample.path.to.field;

2. APPLY TRANSFORMATION:
   const transformed = applyTransformation(fieldValue, transformation_rule);

3. VALIDATE FORMAT:
   const isValid = validateAgainstRegex(transformed, regulatory_pattern);

VALIDATION PATTERNS:

CPF: /^\d{11}$/
CNPJ: /^\d{14}$/
CNPJ_BASE: /^\d{8}$/
DATE_BR: /^\d{2}\/\d{2}\/\d{4}$/
DATE_ISO: /^\d{4}-\d{2}-\d{2}$/
PHONE_BR: /^\+?55?\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}$/
EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
CEP: /^\d{5}-?\d{3}$/

VALIDATION EXAMPLE:
Field: "CNPJ Base (8 digits)"
Source: crm.holder.document = "12345678000190"
Transformation: slice:':8'
Result: "12345678"
Pattern: /^\d{8}$/
Valid: ✓ TRUE (confidence +20)
```

### Agent Dispatch

**Use the Task tool to dispatch the finops-analyzer agent for Gate 1 analysis:**

1. **BEFORE dispatching the agent, check for existing data dictionary:**
   ```javascript
   // STANDARDIZED DICTIONARY PATH - ALWAYS USE THIS PATH
   const DICTIONARY_BASE_PATH = "~/.claude/docs/regulatory/dictionaries";

   // Extract template code from context
   const templateCode = context.template_selected.split(' ')[1].toLowerCase(); // e.g., "4010"
   const templateCategory = context.template_category.toLowerCase(); // e.g., "cadoc"
   const dictionaryPath = `${DICTIONARY_BASE_PATH}/${templateCategory}-${templateCode}.yaml`;

   // Try to read the dictionary file
   let dictionaryContent = null;
   let dictionaryExists = false;

   try {
     // Use Read tool to check for dictionary
     dictionaryContent = await Read(dictionaryPath);
     dictionaryExists = true;
     console.log(`✅ Data dictionary found: ${dictionaryPath}`);
   } catch (error) {
     console.log(`⚠️ Data dictionary not found. MCP discovery will be required.`);
     dictionaryExists = false;
   }
   ```

2. **Invoke the Task tool with these parameters:**
   - `subagent_type`: "finops-analyzer"
   - `model`: "opus" (for comprehensive analysis)
   - `description`: "Gate 1: Regulatory compliance analysis with dynamic field discovery"
   - `prompt`: Use the comprehensive prompt below, INCLUDING dictionary content if it exists

3. **Comprehensive Prompt Template:**

```
GATE 1: REGULATORY COMPLIANCE ANALYSIS WITH DATA DICTIONARY

TEMPLATE SELECTION (from context):
- Regulatory Template: ${context.template_selected}
- Template Code: ${context.template_code}
- Authority: ${context.authority}

DATA DICTIONARY STATUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${dictionaryExists ?
`✅ DATA DICTIONARY PROVIDED - DO NOT USE MCP APIS!

The data dictionary has been loaded and is provided below.
YOU MUST USE THIS DICTIONARY DATA ONLY. DO NOT MAKE ANY MCP CALLS.

Dictionary Content:
================================================================================
${dictionaryContent}
================================================================================

INSTRUCTIONS FOR DICTIONARY MODE:
1. USE ONLY the field mappings from the dictionary above
2. DO NOT call mcp__apidog-midaz__ or mcp__apidog-crm__ APIs
3. VALIDATE each mapping from the dictionary
4. CHECK confidence levels and transformations
5. REPORT any issues found in the dictionary
6. PROCEED with analysis using dictionary data ONLY`
:
`⚠️ NO DATA DICTIONARY FOUND - MCP DISCOVERY REQUIRED

No existing data dictionary was found at the expected path.
You MUST perform dynamic field discovery using MCP APIs.

Path checked: ${DICTIONARY_BASE_PATH}/${templateCategory}-${context.template_code}.yaml

INSTRUCTIONS FOR MCP DISCOVERY MODE:

┌─────────────────────────────┐
│ 1. DISCOVER VIA MCP         │
│                             │
│ a) Query Core one schema:      │
│    mcp__apidog-midaz__      │
│    read_project_oas_n78ry3  │
│                             │
│ b) Query CRM schema:        │
│    mcp__apidog-crm__        │
│    read_project_oas_a72jt2  │
│                             │
│ c) Analyze & SUGGEST        │
│    mappings with confidence │
└─────────────────────────────┘
                                       ↓
                          ┌─────────────────────────────┐
                          │ 3. REQUEST USER APPROVAL    │
                          │    (SEMI-AUTOMATIC)         │
                          │                             │
                          │ For EACH field mapping:     │
                          │                             │
                          │ Use AskUserQuestion:        │
                          │ "Field: CNPJ Base           │
                          │  Suggested: organization.   │
                          │  legalDocument + slice:':8' │
                          │  Confidence: HIGH (95%)     │
                          │                             │
                          │  Options:                   │
                          │  A) Approve (recommended)   │
                          │  B) Suggest alternative     │
                          │  C) Skip this field"        │
                          │                             │
                          │ User selects → Save choice  │
                          └─────────────────────────────┘
                                       ↓
                          ┌─────────────────────────────┐
                          │ 4. CREATE DATA DICTIONARY   │
                          │    (APPROVED MAPPINGS ONLY) │
                          │                             │
                          │ Generate YAML with:         │
                          │ - metadata                  │
                          │ - APPROVED field_mappings   │
                          │ - xml_structure             │
                          │ - validation_rules          │
                          │ - pitfalls                  │
                          │                             │
                          │ Save to:                    │
                          │ DICTIONARY_BASE_PATH/       │
                          │ [template-code].yaml        │
                          │                             │
                          └─────────────────────────────┘`}

CRITICAL: NAMING CONVENTION - SNAKE_CASE STANDARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CONVERT ALL FIELD NAMES TO SNAKE_CASE!

When discovering or mapping fields:
✅ If API returns "legalDocument" → convert to "legal_document"
✅ If API returns "taxId" → convert to "tax_id"
✅ If API returns "openingDate" → convert to "opening_date"
✅ If API returns "naturalPerson" → convert to "natural_person"
✅ If API returns "tax_id" → keep as "tax_id" (already snake_case)

ALWAYS convert camelCase, PascalCase to snake_case!
This is the standard for all regulatory templates.

STEP 1: PROCESS FIELD MAPPINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If dictionary exists:
  - Use field_mappings from YAML
  - Apply documented transformations
  - Follow validation rules
  - Note any pitfalls

If dictionary created (new):
  - Document all discovered mappings
  - Calculate confidence scores
  - Test transformations
  - Identify potential pitfalls

STEP 2: VALIDATE MAPPINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For EACH field mapping:
  - Verify source field exists in system schema
  - Test transformation with example data
  - Validate output format matches regulatory requirement
  - Calculate confidence score (0-100)

STEP 3: GENERATE SPECIFICATION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Output structured report with:

1. Data Dictionary Status:
   - dictionary_found: true/false
   - dictionary_path: "${DICTIONARY_BASE_PATH}/cadoc-4010.yaml"
   - dictionary_created: true/false (if new)

2. Field Mappings:
   For EACH regulatory field:
   - field_code: Official regulatory code
   - field_name: Official regulatory name
   - required: true/false
   - source_system: "midaz" | "crm" | "parameter"
   - source_field: Exact path (e.g., "organization.legalDocument")
   - transformation: Django filter (e.g., "slice:':8'")
   - confidence_score: 0-100
   - confidence_level: HIGH/MEDIUM/LOW
   - validated: true/false
   - example_input: Sample input value
   - example_output: Expected output value

3. Validation Summary:
   - total_fields: Number
   - mapped_fields: Number
   - coverage_percentage: Number
   - avg_confidence: Number

4. Data Dictionary Details (if created):
   - mcp_calls_made: ["midaz", "crm"]
   - mappings_discovered: Number
   - user_approvals_requested: Number
   - user_approvals_granted: Number
   - file_created: Path to new YAML file

STEP 4: USER APPROVAL FLOW (SEMI-AUTOMATIC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**CRITICAL: When data dictionary doesn't exist, request user approval**

For EACH discovered field mapping, use AskUserQuestion tool:

```javascript
// Example for CNPJ field
AskUserQuestion({
  questions: [{
    question: "Approve mapping for regulatory field 'CNPJ Base (8 digits)'?\n\n" +
              "Suggested mapping:\n" +
              "  FROM: CADOC 4010 field 'cnpj' (required)\n" +
              "  TO: organization.legalDocument (Core one)\n" +
              "  Transformation: slice:':8'\n" +
              "  Example: '12345678000195' → '12345678'\n" +
              "  Confidence: HIGH (95%)\n\n" +
              "Found in Core one schema, exact match, correct type.",
    header: "CNPJ Field",
    multiSelect: false,
    options: [
      {
        label: "Approve ✓",
        description: "Use suggested mapping (recommended)"
      },
      {
        label: "Modify",
        description: "I'll provide alternative field path"
      },
      {
        label: "Skip",
        description: "Skip this field for now"
      }
    ]
  }]
});

// If user selects "Approve" → add to approved_mappings
// If user selects "Modify" → ask for alternative via "Other" option
// If user selects "Skip" → don't include in dictionary
```

**Approval Flow:**

1. **Present suggestion clearly:**
   - Show regulatory field name and requirements
   - Show suggested system field and transformation
   - Show confidence level and reasoning
   - Show example input/output

2. **Offer clear options:**
   - Approve (recommended for HIGH confidence)
   - Modify (user provides alternative)
   - Skip (leave unmapped for later)

3. **Handle responses:**
   - Approved → Add to field_mappings in dictionary
   - Modified → Use user's alternative
   - Skipped → Document as unmapped, don't block

4. **Batch approvals when possible:**
   - Can ask up to 4 questions at once
   - Group related fields together
   - But keep questions clear and focused

CRITICAL REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ ALWAYS check for data dictionary FIRST
✅ ONLY call MCP if dictionary doesn't exist
✅ REQUEST user approval for ALL discovered mappings
✅ ONLY save APPROVED mappings to dictionary
✅ CREATE data dictionary after approvals
✅ SAVE dictionary for future use
✅ USE exact field paths from dictionary
✅ VALIDATE all transformations

❌ NEVER skip checking for data dictionary
❌ NEVER call MCP when dictionary exists
❌ NEVER save mappings without user approval
❌ NEVER guess field mappings
❌ NEVER auto-approve without asking user

OUTPUT FORMAT:
Structured YAML that can be saved as data dictionary.
Include ONLY approved field mappings with all details.
Document any skipped/unmapped fields separately.

COMPLETION STATUS: COMPLETE, INCOMPLETE, or NEEDS_DISCUSSION
```

4. **Example Task tool invocation:**
```javascript
// STANDARDIZED DICTIONARY PATH - ALWAYS USE THIS PATH
const DICTIONARY_BASE_PATH = "~/.claude/docs/regulatory/dictionaries";

// First, check for data dictionary
const templateCode = context.template_selected.split(' ')[1].toLowerCase();
const templateCategory = context.template_category.toLowerCase();
const dictionaryPath = `${DICTIONARY_BASE_PATH}/${templateCategory}-${templateCode}.yaml`;

let dictionaryContent = null;
let dictionaryExists = false;

try {
  dictionaryContent = await Read(dictionaryPath);
  dictionaryExists = true;
  console.log('✅ Using existing data dictionary - NO MCP calls needed');
} catch {
  dictionaryExists = false;
  console.log('⚠️ No dictionary found - will use MCP discovery');
}

// Build the prompt with dictionary content if it exists
const fullPrompt = buildGate1Prompt(context, dictionaryExists, dictionaryContent);

// Call the Task tool with the built prompt
Task({
  subagent_type: "finops-analyzer",
  model: "opus",
  description: "Gate 1: Regulatory compliance analysis",
  prompt: fullPrompt
});
```

---

## Capture Gate 1 Response

**Extract and store these elements with enhanced confidence tracking:**

```json
{
  "template_name": "CADOC 4010 - Informações de Cadastro",
  "regulatory_standard": "BACEN_CADOC",
  "authority": "BACEN",
  "submission_frequency": "monthly",
  "submission_deadline": "2025-12-31",
  "total_fields": 45,
  "mandatory_fields": 38,
  "optional_fields": 7,
  "discovery_summary": {
    "crm_fields_available": 25,
    "midaz_fields_available": 15,
    "metadata_fields_used": 5,
    "unmapped_fields": 0
  },
  "field_mappings": [
    {
      "field_code": "001",
      "field_name": "CNPJ da Instituição",
      "required": true,
      "type": "string",
      "format": "8 digits (base CNPJ)",
      "mappings_found": [
        {
          "source": "crm.holder.document",
          "system": "CRM",
          "confidence": 95,
          "match_type": "exact"
        },
        {
          "source": "midaz.organization.legalDocument",
          "system": "MIDAZ",
          "confidence": 70,
          "match_type": "partial"
        }
      ],
      "selected_mapping": "crm.holder.document",
      "confidence_score": 95,
      "confidence_level": "HIGH",
      "reasoning": "Exact match in CRM, primary system for identity data",
      "transformation": "slice:':8'",
      "validation_passed": true,
      "status": "confirmed"
    },
    {
      "field_code": "020",
      "field_name": "Data de Abertura da Conta",
      "required": true,
      "type": "date",
      "format": "YYYY-MM-DD",
      "mappings_found": [
        {
          "source": "crm.alias.bankingDetails.openingDate",
          "system": "CRM",
          "confidence": 90,
          "match_type": "exact"
        },
        {
          "source": "midaz.account.created_at",
          "system": "MIDAZ",
          "confidence": 60,
          "match_type": "pattern"
        }
      ],
      "selected_mapping": "crm.alias.bankingDetails.openingDate",
      "confidence_score": 90,
      "confidence_level": "HIGH",
      "reasoning": "Banking details in CRM has exact opening date field",
      "transformation": "date_format:'%Y-%m-%d'",
      "validation_passed": true,
      "status": "confirmed"
    }
    // ... all fields with confidence tracking
  ],
  "uncertainties": [
    {
      "field_code": "025",
      "field_name": "Código da Atividade Econômica",
      "mappings_attempted": [
        "crm.holder.legalPerson.activity",
        "midaz.account.metadata.cnae"
      ],
      "best_match": {
        "source": "crm.holder.legalPerson.activity",
        "confidence": 45,
        "confidence_level": "LOW"
      },
      "doubt": "Field exists but format uncertain - needs validation in Gate 2",
      "suggested_resolution": "Validate if activity field contains CNAE code format"
    }
  ],
  "compliance_risk": "LOW", // Updated based on confidence levels
  "confidence_summary": {
    "high_confidence_fields": 40,
    "medium_confidence_fields": 4,
    "low_confidence_fields": 1,
    "overall_confidence": 89
  },
  "documentation_used": {
    "official_regulatory": "https://www.bcb.gov.br/estabilidadefinanceira/cadoc4010",
    "implementation_reference": "https://docs.lerian.studio/en/cadoc-4010-and-4016",
    "regulatory_framework": "BACEN Circular 3.869/2017"
  }
}
```

---

## Documentation Sources

### Official Regulatory Sources (SOURCE OF TRUTH)

---

## Red Flags - STOP Immediately

If you catch yourself thinking ANY of these, STOP and re-read the NO EXCEPTIONS section:

### Skip Patterns
- "Skip snake_case conversion for..."
- "Omit prefix for obvious fields"
- "Use camelCase this time"
- "Mixed conventions are fine"
- "Dictionary check is ceremony"

### Partial Compliance
- "Convert only mandatory fields"
- "Prefix only ambiguous fields"
- "Auto-approve HIGH confidence"
- "Map only mandatory fields"
- "75% is close enough to 80%"

### Experience-Based Shortcuts
- "I memorized these mappings"
- "I know where this comes from"
- "We've done this 50 times"
- "The pattern is obvious"
- "Dictionary won't exist anyway"

### Justification Language
- "Unnecessary busywork"
- "Verbose and ugly"
- "Wasting user time"
- "Process over outcome"
- "Being pragmatic"
- "Close enough"
- "Everyone knows"

### If You See These Red Flags

1. **Acknowledge the rationalization** ("I'm trying to skip snake_case")
2. **Read the NO EXCEPTIONS section** (understand why it's required)
3. **Read the Rationalization Table** (see your exact excuse refuted)
4. **Follow the requirement completely** (no modifications)

**Technical requirements are not negotiable. Field mapping errors compound through Gates 2-3.**

---

## Pass/Fail Criteria

### PASS Criteria
- ✅ `COMPLETION STATUS: COMPLETE`
- ✅ 0 Critical gaps (unmapped mandatory fields)
- ✅ Overall confidence score ≥ 80%
- ✅ All mandatory fields mapped (even if LOW confidence)
- ✅ < 10% of fields with LOW confidence
- ✅ Dynamic discovery via MCP executed
- ✅ Documentation was consulted (both official and implementation)
- ✅ CRM checked first for banking/personal data

### FAIL Criteria
- ❌ `COMPLETION STATUS: INCOMPLETE`
- ❌ Critical gaps exist (mandatory fields unmapped)
- ❌ Overall confidence score < 60%
- ❌ > 20% fields with LOW confidence
- ❌ Documentation not consulted
- ❌ MCP discovery not performed
- ❌ Only checked one system (didn't check CRM + Core one)

---

## State Tracking

### After PASS:

Update context and output:
```
SKILL: regulatory-templates-gate1
GATE: 1 - Regulatory Compliance Analysis
STATUS: PASSED
TEMPLATE: {context.template_selected}
FIELDS: {total_fields} total, {mandatory_fields} mandatory
UNCERTAINTIES: {uncertainties.length} to validate in Gate 2
COMPLIANCE_RISK: {compliance_risk}
NEXT: → Gate 2: Technical validation
EVIDENCE: Documentation consulted, all mandatory fields mapped
BLOCKERS: None
```

### After FAIL:

Output without updating context:
```
SKILL: regulatory-templates-gate1
GATE: 1 - Regulatory Compliance Analysis
STATUS: FAILED
TEMPLATE: {context.template_selected}
CRITICAL_GAPS: {critical_gaps.length}
HIGH_UNCERTAINTIES: {high_uncertainties.length}
NEXT: → Fix Critical gaps before proceeding
EVIDENCE: Gate 1 incomplete - missing critical mappings
BLOCKERS: Critical mapping gaps must be resolved
```

---

## Critical Validations

Ensure these patterns are followed:
- Use EXACT patterns from Lerian documentation
- Apply filters like `slice`, `floatformat` as shown in docs
- Follow tipoRemessa rules: "I" for new/rejected, "S" for approved only
- Date formats must match regulatory requirements (YYYY/MM, YYYY-MM-DD)
- CNPJ/CPF formatting rules must be exact

---

## Output to Parent Skill

Return to `regulatory-templates` main skill:

```javascript
{
  "gate1_passed": true/false,
  "gate1_context": {
    // All extracted data from Gate 1
  },
  "uncertainties_count": number,
  "critical_gaps": [],
  "next_action": "proceed_to_gate2" | "fix_gaps_and_retry"
}
```

---

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Documentation not accessible | Try alternative URLs or cached versions |
| Field names don't match Core one | Mark as uncertain for Gate 2 validation |
| Missing mandatory fields | Mark as Critical gap, must resolve |
| Format specifications unclear | Consult both Lerian docs and government specs |

---

## Dynamic Discovery Example

```javascript
// EXAMPLE: Finding "Agência" field for CADOC 4010

// 1. Use pattern dictionary
const patterns = ["branch", "agency", "agencia", "branch_code"];

// 2. Query CRM first (banking data priority)
const crmSchema = mcp__apidog_crm__read_project_oas();
// Search result: crm.alias.bankingDetails.branch ✓ (exact match)

// 3. Query Core one as fallback
const midazSchema = mcp__apidog_midaz__read_project_oas();
// Search result: midaz.account.metadata.branch_code ⚠ (in metadata)

// 4. Calculate confidence
const crmMatch = {
  source: "crm.alias.bankingDetails.branch",
  confidence: 95, // Exact match + primary system
  level: "HIGH"
};

const midazMatch = {
  source: "midaz.account.metadata.branch_code",
  confidence: 45, // Metadata only
  level: "LOW"
};

// 5. Select highest confidence
selectedMapping: "crm.alias.bankingDetails.branch"
```

## Remember

1. **CONVERT TO SNAKE_CASE** - All fields must be snake_case (legal_document not legalDocument)
2. **Use MCP for dynamic discovery** - Never hardcode field paths
3. **CRM first for banking/personal data** - It has the most complete holder info
4. **Official specs are SOURCE OF TRUTH** - Regulatory requirements from government
5. **Lerian docs show IMPLEMENTATION** - How to create templates in their system
6. **Template-specific knowledge is valuable** - Always check for existing sub-skills
7. **Confidence scoring is key** - Always calculate and document confidence
8. **Be conservative with mappings** - Mark uncertain rather than guess
9. **Capture everything** - Gate 2 needs complete context with all attempted mappings
10. **Reference both sources** - Note official specs AND implementation examples
11. **Risk assessment based on confidence** - Low confidence = higher compliance risk

## Important Distinction

⚠️ **Regulatory Compliance vs Implementation**
- **WHAT** (Requirements) = Official government documentation
- **HOW** (Implementation) = Lerian documentation examples
- When validating compliance → Use official specs
- When creating templates → Use Lerian patterns
- Never confuse implementation examples with regulatory requirements