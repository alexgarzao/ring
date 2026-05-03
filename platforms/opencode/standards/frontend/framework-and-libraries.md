## Framework

- React 18+
- Next.js (see version policy below)
- TypeScript strict mode (see `typescript.md`)

### Framework Version Policy

| Scenario | Rule |
|----------|------|
| **New project** | Use **latest stable version** (verify at nextjs.org before starting) |
| **Existing codebase** | **Maintain project's current version** (read package.json) |

**Before starting any project:**
1. For NEW projects: Check https://nextjs.org for latest stable version
2. For EXISTING projects: Read `package.json` to determine current version
3. NEVER hardcode a specific version in implementation - use project's version

---

## Libraries & Tools

### Core

| Library | Use Case |
|---------|----------|
| React 18+ | UI framework |
| Next.js (latest stable) | Full-stack framework (see version policy above) |
| TypeScript 5+ | Type safety |

### State Management

| Library | Use Case |
|---------|----------|
| TanStack Query | Server state (API data) |
| Zustand | Client state (UI state) |
| Context API | Simple shared state |
| Redux Toolkit | Complex global state |

### Forms

| Library | Use Case |
|---------|----------|
| React Hook Form | Form state management |
| Zod | Schema validation |
| @hookform/resolvers | RHF + Zod integration |

### UI Components

| Library | Use Case |
|---------|----------|
| Radix UI | Headless primitives |
| shadcn/ui | Pre-styled Radix components |
| Chakra UI | Full component library |
| Headless UI | Tailwind-native primitives |

### Styling

| Library | Use Case |
|---------|----------|
| TailwindCSS | Utility-first CSS |
| CSS Modules | Scoped CSS |
| Styled Components | CSS-in-JS |
| CSS Variables | Theming |

### Testing

| Library | Use Case |
|---------|----------|
| Vitest | Unit tests |
| Testing Library | Component tests |
| Playwright | E2E tests |
| MSW | API mocking |

---

