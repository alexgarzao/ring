## CI/CD Pipeline (MANDATORY)

This section covers CI/CD pipeline patterns and automation requirements.

### CI Pipeline Stages (MANDATORY)

All services MUST have CI pipelines with these stages:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.24"
      - name: golangci-lint
        uses: golangci/golangci-lint-action@v4

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.24"
      - name: Run tests
        run: make test
      - name: Check coverage
        run: make cover

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run govulncheck
        run: go run golang.org/x/vuln/cmd/govulncheck@latest ./...

  build:
    runs-on: ubuntu-latest
    needs: [lint, test, security]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t ${{ github.repository }}:${{ github.sha }} .
```

### Required CI Stages

| Stage       | Purpose                | Failure Action           |
| ----------- | ---------------------- | ------------------------ |
| lint        | Code quality           | Block merge              |
| test        | Unit tests + coverage  | Block merge              |
| security    | Vulnerability scan     | Block merge              |
| build       | Docker image creation  | Block merge              |
| deploy (CD) | Environment deployment | Manual approval for prod |

### Branch Protection (REQUIRED)

```yaml
# Settings → Branches → Branch protection rules → main

Required checks:
  - lint
  - test
  - security
  - build

Settings:
  - Require a pull request before merging: ✅
  - Require approvals: 1
  - Dismiss stale approvals: ✅
  - Require status checks to pass: ✅
  - Require branches to be up to date: ✅
```

### Detection Commands

```bash
# Find projects without CI config
find . -name "go.mod" -exec dirname {} \; | while read dir; do
  if [ ! -f "$dir/.github/workflows/ci.yml" ] && [ ! -f "$dir/.gitlab-ci.yml" ]; then
    echo "MISSING CI: $dir"
  fi
done
```

### Anti-Rationalization Table

| Rationalization             | Why It's WRONG                                          | Required Action                |
| --------------------------- | ------------------------------------------------------- | ------------------------------ |
| "Local tests are enough"    | Local ≠ CI environment. CI catches env-specific issues. | **Add CI pipeline**            |
| "Security scan is slow"     | Slow scan > production vulnerability.                   | **Include govulncheck**        |
| "We'll add CI later"        | Later = technical debt. Start with CI.                  | **Add CI on project creation** |
| "Manual deployment is fine" | Manual = error-prone + no audit trail.                  | **Automate deployments**       |

---

