## Component Patterns

### Compound Components

```tsx
// Flexible API for complex components
function Tabs({ children, defaultValue }: TabsProps) {
    const [value, setValue] = useState(defaultValue);
    return (
        <TabsContext.Provider value={{ value, setValue }}>
            <div className="tabs">{children}</div>
        </TabsContext.Provider>
    );
}

Tabs.List = function TabsList({ children }: { children: React.ReactNode }) {
    return <div className="tabs-list">{children}</div>;
};

Tabs.Trigger = function TabsTrigger({ value, children }: TabsTriggerProps) {
    const { value: selected, setValue } = useTabsContext();
    return (
        <button
            className={cn('tab', selected === value && 'active')}
            onClick={() => setValue(value)}
        >
            {children}
        </button>
    );
};

Tabs.Content = function TabsContent({ value, children }: TabsContentProps) {
    const { value: selected } = useTabsContext();
    if (value !== selected) return null;
    return <div className="tab-content">{children}</div>;
};

// Usage
<Tabs defaultValue="tab1">
    <Tabs.List>
        <Tabs.Trigger value="tab1">Tab 1</Tabs.Trigger>
        <Tabs.Trigger value="tab2">Tab 2</Tabs.Trigger>
    </Tabs.List>
    <Tabs.Content value="tab1">Content 1</Tabs.Content>
    <Tabs.Content value="tab2">Content 2</Tabs.Content>
</Tabs>
```

### Error Boundaries

```tsx
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback: ReactNode;
}

interface State {
    hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
    state: State = { hasError: false };

    static getDerivedStateFromError(): State {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return this.props.fallback;
        }
        return this.props.children;
    }
}

// Usage
<ErrorBoundary fallback={<ErrorMessage />}>
    <UserProfile userId={userId} />
</ErrorBoundary>
```

---

