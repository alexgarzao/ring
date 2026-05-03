# TypeScript Standards — Module Index

Load ONLY the modules relevant to your current task. Do NOT load all modules.
Read the "Load When" column to decide which modules your task needs.

## Always Load

| Module | Load When |
|--------|-----------|
| version-config.md | Every TypeScript/NestJS task — Node.js and TypeScript version requirements, strict compiler configuration, tsconfig settings |

## Load by Task Context

| Module | Load When |
|--------|-----------|
| frameworks-and-libraries.md | Adding new libraries, checking required package versions, selecting NestJS modules, dependency decisions, Fastify or Express adapter choices |
| type-safety.md | Defining types, interfaces, or DTOs; enforcing no-any rules; using branded types or generics; reviewing type annotations |
| zod-validation-patterns.md | Validating request payloads, parsing external data, defining schemas with Zod, input sanitization, runtime type checking |
| dependency-injection.md | Creating NestJS modules, registering providers, injecting services, setting up IoC container, module organization |
| asynclocalstorage-for-context.md | Propagating request context across async boundaries, correlation IDs, request-scoped data without passing through function params |
| testing.md | Writing or reviewing tests, setting up unit or integration tests, generating mocks with Jest, measuring coverage, testing NestJS controllers or services |
| error-handling.md | Implementing error wrapping, using custom exceptions, propagating errors with context, try/catch patterns |
| function-design.md | Writing new functions, applying single responsibility principle, deciding function signatures, refactoring existing logic |
| file-organization.md | Structuring new modules, organizing imports, deciding barrel exports, splitting large files, co-location rules |
| naming-conventions.md | Naming files, classes, functions, variables; choosing directory names; applying consistent casing conventions |
| rabbitmq-worker-pattern.md | Implementing message queue workers, creating consumers or producers, async processing with RabbitMQ, message acknowledgment, retry patterns |
| always-valid-domain-model.md | Designing domain entities, enforcing invariants at construction time, preventing invalid state, value objects, factory methods |
| bff-architecture-pattern.md | Building Backend-for-Frontend services, orchestrating multiple upstream calls, response aggregation, client-specific APIs |
| three-layer-dto-mapping.md | Converting between domain models and API DTOs, implementing mapper classes, request/response transformation, three-layer data mapping |
| httpservice-lifecycle.md | Using NestJS HttpService, managing HTTP client lifecycle, interceptors, base URL configuration, timeout handling |
| api-routes-pattern.md | Defining REST API routes, implementing controllers, request validation, response serialization, route organization |
| exception-hierarchy.md | Defining custom exception classes, mapping domain errors to HTTP status codes, exception filters, error response format |
| cross-cutting-decorators.md | Implementing cross-cutting concerns, custom decorators, Guards, Interceptors, Pipes, middleware patterns |
| checklist.md | Final pre-PR review, self-verification before submitting TypeScript code for review |
