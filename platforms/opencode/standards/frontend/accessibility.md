## Accessibility

### Required Practices

```tsx
// Always use semantic HTML
<button>Click me</button>  // not <div onClick={}>

// Images need alt text
<img src={user.avatar} alt={`${user.name}'s avatar`} />

// Form inputs need labels
<label htmlFor="email">Email</label>
<input id="email" type="email" />

// Use ARIA when needed
<button aria-label="Close dialog" aria-expanded={isOpen}>
    <XIcon />
</button>

// Keyboard navigation
<div
    role="button"
    tabIndex={0}
    onKeyDown={(e) => e.key === 'Enter' && onClick()}
    onClick={onClick}
>
```

### Focus Management

```tsx
// Focus trap for modals
import { FocusTrap } from '@radix-ui/react-focus-scope';

<FocusTrap>
    <Dialog>...</Dialog>
</FocusTrap>

// Auto-focus on mount
const inputRef = useRef<HTMLInputElement>(null);
useEffect(() => {
    inputRef.current?.focus();
}, []);
```

---

