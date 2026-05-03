## API Routes Pattern (MANDATORY)

**⛔ HARD GATE: Server Actions are FORBIDDEN. All dynamic data MUST flow through API Routes.**

### Why Server Actions Are Forbidden

| Server Actions Problem | Impact |
|-----------------------|--------|
| No centralized error handling | Each action handles errors differently |
| No middleware support | Cannot add auth, logging, rate limiting |
| No API versioning | Breaking changes affect all clients |
| No OpenAPI/Swagger | Cannot generate API documentation |
| Tight coupling | Client directly calls server functions |
| No caching layer | Every call hits the server |

### Required Pattern: API Routes

```typescript
// ✅ CORRECT: API Route with controller resolution
// app/api/organizations/route.ts

// With sindarian-server
import { app } from '@/core/infrastructure/app';

export const GET = app.handler.bind(app);
export const POST = app.handler.bind(app);

// Without sindarian-server
import { NextRequest, NextResponse } from 'next/server';
import { container } from '@/core/infrastructure/container';
import { OrganizationController } from '@/core/infrastructure/http/controllers/organization.controller';
import { GlobalExceptionFilter } from '@/core/infrastructure/filters/global-exception.filter';

const exceptionFilter = new GlobalExceptionFilter();

export async function GET(request: NextRequest) {
    try {
        const controller = container.get(OrganizationController);
        const { searchParams } = new URL(request.url);
        const limit = parseInt(searchParams.get('limit') ?? '10');

        const result = await controller.list(limit);
        return NextResponse.json(result);
    } catch (error) {
        return exceptionFilter.catch(error);
    }
}

export async function POST(request: NextRequest) {
    try {
        const controller = container.get(OrganizationController);
        const body = await request.json();

        const result = await controller.create(body);
        return NextResponse.json(result, { status: 201 });
    } catch (error) {
        return exceptionFilter.catch(error);
    }
}
```

```typescript
// ❌ FORBIDDEN: Server Action
// app/actions/organizations.ts
'use server';

export async function getOrganizations() {
    // FORBIDDEN - This is a Server Action
    const orgs = await db.organizations.findMany();
    return orgs;
}
```

### Dynamic Route Pattern

```typescript
// app/api/organizations/[id]/route.ts

// With sindarian-server
import { app } from '@/core/infrastructure/app';

export const GET = app.handler.bind(app);
export const PUT = app.handler.bind(app);
export const DELETE = app.handler.bind(app);

// Without sindarian-server
export async function GET(
    request: NextRequest,
    { params }: { params: { id: string } }
) {
    try {
        const controller = container.get(OrganizationController);
        const result = await controller.getById(params.id);

        if (!result) {
            return NextResponse.json({ error: 'Not found' }, { status: 404 });
        }

        return NextResponse.json(result);
    } catch (error) {
        return exceptionFilter.catch(error);
    }
}
```

### Client-Side Consumption

```typescript
// hooks/use-organizations.ts
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(res => res.json());

export function useOrganizations(limit: number = 10) {
    const { data, error, isLoading, mutate } = useSWR(
        `/api/organizations?limit=${limit}`,
        fetcher
    );

    return {
        organizations: data,
        isLoading,
        isError: !!error,
        refresh: mutate,
    };
}

// Usage in component
function OrganizationList() {
    const { organizations, isLoading, isError } = useOrganizations();

    if (isLoading) return <Spinner />;
    if (isError) return <ErrorMessage />;

    return (
        <ul>
            {organizations.map(org => (
                <li key={org.id}>{org.name}</li>
            ))}
        </ul>
    );
}
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Server Actions are simpler" | Simplicity ≠ correctness. API Routes provide necessary middleware. | **Use API Routes. Add proper middleware.** |
| "Just a small feature" | Small features grow. Start with correct architecture. | **API Route from day one.** |
| "No external consumers" | Today internal, tomorrow external. API Routes are future-proof. | **API Routes enable evolution.** |
| "Next.js recommends Server Actions" | For forms. Not for data fetching with complex requirements. | **Different tools for different jobs.** |

---

