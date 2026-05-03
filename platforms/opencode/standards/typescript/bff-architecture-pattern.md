## BFF Architecture Pattern (MANDATORY)

**HARD GATE:** All Next.js projects with dynamic data MUST use the BFF (Backend for Frontend) pattern via API Routes. Server Actions are FORBIDDEN.

### Why BFF is Mandatory

| Risk (Without BFF) | Impact |
|--------------------|--------|
| **Security** | API keys, tokens exposed in browser |
| **CORS issues** | Cross-origin requests blocked or misconfigured |
| **Type safety** | No server-side validation before client receives data |
| **Error handling** | Inconsistent error formats across different backends |
| **Performance** | No server-side caching, aggregation, or optimization |

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  src/core/                                                   │
│  ├── domain/              # Business entities, interfaces   │
│  │   ├── entities/        # Domain models                   │
│  │   ├── repositories/    # Repository interfaces           │
│  │   └── services/        # Domain service interfaces       │
│  ├── application/         # Use cases, orchestration        │
│  │   └── use-cases/       # Application logic               │
│  └── infrastructure/      # External implementations        │
│      ├── http/            # HTTP clients, external APIs     │
│      ├── repositories/    # Repository implementations      │
│      └── app.ts           # Application bootstrap           │
└─────────────────────────────────────────────────────────────┘
```

### Dual-Mode Architecture

The BFF architecture supports two modes based on whether `@lerianstudio/sindarian-server` is available:

| Mode | When to Use | Characteristics |
|------|-------------|-----------------|
| **With sindarian-server** | Project has `@lerianstudio/sindarian-server` dependency | Use decorators (@Controller, @Get, @injectable, @inject, @Module) |
| **Without sindarian-server** | Standard Next.js project | Same architecture, manual DI container, no decorators |

**IMPORTANT:** Both modes follow IDENTICAL architecture. The only difference is decorator usage.

### Directory Structure

```
/src/core
  /domain
    /entities
      organization.ts           # Domain entity
    /repositories
      organization-repository.ts # Repository interface
  /application
    /use-cases
      /organization
        get-organizations.use-case.ts
        create-organization.use-case.ts
  /infrastructure
    /http
      /controllers
        organization.controller.ts
      /dto
        midaz-organization.dto.ts
        organization.dto.ts
      /mappers
        midaz-organization.mapper.ts
        organization.mapper.ts
      /services
        midaz-http.service.ts    # External API client
    /repositories
      organization.repository.ts # Implementation
    /modules
      organization.module.ts     # DI module (sindarian) or container setup
    app.ts                       # Bootstrap
```

### With sindarian-server (Decorators)

```typescript
// src/core/infrastructure/http/controllers/organization.controller.ts
import { Controller, Get, Post, Body, Query } from '@lerianstudio/sindarian-server';

@Controller('/organizations')
export class OrganizationController {
    constructor(
        @inject(GetOrganizationsUseCase) private getOrganizations: GetOrganizationsUseCase,
        @inject(CreateOrganizationUseCase) private createOrganization: CreateOrganizationUseCase,
    ) {}

    @Get('/')
    async list(@Query('limit') limit?: number) {
        return this.getOrganizations.execute({ limit: limit ?? 10 });
    }

    @Post('/')
    async create(@Body() body: CreateOrganizationDto) {
        return this.createOrganization.execute(body);
    }
}

// src/core/infrastructure/app.ts
import { ServerFactory } from '@lerianstudio/sindarian-server';
import { AppModule } from './modules/app.module';

export const app = await ServerFactory.create(AppModule);

// app/api/organizations/route.ts (Next.js API Route)
import { app } from '@/core/infrastructure/app';

export const GET = app.handler.bind(app);
export const POST = app.handler.bind(app);
```

### Without sindarian-server (Manual DI)

```typescript
// src/core/infrastructure/http/controllers/organization.controller.ts
export class OrganizationController {
    constructor(
        private getOrganizations: GetOrganizationsUseCase,
        private createOrganization: CreateOrganizationUseCase,
    ) {}

    async list(limit: number = 10) {
        return this.getOrganizations.execute({ limit });
    }

    async create(body: CreateOrganizationDto) {
        return this.createOrganization.execute(body);
    }
}

// src/core/infrastructure/container.ts
import { Container } from 'inversify';

const container = new Container();
container.bind(OrganizationRepository).to(OrganizationRepositoryImpl);
container.bind(GetOrganizationsUseCase).toSelf();
container.bind(CreateOrganizationUseCase).toSelf();
container.bind(OrganizationController).toSelf();

export { container };

// app/api/organizations/route.ts (Next.js API Route)
import { NextRequest, NextResponse } from 'next/server';
import { container } from '@/core/infrastructure/container';
import { OrganizationController } from '@/core/infrastructure/http/controllers/organization.controller';

export async function GET(request: NextRequest) {
    const controller = container.get(OrganizationController);
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') ?? '10');

    try {
        const result = await controller.list(limit);
        return NextResponse.json(result);
    } catch (error) {
        return handleError(error);
    }
}

export async function POST(request: NextRequest) {
    const controller = container.get(OrganizationController);
    const body = await request.json();

    try {
        const result = await controller.create(body);
        return NextResponse.json(result, { status: 201 });
    } catch (error) {
        return handleError(error);
    }
}
```

### Use Case Pattern

```typescript
// src/core/application/use-cases/organization/get-organizations.use-case.ts
import { injectable, inject } from 'inversify';

@injectable()
export class GetOrganizationsUseCase {
    constructor(
        @inject(OrganizationRepository) private repository: OrganizationRepository,
    ) {}

    async execute(params: { limit: number }): Promise<Organization[]> {
        return this.repository.findAll({ limit: params.limit });
    }
}
```

### Anti-Patterns (FORBIDDEN)

| Pattern | Status | Why |
|---------|--------|-----|
| Server Actions | **FORBIDDEN** | No centralized error handling, no middleware support |
| Direct API calls from client | **FORBIDDEN** | Security risk, no aggregation layer |
| Business logic in API routes | **FORBIDDEN** | Must be in use cases |
| Repository in controller | **FORBIDDEN** | Controller → Use Case → Repository |
| Skipping use case for "simple" operations | **FORBIDDEN** | Consistency over convenience |

---

