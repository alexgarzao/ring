# Phase 1: Static Analysis Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Implement the static analysis binary that runs language-specific linters (Go, TypeScript, Python), normalizes their output, and produces `static-analysis.json` for downstream phases.

**Architecture:** Go binary orchestrator that reads `scope.json` (from Phase 0), detects project language, dispatches appropriate linters via subprocess execution, parses their native output formats, filters findings to changed files only, normalizes to a common schema, deduplicates, and outputs aggregate results.

**Tech Stack:**
- Go 1.22+ (binary implementation)
- External tools: golangci-lint, staticcheck, gosec (Go); tsc, eslint (TypeScript); ruff, mypy, pylint, bandit (Python)
- JSON output format

**Global Prerequisites:**
- Environment: macOS or Linux, Go 1.22+
- Tools: git (for repo operations)
- Access: None required (all tools are local)
- State: Clean working tree on `main` branch

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
go version          # Expected: go version go1.22+ or higher
git status          # Expected: clean working tree
ls docs/plans/codereview-enhancement-macro-plan.md  # Expected: file exists
```

## Historical Precedent

**Query:** "static analysis linter codereview Go TypeScript Python"
**Index Status:** Populated (no relevant precedent found)

### Successful Patterns to Reference
- None found - this is a new feature area

### Failure Patterns to AVOID
- None found

### Related Past Plans
- `codereview-enhancement-macro-plan.md`: Parent macro plan defining overall architecture

---

## Task Overview

| # | Task | Description | Time |
|---|------|-------------|------|
| 1 | Initialize Go module | Create `scripts/codereview/go.mod` and directory structure | 3 min |
| 2 | Define common types | Create `internal/lint/types.go` with Finding, Result schemas | 4 min |
| 3 | Create linter runner interface | Define `internal/lint/runner.go` with Linter interface | 4 min |
| 4 | Implement tool executor | Create `internal/lint/executor.go` for subprocess execution | 5 min |
| 5 | Implement Go: golangci-lint | Create `internal/lint/golangci.go` wrapper | 5 min |
| 6 | Implement Go: staticcheck | Create `internal/lint/staticcheck.go` wrapper | 4 min |
| 7 | Implement Go: gosec | Create `internal/lint/gosec.go` wrapper | 4 min |
| 8 | Implement TypeScript: tsc | Create `internal/lint/tsc.go` wrapper | 5 min |
| 9 | Implement TypeScript: eslint | Create `internal/lint/eslint.go` wrapper | 5 min |
| 10 | Implement Python: ruff | Create `internal/lint/ruff.go` wrapper | 4 min |
| 11 | Implement Python: mypy | Create `internal/lint/mypy.go` wrapper | 5 min |
| 12 | Implement Python: pylint | Create `internal/lint/pylint.go` wrapper | 5 min |
| 13 | Implement Python: bandit | Create `internal/lint/bandit.go` wrapper | 4 min |
| 14 | Create scope reader | Create `internal/scope/reader.go` to parse scope.json | 4 min |
| 15 | Create output writer | Create `internal/output/json.go` for JSON output | 3 min |
| 16 | Implement orchestrator | Create `cmd/static-analysis/main.go` | 5 min |
| 17 | Add unit tests: types | Create `internal/lint/types_test.go` | 4 min |
| 18 | Add unit tests: golangci parser | Create `internal/lint/golangci_test.go` | 4 min |
| 19 | Add unit tests: eslint parser | Create `internal/lint/eslint_test.go` | 4 min |
| 20 | Add unit tests: ruff parser | Create `internal/lint/ruff_test.go` | 4 min |
| 21 | Integration test | End-to-end test with sample scope.json | 5 min |
| 22 | Code Review | Run code review checkpoint | 5 min |
| 23 | Build and verify | Build binary and verify with real project | 5 min |

---

## Task 1: Initialize Go Module

**Files:**
- Create: `scripts/codereview/go.mod`
- Create: `scripts/codereview/cmd/static-analysis/.gitkeep`
- Create: `scripts/codereview/internal/lint/.gitkeep`
- Create: `scripts/codereview/internal/scope/.gitkeep`
- Create: `scripts/codereview/internal/output/.gitkeep`

**Prerequisites:**
- Tools: Go 1.22+
- Directory `scripts/` does not exist yet

**Step 1: Create directory structure**

```bash
mkdir -p scripts/codereview/cmd/static-analysis
mkdir -p scripts/codereview/internal/lint
mkdir -p scripts/codereview/internal/scope
mkdir -p scripts/codereview/internal/output
mkdir -p scripts/codereview/bin
```

**Step 2: Create go.mod**

Create file `scripts/codereview/go.mod`:

```go
module github.com/LerianStudio/ring/scripts/codereview

go 1.22

require (
	github.com/stretchr/testify v1.9.0
)
```

**Step 3: Initialize go.sum**

Run: `cd scripts/codereview && go mod tidy`

**Expected output:**
```
go: downloading github.com/stretchr/testify v1.9.0
go: downloading github.com/davecgh/go-spew v1.1.1
go: downloading github.com/pmezard/go-difflib v1.0.0
go: downloading github.com/stretchr/objx v0.5.2
go: downloading gopkg.in/yaml.v3 v3.0.1
```

**Step 4: Verify structure**

Run: `ls -la scripts/codereview/`

**Expected output:**
```
total XX
drwxr-xr-x  ... .
drwxr-xr-x  ... ..
drwxr-xr-x  ... bin
drwxr-xr-x  ... cmd
-rw-r--r--  ... go.mod
-rw-r--r--  ... go.sum
drwxr-xr-x  ... internal
```

**Step 5: Commit**

```bash
git add scripts/codereview/
git commit -m "feat(codereview): initialize Go module for static analysis scripts"
```

**If Task Fails:**

1. **Directory creation fails:**
   - Check: `ls scripts/` (parent may not exist)
   - Fix: Create parent directories first
   - Rollback: `rm -rf scripts/codereview`

2. **go mod tidy fails:**
   - Check: `go version` (needs 1.22+)
   - Fix: Update Go version
   - Rollback: `rm scripts/codereview/go.sum`

---

## Task 2: Define Common Types

**Files:**
- Create: `scripts/codereview/internal/lint/types.go`

**Prerequisites:**
- Task 1 completed (go.mod exists)

**Step 1: Write the types file**

Create file `scripts/codereview/internal/lint/types.go`:

```go
// Package lint provides linter integrations for static analysis.
package lint

// Severity represents the severity level of a finding.
type Severity string

const (
	SeverityCritical Severity = "critical"
	SeverityHigh     Severity = "high"
	SeverityWarning  Severity = "warning"
	SeverityInfo     Severity = "info"
)

// Category represents the category of a finding.
type Category string

const (
	CategorySecurity    Category = "security"
	CategoryBug         Category = "bug"
	CategoryStyle       Category = "style"
	CategoryPerformance Category = "performance"
	CategoryDeprecation Category = "deprecation"
	CategoryComplexity  Category = "complexity"
	CategoryType        Category = "type"
	CategoryUnused      Category = "unused"
	CategoryOther       Category = "other"
)

// Finding represents a single lint finding.
type Finding struct {
	Tool       string   `json:"tool"`
	Rule       string   `json:"rule"`
	Severity   Severity `json:"severity"`
	File       string   `json:"file"`
	Line       int      `json:"line"`
	Column     int      `json:"column"`
	Message    string   `json:"message"`
	Suggestion string   `json:"suggestion,omitempty"`
	Category   Category `json:"category"`
}

// ToolVersions holds version information for all tools used.
type ToolVersions map[string]string

// Summary holds aggregated finding counts by severity.
type Summary struct {
	Critical int `json:"critical"`
	High     int `json:"high"`
	Warning  int `json:"warning"`
	Info     int `json:"info"`
}

// Result is the aggregate output of static analysis.
type Result struct {
	ToolVersions ToolVersions `json:"tool_versions"`
	Findings     []Finding    `json:"findings"`
	Summary      Summary      `json:"summary"`
	Errors       []string     `json:"errors,omitempty"`
}

// NewResult creates a new Result with initialized fields.
func NewResult() *Result {
	return &Result{
		ToolVersions: make(ToolVersions),
		Findings:     make([]Finding, 0),
		Summary:      Summary{},
		Errors:       make([]string, 0),
	}
}

// AddFinding adds a finding and updates the summary.
func (r *Result) AddFinding(f Finding) {
	r.Findings = append(r.Findings, f)
	switch f.Severity {
	case SeverityCritical:
		r.Summary.Critical++
	case SeverityHigh:
		r.Summary.High++
	case SeverityWarning:
		r.Summary.Warning++
	case SeverityInfo:
		r.Summary.Info++
	}
}

// Merge combines another Result into this one.
func (r *Result) Merge(other *Result) {
	for k, v := range other.ToolVersions {
		r.ToolVersions[k] = v
	}
	for _, f := range other.Findings {
		r.AddFinding(f)
	}
	r.Errors = append(r.Errors, other.Errors...)
}

// FilterByFiles returns findings only for the specified files.
func (r *Result) FilterByFiles(files map[string]bool) *Result {
	filtered := NewResult()
	filtered.ToolVersions = r.ToolVersions
	filtered.Errors = r.Errors

	for _, f := range r.Findings {
		if files[f.File] {
			filtered.AddFinding(f)
		}
	}
	return filtered
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/types.go
git commit -m "feat(codereview): add common types for static analysis findings"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Error message for syntax issues
   - Fix: Correct syntax errors
   - Rollback: `git checkout -- scripts/codereview/internal/lint/types.go`

---

## Task 3: Create Linter Runner Interface

**Files:**
- Create: `scripts/codereview/internal/lint/runner.go`

**Prerequisites:**
- Task 2 completed (types.go exists)

**Step 1: Write the runner interface**

Create file `scripts/codereview/internal/lint/runner.go`:

```go
package lint

import "context"

// Language represents a programming language.
type Language string

const (
	LanguageGo         Language = "go"
	LanguageTypeScript Language = "typescript"
	LanguagePython     Language = "python"
)

// Linter defines the interface for all linter implementations.
type Linter interface {
	// Name returns the linter's name (e.g., "golangci-lint", "eslint").
	Name() string

	// Language returns the language this linter supports.
	Language() Language

	// Available checks if the linter is installed and available.
	Available(ctx context.Context) bool

	// Version returns the linter's version string.
	Version(ctx context.Context) (string, error)

	// Run executes the linter and returns findings.
	// projectDir is the root directory of the project.
	// files is the list of files/packages to analyze.
	Run(ctx context.Context, projectDir string, files []string) (*Result, error)
}

// Registry holds all registered linters.
type Registry struct {
	linters map[Language][]Linter
}

// NewRegistry creates a new linter registry.
func NewRegistry() *Registry {
	return &Registry{
		linters: make(map[Language][]Linter),
	}
}

// Register adds a linter to the registry.
func (r *Registry) Register(l Linter) {
	lang := l.Language()
	r.linters[lang] = append(r.linters[lang], l)
}

// GetLinters returns all linters for a specific language.
func (r *Registry) GetLinters(lang Language) []Linter {
	return r.linters[lang]
}

// GetAvailableLinters returns only available linters for a language.
func (r *Registry) GetAvailableLinters(ctx context.Context, lang Language) []Linter {
	var available []Linter
	for _, l := range r.linters[lang] {
		if l.Available(ctx) {
			available = append(available, l)
		}
	}
	return available
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/runner.go
git commit -m "feat(codereview): add Linter interface and Registry for linter management"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Error message for interface definition issues
   - Fix: Ensure all method signatures are correct
   - Rollback: `git checkout -- scripts/codereview/internal/lint/runner.go`

---

## Task 4: Implement Tool Executor

**Files:**
- Create: `scripts/codereview/internal/lint/executor.go`

**Prerequisites:**
- Task 3 completed (runner.go exists)

**Step 1: Write the executor**

Create file `scripts/codereview/internal/lint/executor.go`:

```go
package lint

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

// DefaultTimeout is the default timeout for linter execution.
const DefaultTimeout = 5 * time.Minute

// ExecResult holds the result of command execution.
type ExecResult struct {
	Stdout   []byte
	Stderr   []byte
	ExitCode int
	Err      error
}

// Executor runs external commands.
type Executor struct {
	timeout time.Duration
}

// NewExecutor creates a new command executor.
func NewExecutor() *Executor {
	return &Executor{
		timeout: DefaultTimeout,
	}
}

// WithTimeout sets a custom timeout.
func (e *Executor) WithTimeout(d time.Duration) *Executor {
	e.timeout = d
	return e
}

// Run executes a command and returns the result.
func (e *Executor) Run(ctx context.Context, dir string, name string, args ...string) *ExecResult {
	ctx, cancel := context.WithTimeout(ctx, e.timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, name, args...)
	cmd.Dir = dir

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()

	result := &ExecResult{
		Stdout: stdout.Bytes(),
		Stderr: stderr.Bytes(),
	}

	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			result.ExitCode = exitErr.ExitCode()
			// Many linters return non-zero on findings, which is not an error
			result.Err = nil
		} else if ctx.Err() == context.DeadlineExceeded {
			result.Err = fmt.Errorf("command timed out after %v", e.timeout)
		} else {
			result.Err = err
		}
	}

	return result
}

// CommandAvailable checks if a command is available in PATH.
func (e *Executor) CommandAvailable(ctx context.Context, name string) bool {
	_, err := exec.LookPath(name)
	return err == nil
}

// GetVersion runs a command with --version and extracts the version string.
func (e *Executor) GetVersion(ctx context.Context, name string, args ...string) (string, error) {
	if len(args) == 0 {
		args = []string{"--version"}
	}

	result := e.Run(ctx, "", name, args...)
	if result.Err != nil {
		return "", result.Err
	}

	output := string(result.Stdout)
	if output == "" {
		output = string(result.Stderr)
	}

	// Extract first line and clean up
	lines := strings.Split(strings.TrimSpace(output), "\n")
	if len(lines) > 0 {
		return strings.TrimSpace(lines[0]), nil
	}

	return "unknown", nil
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/executor.go
git commit -m "feat(codereview): add command executor for running external linters"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Import paths and error handling
   - Fix: Correct any typos in imports
   - Rollback: `git checkout -- scripts/codereview/internal/lint/executor.go`

---

## Task 5: Implement Go: golangci-lint

**Files:**
- Create: `scripts/codereview/internal/lint/golangci.go`

**Prerequisites:**
- Task 4 completed (executor.go exists)

**Step 1: Write the golangci-lint wrapper**

Create file `scripts/codereview/internal/lint/golangci.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"path/filepath"
	"strings"
)

// golangciLintOutput represents golangci-lint JSON output.
type golangciLintOutput struct {
	Issues []golangciIssue `json:"Issues"`
}

type golangciIssue struct {
	FromLinter  string           `json:"FromLinter"`
	Text        string           `json:"Text"`
	Severity    string           `json:"Severity"`
	SourceLines []string         `json:"SourceLines"`
	Pos         golangciPosition `json:"Pos"`
}

type golangciPosition struct {
	Filename string `json:"Filename"`
	Line     int    `json:"Line"`
	Column   int    `json:"Column"`
}

// GolangciLint implements the golangci-lint wrapper.
type GolangciLint struct {
	executor *Executor
}

// NewGolangciLint creates a new golangci-lint wrapper.
func NewGolangciLint() *GolangciLint {
	return &GolangciLint{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (g *GolangciLint) Name() string {
	return "golangci-lint"
}

// Language returns the supported language.
func (g *GolangciLint) Language() Language {
	return LanguageGo
}

// Available checks if golangci-lint is installed.
func (g *GolangciLint) Available(ctx context.Context) bool {
	return g.executor.CommandAvailable(ctx, "golangci-lint")
}

// Version returns the golangci-lint version.
func (g *GolangciLint) Version(ctx context.Context) (string, error) {
	version, err := g.executor.GetVersion(ctx, "golangci-lint", "version", "--format", "short")
	if err != nil {
		return "", err
	}
	return strings.TrimPrefix(version, "v"), nil
}

// Run executes golangci-lint on the specified packages.
func (g *GolangciLint) Run(ctx context.Context, projectDir string, packages []string) (*Result, error) {
	result := NewResult()

	version, err := g.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("golangci-lint version check failed: %v", err))
	} else {
		result.ToolVersions["golangci-lint"] = version
	}

	// Build arguments
	args := []string{
		"run",
		"--out-format=json",
		"--issues-exit-code=0", // Don't fail on findings
	}

	// Add packages to analyze
	if len(packages) > 0 {
		args = append(args, packages...)
	} else {
		args = append(args, "./...")
	}

	execResult := g.executor.Run(ctx, projectDir, "golangci-lint", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("golangci-lint execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON output
	var output golangciLintOutput
	if err := json.Unmarshal(execResult.Stdout, &output); err != nil {
		// Try to parse partial output
		result.Errors = append(result.Errors, fmt.Sprintf("golangci-lint output parse warning: %v", err))
		return result, nil
	}

	// Convert to common format
	for _, issue := range output.Issues {
		finding := Finding{
			Tool:     g.Name(),
			Rule:     issue.FromLinter,
			Severity: mapGolangciSeverity(issue.Severity),
			File:     normalizeFilePath(projectDir, issue.Pos.Filename),
			Line:     issue.Pos.Line,
			Column:   issue.Pos.Column,
			Message:  issue.Text,
			Category: mapGolangciCategory(issue.FromLinter),
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapGolangciSeverity maps golangci-lint severity to common severity.
func mapGolangciSeverity(severity string) Severity {
	switch strings.ToLower(severity) {
	case "error":
		return SeverityHigh
	case "warning":
		return SeverityWarning
	default:
		return SeverityInfo
	}
}

// mapGolangciCategory maps linter name to category.
func mapGolangciCategory(linter string) Category {
	switch linter {
	case "gosec", "gocritic":
		return CategorySecurity
	case "staticcheck", "typecheck":
		return CategoryBug
	case "gofmt", "goimports", "govet":
		return CategoryStyle
	case "ineffassign", "deadcode", "unused", "varcheck":
		return CategoryUnused
	case "gocyclo", "gocognit":
		return CategoryComplexity
	case "depguard":
		return CategoryDeprecation
	default:
		return CategoryOther
	}
}

// normalizeFilePath converts absolute paths to relative paths.
func normalizeFilePath(projectDir, filePath string) string {
	if filepath.IsAbs(filePath) {
		if rel, err := filepath.Rel(projectDir, filePath); err == nil {
			return rel
		}
	}
	return filePath
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/golangci.go
git commit -m "feat(codereview): add golangci-lint wrapper for Go static analysis"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON struct tags and method signatures
   - Fix: Ensure struct fields match golangci-lint JSON output
   - Rollback: `git checkout -- scripts/codereview/internal/lint/golangci.go`

---

## Task 6: Implement Go: staticcheck

**Files:**
- Create: `scripts/codereview/internal/lint/staticcheck.go`

**Prerequisites:**
- Task 5 completed

**Step 1: Write the staticcheck wrapper**

Create file `scripts/codereview/internal/lint/staticcheck.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

// staticcheckIssue represents a single staticcheck finding.
type staticcheckIssue struct {
	Code     string             `json:"code"`
	Severity string             `json:"severity"`
	Location staticcheckLocation `json:"location"`
	Message  string             `json:"message"`
	End      staticcheckLocation `json:"end"`
}

type staticcheckLocation struct {
	File   string `json:"file"`
	Line   int    `json:"line"`
	Column int    `json:"column"`
}

// Staticcheck implements the staticcheck wrapper.
type Staticcheck struct {
	executor *Executor
}

// NewStaticcheck creates a new staticcheck wrapper.
func NewStaticcheck() *Staticcheck {
	return &Staticcheck{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (s *Staticcheck) Name() string {
	return "staticcheck"
}

// Language returns the supported language.
func (s *Staticcheck) Language() Language {
	return LanguageGo
}

// Available checks if staticcheck is installed.
func (s *Staticcheck) Available(ctx context.Context) bool {
	return s.executor.CommandAvailable(ctx, "staticcheck")
}

// Version returns the staticcheck version.
func (s *Staticcheck) Version(ctx context.Context) (string, error) {
	version, err := s.executor.GetVersion(ctx, "staticcheck", "-version")
	if err != nil {
		return "", err
	}
	// Extract version from "staticcheck 2024.1.1 (v0.5.1)"
	parts := strings.Fields(version)
	if len(parts) >= 2 {
		return parts[1], nil
	}
	return version, nil
}

// Run executes staticcheck on the specified packages.
func (s *Staticcheck) Run(ctx context.Context, projectDir string, packages []string) (*Result, error) {
	result := NewResult()

	version, err := s.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("staticcheck version check failed: %v", err))
	} else {
		result.ToolVersions["staticcheck"] = version
	}

	// Build arguments
	args := []string{"-f", "json"}

	// Add packages to analyze
	if len(packages) > 0 {
		args = append(args, packages...)
	} else {
		args = append(args, "./...")
	}

	execResult := s.executor.Run(ctx, projectDir, "staticcheck", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("staticcheck execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON lines output (one JSON object per line)
	lines := strings.Split(string(execResult.Stdout), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		var issue staticcheckIssue
		if err := json.Unmarshal([]byte(line), &issue); err != nil {
			continue // Skip malformed lines
		}

		finding := Finding{
			Tool:     s.Name(),
			Rule:     issue.Code,
			Severity: mapStaticcheckSeverity(issue.Code, issue.Severity),
			File:     normalizeFilePath(projectDir, issue.Location.File),
			Line:     issue.Location.Line,
			Column:   issue.Location.Column,
			Message:  issue.Message,
			Category: mapStaticcheckCategory(issue.Code),
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapStaticcheckSeverity maps staticcheck codes to severity.
func mapStaticcheckSeverity(code, severity string) Severity {
	if strings.HasPrefix(code, "SA") {
		return SeverityWarning
	}
	if strings.HasPrefix(code, "S1") {
		return SeverityInfo
	}
	if strings.HasPrefix(code, "ST1") {
		return SeverityInfo
	}
	if severity == "error" {
		return SeverityHigh
	}
	return SeverityWarning
}

// mapStaticcheckCategory maps staticcheck codes to categories.
func mapStaticcheckCategory(code string) Category {
	switch {
	case strings.HasPrefix(code, "SA1"):
		return CategoryBug
	case strings.HasPrefix(code, "SA2"):
		return CategoryBug
	case strings.HasPrefix(code, "SA3"):
		return CategoryBug
	case strings.HasPrefix(code, "SA4"):
		return CategoryBug
	case strings.HasPrefix(code, "SA5"):
		return CategoryBug
	case strings.HasPrefix(code, "SA6"):
		return CategoryPerformance
	case strings.HasPrefix(code, "SA9"):
		return CategorySecurity
	case strings.HasPrefix(code, "S1"):
		return CategoryStyle
	case strings.HasPrefix(code, "ST1"):
		return CategoryStyle
	case strings.HasPrefix(code, "QF"):
		return CategoryStyle
	default:
		return CategoryOther
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/staticcheck.go
git commit -m "feat(codereview): add staticcheck wrapper for Go static analysis"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON struct definitions match staticcheck output
   - Fix: Verify staticcheck JSON format with `staticcheck -f json ./...`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/staticcheck.go`

---

## Task 7: Implement Go: gosec

**Files:**
- Create: `scripts/codereview/internal/lint/gosec.go`

**Prerequisites:**
- Task 6 completed

**Step 1: Write the gosec wrapper**

Create file `scripts/codereview/internal/lint/gosec.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
)

// gosecOutput represents gosec JSON output.
type gosecOutput struct {
	Issues []gosecIssue `json:"Issues"`
	Stats  gosecStats   `json:"Stats"`
}

type gosecIssue struct {
	Severity   string `json:"severity"`
	Confidence string `json:"confidence"`
	RuleID     string `json:"rule_id"`
	Details    string `json:"details"`
	File       string `json:"file"`
	Line       string `json:"line"`
	Column     string `json:"column"`
	Code       string `json:"code"`
}

type gosecStats struct {
	Files int `json:"files"`
	Lines int `json:"lines"`
	Found int `json:"found"`
}

// Gosec implements the gosec wrapper.
type Gosec struct {
	executor *Executor
}

// NewGosec creates a new gosec wrapper.
func NewGosec() *Gosec {
	return &Gosec{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (g *Gosec) Name() string {
	return "gosec"
}

// Language returns the supported language.
func (g *Gosec) Language() Language {
	return LanguageGo
}

// Available checks if gosec is installed.
func (g *Gosec) Available(ctx context.Context) bool {
	return g.executor.CommandAvailable(ctx, "gosec")
}

// Version returns the gosec version.
func (g *Gosec) Version(ctx context.Context) (string, error) {
	version, err := g.executor.GetVersion(ctx, "gosec", "-version")
	if err != nil {
		return "", err
	}
	// Extract version from "Version: X.Y.Z" or similar
	for _, line := range strings.Split(version, "\n") {
		if strings.Contains(line, "Version:") {
			parts := strings.Split(line, ":")
			if len(parts) >= 2 {
				return strings.TrimSpace(parts[1]), nil
			}
		}
	}
	return strings.TrimSpace(version), nil
}

// Run executes gosec on the specified packages.
func (g *Gosec) Run(ctx context.Context, projectDir string, packages []string) (*Result, error) {
	result := NewResult()

	version, err := g.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("gosec version check failed: %v", err))
	} else {
		result.ToolVersions["gosec"] = version
	}

	// Build arguments
	args := []string{
		"-fmt=json",
		"-quiet",
		"-no-fail", // Don't exit non-zero on findings
	}

	// Add packages to analyze
	if len(packages) > 0 {
		args = append(args, packages...)
	} else {
		args = append(args, "./...")
	}

	execResult := g.executor.Run(ctx, projectDir, "gosec", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("gosec execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON output
	var output gosecOutput
	if err := json.Unmarshal(execResult.Stdout, &output); err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("gosec output parse warning: %v", err))
		return result, nil
	}

	// Convert to common format
	for _, issue := range output.Issues {
		line, _ := strconv.Atoi(issue.Line)
		col, _ := strconv.Atoi(issue.Column)

		finding := Finding{
			Tool:     g.Name(),
			Rule:     issue.RuleID,
			Severity: mapGosecSeverity(issue.Severity, issue.Confidence),
			File:     normalizeFilePath(projectDir, issue.File),
			Line:     line,
			Column:   col,
			Message:  issue.Details,
			Category: CategorySecurity,
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapGosecSeverity maps gosec severity and confidence to common severity.
func mapGosecSeverity(severity, confidence string) Severity {
	sev := strings.ToUpper(severity)
	conf := strings.ToUpper(confidence)

	if sev == "HIGH" && conf == "HIGH" {
		return SeverityCritical
	}
	if sev == "HIGH" {
		return SeverityHigh
	}
	if sev == "MEDIUM" {
		return SeverityWarning
	}
	return SeverityInfo
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/gosec.go
git commit -m "feat(codereview): add gosec wrapper for Go security analysis"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: strconv import and JSON struct tags
   - Fix: Verify gosec JSON format with `gosec -fmt=json ./...`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/gosec.go`

---

## Task 8: Implement TypeScript: tsc

**Files:**
- Create: `scripts/codereview/internal/lint/tsc.go`

**Prerequisites:**
- Task 7 completed

**Step 1: Write the tsc wrapper**

Create file `scripts/codereview/internal/lint/tsc.go`:

```go
package lint

import (
	"bufio"
	"context"
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// tscDiagnosticRegex matches TypeScript compiler diagnostic output.
// Format: "file.ts(line,col): error TSxxxx: message"
var tscDiagnosticRegex = regexp.MustCompile(`^(.+)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.+)$`)

// TSC implements the TypeScript compiler type checker wrapper.
type TSC struct {
	executor *Executor
}

// NewTSC creates a new tsc wrapper.
func NewTSC() *TSC {
	return &TSC{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (t *TSC) Name() string {
	return "tsc"
}

// Language returns the supported language.
func (t *TSC) Language() Language {
	return LanguageTypeScript
}

// Available checks if tsc is installed.
func (t *TSC) Available(ctx context.Context) bool {
	// Check for project-local tsc first, then global
	return t.executor.CommandAvailable(ctx, "npx") || t.executor.CommandAvailable(ctx, "tsc")
}

// Version returns the tsc version.
func (t *TSC) Version(ctx context.Context) (string, error) {
	// Try npx tsc first (project-local)
	version, err := t.executor.GetVersion(ctx, "npx", "tsc", "--version")
	if err != nil {
		// Fall back to global tsc
		version, err = t.executor.GetVersion(ctx, "tsc", "--version")
	}
	if err != nil {
		return "", err
	}
	// Extract version from "Version X.Y.Z"
	parts := strings.Fields(version)
	for i, p := range parts {
		if p == "Version" && i+1 < len(parts) {
			return parts[i+1], nil
		}
	}
	return strings.TrimSpace(version), nil
}

// Run executes tsc type checking on the project.
func (t *TSC) Run(ctx context.Context, projectDir string, files []string) (*Result, error) {
	result := NewResult()

	version, err := t.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("tsc version check failed: %v", err))
	} else {
		result.ToolVersions["typescript"] = version
	}

	// Run tsc --noEmit to type check without emitting files
	args := []string{"tsc", "--noEmit", "--pretty", "false"}

	execResult := t.executor.Run(ctx, projectDir, "npx", args...)
	if execResult.Err != nil {
		// Try global tsc
		execResult = t.executor.Run(ctx, projectDir, "tsc", args[1:]...)
		if execResult.Err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("tsc execution failed: %v", execResult.Err))
			return result, nil
		}
	}

	// Parse output line by line
	scanner := bufio.NewScanner(strings.NewReader(string(execResult.Stdout)))
	for scanner.Scan() {
		line := scanner.Text()
		matches := tscDiagnosticRegex.FindStringSubmatch(line)
		if len(matches) != 7 {
			continue
		}

		lineNum, _ := strconv.Atoi(matches[2])
		col, _ := strconv.Atoi(matches[3])

		finding := Finding{
			Tool:     t.Name(),
			Rule:     matches[5], // TSxxxx
			Severity: mapTSCSeverity(matches[4]),
			File:     normalizeFilePath(projectDir, matches[1]),
			Line:     lineNum,
			Column:   col,
			Message:  matches[6],
			Category: CategoryType,
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapTSCSeverity maps tsc error/warning to common severity.
func mapTSCSeverity(level string) Severity {
	switch strings.ToLower(level) {
	case "error":
		return SeverityHigh
	case "warning":
		return SeverityWarning
	default:
		return SeverityInfo
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/tsc.go
git commit -m "feat(codereview): add TypeScript compiler (tsc) wrapper for type checking"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: regexp package import and pattern
   - Fix: Test regexp pattern against sample tsc output
   - Rollback: `git checkout -- scripts/codereview/internal/lint/tsc.go`

---

## Task 9: Implement TypeScript: eslint

**Files:**
- Create: `scripts/codereview/internal/lint/eslint.go`

**Prerequisites:**
- Task 8 completed

**Step 1: Write the eslint wrapper**

Create file `scripts/codereview/internal/lint/eslint.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

// eslintOutput represents eslint JSON output (array of file results).
type eslintOutput []eslintFileResult

type eslintFileResult struct {
	FilePath string         `json:"filePath"`
	Messages []eslintMessage `json:"messages"`
}

type eslintMessage struct {
	RuleID   string `json:"ruleId"`
	Severity int    `json:"severity"` // 1 = warning, 2 = error
	Message  string `json:"message"`
	Line     int    `json:"line"`
	Column   int    `json:"column"`
}

// ESLint implements the eslint wrapper.
type ESLint struct {
	executor *Executor
}

// NewESLint creates a new eslint wrapper.
func NewESLint() *ESLint {
	return &ESLint{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (e *ESLint) Name() string {
	return "eslint"
}

// Language returns the supported language.
func (e *ESLint) Language() Language {
	return LanguageTypeScript
}

// Available checks if eslint is installed.
func (e *ESLint) Available(ctx context.Context) bool {
	return e.executor.CommandAvailable(ctx, "npx")
}

// Version returns the eslint version.
func (e *ESLint) Version(ctx context.Context) (string, error) {
	version, err := e.executor.GetVersion(ctx, "npx", "eslint", "--version")
	if err != nil {
		return "", err
	}
	return strings.TrimPrefix(strings.TrimSpace(version), "v"), nil
}

// Run executes eslint on the specified files.
func (e *ESLint) Run(ctx context.Context, projectDir string, files []string) (*Result, error) {
	result := NewResult()

	version, err := e.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("eslint version check failed: %v", err))
	} else {
		result.ToolVersions["eslint"] = version
	}

	// Build arguments
	args := []string{
		"eslint",
		"--format", "json",
		"--no-error-on-unmatched-pattern",
	}

	// Add files to lint
	if len(files) > 0 {
		args = append(args, files...)
	} else {
		args = append(args, ".")
	}

	execResult := e.executor.Run(ctx, projectDir, "npx", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("eslint execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON output
	var output eslintOutput
	if err := json.Unmarshal(execResult.Stdout, &output); err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("eslint output parse warning: %v", err))
		return result, nil
	}

	// Convert to common format
	for _, file := range output {
		for _, msg := range file.Messages {
			ruleID := msg.RuleID
			if ruleID == "" {
				ruleID = "parse-error"
			}

			finding := Finding{
				Tool:     e.Name(),
				Rule:     ruleID,
				Severity: mapESLintSeverity(msg.Severity),
				File:     normalizeFilePath(projectDir, file.FilePath),
				Line:     msg.Line,
				Column:   msg.Column,
				Message:  msg.Message,
				Category: mapESLintCategory(ruleID),
			}
			result.AddFinding(finding)
		}
	}

	return result, nil
}

// mapESLintSeverity maps eslint severity (1=warn, 2=error) to common severity.
func mapESLintSeverity(severity int) Severity {
	switch severity {
	case 2:
		return SeverityHigh
	case 1:
		return SeverityWarning
	default:
		return SeverityInfo
	}
}

// mapESLintCategory maps eslint rule IDs to categories.
func mapESLintCategory(ruleID string) Category {
	switch {
	case strings.HasPrefix(ruleID, "@typescript-eslint/"):
		return CategoryType
	case strings.Contains(ruleID, "security"):
		return CategorySecurity
	case strings.Contains(ruleID, "no-unused"):
		return CategoryUnused
	case strings.HasPrefix(ruleID, "import/"):
		return CategoryStyle
	case strings.HasPrefix(ruleID, "react"):
		return CategoryStyle
	case ruleID == "parse-error":
		return CategoryBug
	default:
		return CategoryStyle
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/eslint.go
git commit -m "feat(codereview): add ESLint wrapper for TypeScript linting"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON struct definitions for eslint output
   - Fix: Verify eslint JSON format with `npx eslint --format json .`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/eslint.go`

---

## Task 10: Implement Python: ruff

**Files:**
- Create: `scripts/codereview/internal/lint/ruff.go`

**Prerequisites:**
- Task 9 completed

**Step 1: Write the ruff wrapper**

Create file `scripts/codereview/internal/lint/ruff.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

// ruffOutput represents ruff JSON output (array of diagnostics).
type ruffOutput []ruffDiagnostic

type ruffDiagnostic struct {
	Code     string        `json:"code"`
	Message  string        `json:"message"`
	Location ruffLocation  `json:"location"`
	Fix      *ruffFix      `json:"fix"`
	Filename string        `json:"filename"`
}

type ruffLocation struct {
	Row    int `json:"row"`
	Column int `json:"column"`
}

type ruffFix struct {
	Message string `json:"message"`
}

// Ruff implements the ruff linter wrapper.
type Ruff struct {
	executor *Executor
}

// NewRuff creates a new ruff wrapper.
func NewRuff() *Ruff {
	return &Ruff{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (r *Ruff) Name() string {
	return "ruff"
}

// Language returns the supported language.
func (r *Ruff) Language() Language {
	return LanguagePython
}

// Available checks if ruff is installed.
func (r *Ruff) Available(ctx context.Context) bool {
	return r.executor.CommandAvailable(ctx, "ruff")
}

// Version returns the ruff version.
func (r *Ruff) Version(ctx context.Context) (string, error) {
	version, err := r.executor.GetVersion(ctx, "ruff", "--version")
	if err != nil {
		return "", err
	}
	// Extract version from "ruff X.Y.Z"
	parts := strings.Fields(version)
	if len(parts) >= 2 {
		return parts[1], nil
	}
	return strings.TrimSpace(version), nil
}

// Run executes ruff on the specified files.
func (r *Ruff) Run(ctx context.Context, projectDir string, files []string) (*Result, error) {
	result := NewResult()

	version, err := r.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("ruff version check failed: %v", err))
	} else {
		result.ToolVersions["ruff"] = version
	}

	// Build arguments
	args := []string{
		"check",
		"--output-format", "json",
		"--exit-zero", // Don't fail on findings
	}

	// Add files to lint
	if len(files) > 0 {
		args = append(args, files...)
	} else {
		args = append(args, ".")
	}

	execResult := r.executor.Run(ctx, projectDir, "ruff", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("ruff execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON output
	var output ruffOutput
	if err := json.Unmarshal(execResult.Stdout, &output); err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("ruff output parse warning: %v", err))
		return result, nil
	}

	// Convert to common format
	for _, diag := range output {
		suggestion := ""
		if diag.Fix != nil {
			suggestion = diag.Fix.Message
		}

		finding := Finding{
			Tool:       r.Name(),
			Rule:       diag.Code,
			Severity:   mapRuffSeverity(diag.Code),
			File:       normalizeFilePath(projectDir, diag.Filename),
			Line:       diag.Location.Row,
			Column:     diag.Location.Column,
			Message:    diag.Message,
			Suggestion: suggestion,
			Category:   mapRuffCategory(diag.Code),
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapRuffSeverity maps ruff codes to severity.
func mapRuffSeverity(code string) Severity {
	switch {
	case strings.HasPrefix(code, "S"):
		return SeverityHigh // Security
	case strings.HasPrefix(code, "E"):
		return SeverityWarning // Errors
	case strings.HasPrefix(code, "F"):
		return SeverityWarning // Pyflakes
	case strings.HasPrefix(code, "W"):
		return SeverityWarning // Warnings
	case strings.HasPrefix(code, "B"):
		return SeverityWarning // Bugbear
	default:
		return SeverityInfo
	}
}

// mapRuffCategory maps ruff codes to categories.
func mapRuffCategory(code string) Category {
	switch {
	case strings.HasPrefix(code, "S"):
		return CategorySecurity
	case strings.HasPrefix(code, "F"):
		return CategoryBug
	case strings.HasPrefix(code, "E"):
		return CategoryStyle
	case strings.HasPrefix(code, "W"):
		return CategoryStyle
	case strings.HasPrefix(code, "B"):
		return CategoryBug
	case strings.HasPrefix(code, "I"):
		return CategoryStyle // Import sorting
	case strings.HasPrefix(code, "UP"):
		return CategoryDeprecation // Pyupgrade
	case strings.HasPrefix(code, "C"):
		return CategoryComplexity
	default:
		return CategoryOther
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/ruff.go
git commit -m "feat(codereview): add ruff wrapper for Python fast linting"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON struct definitions match ruff output
   - Fix: Verify ruff JSON format with `ruff check --output-format json .`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/ruff.go`

---

## Task 11: Implement Python: mypy

**Files:**
- Create: `scripts/codereview/internal/lint/mypy.go`

**Prerequisites:**
- Task 10 completed

**Step 1: Write the mypy wrapper**

Create file `scripts/codereview/internal/lint/mypy.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

// mypyOutput represents mypy JSON output.
type mypyOutput struct {
	Messages []mypyMessage `json:"messages"`
}

type mypyMessage struct {
	File     string `json:"file"`
	Line     int    `json:"line"`
	Column   int    `json:"column"`
	Severity string `json:"severity"`
	Code     string `json:"code"`
	Message  string `json:"message"`
}

// Mypy implements the mypy type checker wrapper.
type Mypy struct {
	executor *Executor
}

// NewMypy creates a new mypy wrapper.
func NewMypy() *Mypy {
	return &Mypy{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (m *Mypy) Name() string {
	return "mypy"
}

// Language returns the supported language.
func (m *Mypy) Language() Language {
	return LanguagePython
}

// Available checks if mypy is installed.
func (m *Mypy) Available(ctx context.Context) bool {
	return m.executor.CommandAvailable(ctx, "mypy")
}

// Version returns the mypy version.
func (m *Mypy) Version(ctx context.Context) (string, error) {
	version, err := m.executor.GetVersion(ctx, "mypy", "--version")
	if err != nil {
		return "", err
	}
	// Extract version from "mypy X.Y.Z (compiled: yes)"
	parts := strings.Fields(version)
	if len(parts) >= 2 {
		return parts[1], nil
	}
	return strings.TrimSpace(version), nil
}

// Run executes mypy type checking on the specified files.
func (m *Mypy) Run(ctx context.Context, projectDir string, files []string) (*Result, error) {
	result := NewResult()

	version, err := m.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("mypy version check failed: %v", err))
	} else {
		result.ToolVersions["mypy"] = version
	}

	// Build arguments
	args := []string{
		"--output", "json",
		"--no-error-summary",
		"--show-error-codes",
	}

	// Add files to check
	if len(files) > 0 {
		args = append(args, files...)
	} else {
		args = append(args, ".")
	}

	execResult := m.executor.Run(ctx, projectDir, "mypy", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("mypy execution failed: %v", execResult.Err))
		return result, nil
	}

	// mypy JSON output is one JSON object per line
	lines := strings.Split(string(execResult.Stdout), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		var msg mypyMessage
		if err := json.Unmarshal([]byte(line), &msg); err != nil {
			continue // Skip malformed lines
		}

		finding := Finding{
			Tool:     m.Name(),
			Rule:     msg.Code,
			Severity: mapMypySeverity(msg.Severity),
			File:     normalizeFilePath(projectDir, msg.File),
			Line:     msg.Line,
			Column:   msg.Column,
			Message:  msg.Message,
			Category: CategoryType,
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapMypySeverity maps mypy severity to common severity.
func mapMypySeverity(severity string) Severity {
	switch strings.ToLower(severity) {
	case "error":
		return SeverityHigh
	case "warning":
		return SeverityWarning
	case "note":
		return SeverityInfo
	default:
		return SeverityWarning
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/mypy.go
git commit -m "feat(codereview): add mypy wrapper for Python type checking"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON parsing for line-by-line output
   - Fix: Verify mypy JSON format with `mypy --output json .`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/mypy.go`

---

## Task 12: Implement Python: pylint

**Files:**
- Create: `scripts/codereview/internal/lint/pylint.go`

**Prerequisites:**
- Task 11 completed

**Step 1: Write the pylint wrapper**

Create file `scripts/codereview/internal/lint/pylint.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

// pylintOutput represents pylint JSON output (array of messages).
type pylintOutput []pylintMessage

type pylintMessage struct {
	Type       string `json:"type"`     // convention, refactor, warning, error, fatal
	Module     string `json:"module"`
	Obj        string `json:"obj"`
	Line       int    `json:"line"`
	Column     int    `json:"column"`
	Path       string `json:"path"`
	Symbol     string `json:"symbol"`
	Message    string `json:"message"`
	MessageID  string `json:"message-id"`
}

// Pylint implements the pylint wrapper.
type Pylint struct {
	executor *Executor
}

// NewPylint creates a new pylint wrapper.
func NewPylint() *Pylint {
	return &Pylint{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (p *Pylint) Name() string {
	return "pylint"
}

// Language returns the supported language.
func (p *Pylint) Language() Language {
	return LanguagePython
}

// Available checks if pylint is installed.
func (p *Pylint) Available(ctx context.Context) bool {
	return p.executor.CommandAvailable(ctx, "pylint")
}

// Version returns the pylint version.
func (p *Pylint) Version(ctx context.Context) (string, error) {
	version, err := p.executor.GetVersion(ctx, "pylint", "--version")
	if err != nil {
		return "", err
	}
	// Extract version from "pylint X.Y.Z\n..."
	lines := strings.Split(version, "\n")
	if len(lines) > 0 {
		parts := strings.Fields(lines[0])
		if len(parts) >= 2 {
			return parts[1], nil
		}
	}
	return strings.TrimSpace(version), nil
}

// Run executes pylint on the specified files.
func (p *Pylint) Run(ctx context.Context, projectDir string, files []string) (*Result, error) {
	result := NewResult()

	version, err := p.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("pylint version check failed: %v", err))
	} else {
		result.ToolVersions["pylint"] = version
	}

	// Build arguments
	args := []string{
		"--output-format=json",
		"--exit-zero", // Don't fail on findings
	}

	// Add files to lint
	if len(files) > 0 {
		args = append(args, files...)
	} else {
		args = append(args, ".")
	}

	execResult := p.executor.Run(ctx, projectDir, "pylint", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("pylint execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON output
	var output pylintOutput
	if err := json.Unmarshal(execResult.Stdout, &output); err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("pylint output parse warning: %v", err))
		return result, nil
	}

	// Convert to common format
	for _, msg := range output {
		finding := Finding{
			Tool:     p.Name(),
			Rule:     msg.MessageID,
			Severity: mapPylintSeverity(msg.Type),
			File:     normalizeFilePath(projectDir, msg.Path),
			Line:     msg.Line,
			Column:   msg.Column,
			Message:  fmt.Sprintf("%s: %s", msg.Symbol, msg.Message),
			Category: mapPylintCategory(msg.Type, msg.MessageID),
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapPylintSeverity maps pylint message types to severity.
func mapPylintSeverity(msgType string) Severity {
	switch strings.ToLower(msgType) {
	case "fatal", "error":
		return SeverityHigh
	case "warning":
		return SeverityWarning
	case "refactor", "convention":
		return SeverityInfo
	default:
		return SeverityInfo
	}
}

// mapPylintCategory maps pylint message types and IDs to categories.
func mapPylintCategory(msgType, msgID string) Category {
	switch strings.ToLower(msgType) {
	case "fatal", "error":
		return CategoryBug
	case "warning":
		if strings.HasPrefix(msgID, "W0611") || strings.HasPrefix(msgID, "W0612") {
			return CategoryUnused
		}
		return CategoryBug
	case "refactor":
		return CategoryComplexity
	case "convention":
		return CategoryStyle
	default:
		return CategoryOther
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/pylint.go
git commit -m "feat(codereview): add pylint wrapper for comprehensive Python linting"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON struct field tags match pylint output
   - Fix: Verify pylint JSON format with `pylint --output-format=json .`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/pylint.go`

---

## Task 13: Implement Python: bandit

**Files:**
- Create: `scripts/codereview/internal/lint/bandit.go`

**Prerequisites:**
- Task 12 completed

**Step 1: Write the bandit wrapper**

Create file `scripts/codereview/internal/lint/bandit.go`:

```go
package lint

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

// banditOutput represents bandit JSON output.
type banditOutput struct {
	Results []banditResult `json:"results"`
	Metrics banditMetrics  `json:"metrics"`
}

type banditResult struct {
	Code        string            `json:"code"`
	Filename    string            `json:"filename"`
	IssueText   string            `json:"issue_text"`
	IssueSeverity string          `json:"issue_severity"`
	IssueConfidence string        `json:"issue_confidence"`
	LineNumber  int               `json:"line_number"`
	LineRange   []int             `json:"line_range"`
	MoreInfo    string            `json:"more_info"`
	TestID      string            `json:"test_id"`
	TestName    string            `json:"test_name"`
}

type banditMetrics struct {
	TotalIssues int `json:"SEVERITY.HIGH"`
}

// Bandit implements the bandit security scanner wrapper.
type Bandit struct {
	executor *Executor
}

// NewBandit creates a new bandit wrapper.
func NewBandit() *Bandit {
	return &Bandit{
		executor: NewExecutor(),
	}
}

// Name returns the linter name.
func (b *Bandit) Name() string {
	return "bandit"
}

// Language returns the supported language.
func (b *Bandit) Language() Language {
	return LanguagePython
}

// Available checks if bandit is installed.
func (b *Bandit) Available(ctx context.Context) bool {
	return b.executor.CommandAvailable(ctx, "bandit")
}

// Version returns the bandit version.
func (b *Bandit) Version(ctx context.Context) (string, error) {
	version, err := b.executor.GetVersion(ctx, "bandit", "--version")
	if err != nil {
		return "", err
	}
	// Extract version from "bandit X.Y.Z"
	parts := strings.Fields(version)
	if len(parts) >= 2 {
		return parts[1], nil
	}
	return strings.TrimSpace(version), nil
}

// Run executes bandit security analysis on the specified files.
func (b *Bandit) Run(ctx context.Context, projectDir string, files []string) (*Result, error) {
	result := NewResult()

	version, err := b.Version(ctx)
	if err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("bandit version check failed: %v", err))
	} else {
		result.ToolVersions["bandit"] = version
	}

	// Build arguments
	args := []string{
		"-f", "json",
		"-q", // Quiet mode
	}

	// Add files to scan
	if len(files) > 0 {
		args = append(args, files...)
	} else {
		args = append(args, "-r", ".") // Recursive scan
	}

	execResult := b.executor.Run(ctx, projectDir, "bandit", args...)
	if execResult.Err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("bandit execution failed: %v", execResult.Err))
		return result, nil
	}

	// Parse JSON output
	var output banditOutput
	if err := json.Unmarshal(execResult.Stdout, &output); err != nil {
		result.Errors = append(result.Errors, fmt.Sprintf("bandit output parse warning: %v", err))
		return result, nil
	}

	// Convert to common format
	for _, res := range output.Results {
		finding := Finding{
			Tool:       b.Name(),
			Rule:       res.TestID,
			Severity:   mapBanditSeverity(res.IssueSeverity, res.IssueConfidence),
			File:       normalizeFilePath(projectDir, res.Filename),
			Line:       res.LineNumber,
			Column:     1, // Bandit doesn't provide column info
			Message:    fmt.Sprintf("%s: %s", res.TestName, res.IssueText),
			Suggestion: res.MoreInfo,
			Category:   CategorySecurity,
		}
		result.AddFinding(finding)
	}

	return result, nil
}

// mapBanditSeverity maps bandit severity and confidence to common severity.
func mapBanditSeverity(severity, confidence string) Severity {
	sev := strings.ToUpper(severity)
	conf := strings.ToUpper(confidence)

	if sev == "HIGH" && conf == "HIGH" {
		return SeverityCritical
	}
	if sev == "HIGH" {
		return SeverityHigh
	}
	if sev == "MEDIUM" {
		return SeverityWarning
	}
	return SeverityInfo
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/lint/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/bandit.go
git commit -m "feat(codereview): add bandit wrapper for Python security analysis"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: JSON struct definitions match bandit output
   - Fix: Verify bandit JSON format with `bandit -f json -r .`
   - Rollback: `git checkout -- scripts/codereview/internal/lint/bandit.go`

---

## Task 14: Create Scope Reader

**Files:**
- Create: `scripts/codereview/internal/scope/reader.go`

**Prerequisites:**
- Task 13 completed

**Step 1: Write the scope reader**

Create file `scripts/codereview/internal/scope/reader.go`:

```go
// Package scope handles reading and parsing scope.json from Phase 0.
package scope

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/LerianStudio/ring/scripts/codereview/internal/lint"
)

// Scope represents the scope.json structure from Phase 0.
type Scope struct {
	BaseRef   string              `json:"base_ref"`
	HeadRef   string              `json:"head_ref"`
	Language  string              `json:"language"` // Primary detected language
	Files     map[string]FileList `json:"files"`
	Stats     Stats               `json:"stats"`
	Packages  map[string][]string `json:"packages_affected"`
}

// FileList holds categorized file lists.
type FileList struct {
	Modified []string `json:"modified"`
	Added    []string `json:"added"`
	Deleted  []string `json:"deleted"`
}

// Stats holds change statistics.
type Stats struct {
	TotalFiles     int `json:"total_files"`
	TotalAdditions int `json:"total_additions"`
	TotalDeletions int `json:"total_deletions"`
}

// ReadScope reads and parses scope.json from the given path.
func ReadScope(scopePath string) (*Scope, error) {
	data, err := os.ReadFile(scopePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read scope.json: %w", err)
	}

	var scope Scope
	if err := json.Unmarshal(data, &scope); err != nil {
		return nil, fmt.Errorf("failed to parse scope.json: %w", err)
	}

	return &scope, nil
}

// GetLanguage returns the primary language as a lint.Language.
func (s *Scope) GetLanguage() lint.Language {
	switch s.Language {
	case "go":
		return lint.LanguageGo
	case "typescript", "ts":
		return lint.LanguageTypeScript
	case "python", "py":
		return lint.LanguagePython
	default:
		return lint.Language(s.Language)
	}
}

// GetAllFiles returns all changed files (modified + added) for a language.
func (s *Scope) GetAllFiles(lang string) []string {
	files, ok := s.Files[lang]
	if !ok {
		return nil
	}

	var all []string
	all = append(all, files.Modified...)
	all = append(all, files.Added...)
	return all
}

// GetAllFilesMap returns a map of all changed files for quick lookup.
func (s *Scope) GetAllFilesMap() map[string]bool {
	fileMap := make(map[string]bool)
	for _, files := range s.Files {
		for _, f := range files.Modified {
			fileMap[f] = true
		}
		for _, f := range files.Added {
			fileMap[f] = true
		}
	}
	return fileMap
}

// GetPackages returns the affected packages for a language.
func (s *Scope) GetPackages(lang string) []string {
	return s.Packages[lang]
}

// DefaultScopePath returns the default scope.json path.
func DefaultScopePath(projectDir string) string {
	return filepath.Join(projectDir, ".ring", "codereview", "scope.json")
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/scope/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/scope/reader.go
git commit -m "feat(codereview): add scope.json reader for Phase 0 integration"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Import path for lint package
   - Fix: Ensure module path matches go.mod
   - Rollback: `git checkout -- scripts/codereview/internal/scope/reader.go`

---

## Task 15: Create Output Writer

**Files:**
- Create: `scripts/codereview/internal/output/json.go`

**Prerequisites:**
- Task 14 completed

**Step 1: Write the output writer**

Create file `scripts/codereview/internal/output/json.go`:

```go
// Package output handles writing analysis results to files.
package output

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/LerianStudio/ring/scripts/codereview/internal/lint"
)

// Writer handles writing analysis results.
type Writer struct {
	outputDir string
}

// NewWriter creates a new output writer.
func NewWriter(outputDir string) *Writer {
	return &Writer{
		outputDir: outputDir,
	}
}

// EnsureDir creates the output directory if it doesn't exist.
func (w *Writer) EnsureDir() error {
	return os.MkdirAll(w.outputDir, 0755)
}

// WriteResult writes the analysis result to static-analysis.json.
func (w *Writer) WriteResult(result *lint.Result) error {
	return w.writeJSON("static-analysis.json", result)
}

// WriteLanguageResult writes a language-specific result file.
func (w *Writer) WriteLanguageResult(lang lint.Language, result *lint.Result) error {
	filename := fmt.Sprintf("%s-lint.json", lang)
	return w.writeJSON(filename, result)
}

// writeJSON writes data as formatted JSON to a file.
func (w *Writer) writeJSON(filename string, data interface{}) error {
	path := filepath.Join(w.outputDir, filename)

	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	if err := os.WriteFile(path, jsonData, 0644); err != nil {
		return fmt.Errorf("failed to write %s: %w", path, err)
	}

	return nil
}

// DefaultOutputDir returns the default output directory.
func DefaultOutputDir(projectDir string) string {
	return filepath.Join(projectDir, ".ring", "codereview")
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/output/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/output/json.go
git commit -m "feat(codereview): add JSON output writer for analysis results"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Import path for lint package
   - Fix: Ensure module path matches go.mod
   - Rollback: `git checkout -- scripts/codereview/internal/output/json.go`

---

## Task 16: Implement Orchestrator

**Files:**
- Create: `scripts/codereview/cmd/static-analysis/main.go`

**Prerequisites:**
- Tasks 1-15 completed

**Step 1: Write the main orchestrator**

Create file `scripts/codereview/cmd/static-analysis/main.go`:

```go
// Package main implements the static-analysis binary.
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/LerianStudio/ring/scripts/codereview/internal/lint"
	"github.com/LerianStudio/ring/scripts/codereview/internal/output"
	"github.com/LerianStudio/ring/scripts/codereview/internal/scope"
)

func main() {
	// Parse flags
	scopePath := flag.String("scope", "", "Path to scope.json (default: .ring/codereview/scope.json)")
	outputPath := flag.String("output", "", "Output directory (default: .ring/codereview/)")
	verbose := flag.Bool("v", false, "Verbose output")
	timeout := flag.Duration("timeout", 5*time.Minute, "Timeout for analysis")
	flag.Parse()

	// Determine project directory (current working directory)
	projectDir, err := os.Getwd()
	if err != nil {
		log.Fatalf("Failed to get working directory: %v", err)
	}

	// Set default paths
	if *scopePath == "" {
		*scopePath = scope.DefaultScopePath(projectDir)
	}
	if *outputPath == "" {
		*outputPath = output.DefaultOutputDir(projectDir)
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), *timeout)
	defer cancel()

	// Read scope
	if *verbose {
		log.Printf("Reading scope from: %s", *scopePath)
	}
	s, err := scope.ReadScope(*scopePath)
	if err != nil {
		log.Fatalf("Failed to read scope: %v", err)
	}

	// Get language
	lang := s.GetLanguage()
	if *verbose {
		log.Printf("Detected language: %s", lang)
	}

	// Initialize registry and register linters
	registry := lint.NewRegistry()
	registerLinters(registry)

	// Get available linters for detected language
	linters := registry.GetAvailableLinters(ctx, lang)
	if len(linters) == 0 {
		log.Printf("Warning: No linters available for language: %s", lang)
		linters = []lint.Linter{}
	}

	if *verbose {
		log.Printf("Available linters: %d", len(linters))
		for _, l := range linters {
			log.Printf("  - %s", l.Name())
		}
	}

	// Run all available linters
	aggregateResult := lint.NewResult()
	changedFiles := s.GetAllFilesMap()

	for _, linter := range linters {
		if *verbose {
			log.Printf("Running %s...", linter.Name())
		}

		// Get files/packages for this linter
		var targets []string
		if lang == lint.LanguageGo {
			// For Go, use packages
			targets = s.GetPackages("go")
		} else {
			// For TS/Python, use files
			targets = s.GetAllFiles(string(lang))
		}

		result, err := linter.Run(ctx, projectDir, targets)
		if err != nil {
			log.Printf("Warning: %s failed: %v", linter.Name(), err)
			aggregateResult.Errors = append(aggregateResult.Errors, fmt.Sprintf("%s: %v", linter.Name(), err))
			continue
		}

		// Filter to changed files only and merge
		filtered := result.FilterByFiles(changedFiles)
		aggregateResult.Merge(filtered)

		if *verbose {
			log.Printf("  %s: %d findings", linter.Name(), len(filtered.Findings))
		}
	}

	// Deduplicate findings (same file:line:message from different tools)
	deduplicateFindings(aggregateResult)

	// Ensure output directory exists
	writer := output.NewWriter(*outputPath)
	if err := writer.EnsureDir(); err != nil {
		log.Fatalf("Failed to create output directory: %v", err)
	}

	// Write results
	if err := writer.WriteResult(aggregateResult); err != nil {
		log.Fatalf("Failed to write results: %v", err)
	}

	// Write language-specific result
	if err := writer.WriteLanguageResult(lang, aggregateResult); err != nil {
		log.Fatalf("Failed to write language result: %v", err)
	}

	// Print summary
	fmt.Printf("Static analysis complete:\n")
	fmt.Printf("  Files analyzed: %d\n", len(changedFiles))
	fmt.Printf("  Critical: %d\n", aggregateResult.Summary.Critical)
	fmt.Printf("  High: %d\n", aggregateResult.Summary.High)
	fmt.Printf("  Warning: %d\n", aggregateResult.Summary.Warning)
	fmt.Printf("  Info: %d\n", aggregateResult.Summary.Info)
	fmt.Printf("  Output: %s\n", filepath.Join(*outputPath, "static-analysis.json"))

	if len(aggregateResult.Errors) > 0 {
		fmt.Printf("\nWarnings during analysis:\n")
		for _, e := range aggregateResult.Errors {
			fmt.Printf("  - %s\n", e)
		}
	}
}

// registerLinters adds all linters to the registry.
func registerLinters(r *lint.Registry) {
	// Go linters
	r.Register(lint.NewGolangciLint())
	r.Register(lint.NewStaticcheck())
	r.Register(lint.NewGosec())

	// TypeScript linters
	r.Register(lint.NewTSC())
	r.Register(lint.NewESLint())

	// Python linters
	r.Register(lint.NewRuff())
	r.Register(lint.NewMypy())
	r.Register(lint.NewPylint())
	r.Register(lint.NewBandit())
}

// deduplicateFindings removes duplicate findings based on file:line:message.
func deduplicateFindings(result *lint.Result) {
	seen := make(map[string]bool)
	var unique []lint.Finding

	// Reset summary
	result.Summary = lint.Summary{}

	for _, f := range result.Findings {
		key := fmt.Sprintf("%s:%d:%s", f.File, f.Line, f.Message)
		if !seen[key] {
			seen[key] = true
			unique = append(unique, f)

			// Update summary
			switch f.Severity {
			case lint.SeverityCritical:
				result.Summary.Critical++
			case lint.SeverityHigh:
				result.Summary.High++
			case lint.SeverityWarning:
				result.Summary.Warning++
			case lint.SeverityInfo:
				result.Summary.Info++
			}
		}
	}

	result.Findings = unique
}
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build -o bin/static-analysis ./cmd/static-analysis/`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Verify binary exists**

Run: `ls -la scripts/codereview/bin/static-analysis`

**Expected output:**
```
-rwxr-xr-x  1 ... static-analysis
```

**Step 4: Commit**

```bash
git add scripts/codereview/cmd/static-analysis/main.go
git commit -m "feat(codereview): add static-analysis orchestrator binary"
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: All import paths match module structure
   - Fix: Run `go mod tidy` to resolve dependencies
   - Rollback: `git checkout -- scripts/codereview/cmd/static-analysis/main.go`

2. **Binary not created:**
   - Check: `bin/` directory exists
   - Fix: `mkdir -p scripts/codereview/bin`

---

## Task 17: Add Unit Tests: Types

**Files:**
- Create: `scripts/codereview/internal/lint/types_test.go`

**Prerequisites:**
- Task 16 completed

**Step 1: Write tests for types**

Create file `scripts/codereview/internal/lint/types_test.go`:

```go
package lint

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewResult(t *testing.T) {
	result := NewResult()

	assert.NotNil(t, result)
	assert.Empty(t, result.Findings)
	assert.Empty(t, result.ToolVersions)
	assert.Empty(t, result.Errors)
	assert.Equal(t, 0, result.Summary.Critical)
	assert.Equal(t, 0, result.Summary.High)
	assert.Equal(t, 0, result.Summary.Warning)
	assert.Equal(t, 0, result.Summary.Info)
}

func TestResult_AddFinding(t *testing.T) {
	tests := []struct {
		name     string
		severity Severity
		wantCrit int
		wantHigh int
		wantWarn int
		wantInfo int
	}{
		{"critical", SeverityCritical, 1, 0, 0, 0},
		{"high", SeverityHigh, 0, 1, 0, 0},
		{"warning", SeverityWarning, 0, 0, 1, 0},
		{"info", SeverityInfo, 0, 0, 0, 1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NewResult()
			finding := Finding{
				Tool:     "test",
				Rule:     "TEST001",
				Severity: tt.severity,
				File:     "test.go",
				Line:     1,
				Column:   1,
				Message:  "test message",
				Category: CategoryBug,
			}

			result.AddFinding(finding)

			assert.Len(t, result.Findings, 1)
			assert.Equal(t, tt.wantCrit, result.Summary.Critical)
			assert.Equal(t, tt.wantHigh, result.Summary.High)
			assert.Equal(t, tt.wantWarn, result.Summary.Warning)
			assert.Equal(t, tt.wantInfo, result.Summary.Info)
		})
	}
}

func TestResult_Merge(t *testing.T) {
	result1 := NewResult()
	result1.ToolVersions["tool1"] = "1.0.0"
	result1.AddFinding(Finding{
		Tool: "tool1", Rule: "R001", Severity: SeverityHigh,
		File: "a.go", Line: 1, Message: "issue 1",
	})

	result2 := NewResult()
	result2.ToolVersions["tool2"] = "2.0.0"
	result2.AddFinding(Finding{
		Tool: "tool2", Rule: "R002", Severity: SeverityWarning,
		File: "b.go", Line: 2, Message: "issue 2",
	})
	result2.Errors = append(result2.Errors, "error from tool2")

	result1.Merge(result2)

	assert.Len(t, result1.Findings, 2)
	assert.Equal(t, "1.0.0", result1.ToolVersions["tool1"])
	assert.Equal(t, "2.0.0", result1.ToolVersions["tool2"])
	assert.Equal(t, 1, result1.Summary.High)
	assert.Equal(t, 1, result1.Summary.Warning)
	assert.Len(t, result1.Errors, 1)
}

func TestResult_FilterByFiles(t *testing.T) {
	result := NewResult()
	result.ToolVersions["test"] = "1.0.0"
	result.AddFinding(Finding{
		Tool: "test", Rule: "R001", Severity: SeverityHigh,
		File: "changed.go", Line: 1, Message: "in scope",
	})
	result.AddFinding(Finding{
		Tool: "test", Rule: "R002", Severity: SeverityWarning,
		File: "unchanged.go", Line: 1, Message: "out of scope",
	})
	result.Errors = append(result.Errors, "test error")

	files := map[string]bool{"changed.go": true}
	filtered := result.FilterByFiles(files)

	assert.Len(t, filtered.Findings, 1)
	assert.Equal(t, "changed.go", filtered.Findings[0].File)
	assert.Equal(t, 1, filtered.Summary.High)
	assert.Equal(t, 0, filtered.Summary.Warning)
	assert.Equal(t, "1.0.0", filtered.ToolVersions["test"])
	assert.Len(t, filtered.Errors, 1)
}
```

**Step 2: Run tests**

Run: `cd scripts/codereview && go test ./internal/lint/... -v`

**Expected output:**
```
=== RUN   TestNewResult
--- PASS: TestNewResult (0.00s)
=== RUN   TestResult_AddFinding
=== RUN   TestResult_AddFinding/critical
=== RUN   TestResult_AddFinding/high
=== RUN   TestResult_AddFinding/warning
=== RUN   TestResult_AddFinding/info
--- PASS: TestResult_AddFinding (0.00s)
    --- PASS: TestResult_AddFinding/critical (0.00s)
    --- PASS: TestResult_AddFinding/high (0.00s)
    --- PASS: TestResult_AddFinding/warning (0.00s)
    --- PASS: TestResult_AddFinding/info (0.00s)
=== RUN   TestResult_Merge
--- PASS: TestResult_Merge (0.00s)
=== RUN   TestResult_FilterByFiles
--- PASS: TestResult_FilterByFiles (0.00s)
PASS
ok      github.com/LerianStudio/ring/scripts/codereview/internal/lint
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/types_test.go
git commit -m "test(codereview): add unit tests for lint types"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Test assertions match implementation
   - Fix: Adjust test expectations or fix implementation
   - Rollback: `git checkout -- scripts/codereview/internal/lint/types_test.go`

---

## Task 18: Add Unit Tests: golangci Parser

**Files:**
- Create: `scripts/codereview/internal/lint/golangci_test.go`

**Prerequisites:**
- Task 17 completed

**Step 1: Write parser tests**

Create file `scripts/codereview/internal/lint/golangci_test.go`:

```go
package lint

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestMapGolangciSeverity(t *testing.T) {
	tests := []struct {
		input    string
		expected Severity
	}{
		{"error", SeverityHigh},
		{"ERROR", SeverityHigh},
		{"warning", SeverityWarning},
		{"WARNING", SeverityWarning},
		{"info", SeverityInfo},
		{"", SeverityInfo},
		{"unknown", SeverityInfo},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := mapGolangciSeverity(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMapGolangciCategory(t *testing.T) {
	tests := []struct {
		linter   string
		expected Category
	}{
		{"gosec", CategorySecurity},
		{"gocritic", CategorySecurity},
		{"staticcheck", CategoryBug},
		{"typecheck", CategoryBug},
		{"gofmt", CategoryStyle},
		{"goimports", CategoryStyle},
		{"govet", CategoryStyle},
		{"ineffassign", CategoryUnused},
		{"deadcode", CategoryUnused},
		{"unused", CategoryUnused},
		{"varcheck", CategoryUnused},
		{"gocyclo", CategoryComplexity},
		{"gocognit", CategoryComplexity},
		{"depguard", CategoryDeprecation},
		{"unknown", CategoryOther},
	}

	for _, tt := range tests {
		t.Run(tt.linter, func(t *testing.T) {
			result := mapGolangciCategory(tt.linter)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestNormalizeFilePath(t *testing.T) {
	tests := []struct {
		name       string
		projectDir string
		filePath   string
		expected   string
	}{
		{
			name:       "relative path unchanged",
			projectDir: "/project",
			filePath:   "internal/handler.go",
			expected:   "internal/handler.go",
		},
		{
			name:       "absolute path converted",
			projectDir: "/project",
			filePath:   "/project/internal/handler.go",
			expected:   "internal/handler.go",
		},
		{
			name:       "outside project stays absolute",
			projectDir: "/project",
			filePath:   "/other/file.go",
			expected:   "/other/file.go",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := normalizeFilePath(tt.projectDir, tt.filePath)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGolangciLint_Name(t *testing.T) {
	g := NewGolangciLint()
	assert.Equal(t, "golangci-lint", g.Name())
}

func TestGolangciLint_Language(t *testing.T) {
	g := NewGolangciLint()
	assert.Equal(t, LanguageGo, g.Language())
}
```

**Step 2: Run tests**

Run: `cd scripts/codereview && go test ./internal/lint/... -v -run Golangci`

**Expected output:**
```
=== RUN   TestMapGolangciSeverity
...
--- PASS: TestMapGolangciSeverity (0.00s)
=== RUN   TestMapGolangciCategory
...
--- PASS: TestMapGolangciCategory (0.00s)
=== RUN   TestNormalizeFilePath
...
--- PASS: TestNormalizeFilePath (0.00s)
=== RUN   TestGolangciLint_Name
--- PASS: TestGolangciLint_Name (0.00s)
=== RUN   TestGolangciLint_Language
--- PASS: TestGolangciLint_Language (0.00s)
PASS
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/golangci_test.go
git commit -m "test(codereview): add unit tests for golangci-lint parser"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Test assertions match implementation
   - Fix: Verify mapping functions return expected values
   - Rollback: `git checkout -- scripts/codereview/internal/lint/golangci_test.go`

---

## Task 19: Add Unit Tests: eslint Parser

**Files:**
- Create: `scripts/codereview/internal/lint/eslint_test.go`

**Prerequisites:**
- Task 18 completed

**Step 1: Write parser tests**

Create file `scripts/codereview/internal/lint/eslint_test.go`:

```go
package lint

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestMapESLintSeverity(t *testing.T) {
	tests := []struct {
		input    int
		expected Severity
	}{
		{2, SeverityHigh},
		{1, SeverityWarning},
		{0, SeverityInfo},
		{99, SeverityInfo},
	}

	for _, tt := range tests {
		t.Run("", func(t *testing.T) {
			result := mapESLintSeverity(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMapESLintCategory(t *testing.T) {
	tests := []struct {
		ruleID   string
		expected Category
	}{
		{"@typescript-eslint/no-unused-vars", CategoryType},
		{"@typescript-eslint/explicit-function-return-type", CategoryType},
		{"security/detect-object-injection", CategorySecurity},
		{"no-unused-vars", CategoryUnused},
		{"no-unused-expressions", CategoryUnused},
		{"import/order", CategoryStyle},
		{"import/no-unresolved", CategoryStyle},
		{"react/jsx-uses-react", CategoryStyle},
		{"react-hooks/rules-of-hooks", CategoryStyle},
		{"parse-error", CategoryBug},
		{"semi", CategoryStyle},
		{"unknown-rule", CategoryStyle},
	}

	for _, tt := range tests {
		t.Run(tt.ruleID, func(t *testing.T) {
			result := mapESLintCategory(tt.ruleID)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestESLint_Name(t *testing.T) {
	e := NewESLint()
	assert.Equal(t, "eslint", e.Name())
}

func TestESLint_Language(t *testing.T) {
	e := NewESLint()
	assert.Equal(t, LanguageTypeScript, e.Language())
}
```

**Step 2: Run tests**

Run: `cd scripts/codereview && go test ./internal/lint/... -v -run ESLint`

**Expected output:**
```
=== RUN   TestMapESLintSeverity
--- PASS: TestMapESLintSeverity (0.00s)
=== RUN   TestMapESLintCategory
...
--- PASS: TestMapESLintCategory (0.00s)
=== RUN   TestESLint_Name
--- PASS: TestESLint_Name (0.00s)
=== RUN   TestESLint_Language
--- PASS: TestESLint_Language (0.00s)
PASS
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/eslint_test.go
git commit -m "test(codereview): add unit tests for ESLint parser"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Test assertions match implementation
   - Fix: Verify mapping functions
   - Rollback: `git checkout -- scripts/codereview/internal/lint/eslint_test.go`

---

## Task 20: Add Unit Tests: ruff Parser

**Files:**
- Create: `scripts/codereview/internal/lint/ruff_test.go`

**Prerequisites:**
- Task 19 completed

**Step 1: Write parser tests**

Create file `scripts/codereview/internal/lint/ruff_test.go`:

```go
package lint

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestMapRuffSeverity(t *testing.T) {
	tests := []struct {
		code     string
		expected Severity
	}{
		{"S101", SeverityHigh},    // Security
		{"S501", SeverityHigh},    // Security
		{"E501", SeverityWarning}, // Errors
		{"F401", SeverityWarning}, // Pyflakes
		{"W503", SeverityWarning}, // Warnings
		{"B001", SeverityWarning}, // Bugbear
		{"I001", SeverityInfo},    // Import sorting
		{"D100", SeverityInfo},    // Docstring
		{"N801", SeverityInfo},    // Naming
	}

	for _, tt := range tests {
		t.Run(tt.code, func(t *testing.T) {
			result := mapRuffSeverity(tt.code)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMapRuffCategory(t *testing.T) {
	tests := []struct {
		code     string
		expected Category
	}{
		{"S101", CategorySecurity},
		{"S501", CategorySecurity},
		{"F401", CategoryBug},
		{"F841", CategoryBug},
		{"E501", CategoryStyle},
		{"E302", CategoryStyle},
		{"W503", CategoryStyle},
		{"W291", CategoryStyle},
		{"B001", CategoryBug},
		{"B007", CategoryBug},
		{"I001", CategoryStyle},
		{"UP001", CategoryDeprecation},
		{"UP035", CategoryDeprecation},
		{"C901", CategoryComplexity},
		{"D100", CategoryOther},
	}

	for _, tt := range tests {
		t.Run(tt.code, func(t *testing.T) {
			result := mapRuffCategory(tt.code)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestRuff_Name(t *testing.T) {
	r := NewRuff()
	assert.Equal(t, "ruff", r.Name())
}

func TestRuff_Language(t *testing.T) {
	r := NewRuff()
	assert.Equal(t, LanguagePython, r.Language())
}
```

**Step 2: Run tests**

Run: `cd scripts/codereview && go test ./internal/lint/... -v -run Ruff`

**Expected output:**
```
=== RUN   TestMapRuffSeverity
...
--- PASS: TestMapRuffSeverity (0.00s)
=== RUN   TestMapRuffCategory
...
--- PASS: TestMapRuffCategory (0.00s)
=== RUN   TestRuff_Name
--- PASS: TestRuff_Name (0.00s)
=== RUN   TestRuff_Language
--- PASS: TestRuff_Language (0.00s)
PASS
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/lint/ruff_test.go
git commit -m "test(codereview): add unit tests for ruff parser"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Test assertions match implementation
   - Fix: Verify mapping functions
   - Rollback: `git checkout -- scripts/codereview/internal/lint/ruff_test.go`

---

## Task 21: Integration Test

**Files:**
- Create: `scripts/codereview/testdata/scope.json` (test fixture)
- Create: `scripts/codereview/integration_test.go`

**Prerequisites:**
- Task 20 completed

**Step 1: Create test fixture directory**

```bash
mkdir -p scripts/codereview/testdata
```

**Step 2: Create test scope.json**

Create file `scripts/codereview/testdata/scope.json`:

```json
{
  "base_ref": "main",
  "head_ref": "HEAD",
  "language": "go",
  "files": {
    "go": {
      "modified": ["internal/handler/user.go"],
      "added": ["internal/service/notification.go"],
      "deleted": []
    }
  },
  "stats": {
    "total_files": 2,
    "total_additions": 100,
    "total_deletions": 10
  },
  "packages_affected": {
    "go": ["./internal/handler", "./internal/service"]
  }
}
```

**Step 3: Create integration test**

Create file `scripts/codereview/integration_test.go`:

```go
//go:build integration

package main

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/LerianStudio/ring/scripts/codereview/internal/lint"
	"github.com/LerianStudio/ring/scripts/codereview/internal/scope"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestScopeReader(t *testing.T) {
	scopePath := filepath.Join("testdata", "scope.json")
	s, err := scope.ReadScope(scopePath)

	require.NoError(t, err)
	assert.Equal(t, "main", s.BaseRef)
	assert.Equal(t, "HEAD", s.HeadRef)
	assert.Equal(t, "go", s.Language)
	assert.Equal(t, lint.LanguageGo, s.GetLanguage())

	files := s.GetAllFiles("go")
	assert.Len(t, files, 2)
	assert.Contains(t, files, "internal/handler/user.go")
	assert.Contains(t, files, "internal/service/notification.go")

	fileMap := s.GetAllFilesMap()
	assert.True(t, fileMap["internal/handler/user.go"])
	assert.True(t, fileMap["internal/service/notification.go"])
	assert.False(t, fileMap["nonexistent.go"])

	packages := s.GetPackages("go")
	assert.Len(t, packages, 2)
}

func TestLinterRegistry(t *testing.T) {
	ctx := context.Background()
	registry := lint.NewRegistry()

	// Register all linters
	registry.Register(lint.NewGolangciLint())
	registry.Register(lint.NewStaticcheck())
	registry.Register(lint.NewGosec())
	registry.Register(lint.NewTSC())
	registry.Register(lint.NewESLint())
	registry.Register(lint.NewRuff())
	registry.Register(lint.NewMypy())
	registry.Register(lint.NewPylint())
	registry.Register(lint.NewBandit())

	// Check Go linters registered
	goLinters := registry.GetLinters(lint.LanguageGo)
	assert.Len(t, goLinters, 3)

	// Check TS linters registered
	tsLinters := registry.GetLinters(lint.LanguageTypeScript)
	assert.Len(t, tsLinters, 2)

	// Check Python linters registered
	pyLinters := registry.GetLinters(lint.LanguagePython)
	assert.Len(t, pyLinters, 4)

	// Available linters depend on what's installed
	availableGo := registry.GetAvailableLinters(ctx, lint.LanguageGo)
	t.Logf("Available Go linters: %d", len(availableGo))
	for _, l := range availableGo {
		t.Logf("  - %s", l.Name())
	}
}

func TestResultAggregation(t *testing.T) {
	result := lint.NewResult()

	// Simulate findings from multiple tools
	result.AddFinding(lint.Finding{
		Tool:     "golangci-lint",
		Rule:     "SA1019",
		Severity: lint.SeverityWarning,
		File:     "internal/handler/user.go",
		Line:     45,
		Column:   12,
		Message:  "deprecated API",
		Category: lint.CategoryDeprecation,
	})

	result.AddFinding(lint.Finding{
		Tool:     "gosec",
		Rule:     "G401",
		Severity: lint.SeverityHigh,
		File:     "internal/handler/user.go",
		Line:     67,
		Column:   8,
		Message:  "weak crypto",
		Category: lint.CategorySecurity,
	})

	// Verify aggregation
	assert.Len(t, result.Findings, 2)
	assert.Equal(t, 0, result.Summary.Critical)
	assert.Equal(t, 1, result.Summary.High)
	assert.Equal(t, 1, result.Summary.Warning)
	assert.Equal(t, 0, result.Summary.Info)

	// Test filtering
	fileMap := map[string]bool{
		"internal/handler/user.go": true,
	}
	filtered := result.FilterByFiles(fileMap)
	assert.Len(t, filtered.Findings, 2)

	// Filter to non-existent file
	fileMap2 := map[string]bool{
		"other.go": true,
	}
	filtered2 := result.FilterByFiles(fileMap2)
	assert.Len(t, filtered2.Findings, 0)
}

func TestOutputWriterCreatesDirectory(t *testing.T) {
	tmpDir := t.TempDir()
	outputDir := filepath.Join(tmpDir, ".ring", "codereview")

	// Verify directory doesn't exist
	_, err := os.Stat(outputDir)
	assert.True(t, os.IsNotExist(err))

	// Create writer and ensure directory
	// Note: We'd need to import output package, skipping for unit test
}
```

**Step 4: Run integration tests**

Run: `cd scripts/codereview && go test -tags=integration -v`

**Expected output:**
```
=== RUN   TestScopeReader
--- PASS: TestScopeReader (0.00s)
=== RUN   TestLinterRegistry
    integration_test.go:XX: Available Go linters: X
    integration_test.go:XX:   - golangci-lint (if installed)
--- PASS: TestLinterRegistry (0.00s)
=== RUN   TestResultAggregation
--- PASS: TestResultAggregation (0.00s)
PASS
```

**Step 5: Commit**

```bash
git add scripts/codereview/testdata/scope.json scripts/codereview/integration_test.go
git commit -m "test(codereview): add integration tests for static analysis"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Test file paths and JSON fixture validity
   - Fix: Verify testdata directory structure
   - Rollback: `rm -rf scripts/codereview/testdata scripts/codereview/integration_test.go`

---

## Task 22: Code Review

### Task 22: Run Code Review

1. **Dispatch all 5 reviewers in parallel:**
   - REQUIRED SUB-SKILL: Use requesting-code-review
   - All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer, test-reviewer, nil-safety-reviewer)
   - Wait for all to complete

2. **Handle findings by severity (MANDATORY):**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 5 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`
- This tracks tech debt for future resolution

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on [date], severity: Cosmetic)`
- Low-priority improvements tracked inline

3. **Proceed only when:**
   - Zero Critical/High/Medium issues remain
   - All Low issues have TODO(review): comments added
   - All Cosmetic issues have FIXME(nitpick): comments added

---

## Task 23: Build and Verify

**Files:**
- Build: `scripts/codereview/bin/static-analysis`

**Prerequisites:**
- Task 22 completed (code review passed)

**Step 1: Build final binary**

Run: `cd scripts/codereview && go build -o bin/static-analysis ./cmd/static-analysis/`

**Expected output:**
```
(no output - successful build)
```

**Step 2: Verify binary runs**

Run: `scripts/codereview/bin/static-analysis --help`

**Expected output:**
```
Usage of static-analysis:
  -output string
        Output directory (default: .ring/codereview/)
  -scope string
        Path to scope.json (default: .ring/codereview/scope.json)
  -timeout duration
        Timeout for analysis (default 5m0s)
  -v    Verbose output
```

**Step 3: Run all unit tests**

Run: `cd scripts/codereview && go test ./... -v`

**Expected output:**
```
=== RUN   TestNewResult
--- PASS: TestNewResult (0.00s)
...
PASS
ok      github.com/LerianStudio/ring/scripts/codereview/internal/lint   X.XXXs
ok      github.com/LerianStudio/ring/scripts/codereview/internal/scope  X.XXXs
ok      github.com/LerianStudio/ring/scripts/codereview/internal/output X.XXXs
```

**Step 4: Final commit**

```bash
git add scripts/codereview/bin/.gitkeep
git commit -m "feat(codereview): complete Phase 1 static analysis implementation"
```

**Step 5: Tag milestone**

```bash
git tag -a codereview-phase1-complete -m "Phase 1: Static Analysis implementation complete"
```

**If Task Fails:**

1. **Build fails:**
   - Check: `go mod tidy` to resolve dependencies
   - Fix: Address any compilation errors from previous tasks
   - Rollback: Review task-by-task to find issue

2. **Tests fail:**
   - Check: Test output for specific failures
   - Fix: Address test failures before proceeding
   - Don't proceed until all tests pass

---

## Summary

This plan implements Phase 1: Static Analysis for the Codereview Enhancement feature. Upon completion:

**Deliverables:**
- `scripts/codereview/bin/static-analysis` - Main orchestrator binary
- `internal/lint/` - 9 linter wrappers (3 Go, 2 TS, 4 Python)
- `internal/scope/` - Scope reader for Phase 0 integration
- `internal/output/` - JSON output writer
- Unit tests for all parsers and types

**CLI Usage:**
```bash
# Run with defaults (reads .ring/codereview/scope.json)
static-analysis

# Run with custom paths
static-analysis --scope=/path/to/scope.json --output=/path/to/output/

# Verbose mode
static-analysis -v
```

**Output Files:**
- `.ring/codereview/static-analysis.json` - Aggregate results
- `.ring/codereview/{lang}-lint.json` - Language-specific results

**Next Phase:** Phase 2 (AST Extraction) will build on this by adding semantic diff capabilities.
