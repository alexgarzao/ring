## Cross-Cutting Decorators

Cross-cutting concerns (logging, caching, metrics) should be handled via decorators to keep business logic clean.

### LogOperation Decorator

```typescript
// src/core/infrastructure/decorators/log-operation.decorator.ts
type Layer = 'controller' | 'application' | 'infrastructure';

interface LogOperationOptions {
    layer: Layer;
    operation?: string;
}

export function LogOperation(options: LogOperationOptions) {
    return function (
        target: any,
        propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value;
        const operation = options.operation ?? propertyKey;

        descriptor.value = async function (...args: any[]) {
            const startTime = Date.now();
            const logger = (this as any).logger ?? console;

            logger.info(`[${options.layer}] Starting ${operation}`, {
                layer: options.layer,
                operation,
                args: args.length,
            });

            try {
                const result = await originalMethod.apply(this, args);
                const duration = Date.now() - startTime;

                logger.info(`[${options.layer}] Completed ${operation}`, {
                    layer: options.layer,
                    operation,
                    duration,
                    success: true,
                });

                return result;
            } catch (error) {
                const duration = Date.now() - startTime;

                logger.error(`[${options.layer}] Failed ${operation}`, {
                    layer: options.layer,
                    operation,
                    duration,
                    success: false,
                    error: error instanceof Error ? error.message : 'Unknown error',
                });

                throw error;
            }
        };

        return descriptor;
    };
}
```

### Usage

```typescript
// src/core/application/use-cases/organization/get-organizations.use-case.ts
@injectable()
export class GetOrganizationsUseCase {
    constructor(
        @inject(OrganizationRepository) private repository: OrganizationRepository,
        @inject(Logger) private logger: Logger,
    ) {}

    @LogOperation({ layer: 'application' })
    async execute(params: { limit: number }): Promise<Organization[]> {
        return this.repository.findAll({ limit: params.limit });
    }
}

// src/core/infrastructure/http/controllers/organization.controller.ts
@Controller('/organizations')
export class OrganizationController {
    @LogOperation({ layer: 'controller', operation: 'listOrganizations' })
    @Get('/')
    async list(@Query('limit') limit?: number) {
        return this.getOrganizations.execute({ limit: limit ?? 10 });
    }
}
```

### Without Decorators (Function Wrapper)

For projects without decorator support:

```typescript
// src/core/infrastructure/utils/log-operation.ts
export function withLogging<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    options: { layer: string; operation: string; logger?: Logger }
): T {
    return (async (...args: Parameters<T>) => {
        const logger = options.logger ?? console;
        const startTime = Date.now();

        logger.info(`[${options.layer}] Starting ${options.operation}`);

        try {
            const result = await fn(...args);
            logger.info(`[${options.layer}] Completed ${options.operation}`, {
                duration: Date.now() - startTime,
            });
            return result;
        } catch (error) {
            logger.error(`[${options.layer}] Failed ${options.operation}`, {
                duration: Date.now() - startTime,
                error,
            });
            throw error;
        }
    }) as T;
}

// Usage
class GetOrganizationsUseCase {
    execute = withLogging(
        async (params: { limit: number }) => {
            return this.repository.findAll({ limit: params.limit });
        },
        { layer: 'application', operation: 'getOrganizations' }
    );
}
```

### Other Common Decorators

```typescript
// Cache decorator
export function Cached(ttlSeconds: number) {
    return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
        const cache = new Map<string, { value: any; expiry: number }>();
        const original = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            const key = JSON.stringify(args);
            const cached = cache.get(key);

            if (cached && cached.expiry > Date.now()) {
                return cached.value;
            }

            const result = await original.apply(this, args);
            cache.set(key, { value: result, expiry: Date.now() + ttlSeconds * 1000 });
            return result;
        };
    };
}

// Retry decorator
export function Retry(maxAttempts: number, delayMs: number = 1000) {
    return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
        const original = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            let lastError: Error;

            for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                try {
                    return await original.apply(this, args);
                } catch (error) {
                    lastError = error as Error;
                    if (attempt < maxAttempts) {
                        await new Promise(r => setTimeout(r, delayMs * attempt));
                    }
                }
            }

            throw lastError!;
        };
    };
}
```

---

