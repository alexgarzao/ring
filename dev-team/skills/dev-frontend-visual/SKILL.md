---
name: ring:dev-frontend-visual
description: |
  Gate 4 of frontend development cycle — ensures all components have snapshot tests
  covering all states, viewports, and edge cases.

trigger: |
  - Gate 4 (after unit testing complete)
  - Frontend tasks with new or changed UI components

skip_when: |
  - Not inside a frontend development cycle (ring:dev-cycle-frontend)
  - Backend-only project with no UI components
  - Task is documentation-only, configuration-only, or non-code
  - No new UI components added or visual changes made

sequence:
  after: [ring:dev-unit-testing]
  before: [ring:dev-frontend-e2e]

related:
  complementary: [ring:dev-cycle-frontend, ring:qa-analyst-frontend]
---

# Frontend Visual Testing (Gate 4)

Snapshot tests catch visual regressions. Every component state must be captured.

**Block conditions:**
- Missing snapshot for any component state = FAIL
- Snapshot not updated after intentional change = FAIL
- Zero viewport coverage = FAIL

## States to Cover per Component

- Default / Normal
- Loading / Skeleton
- Error state
- Empty state
- Edge cases (long text, max values, RTL)
- Responsive viewports: mobile (375px), tablet (768px), desktop (1280px)

## Step 1: Validate Input

Required: `unit_id` (TASK id), `implementation_files`, `gate0_handoffs`.
Optional: `components_list`, `gate3_handoff`.

## Step 2: Dispatch Frontend QA Analyst

```yaml
Task:
  subagent_type: "ring:qa-analyst-frontend"
  description: "Write visual snapshot tests for {unit_id}"
  prompt: |
    ## Visual Testing — Gate 4

    unit_id: {unit_id}
    components changed: {implementation_files filtered to .tsx}

    Standards: Load via cached_standards or WebFetch:
    https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/frontend/testing-visual.md

    ## Requirements
    - Framework: Vitest + @testing-library/react + jest-snapshot or Storybook
    - For each changed component, create snapshot for ALL states
    - Viewports: 375px (mobile), 768px (tablet), 1280px (desktop)
    - Use jest-image-snapshot or Playwright screenshots for pixel-level regression

    ## Component States Matrix (MANDATORY per component)
    | Component | State | Viewport | Snapshot File | Status |
    |-----------|-------|---------|---------------|--------|

    ## Test Structure (Vitest/React)
    ```typescript
    import { render } from '@testing-library/react';
    import { expect, it, describe } from 'vitest';

    describe('{ComponentName} Snapshots', () => {
      it('renders default state', () => {
        const { container } = render(<ComponentName />);
        expect(container).toMatchSnapshot();
      });

      it('renders loading state', () => {
        const { container } = render(<ComponentName isLoading />);
        expect(container).toMatchSnapshot();
      });

      it('renders error state', () => {
        const { container } = render(<ComponentName error="Something went wrong" />);
        expect(container).toMatchSnapshot();
      });

      it('renders empty state', () => {
        const { container } = render(<ComponentName items={[]} />);
        expect(container).toMatchSnapshot();
      });
    });
    ```

    ## Run command
    npx vitest --reporter=verbose

    ## Required Output
    - Snapshot files created
    - States coverage table
    - All tests PASS
```

## Step 3: Validate Results

```
if all component states covered AND all tests pass:
  → PASS → proceed to Gate 5

if any state missing OR test fails:
  → Re-dispatch with gaps
  → iterations++
```

## Output Format

```markdown
## Visual Testing Result
unit_id | result: PASS/FAIL | iterations

## Components Coverage
| Component | States | Viewports | Snapshots | Status |

## Handoff
gate4_result: PASS | ESCALATED
snapshot_files: [list]
```
