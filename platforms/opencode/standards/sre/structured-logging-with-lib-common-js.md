## Structured Logging with lib-common-js (MANDATORY for TypeScript)

All TypeScript services **MUST** integrate structured logging using `@LerianStudio/lib-common-js`. This ensures consistent observability patterns across all Lerian Studio services.

> **Note**: lib-common-js currently provides logging infrastructure. Telemetry will be added in future versions.

### Required Dependencies

```json
{
  "dependencies": {
    "@LerianStudio/lib-common-js": "^1.0.0"
  }
}
```

### Required Imports

```typescript
import { initializeLogger, Logger } from '@LerianStudio/lib-common-js/logger';
import { loadConfigFromEnv } from '@LerianStudio/lib-common-js/config';
import { createLoggingMiddleware } from '@LerianStudio/lib-common-js/http';
```

### Logging Flow (MANDATORY)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BOOTSTRAP (config.ts)                                        │
│    const logger = initializeLogger()                            │
│    → Creates structured logger once at startup                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ROUTER (routes.ts)                                           │
│    const logMid = createLoggingMiddleware(logger)               │
│    app.use(logMid)            ← Injects logger into request     │
│    ...routes...                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. any layer (handlers, services, repositories)                 │
│    const logger = req.logger || parentLogger                    │
│    logger.info('Processing...', { entityId, requestId })        │
│    → Structured JSON logs with correlation IDs                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Bootstrap Initialization (MANDATORY)

```typescript
// bootstrap/config.ts
import { initializeLogger } from '@LerianStudio/lib-common-js/logger';
import { loadConfigFromEnv } from '@LerianStudio/lib-common-js/config';

export async function initServers(): Promise<Service> {
    // Load configuration from environment
    const config = loadConfigFromEnv<Config>();

    // Initialize logger
    const logger = initializeLogger({
        level: config.logLevel,
        serviceName: config.serviceName,
        serviceVersion: config.serviceVersion,
    });

    logger.info('Service starting', {
        service: config.serviceName,
        version: config.serviceVersion,
        environment: config.envName,
    });

    // Pass logger to router...
}
```

### 2. Router Middleware Setup (MANDATORY)

```typescript
// adapters/http/routes.ts
import { createLoggingMiddleware } from '@LerianStudio/lib-common-js/http';
import express from 'express';

export function createRouter(
    logger: Logger,
    handlers: Handlers
): express.Application {
    const app = express();

    // Create logging middleware - injects logger into request
    const logMid = createLoggingMiddleware(logger);
    app.use(logMid);
    app.use(express.json());

    // ... define routes ...

    return app;
}
```

### 3. Using Logger in Handlers/Services (MANDATORY)

```typescript
// handlers/user-handler.ts
async function createUser(req: Request, res: Response): Promise<void> {
    const logger = req.logger;
    const requestId = req.headers['x-request-id'] as string;

    logger.info('Creating user', {
        requestId,
        email: req.body.email,
    });

    try {
        const user = await userService.create(req.body, logger);
        logger.info('User created successfully', {
            requestId,
            userId: user.id,
        });
        res.status(201).json(user);
    } catch (error) {
        logger.error('Failed to create user', {
            requestId,
            error: error.message,
            stack: error.stack,
        });
        throw error;
    }
}
```

### Required Structured Log Format

All logs **MUST** be JSON formatted with these fields:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "Processing request",
  "service": "api-service",
  "version": "1.2.3",
  "environment": "production",
  "requestId": "req-001",
  "context": {
    "method": "POST",
    "path": "/api/v1/users",
    "userId": "usr_456"
  }
}
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `info` |
| `SERVICE_NAME` | Service identifier | `api-service` |
| `SERVICE_VERSION` | Service version | `1.0.0` |
| `ENV_NAME` | Environment name | `production` |

### lib-common-js Logging Checklist

| Check | What to Verify | Status |
|-------|----------------|--------|
| Logger Init | `initializeLogger()` called in bootstrap | Required |
| Middleware | `createLoggingMiddleware(logger)` configured | Required |
| Request Correlation | Logs include `requestId` from headers | Required |
| Structured Format | All logs are JSON formatted | Required |
| Error Logging | Errors include message, stack, and context | Required |
| No Sensitive Data | Passwords, tokens, PII not logged | Required |
| Log Levels | Appropriate levels used (info, warn, error) | Required |

### What not to Do

```typescript
// FORBIDDEN: Using console.log
console.log('Processing user'); // DON'T do this

// FORBIDDEN: Logging sensitive data
logger.info('User login', { password: user.password }); // never

// FORBIDDEN: Unstructured log messages
logger.info(`Processing user ${userId}`); // DON'T use string interpolation

// CORRECT: Always use lib-common-js structured logging
const logger = initializeLogger(config);
logger.info('Processing user', { userId, requestId }); // Structured fields
```

### Standards Compliance Categories (TypeScript Logging)

When evaluating a codebase for lib-common-js logging compliance, check these categories:

| Category | Expected Pattern | Evidence Location |
|----------|------------------|-------------------|
| Logger Init | `initializeLogger()` | `src/bootstrap/config.ts` |
| Middleware Setup | `createLoggingMiddleware(logger)` | `src/adapters/http/routes.ts` |
| Request Correlation | `requestId` in all logs | Handlers, services |
| JSON Format | Structured JSON output | All log statements |
| Error Logging | Error object with stack trace | Error handlers |
| No console.log | No direct console usage | Entire codebase |
| No Sensitive Data | Passwords, tokens excluded | All log statements |

---

