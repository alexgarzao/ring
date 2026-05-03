## Styling Standards

### TailwindCSS Best Practices

```tsx
// Use semantic class groupings
<div className="
    flex items-center justify-between
    p-4 gap-4
    bg-white dark:bg-gray-900
    border border-gray-200 rounded-lg
    hover:shadow-md transition-shadow
">

// Extract repeated patterns to components
function Card({ children, className }: CardProps) {
    return (
        <div className={cn(
            'bg-white dark:bg-gray-900',
            'border border-gray-200 rounded-lg',
            'p-4 shadow-sm',
            className
        )}>
            {children}
        </div>
    );
}
```

### CSS Variables for Theming

```css
:root {
    --color-primary: 220 90% 56%;
    --color-secondary: 262 83% 58%;
    --color-background: 0 0% 100%;
    --color-foreground: 222 47% 11%;
    --color-muted: 210 40% 96%;
    --color-border: 214 32% 91%;
    --radius: 0.5rem;
}

.dark {
    --color-background: 222 47% 11%;
    --color-foreground: 210 40% 98%;
    --color-muted: 217 33% 17%;
    --color-border: 217 33% 17%;
}
```

### Mobile-First Responsive Design

```tsx
// Always start mobile, scale up
<div className="
    grid grid-cols-1
    sm:grid-cols-2
    lg:grid-cols-3
    xl:grid-cols-4
    gap-4
">

// Responsive text
<h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold">

// Hide/show based on breakpoint
<div className="hidden md:block">Desktop only</div>
<div className="md:hidden">Mobile only</div>
```

---

