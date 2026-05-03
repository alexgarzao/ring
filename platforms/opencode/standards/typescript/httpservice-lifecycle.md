## HttpService Lifecycle

The HttpService pattern provides hooks for request/response processing when calling external APIs.

### Lifecycle Hooks

```typescript
// src/core/infrastructure/http/services/base-http.service.ts
export abstract class BaseHttpService {
    protected baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    // Hook 1: Create default headers and config
    protected createDefaults(): RequestInit {
        return {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        };
    }

    // Hook 2: Modify request before sending
    protected onBeforeFetch(url: string, init: RequestInit): RequestInit {
        // Add auth token, request ID, etc.
        return {
            ...init,
            headers: {
                ...init.headers,
                'X-Request-ID': crypto.randomUUID(),
            },
        };
    }

    // Hook 3: Process response after receiving
    protected async onAfterFetch<T>(response: Response): Promise<T> {
        if (!response.ok) {
            throw await this.handleError(response);
        }
        return response.json();
    }

    // Hook 4: Handle errors
    protected async catch(error: unknown): Promise<never> {
        if (error instanceof ApiException) {
            throw error;
        }
        throw new ApiException('External service error', 500, { cause: error });
    }

    // Main fetch method using hooks
    protected async fetch<T>(path: string, init: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const defaults = this.createDefaults();
        const merged = { ...defaults, ...init, headers: { ...defaults.headers, ...init.headers } };
        const finalInit = this.onBeforeFetch(url, merged);

        try {
            const response = await fetch(url, finalInit);
            return await this.onAfterFetch<T>(response);
        } catch (error) {
            return this.catch(error);
        }
    }
}
```

### Implementation Example

```typescript
// src/core/infrastructure/http/services/midaz-http.service.ts
import { injectable } from 'inversify';

@injectable()
export class Core oneHttpService extends BaseHttpService {
    constructor() {
        super(process.env.MIDAZ_API_URL!);
    }

    protected createDefaults(): RequestInit {
        return {
            ...super.createDefaults(),
            headers: {
                ...super.createDefaults().headers,
                'Authorization': `Bearer ${process.env.MIDAZ_API_TOKEN}`,
            },
        };
    }

    protected onBeforeFetch(url: string, init: RequestInit): RequestInit {
        const modified = super.onBeforeFetch(url, init);
        // Add Core one-specific headers
        return {
            ...modified,
            headers: {
                ...modified.headers,
                'X-Core one-Client': 'bff-service',
            },
        };
    }

    protected async onAfterFetch<T>(response: Response): Promise<T> {
        // Log response metrics
        console.log(`[Core one] ${response.status} - ${response.url}`);
        return super.onAfterFetch<T>(response);
    }

    protected async catch(error: unknown): Promise<never> {
        // Transform to Core one-specific exception
        if (error instanceof Response) {
            const body = await error.json().catch(() => ({}));
            throw new Core oneApiException(body.message ?? 'Core one API error', error.status, body);
        }
        return super.catch(error);
    }

    // Service-specific methods
    async getOrganizations(limit: number): Promise<Core oneOrganizationDto[]> {
        return this.fetch<Core oneOrganizationDto[]>(`/organizations?limit=${limit}`);
    }

    async createOrganization(data: CreateCore oneOrganizationDto): Promise<Core oneOrganizationDto> {
        return this.fetch<Core oneOrganizationDto>('/organizations', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
}
```

### Hook Execution Order

```
1. createDefaults()      → Base configuration
2. onBeforeFetch()       → Request modification (auth, headers)
3. fetch()               → Actual HTTP call
4. onAfterFetch()        → Response processing (success path)
   OR
4. catch()               → Error handling (failure path)
```

---

