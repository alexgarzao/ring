---
name: ring:dev-docker-security
description: |
  Creates or audits Dockerfiles and Docker image configurations to achieve
  Docker Hub Health Score grade A. Enforces all evaluable security policies
  and supply chain best practices.

trigger: |
  - Creating a new Dockerfile
  - Auditing an existing Dockerfile for security
  - Preparing images for Docker Hub publication
  - Docker Hub health score is below grade A

related:
  complementary: [ring:dev-devops, ring:dev-sre]

input_schema:
  required:
    - name: dockerfile_path
      type: string
      description: "Path to the Dockerfile to create or audit"
  optional:
    - name: base_image
      type: string
      description: "Preferred base image (e.g., gcr.io/distroless/static-debian12)"
    - name: language
      type: string
      enum: [go, typescript, python, rust, java]
      description: "Programming language of the application"
    - name: service_type
      type: string
      enum: [api, worker, batch, cli]
      description: "Type of service"
    - name: mode
      type: string
      enum: [create, audit]
      default: audit
      description: "Create a new Dockerfile or audit an existing one"

output_schema:
  format: markdown
  required_sections:
    - name: "Health Score Compliance"
      pattern: "^## Health Score Compliance"
      required: true
    - name: "Policy Results"
      pattern: "^### Policy Results"
      required: true
    - name: "Actions Taken"
      pattern: "^## Actions Taken"
      required: true
  metrics:
    - name: result
      type: enum
      values: [PASS, FAIL]
    - name: policies_met
      type: integer
    - name: policies_total
      type: integer
---

# Docker Security — Docker Hub Health Score Grade A

## Overview

This skill creates or audits Dockerfiles and image configurations to achieve **Docker Hub Health Score grade A**. It enforces all security policies that Docker Hub evaluates automatically on every pushed image.

## Docker Hub Health Score Policies

Docker Hub calculates a health score for every image based on these policies:

| # | Policy | Weight | How to Comply |
|---|--------|--------|---------------|
| 1 | **Default non-root user** | Required | Dockerfile MUST have a `USER` directive with a non-root user |
| 2 | **No fixable critical/high CVEs** | Required | Zero critical or high severity vulnerabilities with available fixes |
| 3 | **No high-profile vulnerabilities** | Required | Zero CVEs present in the CISA Known Exploited Vulnerabilities (KEV) catalog |
| 4 | **No AGPL v3 licenses** | Required | No packages with AGPL-3.0-only or AGPL-3.0-or-later licenses |
| 5 | **Supply chain attestations** | Required | SBOM and provenance attestations attached to pushed images |
| 6 | **No outdated base images** | Optional | Base image tag is the latest available (only evaluated for Docker Hub hosted images) |
| 7 | **No unapproved base images** | Optional | Base image is in the organization's approved list (only evaluated for Docker Hub hosted images) |

Policies 6 and 7 are **optional** — they are only evaluated when the base image is hosted on Docker Hub. Images from `gcr.io`, `ghcr.io`, or other registries are not tracked, and these policies show as "not evaluated" without penalizing the score. In practice, we often use non-Docker Hub base images (e.g., `gcr.io/distroless`) for their security benefits, so these policies will not apply. Do not treat them as blockers.

---

## Step 1: Analyze Current State

```text
1. Read the Dockerfile (if mode=audit)
2. Identify:
   - Base image and registry
   - Build stages (multi-stage?)
   - USER directive (present? non-root?)
   - COPY/ADD patterns (unnecessary files?)
   - Package installation (pinned versions?)
   - Final image size indicators
3. If mode=create, gather requirements from inputs
```

## Pipeline Enforcement

These policies are **not just guidelines** — they are automatically enforced in the CI/CD pipeline. When a pull request is opened and contains changes to any application component, the **PR Security Scan** workflow runs and blocks the merge if any required policy fails.

### What happens on every PR

1. **Docker image is built** locally from the Dockerfile in the PR
2. **Trivy scans** the built image for vulnerabilities (SARIF + JSON outputs)
3. **Trivy license scan** checks all packages in the image for AGPL-3.0 licenses
4. **Dockerfile analysis** verifies the presence of a non-root `USER` directive
5. **CISA KEV cross-reference** downloads the Known Exploited Vulnerabilities catalog and checks if any CVE found by Trivy is in the catalog
6. **Health Score Compliance table** is posted as a PR comment with pass/fail for each policy

### PR comment example

```
## Docker Hub Health Score Compliance

#### ✅ Policies — 4/4 met

| Policy | Status |
|--------|--------|
| Default non-root user | ✅ Passed |
| No fixable critical/high CVEs | ✅ Passed |
| No high-profile vulnerabilities | ✅ Passed |
| No AGPL v3 licenses | ✅ Passed |
```

### Merge gate

If **any policy fails**, the workflow sets `has-findings: true` and the pipeline exits with error. The PR **cannot be merged** until all policies pass. This means:

- A missing `USER` directive in the Dockerfile blocks the PR
- A single fixable critical/high CVE blocks the PR
- A CISA KEV vulnerability blocks the PR
- An AGPL-3.0 licensed package blocks the PR

### Supply chain attestations (build-time only)

Policy 5 (SBOM + provenance) is evaluated only on release builds, not on PR scans. The build pipeline attaches these attestations automatically:

```yaml
sbom: generator=docker/scout-sbom-indexer:latest
provenance: mode=max
```

No action is needed in the Dockerfile — this is handled by the pipeline configuration.

---

## Step 2: Apply Security Policies

### Policy 1 — Default Non-Root User

**MANDATORY.** Every Dockerfile MUST set a non-root user.

```dockerfile
# For distroless images (preferred for Go)
USER nonroot:nonroot

# For Alpine-based images
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# For Debian/Ubuntu-based images
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser
```

Rules:
- `USER` directive MUST appear after all `RUN`, `COPY`, and package installation steps
- `USER root` alone does NOT satisfy this policy — user must be non-root
- The user must exist in the image (created via `RUN` or pre-existing like `nonroot` in distroless)
- Never use numeric UID 0

### Policy 2 — No Fixable Critical/High CVEs

Minimize the attack surface:

```dockerfile
# Use minimal base images
FROM gcr.io/distroless/static-debian12    # For statically compiled binaries (Go)
FROM gcr.io/distroless/base-debian12      # For dynamically linked binaries
FROM node:22-alpine                        # For Node.js (Alpine = fewer packages)

# Pin package versions in multi-stage builder
RUN apk add --no-cache \
    ca-certificates=20241010-r0 \
    tzdata=2025a-r0

# Don't install unnecessary packages
# Don't leave package managers in the final image
# Use multi-stage builds to exclude build tools
```

Best practices:
- **Prefer distroless** — ~0 CVEs by default (no shell, no package manager)
- **Alpine over Debian/Ubuntu** — fewer packages = fewer CVEs
- **Multi-stage builds** — build tools stay in builder stage, only runtime in final
- **Pin versions** — avoid pulling packages with newly discovered CVEs
- **Update base images regularly** — outdated images accumulate CVEs

### Policy 3 — No High-Profile Vulnerabilities (CISA KEV)

Same approach as Policy 2. CISA KEV vulnerabilities are a subset of all CVEs — they are actively exploited in the wild. The remediation is the same:
- Use minimal base images
- Keep images up to date
- Fix or remove packages with known KEV entries

### Policy 4 — No AGPL v3 Licenses

```dockerfile
# In multi-stage builder, verify licenses before copying to final
RUN go-licenses check ./... 2>&1 | grep -i "AGPL" && exit 1 || true

# For Node.js
RUN npx license-checker --failOn 'AGPL-3.0'
```

Best practices:
- Audit dependencies before adding them
- Use `trivy fs --scanners license` to check for AGPL-3.0
- If an AGPL dependency is found, replace it with an alternative
- This policy applies to ALL packages in the final image, including OS packages

### Policy 5 — Supply Chain Attestations

This is NOT a Dockerfile concern — it is configured in the **build pipeline**:

```yaml
# In docker/build-push-action
- uses: docker/build-push-action@v7
  with:
    push: true
    sbom: generator=docker/scout-sbom-indexer:latest
    provenance: mode=max
```

When auditing, verify that the CI/CD pipeline includes:
- `sbom:` parameter with a valid SBOM generator
- `provenance: mode=max` for full build provenance

### Policies 6 & 7 — Base Image Freshness and Approval (Optional)

These policies are **not blockers** for grade A when using non-Docker Hub base images. We frequently use `gcr.io/distroless` for its minimal attack surface, which means these policies are skipped automatically.

If using Docker Hub base images:
- Use specific version tags, not `:latest`
- Regularly update to the newest available tag
- Configure approved base images in Docker Hub organization settings

---

## Step 3: Dockerfile Template

### Go Service (API/Worker)

```dockerfile
# ── Builder ──
FROM golang:1.24-alpine AS builder

RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -o /app/server ./cmd/app

# ── Production ──
FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

EXPOSE 8080

USER nonroot:nonroot

ENTRYPOINT ["/server"]
```

### Node.js Service

```dockerfile
# ── Builder ──
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# ── Production ──
FROM node:22-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

EXPOSE 3000

USER appuser

CMD ["node", "dist/index.js"]
```

### Python Service

```dockerfile
# ── Builder ──
FROM python:3.13-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY . .

# ── Production ──
FROM python:3.13-slim

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /app .

EXPOSE 8000

USER appuser

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Step 4: Audit Checklist

When auditing an existing Dockerfile, check each item:

```text
CRITICAL (blocks grade A):
[ ] USER directive exists with non-root user
[ ] Multi-stage build (build tools not in final image)
[ ] Minimal base image (distroless/alpine preferred)
[ ] No unnecessary packages in final stage
[ ] No secrets or credentials in image layers

HIGH (impacts CVE count):
[ ] Base image is up to date
[ ] Package versions are pinned
[ ] No development dependencies in final image
[ ] Build cache is leveraged (COPY go.mod before source)

MEDIUM (best practices):
[ ] .dockerignore exists and excludes .git, node_modules, etc.
[ ] COPY used instead of ADD (unless extracting archives)
[ ] Labels present (maintainer, version)
[ ] Single ENTRYPOINT, no CMD overrides unless intentional

SUPPLY CHAIN (pipeline check):
[ ] Build pipeline includes sbom: parameter
[ ] Build pipeline includes provenance: mode=max
[ ] Images are pushed to Docker Hub (not just local)
```

---

## Step 5: Generate Report

```markdown
## Health Score Compliance

**Target:** Grade A
**Result:** [PASS|FAIL]

### Policy Results

| Policy | Status | Details |
|--------|--------|---------|
| Default non-root user | [PASS/FAIL] | USER [username] at line [N] |
| No fixable critical/high CVEs | [PASS/RISK] | Base: [image], [N] packages in final |
| No high-profile vulnerabilities | [PASS/RISK] | Base image [up to date/outdated] |
| No AGPL v3 licenses | [PASS/RISK] | [N] dependencies audited |
| Supply chain attestations | [PASS/MISSING] | sbom: [yes/no], provenance: [yes/no] |

## Actions Taken

| File | Action | Changes |
|------|--------|---------|
| Dockerfile | [CREATED/UPDATED] | [summary] |
| .dockerignore | [CREATED/UPDATED/UNCHANGED] | [summary] |

## Recommendations

[Only if FAIL or RISK items exist]
```

---

## Severity Calibration

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Directly blocks grade A | Missing USER directive, running as root, secrets in layers |
| **HIGH** | Likely causes CVE failures | Using full debian base, unpinned versions, outdated base |
| **MEDIUM** | Reduces security posture | No .dockerignore, ADD instead of COPY, no multi-stage |
| **LOW** | Best practice deviation | Missing labels, suboptimal layer ordering |

---

## Quick Reference — Minimal Secure Dockerfile

The absolute minimum for grade A compliance:

```dockerfile
FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/binary /binary
USER nonroot:nonroot
ENTRYPOINT ["/binary"]
```

Combined with pipeline configuration:

```yaml
sbom: generator=docker/scout-sbom-indexer:latest
provenance: mode=max
```

This achieves grade A by:
1. `USER nonroot` — non-root user policy
2. Distroless — near-zero CVEs and no AGPL packages
3. No exploitable packages — no KEV matches
4. Pipeline attestations — SBOM + provenance
