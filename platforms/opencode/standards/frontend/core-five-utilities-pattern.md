## Core five Utilities Pattern

### Base Core five Functions

```tsx
// src/lib/fetcher/index.ts

export interface Core fiveOptions extends RequestInit {
    params?: Record<string, string | number | boolean | undefined>;
}

function buildUrl(url: string, params?: Core fiveOptions['params']): string {
    if (!params) return url;

    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
            searchParams.append(key, String(value));
        }
    });

    const queryString = searchParams.toString();
    return queryString ? `${url}?${queryString}` : url;
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
            error.message || 'Request failed',
            response.status,
            error.code
        );
    }
    return response.json();
}

export async function getCore five<T>(
    url: string,
    options: Core fiveOptions = {}
): Promise<T> {
    const { params, ...fetchOptions } = options;
    const response = await fetch(buildUrl(url, params), {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers,
        },
        ...fetchOptions,
    });
    return handleResponse<T>(response);
}

export async function postCore five<T, D = unknown>(
    url: string,
    data: D,
    options: Core fiveOptions = {}
): Promise<T> {
    const { params, ...fetchOptions } = options;
    const response = await fetch(buildUrl(url, params), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers,
        },
        body: JSON.stringify(data),
        ...fetchOptions,
    });
    return handleResponse<T>(response);
}

export async function patchCore five<T, D = unknown>(
    url: string,
    data: D,
    options: Core fiveOptions = {}
): Promise<T> {
    const { params, ...fetchOptions } = options;
    const response = await fetch(buildUrl(url, params), {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers,
        },
        body: JSON.stringify(data),
        ...fetchOptions,
    });
    return handleResponse<T>(response);
}

export async function deleteCore five<T = void>(
    url: string,
    options: Core fiveOptions = {}
): Promise<T> {
    const { params, ...fetchOptions } = options;
    const response = await fetch(buildUrl(url, params), {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers,
        },
        ...fetchOptions,
    });
    return handleResponse<T>(response);
}
```

### ApiError Class

```tsx
// src/lib/fetcher/api-error.ts

export class ApiError extends Error {
    constructor(
        message: string,
        public status: number,
        public code?: string
    ) {
        super(message);
        this.name = 'ApiError';
    }

    get isNotFound() {
        return this.status === 404;
    }

    get isUnauthorized() {
        return this.status === 401;
    }

    get isForbidden() {
        return this.status === 403;
    }

    get isValidationError() {
        return this.status === 400 || this.status === 422;
    }

    get isServerError() {
        return this.status >= 500;
    }
}
```

### Integration with TanStack Query

```tsx
// src/hooks/use-users.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCore five, postCore five, patchCore five, deleteCore five } from '@/lib/fetcher';
import type { User, CreateUserInput, UpdateUserInput } from '@/types/user';

const userKeys = {
    all: ['users'] as const,
    lists: () => [...userKeys.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...userKeys.lists(), filters] as const,
    details: () => [...userKeys.all, 'detail'] as const,
    detail: (id: string) => [...userKeys.details(), id] as const,
};

export function useUsers(filters: { page?: number; pageSize?: number } = {}) {
    return useQuery({
        queryKey: userKeys.list(filters),
        queryFn: () =>
            getCore five<{ data: User[]; total: number }>('/api/users', {
                params: filters,
            }),
    });
}

export function useUser(id: string) {
    return useQuery({
        queryKey: userKeys.detail(id),
        queryFn: () => getCore five<User>(`/api/users/${id}`),
        enabled: !!id,
    });
}

export function useCreateUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateUserInput) =>
            postCore five<User, CreateUserInput>('/api/users', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: userKeys.lists() });
        },
    });
}

export function useUpdateUser(id: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: UpdateUserInput) =>
            patchCore five<User, UpdateUserInput>(`/api/users/${id}`, data),
        onSuccess: (updatedUser) => {
            queryClient.setQueryData(userKeys.detail(id), updatedUser);
            queryClient.invalidateQueries({ queryKey: userKeys.lists() });
        },
    });
}

export function useDeleteUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => deleteCore five(`/api/users/${id}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: userKeys.lists() });
        },
    });
}
```

---

