# Frontend Standards — Module Index

Load ONLY the modules relevant to your current task. Do NOT load all modules.
Read the "Load When" column to decide which modules your task needs.

## Always Load

| Module | Load When |
|--------|-----------|
| framework-and-libraries.md | Every frontend task — Next.js version, required libraries, package versions, dependency decisions |

## Load by Task Context

| Module | Load When |
|--------|-----------|
| state-management-patterns.md | Managing client or server state, using Zustand or React Query, global state patterns, cache invalidation, optimistic updates |
| form-patterns.md | Building or modifying forms, using React Hook Form, form validation, controlled vs uncontrolled inputs, form submission handling |
| styling-standards.md | Applying styles, using Tailwind CSS classes, theming, dark mode, CSS-in-JS decisions, design token usage |
| typography-standards.md | Setting font sizes, weights, line heights, text hierarchy, heading styles, body text, responsive typography |
| animation-standards.md | Adding animations or transitions, using Framer Motion, micro-interactions, performance-aware motion, reduced-motion support |
| component-patterns.md | Creating or refactoring React components, composition patterns, props design, compound components, render props |
| file-organization.md | Structuring feature folders, organizing components, co-location rules, barrel exports, deciding module boundaries |
| accessibility.md | Implementing ARIA attributes, keyboard navigation, focus management, screen reader support, WCAG compliance |
| performance.md | Optimizing bundle size, lazy loading, code splitting, image optimization, Core Web Vitals, memoization patterns |
| directory-structure.md | Setting up project directories, placing new files, monorepo organization, feature vs shared folders |
| forbidden-patterns.md | Reviewing code for anti-patterns, avoiding common mistakes, enforcing prohibited approaches in the codebase |
| standards-compliance-categories.md | Understanding compliance levels, categorizing code quality issues, audit criteria |
| form-field-abstraction-layer.md | Building reusable form field components, abstracting React Hook Form integration, field-level validation, form field composition |
| provider-composition-pattern.md | Setting up React context providers, composing multiple providers, avoiding prop drilling, provider ordering |
| custom-hooks-patterns.md | Writing custom React hooks, extracting reusable stateful logic, hook composition, lifecycle patterns |
| core-five-utilities-pattern.md | Using the five core utility patterns, shared utility hooks and functions, cross-cutting frontend concerns |
| client-side-error-handling.md | Handling API errors on the client, error boundaries, toast notifications, retry logic, graceful degradation |
| data-table-pattern.md | Implementing data tables, sorting, filtering, pagination on the frontend, server-side vs client-side table patterns |
| checklist.md | Final pre-PR review, self-verification before submitting frontend code for review |
