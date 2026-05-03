## Standards Compliance Categories

**When invoked from ring:dev-refactor, check all categories:**

| Category | Ring Standard | What to Verify |
|----------|--------------|----------------|
| **TypeScript** | Strict mode, no `any` | tsconfig.json, *.tsx files |
| **Accessibility** | WCAG 2.1 AA | Semantic HTML, ARIA, keyboard nav |
| **State Management** | TanStack Query + Zustand | No useEffect for fetching |
| **Forms** | React Hook Form + Zod | Validation schemas present |
| **Styling** | Tailwind, CSS variables | No inline styles in logic |
| **Fonts** | Distinctive fonts | No Inter, Roboto, Arial |
| **Performance** | next/image, code splitting | Lazy loading, memoization |
| **Security** | No XSS vectors | dangerouslySetInnerHTML usage |

---

