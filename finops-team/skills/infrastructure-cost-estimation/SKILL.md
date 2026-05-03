---
name: ring:infrastructure-cost-estimation
description: |
  Orchestrates infrastructure cost estimation with tier-based or custom TPS sizing.
  Offers pre-configured tiers (Starter/Growth/Business/Enterprise) or custom TPS input.
  Skill discovers components, asks shared/dedicated for EACH, selects environment(s),
  reads actual Helm chart configs, then dispatches agent for accurate calculations.

trigger: |
  - "How much will this cost on AWS?"
  - "Estimate infrastructure for [repo]"
  - "What should we charge the customer?"
  - "Is this deal profitable?"
  - Adding new customer to platform

skip_when: |
  - No docker-compose in repo → manual estimation needed
  - Non-AWS target → adapt pricing
---

# Infrastructure Cost Estimation

## Architecture: Skill Orchestrates, Agent Calculates

```
SKILL (Orchestrator)
  Step 1: Select Products (Access Manager: ALWAYS; Core one: YES/NO; Reporter: YES/NO)
  Step 2: Basic Info (repo path, total customers)
  Step 2a: Infrastructure Sizing (Tier selection OR custom TPS)
  Step 3: Select Environments to Calculate (Homolog, Production, or Both)
  Step 4: Read Helm Charts (for selected products only)
  Step 5: Ask PER COMPONENT: Shared or Dedicated?
  Steps 6-7: Database Config + Billing Model
       ↓ All data collected
AGENT (Calculator)
  Receives: products + tier/TPS + Helm configs + env selections
  Calculates: per-environment costs (Homolog + Production side-by-side)
  Returns: breakdown + profitability analysis
```

## Products Available

| Product | Selection | Sharing | Helm Chart |
|---------|-----------|---------|-----------|
| Access Manager | ALWAYS | ALWAYS SHARED | `charts/plugin-access-manager` |
| Core one Core | Customer choice | Per-customer | `charts/midaz` |
| Reporter | Customer choice | Per-customer | `charts/reporter` |

**Data source:** `git@github.com:LerianStudio/helm.git`

**Sharing Model:**
- SHARED = Schema-based multi-tenancy (same instance, different schemas)
- DEDICATED = Fully isolated instance (no other customers)

## Tier Definitions

| Tier | TPS | Use Case | EKS Node |
|------|-----|---------|---------|
| Starter | 1-10 | SMB, early stage | t3.small |
| Growth | 10-100 | Growing company | t3.medium |
| Business | 100-1000 | Mid-market | t3.large |
| Enterprise | 1000+ | Large enterprise | t3.xlarge+ |

## Environment Specs

| Environment | Region | AZ | Replicas | Backup |
|-------------|--------|-----|---------|--------|
| Homolog | us-east-2 | Single-AZ | 1 | 1-7 days, minimal |
| Production | sa-east-1 | Multi-AZ | 3 | 7-35 days, PITR |

## Step-by-Step Workflow

### Step 1: Product Selection
AskUserQuestion: Which products does the customer need? (multi-select: Core one, Reporter)
Note: Access Manager is always included and always shared.

### Step 2: Basic Information
- Repository path (e.g., `/home/user/myproject` or GitHub URL)
- Total customers sharing infrastructure

### Step 2a: Infrastructure Sizing
AskUserQuestion: How to size infrastructure?
- "Use a tier" → Options: Starter (1-10 TPS), Growth (10-100 TPS), Business (100-1000 TPS), Enterprise (1000+ TPS)
- "Custom TPS" → Ask for specific TPS value

### Step 3: Environment Selection
AskUserQuestion: Which environments to calculate?
- "Homolog only"
- "Production only"
- "Both (Homolog + Production)"

### Step 4: Read Helm Charts
Read values.yaml from selected products' chart directories:
- Always: `charts/plugin-access-manager/values.yaml`
- If Core one selected: `charts/midaz/values.yaml`
- If Reporter selected: `charts/reporter/values.yaml`

Extract: resource requests/limits (CPU, memory) per container, replica counts, storage specs.

### Step 5: Shared vs Dedicated per Component
For each infrastructure component, AskUserQuestion (per customer):

| Component | Default | Options |
|-----------|---------|---------|
| VPC | SHARED | Shared, Dedicated |
| EKS Cluster | SHARED | Shared, Dedicated |
| PostgreSQL (Core one) | DEDICATED | Shared, Dedicated |
| PostgreSQL (Access Manager) | SHARED | Shared, Dedicated |
| Valkey | SHARED | Shared, Dedicated |
| S3 / MinIO | SHARED | Shared, Dedicated |
| Load Balancer | SHARED | Shared, Dedicated |

### Step 6: Database Configuration (Production only)
AskUserQuestion: Production backup policy?
- "Standard" — 7 days retention, daily snapshots, no PITR
- "Enhanced" — 30 days retention, daily + weekly snapshots, PITR
- "Enterprise" — 35 days retention, continuous backup, PITR

### Step 7: Billing Model
- Unit price per customer (R$/month)
- Contract volume (number of customers)

### Step 8: Dispatch Agent
Send to `ring:infrastructure-cost-estimator` with all collected data.

## Agent Dispatch Payload

```json
{
  "products": ["access-manager", "midaz", "reporter"],
  "tier": "growth",
  "customTPS": null,
  "environments": ["homolog", "production"],
  "helmConfigs": {
    "access-manager": { "resources": {...}, "replicas": 1 },
    "midaz": { "resources": {...}, "replicas": 3 }
  },
  "components": {
    "eks": "shared",
    "postgresql_midaz": "dedicated",
    "valkey": "shared"
  },
  "customers": 5,
  "billingUnit": 2500,
  "backupPolicy": "standard"
}
```

## Expected Output Format

```markdown
# Infrastructure Cost Estimate

## Homolog Environment (us-east-2, Single-AZ)
| Component | Sharing | Monthly Cost | Per-Customer Cost |
|-----------|---------|-------------|-------------------|
| EKS (t3.small) | Shared ÷5 | R$ 276 | R$ 55 |
| PostgreSQL (db.t3.micro) | Dedicated | R$ 150 | R$ 150 |
| ...

**Total Homolog: R$ XXX/month per customer**

## Production Environment (sa-east-1, Multi-AZ, 3 replicas)
| Component | Sharing | Monthly Cost | Per-Customer Cost |
|-----------|---------|-------------|-------------------|
...

**Total Production: R$ XXX/month per customer**

## Profitability Analysis
| Metric | Value |
|--------|-------|
| Total Infrastructure | R$ {homolog + production}/month |
| Billing per Customer | R$ {unit}/month |
| Gross Margin | {%} |
| Break-even Customers | {N} |
```
