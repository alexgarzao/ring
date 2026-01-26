# UX Acceptance Criteria

## Feature: SSO Login

## Functional Criteria
- [ ] User can select SSO provider (Google/Microsoft) in less than 2 clicks
- [ ] Visual feedback on all button clicks (loading state)
- [ ] Redirect to dashboard after successful authentication
- [ ] Error message displayed on authentication failure

## Usability Criteria
- [ ] Main flow is intuitive (no instruction needed)
- [ ] Errors are clear and include recovery action
- [ ] Works on mobile (responsive)

## Accessibility Criteria
- [ ] Keyboard navigable (Tab order correct)
- [ ] Adequate contrast (WCAG AA)
- [ ] Labels on all interactive elements
- [ ] Screen reader compatible (aria-labels)

## State Coverage
| State | When | What to Show |
|-------|------|--------------|
| Default | Page load | SSO provider buttons |
| Loading | After click, awaiting redirect | Spinner on clicked button |
| Error | Auth failed | Toast with error message + retry |
| Success | Auth complete | Redirect to /dashboard |
