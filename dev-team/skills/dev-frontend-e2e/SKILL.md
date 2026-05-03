---
name: ring:dev-frontend-e2e
description: |
  Gate 5 of frontend development cycle — ensures all user flows from product-designer
  have passing Playwright E2E tests across Chromium, Firefox, and WebKit.

trigger: |
  - Gate 5 (after visual testing complete)
  - Frontend development tasks with user-facing flows

skip_when: |
  - Not inside a frontend development cycle (ring:dev-cycle-frontend)
  - Backend-only project with no UI components
  - Task is documentation-only, configuration-only, or non-code
  - No user-facing flows were added or changed

sequence:
  after: [ring:dev-frontend-visual]
  before: [ring:dev-frontend-performance]

related:
  complementary: [ring:dev-cycle-frontend, ring:qa-analyst-frontend]
---

# Frontend E2E Testing (Gate 5)

Every user flow from product-designer must have a passing Playwright test.
Every error state users can encounter must be tested.

**Block conditions:**
- Untested user flow = FAIL
- No error path tests = FAIL
- Fails on any browser (Chromium/Firefox/WebKit) = FAIL
- Flaky tests (fail on consecutive runs) = FAIL

## Step 1: Validate Input

Required: `unit_id` (TASK id), `implementation_files`, `gate0_handoffs`.
Optional: `user_flows_path`, `backend_handoff` (endpoints, contracts).

## Step 2: Discover User Flows

Load user flows from product-designer artifacts:
- `docs/ux/user-flows.md` — primary source
- `docs/ux/ux-criteria.md` — acceptance criteria per flow
- `design/wireframes/` — visual reference

If not found → dispatch `ring:codebase-explorer` to identify flows from implemented components.

## Step 3: Dispatch Frontend QA Analyst

```yaml
Task:
  subagent_type: "ring:qa-analyst-frontend"
  description: "Write Playwright E2E tests for {unit_id}"
  prompt: |
    ## E2E Testing — Gate 5

    unit_id: {unit_id}
    implementation_files: {implementation_files}
    user_flows: {user_flows}

    Standards: Load via cached_standards or WebFetch:
    https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/frontend/testing-e2e.md

    ## Requirements
    - Framework: Playwright
    - Browsers: Chromium + Firefox + WebKit (ALL three required)
    - Viewports: desktop (1280x720) + mobile (375x812) for each flow
    - Selectors: semantic ONLY — getByRole, getByLabel, getByTestId
      NO: page.locator('.btn'), page.locator('#id')

    ## Flows to Cover
    For each user flow:
    1. Happy path — complete flow succeeds
    2. Error paths — API 500, timeout, validation errors, empty states
    3. Edge cases from ux-criteria.md

    ## Test Structure
    ```typescript
    import { test, expect } from '@playwright/test';

    test.describe('{Flow Name}', () => {
      test.beforeEach(async ({ page }) => {
        // Setup
      });

      test('should {happy path description}', async ({ page }) => {
        // arrange
        await page.goto('/path');
        // act
        await page.getByRole('button', { name: 'Submit' }).click();
        // assert
        await expect(page.getByRole('heading', { name: 'Success' })).toBeVisible();
      });

      test('should handle API error gracefully', async ({ page }) => {
        // mock API error
        await page.route('/api/endpoint', route => route.fulfill({ status: 500 }));
        // verify error state
        await expect(page.getByRole('alert')).toContainText('Something went wrong');
      });
    });
    ```

    ## playwright.config.ts
    ```typescript
    projects: [
      { name: 'chromium', use: devices['Desktop Chrome'] },
      { name: 'firefox', use: devices['Desktop Firefox'] },
      { name: 'webkit', use: devices['Desktop Safari'] },
      { name: 'mobile-chrome', use: devices['Pixel 5'] },
    ]
    ```

    ## Required Output
    - Test files created
    - Flows coverage table
    - Run command: npx playwright test
    - Results: 3 consecutive runs, all PASS, all browsers
```

## Step 4: Validate Results

```
if all flows covered AND all browsers pass (3 consecutive runs):
  → PASS → proceed to Gate 6

if any failure:
  → Re-dispatch with specific gaps
  → iterations++

if iterations >= 3:
  → Escalate to user
```

## Output Format

```markdown
## E2E Testing Result
unit_id | result: PASS/FAIL | iterations

## Flow Coverage
| Flow | Happy Path | Error Paths | Browsers | Status |

## Handoff
gate5_result: PASS | ESCALATED
test_files: [list]
```
