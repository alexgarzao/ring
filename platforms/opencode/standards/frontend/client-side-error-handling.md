## Client-Side Error Handling

### ErrorBoundary Component

```tsx
// src/components/error-boundary.tsx
'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryProps {
    children: ReactNode;
    fallback?: ReactNode;
    onReset?: () => void;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        // Report to error tracking service (e.g., Sentry)
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
        this.props.onReset?.();
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="flex flex-col items-center justify-center p-8 text-center">
                    <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
                    <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
                    <p className="text-muted-foreground mb-4">
                        {this.state.error?.message || 'An unexpected error occurred'}
                    </p>
                    <Button onClick={this.handleReset} variant="outline">
                        Try again
                    </Button>
                </div>
            );
        }

        return this.props.children;
    }
}
```

### API Error Helpers

```tsx
// src/lib/error-helpers.ts
import { toast } from '@/components/ui/use-toast';
import { ApiError } from '@/lib/fetcher/api-error';

export function handleApiError(error: unknown): void {
    if (error instanceof ApiError) {
        if (error.isUnauthorized) {
            toast({
                variant: 'destructive',
                title: 'Session Expired',
                description: 'Please log in again.',
            });
            // Redirect to login
            window.location.href = '/login';
            return;
        }

        if (error.isForbidden) {
            toast({
                variant: 'destructive',
                title: 'Access Denied',
                description: 'You do not have permission to perform this action.',
            });
            return;
        }

        if (error.isValidationError) {
            toast({
                variant: 'destructive',
                title: 'Validation Error',
                description: error.message,
            });
            return;
        }

        if (error.isServerError) {
            toast({
                variant: 'destructive',
                title: 'Server Error',
                description: 'Something went wrong. Please try again later.',
            });
            return;
        }

        toast({
            variant: 'destructive',
            title: 'Error',
            description: error.message,
        });
        return;
    }

    // Unknown error
    toast({
        variant: 'destructive',
        title: 'Error',
        description: 'An unexpected error occurred.',
    });
}
```

### Error Recovery Patterns

```tsx
// Using with TanStack Query mutations
import { useToast } from '@/components/ui/use-toast';
import { handleApiError } from '@/lib/error-helpers';

function CreateUserForm() {
    const { toast } = useToast();
    const createUser = useCreateUser();

    const onSubmit = async (data: CreateUserInput) => {
        try {
            await createUser.mutateAsync(data);
            toast({
                title: 'Success',
                description: 'User created successfully.',
            });
        } catch (error) {
            handleApiError(error);
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            {/* form fields */}
            {createUser.isError && (
                <Alert variant="destructive">
                    <AlertDescription>
                        Failed to create user. Please try again.
                    </AlertDescription>
                </Alert>
            )}
        </form>
    );
}
```

### Query Error Handling

```tsx
// Global error handler for React Query
import { QueryClient } from '@tanstack/react-query';
import { handleApiError } from '@/lib/error-helpers';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: (failureCount, error) => {
                // Don't retry on 4xx errors
                if (error instanceof ApiError && error.status < 500) {
                    return false;
                }
                return failureCount < 3;
            },
        },
        mutations: {
            onError: (error) => {
                handleApiError(error);
            },
        },
    },
});
```

---

