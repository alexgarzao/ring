---
name: ring:infrastructure-cost-estimation
version: 5.0.0
description: |
  Orchestrates infrastructure cost estimation with per-component sharing model.
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
┌─────────────────────────────────────────────────────────────┐
│                    SKILL (Orchestrator)                     │
│                                                             │
│  Step 1: Select Products                                    │
│    - Access Manager: ALWAYS (shared platform)               │
│    - Core one Core: [YES / NO]                                 │
│    - Reporter: [YES / NO]                                   │
│                                                             │
│  Step 2: Basic Info                                         │
│    - Repo path, TPS, Total customers                        │
│                                                             │
│  Step 3: Select Environment(s) to Calculate                 │
│    - [x] Homolog (us-east-2, Single-AZ, 1 replica)         │
│    - [x] Production (sa-east-1, Multi-AZ, 3 replicas)      │
│                                                             │
│  Step 4: Read Helm Charts (for selected products only)      │
│    - ALWAYS: charts/plugin-access-manager/values.yaml       │
│    - If Core one: charts/midaz/values.yaml                     │
│    - If Reporter: charts/reporter/values.yaml               │
│                                                             │
│  Step 5: Ask PER COMPONENT: Shared or Dedicated?            │
│    - VPC, EKS, PostgreSQL, Valkey, etc.                     │
│                                                             │
│  Steps 6-7: Database Config + Billing Model                 │
│                                                             │
│  ↓ All data collected (products + Helm configs)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT (Calculator)                       │
│                                                             │
│  Receives: Products selected + Helm configs → Calculates:   │
│  - Infrastructure costs PER ENVIRONMENT (Homolog + Prod)    │
│  - EKS node sizing from actual CPU/memory requirements      │
│  - Cost attribution (shared ÷ customers, dedicated = full)  │
│  - Access Manager costs ALWAYS shared across ALL customers  │
│  - Profitability analysis (using combined env costs)        │
│                                                             │
│  Returns: Side-by-side Homolog vs Production breakdown      │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Select Products for This Customer

**Ask which products the customer needs:**

| Product | Selection | Sharing | Services |
|---------|-----------|---------|----------|
| **Access Manager** | ALWAYS INCLUDED | ALWAYS SHARED | identity, auth |
| **Core one Core** | Required | Customer choice | onboarding, transaction, ledger, crm |
| **Reporter** | Optional | Customer choice | manager, worker, frontend |

**Use AskUserQuestion for product selection:**
```
AskUserQuestion:
  question: "Which products does this customer need? (Access Manager is always included)"
  header: "Products"
  multiSelect: true
  options:
    - label: "Core one Core + Reporter (Recommended)"
      description: "Full platform: ledger + regulatory reporting"
    - label: "Core one Core only"
      description: "Base ledger platform without reporting"
```

**Product → Helm Chart Mapping:**

| Product | Helm Chart | Always Read |
|---------|------------|-------------|
| Access Manager | `charts/plugin-access-manager/values.yaml` | YES (always shared) |
| Core one Core | `charts/midaz/values.yaml` | If selected |
| Reporter | `charts/reporter/values.yaml` | If selected |

---

## Step 2: Gather Basic Information

| Input | Required | Question | Example |
|-------|----------|----------|---------|
| **Repo Path** | Yes | "What is the application repository path?" | `/workspace/midaz` |
| **Helm Charts Repo** | Optional | "Path to LerianStudio/helm repository?" | `/workspace/helm` |
| **TPS** | Yes | "What is the expected TPS?" | `100` |
| **Total Customers** | Yes | "How many customers share the platform?" | `5` |

**Why Helm Charts Repo?** LerianStudio/helm contains actual CPU/memory configurations per service. Without it, the agent uses Core one default values.

---

## Step 3: Select Environment(s) to Calculate

**Ask which environments need cost estimation:**

| Environment | Region | Configuration | Use Case |
|-------------|--------|---------------|----------|
| **Homolog** | us-east-2 (Ohio) | Single-AZ, 1 replica, ~35% cheaper | Testing, staging |
| **Production** | sa-east-1 (São Paulo) | Multi-AZ, 3 replicas, full HA | Live traffic |

**Use AskUserQuestion for environment selection:**
```
AskUserQuestion:
  question: "Which environments should be estimated?"
  header: "Environments"
  multiSelect: true
  options:
    - label: "Both (Recommended)"
      description: "Calculate Homolog + Production costs for complete picture"
    - label: "Production only"
      description: "Calculate only production environment (São Paulo)"
    - label: "Homolog only"
      description: "Calculate only homolog/staging environment (Ohio)"
```

**Environment Differences:**

| Aspect | Homolog | Production |
|--------|---------|------------|
| **Region** | us-east-2 (Ohio) | sa-east-1 (São Paulo) |
| **Pricing** | ~35% cheaper | Full price |
| **Replicas** | 1 per service | 3 per service (HA) |
| **Database** | Single-AZ | Multi-AZ + Read Replicas |
| **NAT Gateways** | 1 (single AZ) | 3 (one per AZ) |

---

## Step 4: Read Selected Product Helm Charts

### 4a. Always Read Access Manager (ALWAYS SHARED)

**Access Manager is platform-level infrastructure - ALWAYS included, ALWAYS shared across all customers.**

```
ALWAYS READ: charts/plugin-access-manager/values.yaml

Services:
- identity (100m CPU, 128Mi memory)
- auth (500m CPU, 256Mi memory)

Infrastructure (shared):
- auth-database (PostgreSQL for Casdoor)
- valkey (session cache)
```

**Cost Attribution:** Access Manager costs are ALWAYS divided by total platform customers.

### 4b. Read Selected Products (Based on Step 1)

**Read ONLY the Helm charts for products selected in Step 1:**

| Product Selected | Helm Chart to Read | Services |
|------------------|-------------------|----------|
| **Core one Core** (if selected) | `charts/midaz/values.yaml` | onboarding, transaction, ledger, crm |
| **Reporter** (if selected) | `charts/reporter/values.yaml` | manager, worker, frontend |

**Example - Customer selected "Core one Core + Reporter":**
```
Read: charts/plugin-access-manager/values.yaml  → ALWAYS (shared platform)
Read: charts/midaz/values.yaml                  → Selected
Read: charts/reporter/values.yaml               → Selected
```

**Example - Customer selected "Core one Core only":**
```
Read: charts/plugin-access-manager/values.yaml  → ALWAYS (shared platform)
Read: charts/midaz/values.yaml                  → Selected
Skip: charts/reporter/values.yaml               → Not selected
```

### 4c. Extract Resource Configurations

**Source:** `git@github.com:LerianStudio/helm.git`

**For each service, extract:**
```yaml
resources:
  requests:
    cpu: ???m      # CPU request in millicores
    memory: ???Mi  # Memory request
autoscaling:
  minReplicas: ?   # Minimum replicas
  maxReplicas: ?   # Maximum replicas
```

**Example from LerianStudio/helm values.yaml:**
```yaml
transaction:
  replicaCount: 3
  resources:
    requests:
      cpu: 2000m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 512Mi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 9
```

**If no Helm repo available**, use Core one default values from this document.

### 4d. Read Actual Resources (DYNAMIC - from LerianStudio/helm)

**MUST read actual values at runtime - DO NOT use hardcoded values.**

**Source Repository:** `git@github.com:LerianStudio/helm.git`

**Files to Read:**

| Chart | Path | Services |
|-------|------|----------|
| **Core one Core** | `charts/midaz/values.yaml` | onboarding, transaction, ledger, crm |
| **Reporter** | `charts/reporter/values.yaml` | manager, worker, frontend |
| **Access Manager** | `charts/plugin-access-manager/values.yaml` | identity, auth |

**What to Extract per Service:**

```yaml
# For each service, extract:
resources:
  requests:
    cpu: ???m      # CPU request in millicores
    memory: ???Mi  # Memory request
  limits:
    cpu: ???m      # CPU limit
    memory: ???Mi  # Memory limit

autoscaling:
  minReplicas: ?   # Minimum replicas
  maxReplicas: ?   # Maximum replicas

# For databases (postgresql, mongodb, valkey, rabbitmq):
# Look for resourcesPreset or explicit resources block
```

**How to Read:**

1. If local clone exists: `Read tool` on values.yaml files
2. If no local clone: `WebFetch` from GitHub raw URLs:
   - `https://raw.githubusercontent.com/LerianStudio/helm/main/charts/midaz/values.yaml`
   - `https://raw.githubusercontent.com/LerianStudio/helm/main/charts/reporter/values.yaml`
   - `https://raw.githubusercontent.com/LerianStudio/helm/main/charts/plugin-access-manager/values.yaml`

**Fallback:** If plugin/service not found, use Core one core setup as baseline.

---

## Step 5: Ask Per-Component Sharing Model (CRITICAL)

<critical-warning>
⛔ **HARD GATE: MUST ASK ABOUT ALL DATABASE COMPONENTS**

This step requires asking about **BOTH** database types in a SINGLE question:
- **PostgreSQL** (RDS) - Relational database
- **DocumentDB** (MongoDB) - Document database

**FORBIDDEN:** Asking only about PostgreSQL and forgetting DocumentDB.
**REQUIRED:** Use the multiSelect AskUserQuestion with ALL components listed.
</critical-warning>

> **Reference:** See [infrastructure-cost-estimation-guide.md](../../docs/infrastructure-cost-estimation-guide.md#component-sharing-model-critical-input) for:
> - Sharing model definitions (SHARED vs DEDICATED vs ALWAYS SHARED)
> - How sharing works in practice per component
> - NAT Gateway architecture (ALWAYS SHARED)

**Components That MUST Be Asked:**
1. VPC, 2. EKS Nodes, 3. **PostgreSQL**, 4. **DocumentDB**, 5. Valkey, 6. RabbitMQ

**Note:** NAT Gateway and ALB are ALWAYS SHARED (platform-level resources).

**MANDATORY: Use AskUserQuestion tool with multiSelect:**

```
AskUserQuestion:
  question: "Which components need DEDICATED instances? (All others use schema-based sharing)"
  header: "Dedicated"
  multiSelect: true
  options:
    - label: "VPC"
      description: "Fully isolated network (separate VPC per customer)"
    - label: "PostgreSQL"
      description: "Fully isolated RDS instance (not schema-based)"
    - label: "DocumentDB"
      description: "Fully isolated DocumentDB cluster"
    - label: "Valkey"
      description: "Fully isolated ElastiCache cluster"
    - label: "RabbitMQ"
      description: "Fully isolated Amazon MQ broker"
    - label: "EKS Nodes"
      description: "Dedicated compute nodes (separate node group)"
```

**Step 5 Verification Checklist:**
```
[ ] Used multiSelect question (not individual questions per component)
[ ] PostgreSQL included in options
[ ] DocumentDB included in options
[ ] All 6 configurable components listed
[ ] User response captured for ALL components

If any checkbox is NO → STOP and fix before proceeding to Step 6.
```

---

## Step 6: Database Configuration (Production Only)

**For PRODUCTION environment, ask about database HA configuration:**

### Multi-AZ (High Availability)

| Option | Description | Cost Impact |
|--------|-------------|-------------|
| **Multi-AZ = YES** | Automatic failover, standby in different AZ | 2x database cost |
| **Multi-AZ = NO** | No automatic failover | 1x database cost |

**Default:** Production = Multi-AZ YES, Homolog = Multi-AZ NO

### Read Replicas (Scale Reads)

| TPS Range | Recommended Replicas | Why |
|-----------|---------------------|-----|
| < 100 TPS | 0 replicas | Primary can handle load |
| 100-300 TPS | 1 replica | Offload read queries |
| > 300 TPS | 2 replicas | Distribute read load |

**Use AskUserQuestion for database HA:**
```
AskUserQuestion:
  question: "For PRODUCTION databases, what HA configuration?"
  header: "Database HA"
  multiSelect: false
  options:
    - label: "Multi-AZ + Read Replicas (Recommended)"
      description: "Full HA: automatic failover + read scaling"
    - label: "Multi-AZ only"
      description: "Automatic failover, no read replicas"
    - label: "Single-AZ (Not recommended)"
      description: "No HA - only for cost-sensitive scenarios"
```

**Note:** Homolog/Staging always uses Single-AZ, no read replicas (testing only).

---

## Step 6b: Backup Configuration (Per Environment)

**Backup policies differ significantly between Homolog and Production:**

### Backup Types

| Backup Type | Description | AWS Service |
|-------------|-------------|-------------|
| **RDS Automated Backups** | Point-in-Time Recovery (PITR) | Included in RDS |
| **RDS Snapshots** | Manual/scheduled full backups | RDS Snapshots |
| **S3 Application Backups** | Application data exports | S3 Standard |
| **DocumentDB Backups** | Continuous backup + snapshots | DocumentDB |

### Environment-Specific Defaults

| Environment | Backup Type | Retention | PITR | Cost |
|-------------|-------------|-----------|------|------|
| **Homolog** | Automated only | 1-7 days | No | Minimal |
| **Production** | Full (automated + snapshots) | 7-35 days | Yes | Higher |

### Backup Cost Components

| Component | Pricing | Notes |
|-----------|---------|-------|
| **RDS Automated Backup** | Free up to DB size | Beyond DB size: R$ 0.10/GB/month |
| **RDS Snapshots** | R$ 0.10/GB/month | Per snapshot retained |
| **S3 Standard** | R$ 0.12/GB/month | Application backups |
| **S3 Glacier** | R$ 0.02/GB/month | Archive (30+ days) |
| **DocumentDB Backup** | R$ 0.10/GB/month | Beyond retention period |

### Backup Sizing by TPS

| TPS | DB Storage | Homolog Backup | Production Backup | S3 App Backup |
|-----|------------|----------------|-------------------|---------------|
| **1-50** | 50GB | ~0 (free tier) | ~50GB × 2 snapshots | 25GB |
| **50-200** | 150GB | ~0 (free tier) | ~150GB × 3 snapshots | 75GB |
| **200-500** | 500GB | ~50GB (excess) | ~500GB × 4 snapshots | 250GB |

### Backup Configuration Questions

**Use AskUserQuestion for backup policy:**
```
AskUserQuestion:
  question: "What backup retention policy for PRODUCTION?"
  header: "Backup Policy"
  multiSelect: false
  options:
    - label: "Standard (7-day retention, daily snapshots) (Recommended)"
      description: "7-day PITR + 7 daily snapshots (moderate cost)"
    - label: "Extended (35-day retention, daily + weekly snapshots)"
      description: "35-day PITR + daily/weekly snapshots (higher cost)"
    - label: "Minimal (1-day retention, weekly snapshots)"
      description: "1-day PITR + weekly snapshots (lower cost, higher risk)"
```

**Homolog Backup Policy:**
- Always minimal (1-7 day retention)
- No additional snapshots needed (testing environment)
- Cost: Typically free (within RDS automated backup limit)

---

## Step 7: Gather Billing Model

| Input | Question | Example |
|-------|----------|---------|
| **Billing Unit** | "What is the billing unit?" | `transaction` |
| **Price per Unit** | "What price per unit?" | `R$ 0.10` |
| **Expected Volume** | "Expected monthly volume?" | `1,000,000` |

---

## Step 8: Dispatch Agent with Complete Data

**BEFORE dispatching, skill MUST read actual resource configs:**

### 8a. Read Current Values from LerianStudio/helm (Based on Selected Products)

```
# ALWAYS read (platform-level, shared)
Read: charts/plugin-access-manager/values.yaml → Extract: identity, auth resources

# Read based on product selection (Step 1)
If Core one Core selected:
  Read: charts/midaz/values.yaml → Extract: onboarding, transaction, ledger, crm resources

If Reporter selected:
  Read: charts/reporter/values.yaml → Extract: manager, worker, frontend resources

# Also extract database configurations for selected products
```

### 8b. Dispatch Agent with Collected Data

**Only dispatch AFTER reading actual values for selected products:**

```
Task tool:
  subagent_type: "ring:infrastructure-cost-estimator"
  model: "opus"
  prompt: |
    Calculate infrastructure costs and profitability.

    ALL DATA PROVIDED (do not ask questions):

    Products Selected:
    - Access Manager: ALWAYS INCLUDED (shared platform)
    - Core one Core: YES
    - Reporter: YES

    Infrastructure:
    - App Repo: /workspace/midaz
    - Helm Charts Source: LerianStudio/helm (values read below)
    - TPS: 100
    - Total Customers on Platform: 5

    Environments to Calculate: [Homolog, Production]

    Actual Resource Configurations (READ from LerianStudio/helm for selected products):

    # Access Manager (ALWAYS - shared platform)
    [INSERT VALUES FROM charts/plugin-access-manager/values.yaml]

    # Core one Core (selected)
    [INSERT VALUES FROM charts/midaz/values.yaml]

    # Reporter (selected)
    [INSERT VALUES FROM charts/reporter/values.yaml]

    Component Sharing Model:
    | Component | Sharing | Customers |
    |-----------|---------|-----------|
    | VPC | SHARED | 5 |
    | EKS Cluster | SHARED | 5 |
    | EKS Nodes | SHARED | 5 |
    | PostgreSQL | DEDICATED | 1 |
    | Valkey | SHARED | 5 |
    | DocumentDB | SHARED | 5 |
    | RabbitMQ | SHARED | 5 |
    | ALB | SHARED | 5 |
    | NAT Gateway | ALWAYS SHARED | ALL |

    Database Configuration (Production):
    - Multi-AZ: YES
    - Read Replicas: Based on TPS (see Step 5)

    Database Configuration (Homolog):
    - All databases: Single-AZ, No replicas (testing only)

    Billing Model:
    - Billing Unit: transaction
    - Price per Unit: R$ 0.10
    - Expected Volume: 1,000,000/month

    Calculate and return:
    1. Discovered Services (from Helm charts)
    2. Compute Resources (from actual configs - calculate EKS nodes needed)
    3. Service Component Dependencies (which services use which components + Access Manager as ALWAYS SHARED)
    4. HOMOLOG Environment Costs (Ohio, Single-AZ, 1 replica)
    5. PRODUCTION Environment Costs (São Paulo, Multi-AZ, 3 replicas)
    6. Environment Comparison Summary (side-by-side)
    7. Cost by Category (compute, database, cache, network, storage)
    8. Shared vs Dedicated Summary
    9. TPS Capacity Analysis
    10. Profitability Analysis (using combined homolog + production costs)
    11. Summary with recommendations
```

---

## Quick Reference

> **Pricing Tables:** See [infrastructure-cost-estimation-guide.md](../../docs/infrastructure-cost-estimation-guide.md#pricing-reference) for complete AWS pricing (São Paulo and Ohio regions).

---

## Expected Output Sections (from Agent)

> **Full Output Format:** See [infrastructure-cost-estimation-guide.md](../../docs/infrastructure-cost-estimation-guide.md#outputs) for detailed output section descriptions.

The agent returns 11 required sections:
1. Discovered Services
2. Compute Resources (from LerianStudio/helm)
3. Homolog Environment Costs
4. Production Environment Costs
5. Environment Comparison
6. Infrastructure Components (Consolidated)
7. Cost by Category
8. Shared vs Dedicated Summary
9. TPS Capacity Analysis
10. Profitability Analysis (Combined Environments)
11. Summary

---

## Example Workflow

### User Request:
> "Estimate costs for Core one with 100 TPS, 5 customers sharing, PostgreSQL dedicated"

### Step 1: Select Products
```
Products Selected:
- Access Manager: ALWAYS INCLUDED (shared)
- Core one Core: YES
- Reporter: YES (full platform)
```

### Steps 2-7: Skill Gathers Data
```
Repo: /workspace/midaz
TPS: 100
Total Customers: 5
Environments: Both (Homolog + Production)

Component Sharing:
- EKS Cluster: SHARED (5)
- PostgreSQL: DEDICATED (1)  ← user specified
- Valkey: SHARED (5)
- DocumentDB: SHARED (5)
- RabbitMQ: SHARED (5)

Billing:
- Unit: transaction
- Price: R$ 0.10
- Volume: 1,000,000/month
```

### Step 8a: Skill Reads LerianStudio/helm (for selected products)
```
# ALWAYS read (platform-level)
Read: charts/plugin-access-manager/values.yaml
  → identity: 100m CPU, 128Mi memory, 1-3 replicas
  → auth: 500m CPU, 256Mi memory, 3-9 replicas

# Core one Core (selected)
Read: charts/midaz/values.yaml
  → onboarding: 1500m CPU, 512Mi memory, 2-5 replicas
  → transaction: 2000m CPU, 512Mi memory, 3-9 replicas
  → ledger: 1500m CPU, 256Mi memory, 2-9 replicas

# Reporter (selected)
Read: charts/reporter/values.yaml
  → manager: 100m CPU, 256Mi memory
  → worker: 100m CPU, 128Mi memory
  → frontend: 100m CPU, 128Mi memory
```

### Step 8b: Skill Dispatches Agent
```
Agent receives: Products selected + actual Helm values + all collected data
```

### Agent Returns:
```
## Summary

| Metric | Value |
|--------|-------|
| Shared Infrastructure | R$ 1,018/customer |
| Dedicated Infrastructure | R$ 1,490/customer |
| **Total Cost/Customer** | **R$ 2,508/month** |
| Monthly Revenue | R$ 100,000 |
| Gross Profit | R$ 97,492 |
| Gross Margin | 97.5% |
```

---

## Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Assume all components are shared" | Customer may have dedicated DB | **ASK for each component** |
| "Skip component questions" | Cost attribution will be wrong | **Must ask shared/dedicated** |
| "Agent can figure it out" | Agent calculates, skill orchestrates | **Skill collects all data** |
| "Just use total customers" | Some components may be dedicated | **Per-component model required** |
| "Asked about PostgreSQL, that covers databases" | **PostgreSQL ≠ DocumentDB** - they are separate components with different costs | **MUST ask about BOTH PostgreSQL AND DocumentDB** |
| "DocumentDB is obviously shared/dedicated like PostgreSQL" | Customer may want different isolation levels for different data types | **Ask about each database separately in multiSelect** |
| "I'll ask about databases separately" | Separate questions risk forgetting one | **Use single multiSelect with ALL components** |

---

## Checklist Before Dispatch

```
[ ] Products selected (Core one Core, Reporter)?
[ ] Access Manager included (ALWAYS)?
[ ] Repo path collected?
[ ] TPS collected?
[ ] Total customers collected?
[ ] Environments selected (Homolog, Production, Both)?
[ ] LerianStudio/helm values read for selected products?

DATABASE COMPONENTS (CRITICAL - verify BOTH):
[ ] PostgreSQL sharing model collected? (SHARED or DEDICATED)
[ ] DocumentDB sharing model collected? (SHARED or DEDICATED)

OTHER COMPONENTS:
[ ] VPC sharing model collected?
[ ] EKS Nodes sharing model collected?
[ ] Valkey sharing model collected?
[ ] RabbitMQ sharing model collected?

BILLING:
[ ] Billing unit collected?
[ ] Price per unit collected?
[ ] Expected volume collected?

If any NO → Ask user first, then dispatch.
⛔ If PostgreSQL OR DocumentDB is missing → STOP and ask about BOTH databases.
```
