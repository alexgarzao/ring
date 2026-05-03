## State Management Patterns

### Server State with TanStack Query

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Query key factory
const userKeys = {
    all: ['users'] as const,
    lists: () => [...userKeys.all, 'list'] as const,
    list: (filters: UserFilters) => [...userKeys.lists(), filters] as const,
    details: () => [...userKeys.all, 'detail'] as const,
    detail: (id: string) => [...userKeys.details(), id] as const,
};

// Typed query hook
function useUser(userId: string) {
    return useQuery({
        queryKey: userKeys.detail(userId),
        queryFn: () => fetchUser(userId),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

// Mutation with cache update
function useCreateUser() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createUser,
        onSuccess: (newUser) => {
            // Update cache
            queryClient.setQueryData(
                userKeys.detail(newUser.id),
                newUser
            );
            // Invalidate list
            queryClient.invalidateQueries({
                queryKey: userKeys.lists(),
            });
        },
    });
}
```

### Client State with Zustand

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
    theme: 'light' | 'dark';
    sidebarOpen: boolean;
    setTheme: (theme: 'light' | 'dark') => void;
    toggleSidebar: () => void;
}

const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            theme: 'light',
            sidebarOpen: true,
            setTheme: (theme) => set({ theme }),
            toggleSidebar: () => set((state) => ({
                sidebarOpen: !state.sidebarOpen
            })),
        }),
        { name: 'ui-storage' }
    )
);

// Usage in component
function Header() {
    const { theme, setTheme } = useUIStore();
    return <ThemeToggle theme={theme} onChange={setTheme} />;
}
```

---

