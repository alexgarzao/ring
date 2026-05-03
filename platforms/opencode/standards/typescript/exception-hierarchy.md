## Exception Hierarchy

**HARD GATE:** All BFF services MUST use a consistent exception hierarchy with GlobalExceptionFilter.

### Base Exception

```typescript
// src/core/infrastructure/exceptions/api.exception.ts
export class ApiException extends Error {
    constructor(
        message: string,
        public readonly statusCode: number = 500,
        public readonly details?: Record<string, unknown>,
        public readonly code?: string,
    ) {
        super(message);
        this.name = this.constructor.name;
    }

    toJSON() {
        return {
            error: {
                code: this.code ?? this.name,
                message: this.message,
                statusCode: this.statusCode,
                ...(this.details && { details: this.details }),
            },
        };
    }
}
```

### Common Exceptions

```typescript
// src/core/infrastructure/exceptions/index.ts
export class ValidationException extends ApiException {
    constructor(errors: Record<string, string[]>) {
        super('Validation failed', 400, { fields: errors }, 'VALIDATION_ERROR');
    }
}

export class NotFoundException extends ApiException {
    constructor(resource: string, id?: string) {
        super(
            id ? `${resource} with id ${id} not found` : `${resource} not found`,
            404,
            { resource, id },
            'NOT_FOUND'
        );
    }
}

export class UnauthorizedException extends ApiException {
    constructor(message = 'Unauthorized') {
        super(message, 401, undefined, 'UNAUTHORIZED');
    }
}

export class ForbiddenException extends ApiException {
    constructor(message = 'Forbidden') {
        super(message, 403, undefined, 'FORBIDDEN');
    }
}

export class ConflictException extends ApiException {
    constructor(resource: string, field: string) {
        super(
            `${resource} with this ${field} already exists`,
            409,
            { resource, field },
            'CONFLICT'
        );
    }
}

// External service exception
export class Core oneApiException extends ApiException {
    constructor(message: string, statusCode: number, details?: Record<string, unknown>) {
        super(message, statusCode, details, 'MIDAZ_API_ERROR');
    }
}
```

### GlobalExceptionFilter

```typescript
// src/core/infrastructure/filters/global-exception.filter.ts
import { NextResponse } from 'next/server';
import { ApiException } from '../exceptions/api.exception';
import { ZodError } from 'zod';

export class GlobalExceptionFilter {
    catch(error: unknown): NextResponse {
        // Known API exceptions
        if (error instanceof ApiException) {
            return NextResponse.json(error.toJSON(), { status: error.statusCode });
        }

        // Zod validation errors
        if (error instanceof ZodError) {
            return NextResponse.json({
                error: {
                    code: 'VALIDATION_ERROR',
                    message: 'Validation failed',
                    statusCode: 400,
                    details: { fields: error.flatten().fieldErrors },
                },
            }, { status: 400 });
        }

        // Unknown errors - don't leak details
        console.error('[GlobalExceptionFilter] Unhandled error:', error);

        return NextResponse.json({
            error: {
                code: 'INTERNAL_ERROR',
                message: 'An unexpected error occurred',
                statusCode: 500,
            },
        }, { status: 500 });
    }
}
```

### Usage in Controllers

```typescript
// src/core/infrastructure/http/controllers/organization.controller.ts
export class OrganizationController {
    async getById(id: string): Promise<Organization> {
        const organization = await this.repository.findById(id);

        if (!organization) {
            throw new NotFoundException('Organization', id);
        }

        return organization;
    }

    async create(dto: CreateOrganizationDto): Promise<Organization> {
        // Validation
        const parsed = createOrganizationSchema.safeParse(dto);
        if (!parsed.success) {
            throw new ValidationException(parsed.error.flatten().fieldErrors);
        }

        // Check duplicate
        const existing = await this.repository.findByName(dto.name);
        if (existing) {
            throw new ConflictException('Organization', 'name');
        }

        return this.createUseCase.execute(parsed.data);
    }
}
```

---

