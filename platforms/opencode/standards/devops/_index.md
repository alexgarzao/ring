# DevOps Standards — Module Index

Load ONLY the modules relevant to your current task. Do NOT load all modules.
Read the "Load When" column to decide which modules your task needs.

## Always Load

| Module | Load When |
|--------|-----------|
| infrastructure.md | Every DevOps task — cloud provider (AWS), IaC patterns, Terraform conventions, environment configuration |

## Load by Task Context

| Module | Load When |
|--------|-----------|
| containers.md | Writing or modifying Dockerfiles, multi-stage builds, container optimization, image tagging, base image selection |
| helm.md | Creating or updating Helm charts, writing values.yaml, templating Kubernetes manifests, chart versioning, release management |
| observability.md | Adding metrics, logs, or traces to infrastructure, configuring Prometheus or Grafana, alerting rules, dashboards |
| security.md | Hardening services, managing secrets, configuring RBAC, network policies, vulnerability scanning, least-privilege patterns |
| makefile-standards.md | Writing or modifying Makefiles, adding build targets, standardizing CLI commands, automating local development tasks |
| cicd-pipeline.md | Creating or modifying CI/CD pipelines, GitHub Actions workflows, build automation, deploy pipelines, environment promotion |
| checklist.md | Final pre-PR review, self-verification before submitting DevOps changes for review |
