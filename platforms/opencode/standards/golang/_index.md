# Go Standards — Module Index

Load ONLY the modules relevant to your current task. Do NOT load all modules.

## Always Load
| Module | Description |
|--------|-------------|
| core-deps.md | lib-commons v5 foundation — required imports, what it provides |

## Load by Task Context
| Module | Keywords | Load When |
|--------|----------|-----------|
| version.md | go version, minimum version, go 1.24 | Checking Go version requirements |
| frameworks.md | fiber, mongo, redis, rabbitmq, library, dependency | Adding new libraries or frameworks |
| configuration.md | config, env, viper, environment variable, yaml | Adding/modifying configuration |
| observability.md | tracing, metrics, spans, otel, instrumentation, trace, prometheus | Adding/modifying service methods, new endpoints, instrumentation |
| bootstrap.md | main.go, service.go, config.go, initialization, startup, server, http | New project setup, app startup changes |
| auth.md | JWT, OAuth2, Access Manager, middleware, protected, authorization, token | Auth routes, protected endpoints, permission checks |
| licensing.md | license, plan, feature flag, entitlement, License Manager | Feature gating, license checks |
| data-transform.md | ToEntity, FromEntity, conversion, mapper, domain, model | Converting between domain and persistence models |
| error-codes.md | error code, ErrCode, constant, error convention | Defining or using error codes |
| error-handling.md | error handling, wrap, unwrap, errors.Is, pkg/errors | Error propagation, handling patterns |
| function-design.md | function, signature, parameter, return, design | Writing new functions or refactoring existing ones |
| pagination.md | pagination, page, cursor, offset, limit, list | Implementing list endpoints or paginated queries |
| testing.md | test, unit test, mock, testify, assert, integration test | Writing or modifying tests |
| logging.md | log, logger, zap, logrus, structured logging | Adding or modifying log statements |
| linting.md | lint, golangci, staticcheck, vet | Linting configuration or fixing lint issues |
| architecture.md | architecture, directory, structure, package, layer, repo, usecase | Project structure, new packages, layering decisions |
| concurrency.md | goroutine, channel, mutex, sync, concurrent, race | Writing concurrent code |
| rabbitmq.md | rabbitmq, worker, consumer, producer, queue, amqp, message broker | RabbitMQ workers, event publishing/consuming |
| safe-goroutines.md | goroutine, panic, cruntime, safe goroutine | Spawning goroutines safely |
| assertions.md | cassert, assert, invariant, validation | Using assertion helpers |
| metrics.md | cmetrics, custom metric, counter, gauge, histogram | Defining or recording custom metrics |
| safe-math.md | safe math, overflow, arithmetic, integer | Arithmetic operations that may overflow |
| crypto.md | crypto, hash, encrypt, decrypt, commons/crypto | Cryptographic operations |
| backoff.md | backoff, retry, exponential, jitter | Retry logic with backoff |
| circuit-breaker.md | circuit breaker, external call, resilience, fallback, http client | Calls to external services |
| outbox.md | outbox, transactional outbox, event publishing, commons/outbox | Reliable event publishing with outbox pattern |
| compliance-format.md | compliance, standards check, output format, review | Reviewing code against standards, compliance output |
| checklist.md | checklist, pre-PR, review, final check | Pre-PR checklist, final review before submitting |
