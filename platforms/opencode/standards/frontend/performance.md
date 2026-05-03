## Performance

### Code Splitting

```tsx
import { lazy, Suspense } from 'react';

// Lazy load heavy components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));

// Use Suspense
<Suspense fallback={<LoadingSpinner />}>
    <Dashboard />
</Suspense>
```

### Image Optimization

```tsx
import Image from 'next/image';

// Always use next/image
<Image
    src={user.avatar}
    alt={user.name}
    width={48}
    height={48}
    priority={isAboveFold}
/>
```

### Memoization

```tsx
// Memo expensive components
const ExpensiveList = memo(function ExpensiveList({ items }: Props) {
    return items.map(item => <ExpensiveItem key={item.id} {...item} />);
});

// useMemo for expensive calculations
const sortedItems = useMemo(
    () => items.sort((a, b) => b.score - a.score),
    [items]
);

// useCallback for stable references
const handleClick = useCallback((id: string) => {
    setSelectedId(id);
}, []);
```

---

