## Provider Composition Pattern

### Provider Order (MANDATORY)

Providers MUST be composed in a specific order to ensure proper context availability.

```tsx
// src/app/providers.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from 'next-auth/react';
import { ThemeProvider } from 'next-themes';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useState } from 'react';

interface ProvidersProps {
    children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 60 * 1000, // 1 minute
                        refetchOnWindowFocus: false,
                    },
                },
            })
    );

    return (
        <SessionProvider>
            <QueryClientProvider client={queryClient}>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                    disableTransitionOnChange
                >
                    <TooltipProvider>
                        {children}
                        <Toaster />
                    </TooltipProvider>
                </ThemeProvider>
            </QueryClientProvider>
        </SessionProvider>
    );
}
```

### Provider Order Rules

| Order | Provider | Reason |
|-------|----------|--------|
| 1 | SessionProvider | Auth must be outermost for all components to access session |
| 2 | QueryClientProvider | Data fetching needs session for authenticated requests |
| 3 | ThemeProvider | Theme should wrap UI components |
| 4 | TooltipProvider | Radix tooltips need provider context |
| 5 | App-specific providers | Feature-specific contexts |

### Layout Integration

```tsx
// src/app/layout.tsx
import { Providers } from './providers';

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
```

### Feature-Specific Providers

For feature-specific state, create scoped providers:

```tsx
// src/features/organization/providers/OrganizationProvider.tsx
'use client';

import { createContext, useContext, useState } from 'react';

interface OrganizationContextValue {
    organizationId: string | null;
    setOrganizationId: (id: string | null) => void;
}

const OrganizationContext = createContext<OrganizationContextValue | null>(null);

export function OrganizationProvider({ children }: { children: React.ReactNode }) {
    const [organizationId, setOrganizationId] = useState<string | null>(null);

    return (
        <OrganizationContext.Provider value={{ organizationId, setOrganizationId }}>
            {children}
        </OrganizationContext.Provider>
    );
}

export function useOrganization() {
    const context = useContext(OrganizationContext);
    if (!context) {
        throw new Error('useOrganization must be used within OrganizationProvider');
    }
    return context;
}
```

---

