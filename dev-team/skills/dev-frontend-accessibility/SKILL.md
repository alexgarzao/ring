---
name: ring:dev-frontend-accessibility
description: |
  Gate 2 of frontend development cycle — ensures all components pass axe-core
  automated accessibility scans with zero WCAG 2.1 AA violations.

trigger: |
  - Gate 2 (after DevOps setup)
  - Frontend tasks with UI components

skip_when: |
  - Not inside a frontend development cycle (ring:dev-cycle-frontend)
  - Backend-only project with no UI components
  - Task is documentation-only, configuration-only, or non-code
  - Changes limited to build tooling, CI/CD, or infrastructure

sequence:
  after: [ring:dev-devops]
  before: [ring:dev-unit-testing]

related:
  complementary: [ring:dev-cycle-frontend, ring:qa-analyst-frontend]
---

# Frontend Accessibility Testing (Gate 2)

WCAG 2.1 AA compliance is mandatory for all applications. No exceptions.

**Block conditions:**
- Any axe-core CRITICAL violation = FAIL
- Any axe-core SERIOUS violation = FAIL
- Missing keyboard navigation = FAIL
- Missing focus management = FAIL

## WCAG 2.1 AA Core Requirements

| Criterion | Requirement |
|-----------|-------------|
| Color contrast | Text ≥ 4.5:1, large text ≥ 3:1 |
| Keyboard navigation | All interactive elements reachable by Tab |
| Focus visibility | Focus indicator visible on all elements |
| Semantic HTML | Proper heading hierarchy, landmark regions |
| Form labels | All inputs have associated labels |
| Images | All `<img>` have meaningful `alt` attributes |
| Error messages | Errors announced to screen readers |
| Link purpose | Links describe destination (not "click here") |

## Step 1: Validate Input

Required: `unit_id` (TASK id), `implementation_files`, `gate0_handoffs`.
Optional: `components_list`, `gate1_handoff`.

## Step 2: Dispatch Frontend QA Analyst

```yaml
Task:
  subagent_type: "ring:qa-analyst-frontend"
  description: "Accessibility testing for {unit_id}"
  prompt: |
    ## Accessibility Testing — Gate 2

    unit_id: {unit_id}
    components changed: {implementation_files filtered to .tsx}

    Standards: Load via cached_standards or WebFetch:
    https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/frontend/testing-accessibility.md

    ## Required Checks

    ### 1. axe-core Automated Scan (per component)
    ```typescript
    import { render } from '@testing-library/react';
    import { axe, toHaveNoViolations } from 'jest-axe';
    expect.extend(toHaveNoViolations);

    it('has no accessibility violations', async () => {
      const { container } = render(<ComponentName />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
    ```
    Run on ALL states: default, loading, error, empty, interactive.

    ### 2. Keyboard Navigation
    - Tab order follows visual order
    - All interactive elements reachable (buttons, links, inputs, selects)
    - No keyboard traps
    - Escape key closes modals/dropdowns

    ### 3. Focus Management
    - Focus visible on all interactive elements
    - Focus moves to new content after navigation
    - Modal: focus trapped inside when open, restored when closed

    ### 4. Semantic HTML Verification
    ```bash
    # Check heading hierarchy
    grep -rn "<h[1-6]" --include='*.tsx' src/
    # Check landmark regions
    grep -rn "role=\"main\"\|<main\|<nav\|<header\|<footer\|<aside" --include='*.tsx' src/
    ```

    ### 5. Color Contrast (spot check)
    Use browser DevTools accessibility panel or contrast checking tool.
    Flag any computed contrast below 4.5:1 for normal text, 3:1 for large.

    ## Violations Report Template
    | Component | Violation | Severity | WCAG Criterion | Fix Required |

    ## Required Output
    - axe-core test files
    - Violations table (zero critical/serious required)
    - Keyboard navigation checklist
    - All tests pass
```

## Step 3: Validate Results

```
if zero critical/serious violations AND keyboard nav passes:
  → PASS → proceed to Gate 3

if any critical/serious violation:
  → Dispatch ring:frontend-engineer to fix
  → Re-run accessibility tests
  → iterations++
```

## Output Format

```markdown
## Accessibility Testing Result
unit_id | result: PASS/FAIL | iterations | violations: N

## Violations Found
| Component | Type | Severity | WCAG | Fixed |

## Keyboard Navigation
| Component | Keyboard Reachable | Focus Visible | Status |

## Handoff
gate2_result: PASS | ESCALATED
violations_critical: 0
violations_serious: 0
```
