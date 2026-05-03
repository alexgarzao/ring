---
name: ring:using-finops-team
description: |
  3 FinOps agents: 2 for Brazilian financial regulatory compliance (BACEN, RFB,
  Open Banking), 1 for infrastructure cost estimation when onboarding customers.
  Supports any regulatory template via open intake system.

trigger: |
  - Brazilian regulatory reporting (BACEN, RFB)
  - Financial compliance requirements
  - Open Banking specifications
  - Template generation for Reporter platform
  - Infrastructure cost estimation for new customers
  - AWS capacity planning and pricing

skip_when: |
  - Non-Brazilian regulations → use appropriate resources
  - Non-AWS infrastructure → adapt formulas
  - One-time cost question → direct calculation
---

# Using Ring FinOps & Regulatory Agents

The ring-finops-team plugin provides 3 specialized FinOps agents. Use them via `Task tool with subagent_type:`.

Follow the **ORCHESTRATOR principle** from `ring:using-ring`. Dispatch agents to handle FinOps complexity; don't implement compliance manually.

## 3 FinOps Specialists

### 1. Infrastructure Cost Estimator
**Skill:** `ring:infrastructure-cost-estimation` (orchestrator skill)

For customer onboarding cost analysis. Orchestrates data collection, then dispatches `ring:infrastructure-cost-estimator` for calculations.

**Entry point:** Load `ring:infrastructure-cost-estimation` skill.

**Products:** Access Manager (always), Core one (optional), Reporter (optional)

**Environments:** Homolog (us-east-2, Single-AZ) and/or Production (sa-east-1, Multi-AZ)

**Backup policy differences:**

| Environment | Retention | PITR | Cost Impact |
|-------------|-----------|------|-------------|
| Homolog | 1-7 days | No | ~Free |
| Production | 7-35 days | Yes | R$ 38-580/month (TPS-based) |

### 2. Regulatory Templates
**Skill:** `ring:regulatory-templates` (orchestrator skill)

For Brazilian regulatory compliance template creation (BACEN, RFB, CVM, SUSEP, COAF).

**Supported templates:**

| Authority | Template Type |
|-----------|--------------|
| BACEN | CADOC 4010, 4016, 4111 |
| BACEN | APIX 001, 002 |
| RFB | e-Financeira (6 event types) |
| RFB | DIMP v10 |
| Any | New spec via URL/XSD/PDF intake |

**Workflow:** 5 stages — Setup → Gate 1 (mapping) → Gate 2 (validation) → Gate 3 (generation) → optional Test + Contribution

**Penalties for errors:** R$10,000-R$500,000 (BACEN); criminal liability (RFB false declarations)

**Entry point:** Load `ring:regulatory-templates` skill.

### 3. Direct Agent Access (for specific tasks)

| Agent | Use When |
|-------|---------|
| `ring:infrastructure-cost-estimator` | Already have all data, need calculations only |
| `ring:finops-analyzer` | Regulatory analysis and mapping validation |
| `ring:finops-automation` | Template file generation (Gate 3) |

## Domain Boundaries

| Need | Use |
|------|-----|
| New customer cost estimate | ring:infrastructure-cost-estimation |
| BACEN/RFB template creation | ring:regulatory-templates |
| Spot cost calculation | ring:infrastructure-cost-estimator directly |
| Template analysis only | ring:finops-analyzer directly |
| Template generation only | ring:finops-automation directly |
| Non-Brazilian regulation | Not covered — use appropriate resources |
