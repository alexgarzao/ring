# Go Standards — Module Index

Load ONLY the modules relevant to your current task. Do NOT load all modules.
Read the "Load When" column to decide which modules your task needs.

## Always Load

| Module | Load When |
|--------|-----------|
| core-deps.md | Every Go task — lib-commons v5 foundation, required imports, package aliases |

## Load by Task Context

| Module | Load When |
|--------|-----------|
| version.md | Checking or setting Go version requirements, updating go.mod |
| frameworks.md | Adding new libraries, checking required package versions, dependency decisions |
| configuration.md | Adding or modifying environment variables, config structs, viper setup, nested configuration patterns |
| observability.md | Adding or modifying service methods, creating new endpoints, implementing tracing/metrics, OpenTelemetry spans, instrumenting code, adding distributed tracing to outgoing calls |
| bootstrap.md | Creating a new service from scratch, modifying main.go or service.go, changing app initialization, setting up staged startup or graceful shutdown |
| auth.md | Implementing authentication or authorization, adding protected routes, JWT validation, Access Manager middleware, OAuth2 flows, service-to-service auth |
| licensing.md | Adding license checks, feature gating, License Manager integration, plan-based entitlements |
| data-transform.md | Converting between domain models and persistence models, implementing ToEntity/FromEntity patterns, writing mappers |
| error-codes.md | Defining new error codes, creating service-specific error constants, implementing the error code convention |
| error-handling.md | Implementing error wrapping, using errors.Is/errors.As, propagating errors with context |
| function-design.md | Writing new functions, refactoring existing ones, applying single responsibility principle, deciding function signatures |
| pagination.md | Implementing list endpoints, returning partial results, cursor-based or offset-based pagination, querying collections with limits |
| testing.md | Writing or reviewing tests, setting up table-driven tests, generating mocks, measuring coverage, edge case patterns |
| logging.md | Adding or modifying log statements, migrating from fmt/log to structured logging, checking forbidden logging patterns |
| linting.md | Configuring golangci-lint, fixing lint issues, setting up pre-commit hooks |
| architecture.md | Setting up project structure, creating new packages, deciding layer boundaries, implementing hexagonal/ports-and-adapters pattern |
| concurrency.md | Writing concurrent code, using goroutines with context, channel patterns, sync primitives, race condition prevention |
| rabbitmq.md | Implementing message queue workers, creating consumers or producers, async processing, exponential backoff, message acknowledgment |
| safe-goroutines.md | Spawning goroutines safely, panic recovery in goroutines, using cruntime policies |
| assertions.md | Using domain validation helpers, cassert patterns, invariant checking that returns errors instead of panicking |
| metrics.md | Defining custom metrics, using cmetrics typed counters/histograms, metric naming conventions |
| safe-math.md | Performing arithmetic on financial values, preventing integer overflow, safe division |
| crypto.md | Encrypting or hashing data, AES-GCM encryption, HMAC-SHA256, using commons/crypto |
| backoff.md | Implementing retry logic with exponential backoff, jitter strategies |
| circuit-breaker.md | Calling external services, implementing resilience patterns, using sony/gobreaker, health checker integration, fallback behavior |
| outbox.md | Publishing events reliably, transactional outbox pattern, ensuring at-least-once delivery |
| compliance-format.md | Reviewing code against Ring standards, producing compliance reports, standards coverage output format |
| checklist.md | Final pre-PR review, self-verification before submitting code for review |
