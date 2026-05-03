## Forbidden Patterns

**The following patterns are never allowed. Agents MUST refuse to implement these:**

### TypeScript Anti-Patterns

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `any` type | Defeats TypeScript purpose | Use proper types, `unknown`, or generics |
| Type assertions without validation | Runtime errors | Use type guards or Zod parsing |
| `// @ts-ignore` or `// @ts-expect-error` | Hides real errors | Fix the type issue properly |
| Non-strict mode | Allows unsafe code | Enable `"strict": true` in tsconfig |

### Accessibility Anti-Patterns

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `<div onClick={}>` for buttons | Not keyboard accessible | Use `<button>` element |
| `<span onClick={}>` for links | Not keyboard accessible | Use `<a href="">` element |
| Missing `alt` on images | Screen readers can't describe | Always provide descriptive alt text |
| Missing form labels | Inputs not associated | Use `<label htmlFor="">` |
| `tabIndex > 0` | Breaks natural tab order | Use `tabIndex={0}` or semantic HTML |
| `outline: none` without alternative | Removes focus visibility | Provide custom focus styles |

### State Management Anti-Patterns

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `useEffect` for data fetching | Race conditions, no caching | Use TanStack Query |
| Props drilling > 3 levels | Unmaintainable | Use Context or Zustand |
| Storing server state in Redux/Zustand | Stale data, duplicate cache | Use TanStack Query for server state |
| `useState` for form state | No validation, verbose | Use React Hook Form |

### Security Anti-Patterns

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `dangerouslySetInnerHTML` without sanitization | XSS vulnerability | Use DOMPurify or avoid entirely |
| Storing tokens in localStorage | XSS can steal tokens | Use httpOnly cookies |
| Hardcoded API keys in frontend | Exposed in bundle | Use environment variables, BFF |
| Unvalidated URL redirects | Open redirect vulnerability | Whitelist allowed domains |

### Font Anti-Patterns

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `font-family: 'Inter'` | Generic AI aesthetic | Use Geist, Satoshi, Cabinet Grotesk |
| `font-family: 'Roboto'` | Generic, overused | Use General Sans, Clash Display |
| `font-family: 'Arial'` | System font, no character | Use distinctive web fonts |
| `font-family: system-ui` | No brand identity | Define specific font stack |

### Performance Anti-Patterns

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `<img>` without next/image | No optimization | Use `next/image` component |
| Inline styles in loops | Creates new objects each render | Use className or CSS Modules |
| Missing `key` prop in lists | React can't optimize | Always provide stable keys |
| `useMemo`/`useCallback` everywhere | Premature optimization | Only when actually needed |

**If existing code uses FORBIDDEN patterns → Report as blocker, DO NOT extend.**

---

