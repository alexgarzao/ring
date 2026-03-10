---
name: ring:dev-helm
description: |
  Mandatory skill for creating and maintaining Helm charts following Lerian conventions.
  Enforces standardized chart structure, values organization, template patterns,
  security defaults, and dependency management.

trigger: |
  - Creating a new Helm chart for any Lerian service
  - Modifying an existing Helm chart (adding components, dependencies, templates)
  - Reviewing a Helm chart PR for convention compliance
  - Migrating a docker-compose setup to Helm

NOT_skip_when: |
  - "It's a simple chart, I don't need all that" → Every chart grows. Structure prevents debt.
  - "I'll add security later" → Security is foundational, not an afterthought.
  - "The defaults are fine" → Lerian has specific conventions that MUST be followed.
  - "I'll just copy another chart" → Copying without understanding introduces drift. Use this skill.

skip_when: |
  - Modifying only application code (no chart changes)
  - Working on non-Helm deployment (docker-compose only) → Use ring:dev-devops

sequence:
  after: [ring:dev-devops]
  before: [ring:dev-sre]

dependencies: [ring:dev-devops]
role: orchestrator

related:
  complementary: [ring:dev-devops, ring:dev-sre, ring:dev-implementation]
  similar: [ring:dev-devops]

input_schema:
  required:
    - name: service_name
      type: string
      description: "Name of the service (e.g., reporter, tracer, plugin-fees)"
    - name: chart_type
      type: string
      enum: [single, multi-component, umbrella]
      description: "Chart architecture type"
    - name: components
      type: array
      items: string
      description: "List of components (e.g., [manager, worker] or [pix, inbound, outbound])"
  optional:
    - name: dependencies
      type: array
      items: string
      description: "Infrastructure dependencies (postgresql, mongodb, rabbitmq, valkey, keda)"
    - name: has_worker
      type: boolean
      description: "Whether the service has a background worker (ScaledJob/Deployment)"
      default: false
    - name: namespace
      type: string
      description: "Target Kubernetes namespace"

output_schema:
  format: markdown
  required_sections:
    - name: "Chart Structure"
      pattern: "^## Chart Structure"
      required: true
    - name: "Validation Results"
      pattern: "^## Validation Results"
      required: true
  metrics:
    - name: compliance_status
      type: enum
      values: [PASS, FAIL, PARTIAL]
    - name: files_created
      type: integer

verification:
  automated:
    - command: "helm lint ."
      description: "Helm linter passes"
      success_pattern: "0 chart\\(s\\) failed"
    - command: "helm template test . 2>&1 | head -5"
      description: "Template renders without errors"
      success_pattern: "^(apiVersion|---)"
  manual:
    - "All values.yaml fields follow Lerian naming conventions"
    - "Secrets do not contain real credentials"
    - "Health check paths match application endpoints"
---

# Helm Chart Creation & Maintenance (Lerian Conventions)

## Overview

This skill enforces Lerian's Helm chart conventions across all services. Every Helm chart MUST follow these patterns to ensure consistency, security, and operability across the platform.

**Reference repository:** `Documents/Lerian/helm/charts/`
**Executor agent:** `ring:helm-engineer`

## CRITICAL: Role Clarification

| Who | Responsibility |
|-----|----------------|
| **This Skill (ring:dev-helm)** | Orchestrates the workflow: validates input, dispatches agent, verifies output |
| **Agent (ring:helm-engineer)** | Executes: reads app source, creates chart files, validates with helm lint |

---

## Step 1: Validate Input

<verify_before_proceed>
- service_name is provided
- chart_type is one of: single, multi-component, umbrella
- components list is not empty
</verify_before_proceed>

```text
REQUIRED INPUT:
- service_name: name of the service
- chart_type: single | multi-component | umbrella
- components: list of component names

OPTIONAL INPUT:
- dependencies: [postgresql, mongodb, rabbitmq, valkey, keda]
- has_worker: true/false
- namespace: target namespace

if any REQUIRED input is missing:
  → STOP and report: "Missing required input: [field]"
```

---

## Step 2: Scaffold Chart Structure

MUST create the following directory structure:

```text
{service_name}/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   │
│   ├── {component}/            # One directory per component
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── ingress.yaml
│   │   ├── hpa.yaml
│   │   ├── pdb.yaml
│   │   └── sa.yaml             # ServiceAccount (if needed)
│   │
│   └── common/                 # Shared resources (if multi-component)
│       └── (shared templates)
│
└── charts/                     # Populated by helm dependency build
```

### Chart.yaml Convention

```yaml
apiVersion: v2
name: {service_name}-helm              # ALWAYS suffix with -helm
description: A Helm chart for deploying {service_name}
type: application
home: https://github.com/LerianStudio/{service_name}/tree/main/deploy/charts/{service_name}
sources:
  - https://github.com/LerianStudio/{service_name}
maintainers:
  - name: "Lerian Studio"
    email: "support@lerian.studio"
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - midaz
  - lerian
  - {service_name}
icon: https://avatars.githubusercontent.com/u/148895005?s=200&v=4
```

<cannot_skip>
Chart name MUST have `-helm` suffix.
Exceptions ONLY for: `plugin-access-manager`, `otel-collector-lerian`.
</cannot_skip>

### Naming Convention Exceptions

```text
CHART NAME RULES:
- Default: {service_name}-helm (e.g., reporter-helm, tracer-helm)
- Exception: plugin-access-manager (no -helm suffix)
- Exception: otel-collector-lerian (no -helm suffix)

if service_name is NOT in exception list:
  → chart name = {service_name}-helm
```

---

## Step 3: Create _helpers.tpl

MUST define these helper functions per component:

```text
FOR EACH component in components:
  DEFINE:
    - {component}.name          → truncated to 63 chars
    - {component}.fullname      → truncated to 63 chars
    - {component}.chart         → {chartName}-{version} replacing + with _
    - {component}.labels        → standard Kubernetes labels
    - {component}.selectorLabels → app.kubernetes.io/name + instance
    - {component}.versionLabelValue → truncated to 63 chars

  ALSO DEFINE (if applicable):
    - {component}.serviceAccountName
    - global.namespace          → from namespaceOverride or Release.Namespace
    - plugin.version            → from Chart.AppVersion
```

### Mandatory Labels

```yaml
labels:
  helm.sh/chart: {{ include "{component}.chart" .context }}
  app.kubernetes.io/name: {{ .name }}
  app.kubernetes.io/instance: {{ .context.Release.Name }}
  app.kubernetes.io/version: {{ include "{component}.versionLabelValue" .context }}
  app.kubernetes.io/managed-by: {{ .context.Release.Service }}
```

For multi-component charts, ALSO add:
```yaml
  app.kubernetes.io/component: {component-name}
  app.kubernetes.io/part-of: {service_name}
```

---

## Step 4: Create values.yaml

<cannot_skip>
values.yaml MUST follow this exact structure. Do NOT invent custom structures.
</cannot_skip>

### Top-Level Structure

```yaml
# 1. Global overrides
nameOverride: ""
fullnameOverride: ""
namespaceOverride: "{namespace}"

# 2. Global external dependency configuration (if applicable)
global:
  externalPostgresDefinitions:
    enabled: false
    connection:
      host: ""
      port: "5432"
    postgresAdminLogin:
      useExistingSecret:
        name: ""
      username: ""
      password: ""
    credentials:
      useExistingSecret:
        name: ""
      username: ""
      password: ""

# 3. Per-component configuration (REPEAT for each component)
{component}:
  name: "{service_name}-{component}"
  enabled: true
  replicaCount: 1
  revisionHistoryLimit: 10

  image:
    repository: ghcr.io/lerianstudio/{service_name}-{component}
    pullPolicy: IfNotPresent
    tag: "1.0.0"
  imagePullSecrets: []

  nameOverride: ""
  fullnameOverride: ""

  annotations: {}
  podAnnotations: {}

  deploymentStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0

  service:
    type: ClusterIP                    # ALWAYS ClusterIP
    port: {assigned_port}
    annotations: {}

  ingress:
    enabled: false
    className: "nginx"
    annotations: {}
    hosts: []
    tls: []

  resources:
    limits:
      cpu: 200m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi

  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
    targetMemoryUtilizationPercentage: 80
    scaleDownStabilizationSeconds: 300

  pdb:
    enabled: true
    maxUnavailable: 1
    minAvailable: 0
    annotations: {}

  readinessProbe:
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 3
    successThreshold: 1
    failureThreshold: 3

  livenessProbe:
    initialDelaySeconds: 15
    periodSeconds: 20
    timeoutSeconds: 5
    successThreshold: 1
    failureThreshold: 3

  nodeSelector: {}
  tolerations: {}
  affinity: {}

  useExistingSecret: false
  existingSecretName: ""

  serviceAccount:
    create: true
    annotations: {}
    name: ""

  configmap:
    annotations: {}
    # Non-sensitive configuration
    ENV_NAME: "development"
    VERSION: "v1.0.0"
    SERVER_PORT: "{port}"
    SERVER_ADDRESS: ":{port}"
    LOG_LEVEL: "debug"
    # ... service-specific vars

  secrets: {}
    # Sensitive configuration (passwords, keys, tokens)
    # DB_PASSWORD: ""
    # API_KEY: ""

  extraEnvVars: {}

# 4. Common shared configuration (if multi-component)
common:
  configmap:
    ENV_NAME: "development"
    # Shared vars across all components

# 5. Dependency configurations
# ... (postgresql, mongodb, rabbitmq, valkey, keda)
```

### ConfigMap vs Secrets Split Rule

```text
CONFIGMAP (non-sensitive):
  - Server settings (port, address, log level)
  - Database hosts, names, users (NOT passwords)
  - Service URLs and endpoints
  - Feature flags and timeouts
  - Swagger/documentation config
  - Telemetry settings

SECRETS (sensitive):
  - Database passwords
  - API keys and secrets
  - OAuth client ID/secret pairs
  - License keys
  - Webhook secrets
  - Encryption keys
  - RabbitMQ passwords

RULE: If exposed in a log or error message would be "bad" → Secret
```

### Mandatory Environment Variable Groups

```text
FOR EVERY service, MUST include:

1. APP CONFIG:
   ENV_NAME, VERSION, SERVER_PORT, SERVER_ADDRESS, LOG_LEVEL

2. TELEMETRY (if applicable):
   ENABLE_TELEMETRY, OTEL_RESOURCE_SERVICE_NAME, OTEL_LIBRARY_NAME,
   OTEL_RESOURCE_SERVICE_VERSION, OTEL_RESOURCE_DEPLOYMENT_ENVIRONMENT,
   OTEL_EXPORTER_OTLP_ENDPOINT

3. HEALTH (if service has health endpoint):
   HEALTH_PORT (for workers without HTTP server)

4. AUTH (if applicable):
   PLUGIN_AUTH_ENABLED, PLUGIN_AUTH_ADDRESS

5. DATABASE (per type used):
   PostgreSQL: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSL_MODE
   MongoDB: MONGO_URI, MONGO_HOST, MONGO_PORT, MONGO_NAME, MONGO_USER, MONGO_PASSWORD
   Redis/Valkey: REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, REDIS_PROTOCOL
   RabbitMQ: RABBITMQ_URI, RABBITMQ_HOST, RABBITMQ_PORT_AMQP, RABBITMQ_DEFAULT_USER,
             RABBITMQ_DEFAULT_PASS

VERIFY: Compare with application's .env.example or config struct to ensure
        ALL env vars are covered. Missing vars cause runtime failures.
```

<block_condition>
HARD GATE: MUST read the application's .env.example or config.go to extract
ALL expected environment variables. Do NOT guess. Missing env vars are the
#1 cause of CrashLoopBackOff in production.
</block_condition>

---

## Step 5: Dispatch Agent

<dispatch_required agent="ring:helm-engineer">
Create/update Helm chart following Lerian conventions.
</dispatch_required>

```yaml
Task:
  subagent_type: "ring:helm-engineer"
  description: "Create Helm chart for {service_name}"
  prompt: |
    ⛔ MANDATORY: Create Helm chart following Lerian conventions.

    ## Context
    - **Service:** {service_name}
    - **Components:** {components}
    - **Dependencies:** {dependencies}
    - **Chart Type:** {chart_type}

    ## Required Steps
    1. Read application .env.example and config struct
    2. Verify health check endpoints in application source
    3. Create chart structure per Lerian conventions
    4. Map ALL env vars to configmap/secrets
    5. Validate with helm lint and helm template

    ## Required Output
    - Standards Verification (FIRST)
    - Env Var Coverage table (100% coverage required)
    - Validation Results (helm lint MUST pass)
```

```text
if agent returns env_vars_missing > 0:
  → FAIL: "Chart has missing env vars. Fix before proceeding."

if agent returns helm_lint_status == FAIL:
  → Re-dispatch agent with specific lint errors

if all checks PASS:
  → Proceed to Step 6 (Validation)
```

---

## Step 6: Templates Reference

### Deployment Template

MUST include these sections in order:

```text
1. Conditional guard: {{- if .Values.{component}.enabled }}
2. metadata: name, namespace, labels, annotations
3. spec.replicas: conditional on autoscaling.enabled
4. spec.strategy: from values
5. spec.selector.matchLabels
6. spec.template.metadata: labels + podAnnotations
7. spec.template.spec:
   a. imagePullSecrets
   b. serviceAccountName
   c. securityContext (pod-level)
   d. initContainers (wait-for-dependencies if needed)
   e. containers:
      - name, image, imagePullPolicy
      - ports (containerPort, named "http")
      - envFrom (secretRef + configMapRef)
      - env (dynamic: HOST_IP for OTEL, AWS IAM endpoint)
      - resources
      - readinessProbe (httpGet to /health)
      - livenessProbe (httpGet to /health)
      - securityContext (container-level)
   f. AWS IAM sidecar (conditional)
   g. volumes (conditional)
   h. nodeSelector, affinity, tolerations
```

### Health Check Path Convention

<cannot_skip>
MUST verify health check paths against the actual application code.
Do NOT assume paths. Common patterns:
</cannot_skip>

```text
VERIFY health endpoints by reading application source code:
  - Go: Look for mux.HandleFunc("/health", ...) or router.GET("/health", ...)
  - Node.js: Look for app.get("/health", ...) or app.get("/api/admin/health/ready", ...)

COMMON PATHS:
  - /health           → Most Go services (liveness)
  - /ready            → Readiness with dependency checks
  - /healthz          → Alternative convention
  - /api/admin/health/ready → Next.js services (product-console)

NEVER use paths that don't exist in the application.
Wrong probe paths = CrashLoopBackOff.
```

### initContainers Pattern (wait-for-dependencies)

```yaml
initContainers:
  - name: wait-for-dependencies
    image: busybox:1.37
    envFrom:
    - configMapRef:
        name: {{ include "{component}.fullname" . }}
    command:
      - /bin/sh
      - -c
      - >
        for svc in "$DB_HOST:$DB_PORT" "$RABBITMQ_HOST:$RABBITMQ_PORT_AMQP";
        do
          echo "Checking $svc...";
          while ! nc -z $(echo $svc | cut -d: -f1) $(echo $svc | cut -d: -f2); do
            echo "$svc is not ready yet, waiting...";
            sleep 5;
          done;
          echo "$svc is ready!";
        done;
```

### envFrom Pattern (Bulk Injection)

```yaml
envFrom:
- secretRef:
    name: {{ if .Values.{component}.useExistingSecret }}{{ .Values.{component}.existingSecretName }}{{ else }}{{ include "{component}.fullname" . }}{{ end }}
- configMapRef:
    name: {{ include "{component}.fullname" . }}
```

### Dynamic Environment Variables

```yaml
# OpenTelemetry (only when enabled)
{{- if eq (toString .Values.{component}.configmap.ENABLE_TELEMETRY) "true" }}
env:
- name: "HOST_IP"
  valueFrom:
    fieldRef:
      fieldPath: status.hostIP
- name: "OTEL_EXPORTER_OTLP_ENDPOINT"
  value: "$(HOST_IP):4317"
{{- end }}

# AWS IAM Roles Anywhere (only when enabled)
{{- if and .Values.aws .Values.aws.rolesAnywhere .Values.aws.rolesAnywhere.enabled }}
- name: AWS_EC2_METADATA_SERVICE_ENDPOINT
  value: "http://127.0.0.1:{{ .Values.aws.rolesAnywhere.sidecar.port | default 9911 }}"
- name: AWS_EC2_METADATA_SERVICE_ENDPOINT_MODE
  value: "IPv4"
{{- end }}
```

### Security Context Defaults

```yaml
# Pod-level
securityContext:
  fsGroup: 65532                    # Only with AWS IAM sidecar

# Container-level (MANDATORY)
securityContext:
  runAsUser: 1000                   # NEVER 0 (root)
  runAsGroup: 1000
  runAsNonRoot: true
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true      # When possible
```

<forbidden>
Running containers as root (runAsUser: 0) unless explicitly justified
(e.g., reconciliation workers needing log file writes).
</forbidden>

### HPA Template

```text
CONDITIONAL: Only render when autoscaling.enabled AND not using KEDA

Guard: {{- if .Values.{component}.autoscaling.enabled }}

MUST use apiVersion: autoscaling/v2
MUST include both CPU and memory metrics (conditional on values)
MUST include scaleDown stabilization window
```

### ConfigMap Template

```text
MUST include:
1. Common shared values: {{- range $key, $value := .Values.common.configmap }}
2. Component-specific values: {{- range $key, $value := .Values.{component}.configmap }}
3. Extra env vars: {{- with .Values.{component}.extraEnvVars }}

ALL values MUST be quoted: {{ $value | quote }}
```

### Secrets Template

```text
TWO valid patterns:

Pattern 1 (b64enc - explicit encoding):
  data:
    KEY: {{ .Values.secrets.KEY | default "" | b64enc | quote }}

Pattern 2 (stringData - auto encoding, Lerian preferred):
  stringData:
    {{- range $key, $value := .Values.{component}.secrets }}
    {{ $key }}: {{ $value | quote }}
    {{- end }}

MUST have helm hook annotations:
  annotations:
    "helm.sh/hook": "pre-install,pre-upgrade"
    "helm.sh/hook-weight": "-5"

MUST support existing secrets:
  {{- if not .Values.{component}.useExistingSecret }}
```

---

## Step 7: Worker Component (if has_worker)

<verify_before_proceed>
- Is there a background worker/consumer component?
- Does it use KEDA ScaledJob or standard Deployment?
</verify_before_proceed>

### Dual-Mode Worker Pattern

MUST support both KEDA (default) and Deployment modes:

```text
MODE SELECTION:
  if keda.enabled OR keda.external:
    → Render ScaledJob (keda-scaled-job.yaml)
    → Render TriggerAuthentication (common/keda-trigger-authentication.yaml)
  else:
    → Render Deployment (deployment.yaml)
    → Render HPA (hpa.yaml)

GUARD in templates:
  ScaledJob:   {{- if or .Values.keda.enabled .Values.keda.external }}
  Deployment:  {{- if not (or .Values.keda.enabled .Values.keda.external) }}
```

### ScaledJob Template (KEDA mode)

```text
MUST include:
- jobTargetRef with backoffLimit, ttlSecondsAfterFinished, activeDeadlineSeconds
- Container spec matching Deployment pattern (envFrom, resources, etc.)
- restartPolicy: Never
- Triggers with authenticationRef
- Polling interval, history limits, maxReplicaCount
```

### Worker Deployment Template (non-KEDA mode)

```text
MUST include:
- Same container spec as ScaledJob
- initContainers for dependency checks
- readinessProbe and livenessProbe
- VERIFY health endpoint paths against application code
- replicaCount as minimum pool size (typically 2+)
```

---

## Step 8: Dependencies Configuration

### Supported Dependencies

```text
FOR EACH dependency in dependencies:

  postgresql:
    Chart: bitnami/postgresql (version 16.x)
    Condition: postgresql.enabled
    Values: auth.username, auth.password, auth.database, persistence.size

  mongodb:
    Chart: bitnami/mongodb (version 16.x)
    Condition: mongodb.enabled
    Values: auth.rootUser, auth.rootPassword, persistence.size

  rabbitmq:
    Chart: groundhog2k/rabbitmq (version 2.x)
    Condition: rabbitmq.enabled
    Values: authentication, persistence.size

  valkey:
    Chart: valkey/valkey (version 0.7.x)
    Condition: valkey.enabled
    Values: auth.enabled, auth.password

  keda:
    Chart: kedacore/keda (version 2.17.x)
    Condition: keda.enabled
    Tags: [keda-operator]
    Values: crds.install, webhookCerts.generate, operator.resources

  otel-collector-lerian:
    Chart: oci://registry-1.docker.io/lerianstudio/otel-collector-lerian
    Condition: otel-collector-lerian.enabled
```

### Bootstrap Jobs (External Dependencies)

```text
if global.externalPostgresDefinitions.enabled:
  → Create bootstrap-postgres.yaml Job
  → Idempotent: Check if DB exists before creating
  → Use initContainer to wait for DB availability
  → Create role, database, grant privileges

if global.externalRabbitmqDefinitions.enabled:
  → Create bootstrap-rabbitmq.yaml Job
  → Create vhost, user, permissions
```

---

## Step 9: Validate Chart

<cannot_skip>
ALL checks MUST pass before chart is considered complete.
</cannot_skip>

### Automated Validation

```text
RUN in order:

1. helm lint .
   → MUST pass with 0 failures

2. helm template test .
   → MUST render without errors

3. helm template test . --set keda.enabled=false
   → MUST render without errors (if worker exists)

4. Verify ALL application env vars are covered:
   → Read app's .env.example or config struct
   → Compare with configmap + secrets in values.yaml
   → REPORT any missing vars

5. Verify health check paths:
   → Read app's health endpoint registration code
   → Compare with probe paths in deployment template
   → REPORT any mismatches
```

### Manual Checklist

```text
CHECK each item:

[ ] Chart.yaml name has -helm suffix (unless exception)
[ ] All values quoted in ConfigMap ({{ $value | quote }})
[ ] No hardcoded credentials in values.yaml (use placeholders)
[ ] Security context: runAsNonRoot: true, drop ALL capabilities
[ ] Service type is ClusterIP (never NodePort or LoadBalancer)
[ ] HPA enabled by default with CPU and memory metrics
[ ] PDB enabled by default
[ ] Probes match actual application health endpoints
[ ] initContainers wait for all infrastructure dependencies
[ ] Secrets support useExistingSecret pattern
[ ] All env vars from app's .env.example are present
[ ] OTEL injection is conditional on ENABLE_TELEMETRY
[ ] AWS IAM sidecar is conditional on aws.rolesAnywhere.enabled
[ ] Ingress disabled by default
```

---

## Pressure Resistance

See [shared-patterns/shared-pressure-resistance.md](../shared-patterns/shared-pressure-resistance.md)

| User Says | Your Response |
|-----------|---------------|
| "Skip the security context" | "Security context is **MANDATORY**. All containers MUST run as non-root." |
| "We don't need PDB" | "PDB is **REQUIRED** for production readiness. Adding it now." |
| "Just use the default health path" | "**MUST verify** health paths against application code. Wrong paths cause CrashLoopBackOff." |
| "We'll add env vars later" | "Missing env vars are the #1 cause of deployment failures. Reading .env.example now." |
| "No need for existing secret support" | "**MANDATORY** for production. Teams use external secret managers." |

---

## Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Health probes are the same for all services" | Each service has unique endpoints. Wrong paths = CrashLoopBackOff | **MUST read application source code** |
| "We can use NodePort for testing" | Lerian convention: always ClusterIP. Ingress handles external access | **Set service.type: ClusterIP** |
| "Secrets can use default values" | Default passwords in values.yaml are a security risk | **Use empty strings or placeholders** |
| "One configmap for everything" | Sensitive data MUST be in Secrets, not ConfigMap | **Split per ConfigMap vs Secrets rule** |
| "The chart works, so it's done" | Must validate against app env vars AND lint AND template render | **Run ALL validation steps** |
| "initContainers are overkill" | Without dependency checks, pods crash before DB is ready | **Add wait-for-dependencies** |

---

## Execution Report Format

```markdown
## Helm Chart Report: {service_name}

**Status:** [PASS|FAIL|PARTIAL]
**Chart Type:** [single|multi-component|umbrella]
**Components:** [list]
**Dependencies:** [list]

## Files Created/Modified
| File | Action | Status |
|------|--------|--------|
| Chart.yaml | CREATED | OK |
| values.yaml | CREATED | OK |
| templates/_helpers.tpl | CREATED | OK |
| templates/{component}/deployment.yaml | CREATED | OK |
| ... | ... | ... |

## Env Var Coverage
| Source (.env.example) | In ConfigMap | In Secrets | Status |
|-----------------------|-------------|------------|--------|
| SERVER_PORT | YES | - | OK |
| DB_PASSWORD | - | YES | OK |
| MISSING_VAR | NO | NO | MISSING |

## Validation Results
| Check | Status |
|-------|--------|
| helm lint | PASS/FAIL |
| helm template (default) | PASS/FAIL |
| helm template (no keda) | PASS/FAIL |
| Health paths verified | PASS/FAIL |
| All env vars covered | PASS/FAIL |
| Security context | PASS/FAIL |
| No hardcoded secrets | PASS/FAIL |

## Notes
- [Any deviations from standard with justification]
```
