# SRE Standards — Module Index

Load ONLY the modules relevant to your current task. Do NOT load all modules.
Read the "Load When" column to decide which modules your task needs.

## Always Load

| Module | Load When |
|--------|-----------|
| observability-and-logging.md | Every SRE task — observability pillars overview, structured logging patterns, log levels, forbidden logging practices |

## Load by Task Context

| Module | Load When |
|--------|-----------|
| tracing.md | Implementing distributed tracing, adding trace spans, propagating context across services, trace sampling, span attributes |
| opentelemetry-with-lib-commons.md | Instrumenting Go services with OpenTelemetry, using lib-commons tracing helpers, setting up OTLP exporters, span context propagation in Go |
| structured-logging-with-lib-common-js.md | Instrumenting TypeScript/Node.js services with structured logging, using lib-common-js logger, correlation IDs in logs, log context in async flows |
| health-checks.md | Implementing health check endpoints, liveness vs readiness probes, Kubernetes probe configuration, dependency health reporting |
| checklist.md | Final pre-PR review, self-verification before submitting SRE or observability changes for review |
