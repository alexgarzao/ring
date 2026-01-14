# Phase 5: Context Compilation Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans to implement this plan task-by-task.

**Goal:** Implement the context compilation phase that aggregates all analysis outputs (Phases 0-4) into reviewer-specific markdown files, and create the main orchestrator that runs all phases in sequence.

**Architecture:** Two Go binaries - `compile-context` reads JSON outputs from all phases and generates reviewer-specific markdown context files; `run-all` orchestrates the entire pipeline from scope detection through context compilation.

**Tech Stack:**
- Go 1.22+ (binary implementation)
- Template-based markdown generation
- JSON parsing for phase outputs
- No external dependencies (stdlib only)

**Global Prerequisites:**
- Environment: macOS or Linux, Go 1.22+
- Tools: git (for repo operations)
- Access: None required (all tools are local)
- State: Clean working tree on feature branch
- Previous phases: Phase 0-4 binaries must be implemented

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
go version          # Expected: go version go1.22+ or higher
git status          # Expected: clean working tree
ls scripts/ring:codereview/go.mod  # Expected: file exists (from Phase 0/1)
ls scripts/ring:codereview/internal/ring:lint/  # Expected: linter wrappers exist (from Phase 1)
```

## Historical Precedent

**Query:** "ring:codereview context compilation reviewer analysis"
**Index Status:** Populated (no direct matches)

### Successful Patterns to Reference
- Phase 0/1 plans established Go binary structure in `scripts/ring:codereview/`
- Internal packages pattern: `internal/{domain}/` for shared code
- JSON output/input pattern for inter-phase communication

### Failure Patterns to AVOID
- None found - this is a new feature area

### Related Past Plans
- `ring:codereview-enhancement-macro-plan.md`: Parent macro plan defining context file templates
- `2026-01-13-ring:codereview-phase0-scope-detector.md`: Established Go module structure
- `2026-01-13-ring:codereview-phase1-static-analysis.md`: Established lint output formats

---

## File Structure Overview

```
scripts/ring:codereview/
├── cmd/
│   ├── compile-context/          # Phase 5 binary
│   │   └── main.go
│   └── run-all/                  # Main orchestrator binary
│       └── main.go
├── internal/
│   └── context/                  # Context compilation package
│       ├── compiler.go           # Main aggregation logic
│       ├── compiler_test.go      # Tests
│       ├── templates.go          # Markdown templates
│       ├── templates_test.go     # Template tests
│       ├── reviewer_mappings.go  # Data-to-reviewer mappings
│       └── reviewer_mappings_test.go
└── Makefile                      # Updated with new targets
```

---

## Task Overview

| # | Task | Description | Time |
|---|------|-------------|------|
| 1 | Create context package structure | Set up `internal/context/` directory | 2 min |
| 2 | Define input types | Create structs for reading phase outputs | 5 min |
| 3 | Implement reviewer mappings | Map data sources to reviewers | 5 min |
| 4 | Write templates for ring:code-reviewer | Markdown template for code quality context | 5 min |
| 5 | Write templates for ring:security-reviewer | Markdown template for security context | 5 min |
| 6 | Write templates for ring:business-logic-reviewer | Markdown template for business logic context | 4 min |
| 7 | Write templates for ring:test-reviewer | Markdown template for testing context | 4 min |
| 8 | Write templates for ring:nil-safety-reviewer | Markdown template for nil safety context | 4 min |
| 9 | Implement compiler core | Main aggregation logic | 5 min |
| 10 | Implement file reader | Read and parse phase outputs | 5 min |
| 11 | Implement context writer | Write reviewer context files | 4 min |
| 12 | Implement compile-context CLI | Binary entry point | 5 min |
| 13 | Implement run-all orchestrator | Main pipeline orchestrator | 5 min |
| 14 | Add unit tests: reviewer mappings | Test data mapping logic | 4 min |
| 15 | Add unit tests: templates | Test template rendering | 4 min |
| 16 | Add unit tests: compiler | Test aggregation logic | 5 min |
| 17 | Integration test | End-to-end with sample data | 5 min |
| 18 | Update Makefile | Add build targets | 3 min |
| 19 | Code Review | Run code review checkpoint | 5 min |
| 20 | Build and verify | Build binaries and verify | 3 min |

---

## Task 1: Create Context Package Structure

**Files:**
- Create: `scripts/ring:codereview/internal/context/`

**Prerequisites:**
- Go module exists at `scripts/ring:codereview/go.mod`

**Step 1: Create directory**

```bash
mkdir -p scripts/ring:codereview/internal/context
```

**Step 2: Verify structure**

Run: `ls -la scripts/ring:codereview/internal/`

**Expected output:**
```
total XX
drwxr-xr-x  ... .
drwxr-xr-x  ... ..
drwxr-xr-x  ... context
drwxr-xr-x  ... git
drwxr-xr-x  ... lint
drwxr-xr-x  ... output
drwxr-xr-x  ... scope
```

**If Task Fails:**

1. **Directory creation fails:**
   - Check: `ls scripts/ring:codereview/internal/` (parent exists?)
   - Fix: Verify Phase 0 was completed
   - Rollback: N/A (no files created)

---

## Task 2: Define Input Types

**Files:**
- Create: `scripts/ring:codereview/internal/context/types.go`

**Prerequisites:**
- Task 1 completed

**Step 1: Write the types file**

Create file `scripts/ring:codereview/internal/context/types.go`:

```go
// Package context provides context compilation for code review.
// It aggregates outputs from all analysis phases and generates
// reviewer-specific context files.
package context

// PhaseOutputs holds all the outputs from analysis phases.
type PhaseOutputs struct {
	Scope           *ScopeData           `json:"scope"`
	StaticAnalysis  *StaticAnalysisData  `json:"static_analysis"`
	AST             *ASTData             `json:"ast"`
	CallGraph       *CallGraphData       `json:"call_graph"`
	DataFlow        *DataFlowData        `json:"data_flow"`
	Errors          []string             `json:"errors,omitempty"`
}

// ScopeData represents Phase 0 output (scope.json).
type ScopeData struct {
	BaseRef          string   `json:"base_ref"`
	HeadRef          string   `json:"head_ref"`
	Language         string   `json:"language"`
	ModifiedFiles    []string `json:"modified"`
	AddedFiles       []string `json:"added"`
	DeletedFiles     []string `json:"deleted"`
	TotalFiles       int      `json:"total_files"`
	TotalAdditions   int      `json:"total_additions"`
	TotalDeletions   int      `json:"total_deletions"`
	PackagesAffected []string `json:"packages_affected"`
}

// StaticAnalysisData represents Phase 1 output (static-analysis.json).
type StaticAnalysisData struct {
	ToolVersions map[string]string `json:"tool_versions"`
	Findings     []Finding         `json:"findings"`
	Summary      FindingSummary    `json:"summary"`
	Errors       []string          `json:"errors,omitempty"`
}

// Finding represents a single lint/analysis finding.
type Finding struct {
	Tool       string `json:"tool"`
	Rule       string `json:"rule"`
	Severity   string `json:"severity"`
	File       string `json:"file"`
	Line       int    `json:"line"`
	Column     int    `json:"column"`
	Message    string `json:"message"`
	Suggestion string `json:"suggestion,omitempty"`
	Category   string `json:"category"`
}

// FindingSummary holds counts by severity.
type FindingSummary struct {
	Critical int `json:"critical"`
	High     int `json:"high"`
	Warning  int `json:"warning"`
	Info     int `json:"info"`
}

// ASTData represents Phase 2 output ({lang}-ast.json).
type ASTData struct {
	Functions     FunctionChanges     `json:"functions"`
	Types         TypeChanges         `json:"types"`
	Interfaces    InterfaceChanges    `json:"interfaces,omitempty"`
	Classes       ClassChanges        `json:"classes,omitempty"`
	Imports       ImportChanges       `json:"imports"`
	ErrorHandling ErrorHandlingData   `json:"error_handling,omitempty"`
}

// FunctionChanges holds function-level changes.
type FunctionChanges struct {
	Modified []FunctionDiff `json:"modified"`
	Added    []FunctionInfo `json:"added"`
	Deleted  []FunctionInfo `json:"deleted"`
}

// FunctionDiff represents a modified function.
type FunctionDiff struct {
	Name      string       `json:"name"`
	File      string       `json:"file"`
	Package   string       `json:"package,omitempty"`
	Module    string       `json:"module,omitempty"`
	Receiver  string       `json:"receiver,omitempty"`
	Before    FunctionInfo `json:"before"`
	After     FunctionInfo `json:"after"`
	Changes   []string     `json:"changes"`
}

// FunctionInfo holds function details.
type FunctionInfo struct {
	Name      string      `json:"name,omitempty"`
	Signature string      `json:"signature"`
	File      string      `json:"file,omitempty"`
	Package   string      `json:"package,omitempty"`
	LineStart int         `json:"line_start"`
	LineEnd   int         `json:"line_end"`
	Params    []ParamInfo `json:"params,omitempty"`
	Returns   []TypeInfo  `json:"returns,omitempty"`
}

// ParamInfo holds parameter details.
type ParamInfo struct {
	Name    string `json:"name"`
	Type    string `json:"type"`
	Default string `json:"default,omitempty"`
}

// TypeInfo holds type information.
type TypeInfo struct {
	Type string `json:"type"`
}

// TypeChanges holds struct/type changes.
type TypeChanges struct {
	Modified []TypeDiff `json:"modified"`
	Added    []TypeInfo `json:"added"`
	Deleted  []TypeInfo `json:"deleted"`
}

// TypeDiff represents a modified type.
type TypeDiff struct {
	Name    string     `json:"name"`
	Kind    string     `json:"kind"`
	File    string     `json:"file"`
	Before  FieldsData `json:"before"`
	After   FieldsData `json:"after"`
	Changes []string   `json:"changes"`
}

// FieldsData holds struct field information.
type FieldsData struct {
	Fields []FieldInfo `json:"fields"`
}

// FieldInfo represents a struct field.
type FieldInfo struct {
	Name string `json:"name"`
	Type string `json:"type"`
	Tags string `json:"tags,omitempty"`
}

// InterfaceChanges holds interface changes (Go/TS).
type InterfaceChanges struct {
	Modified []InterfaceDiff `json:"modified"`
	Added    []InterfaceInfo `json:"added"`
	Deleted  []InterfaceInfo `json:"deleted"`
}

// InterfaceDiff represents a modified interface.
type InterfaceDiff struct {
	Name    string        `json:"name"`
	File    string        `json:"file"`
	Before  InterfaceInfo `json:"before"`
	After   InterfaceInfo `json:"after"`
	Changes []string      `json:"changes"`
}

// InterfaceInfo holds interface details.
type InterfaceInfo struct {
	Name    string   `json:"name,omitempty"`
	Methods []string `json:"methods"`
}

// ClassChanges holds class changes (TS/Python).
type ClassChanges struct {
	Modified []ClassDiff `json:"modified"`
	Added    []ClassInfo `json:"added"`
	Deleted  []ClassInfo `json:"deleted"`
}

// ClassDiff represents a modified class.
type ClassDiff struct {
	Name    string    `json:"name"`
	File    string    `json:"file"`
	Before  ClassInfo `json:"before"`
	After   ClassInfo `json:"after"`
	Changes []string  `json:"changes"`
}

// ClassInfo holds class details.
type ClassInfo struct {
	Name       string   `json:"name,omitempty"`
	Methods    []string `json:"methods"`
	Attributes []string `json:"attributes,omitempty"`
}

// ImportChanges holds import changes.
type ImportChanges struct {
	Added   []ImportInfo `json:"added"`
	Removed []ImportInfo `json:"removed"`
}

// ImportInfo represents an import statement.
type ImportInfo struct {
	File   string   `json:"file"`
	Path   string   `json:"path,omitempty"`
	Module string   `json:"module,omitempty"`
	Names  []string `json:"names,omitempty"`
}

// ErrorHandlingData holds error handling changes (Go).
type ErrorHandlingData struct {
	NewErrorReturns     []ErrorReturn `json:"new_error_returns"`
	RemovedErrorChecks  []ErrorCheck  `json:"removed_error_checks"`
}

// ErrorReturn represents a new error return path.
type ErrorReturn struct {
	Function  string `json:"function"`
	File      string `json:"file"`
	Line      int    `json:"line"`
	ErrorType string `json:"error_type"`
	Message   string `json:"message"`
}

// ErrorCheck represents a removed error check.
type ErrorCheck struct {
	Function string `json:"function"`
	File     string `json:"file"`
	Line     int    `json:"line"`
}

// CallGraphData represents Phase 3 output ({lang}-calls.json).
type CallGraphData struct {
	ModifiedFunctions []FunctionCallGraph `json:"modified_functions"`
	ImpactAnalysis    ImpactSummary       `json:"impact_analysis"`
}

// FunctionCallGraph holds call graph data for a function.
type FunctionCallGraph struct {
	Function     string         `json:"function"`
	File         string         `json:"file"`
	Callers      []CallSite     `json:"callers"`
	Callees      []CallSite     `json:"callees"`
	TestCoverage []TestCoverage `json:"test_coverage"`
}

// CallSite represents a call site.
type CallSite struct {
	Function string `json:"function"`
	File     string `json:"file"`
	Line     int    `json:"line"`
	CallSite string `json:"call_site,omitempty"`
}

// TestCoverage represents test coverage for a function.
type TestCoverage struct {
	TestFunction string `json:"test_function"`
	File         string `json:"file"`
	Line         int    `json:"line"`
}

// ImpactSummary holds impact analysis summary.
type ImpactSummary struct {
	DirectCallers     int      `json:"direct_callers"`
	TransitiveCallers int      `json:"transitive_callers"`
	AffectedTests     int      `json:"affected_tests"`
	AffectedPackages  []string `json:"affected_packages,omitempty"`
	AffectedModules   []string `json:"affected_modules,omitempty"`
}

// DataFlowData represents Phase 4 output ({lang}-flow.json).
type DataFlowData struct {
	Flows      []DataFlow   `json:"flows"`
	NilSources []NilSource  `json:"nil_sources,omitempty"`
	Summary    FlowSummary  `json:"summary"`
}

// DataFlow represents a data flow path.
type DataFlow struct {
	ID        string     `json:"id"`
	Source    FlowSource `json:"source"`
	Path      []FlowStep `json:"path"`
	Sink      FlowSink   `json:"sink"`
	Sanitized bool       `json:"sanitized"`
	Risk      string     `json:"risk"`
	Notes     string     `json:"notes,omitempty"`
}

// FlowSource represents where data enters.
type FlowSource struct {
	Type       string `json:"type"`
	Subtype    string `json:"subtype,omitempty"`
	Framework  string `json:"framework,omitempty"`
	Variable   string `json:"variable"`
	File       string `json:"file"`
	Line       int    `json:"line"`
	Expression string `json:"expression"`
}

// FlowStep represents a step in data flow.
type FlowStep struct {
	Step          int    `json:"step"`
	File          string `json:"file"`
	Line          int    `json:"line"`
	Expression    string `json:"expression"`
	Operation     string `json:"operation"`
	SanitizerType string `json:"sanitizer_type,omitempty"`
}

// FlowSink represents where data exits.
type FlowSink struct {
	Type       string `json:"type"`
	Subtype    string `json:"subtype,omitempty"`
	File       string `json:"file"`
	Line       int    `json:"line"`
	Expression string `json:"expression"`
}

// NilSource represents a potential nil source.
type NilSource struct {
	Variable        string `json:"variable"`
	File            string `json:"file"`
	Line            int    `json:"line"`
	Expression      string `json:"expression"`
	Checked         bool   `json:"checked"`
	CheckLine       int    `json:"check_line,omitempty"`
	CheckExpression string `json:"check_expression,omitempty"`
	Risk            string `json:"risk,omitempty"`
	Notes           string `json:"notes,omitempty"`
}

// FlowSummary holds data flow summary.
type FlowSummary struct {
	TotalFlows       int `json:"total_flows"`
	SanitizedFlows   int `json:"sanitized_flows"`
	UnsanitizedFlows int `json:"unsanitized_flows"`
	HighRisk         int `json:"high_risk"`
	MediumRisk       int `json:"medium_risk"`
	LowRisk          int `json:"low_risk"`
	NilRisks         int `json:"nil_risks,omitempty"`
	NoneRisks        int `json:"none_risks,omitempty"`
}

// ReviewerContext holds the compiled context for a specific reviewer.
type ReviewerContext struct {
	ReviewerName string
	Title        string
	Content      string
}
```

**Step 2: Verify compilation**

Run: `cd scripts/ring:codereview && go build ./internal/context/... && cd ../..`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/internal/context/types.go
git commit -m "feat(ring:codereview): add input types for context compilation

Phase 5 types for reading outputs from all analysis phases (0-4).
Includes structures for scope, static analysis, AST, call graph,
and data flow data."
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Error message for syntax issues
   - Fix: Correct JSON tags or type definitions
   - Rollback: `rm scripts/ring:codereview/internal/context/types.go`

---

## Task 3: Implement Reviewer Mappings

**Files:**
- Create: `scripts/ring:codereview/internal/context/reviewer_mappings.go`

**Prerequisites:**
- Task 2 completed

**Step 1: Write the failing test**

Create file `scripts/ring:codereview/internal/context/reviewer_mappings_test.go`:

```go
package context

import (
	"testing"
)

func TestReviewerNames(t *testing.T) {
	expected := []string{
		"ring:code-reviewer",
		"ring:security-reviewer",
		"ring:business-logic-reviewer",
		"ring:test-reviewer",
		"ring:nil-safety-reviewer",
	}

	names := GetReviewerNames()
	if len(names) != len(expected) {
		t.Errorf("GetReviewerNames() returned %d names, want %d", len(names), len(expected))
	}

	for i, name := range expected {
		if names[i] != name {
			t.Errorf("GetReviewerNames()[%d] = %q, want %q", i, names[i], name)
		}
	}
}

func TestGetReviewerDataSources(t *testing.T) {
	tests := []struct {
		reviewer string
		wantLen  int
	}{
		{"ring:code-reviewer", 2},      // static-analysis, semantic-diff
		{"ring:security-reviewer", 2},  // static-analysis (security), security-summary
		{"ring:business-logic-reviewer", 2}, // semantic-diff, impact-summary
		{"ring:test-reviewer", 1},      // impact-summary (test coverage)
		{"ring:nil-safety-reviewer", 1}, // data-flow (nil_sources)
	}

	for _, tt := range tests {
		t.Run(tt.reviewer, func(t *testing.T) {
			sources := GetReviewerDataSources(tt.reviewer)
			if len(sources) != tt.wantLen {
				t.Errorf("GetReviewerDataSources(%q) returned %d sources, want %d",
					tt.reviewer, len(sources), tt.wantLen)
			}
		})
	}
}

func TestFilterFindingsByCategory(t *testing.T) {
	findings := []Finding{
		{Category: "security", Severity: "high", Message: "SQL injection"},
		{Category: "style", Severity: "info", Message: "line too long"},
		{Category: "bug", Severity: "warning", Message: "unused var"},
		{Category: "security", Severity: "warning", Message: "weak hash"},
	}

	securityFindings := FilterFindingsByCategory(findings, "security")
	if len(securityFindings) != 2 {
		t.Errorf("FilterFindingsByCategory(security) returned %d, want 2", len(securityFindings))
	}

	styleFindings := FilterFindingsByCategory(findings, "style")
	if len(styleFindings) != 1 {
		t.Errorf("FilterFindingsByCategory(style) returned %d, want 1", len(styleFindings))
	}
}

func TestFilterFindingsBySeverity(t *testing.T) {
	findings := []Finding{
		{Severity: "critical", Message: "crash"},
		{Severity: "high", Message: "security"},
		{Severity: "warning", Message: "style"},
		{Severity: "info", Message: "hint"},
		{Severity: "high", Message: "another"},
	}

	// Filter high and above
	highAndAbove := FilterFindingsBySeverity(findings, "high")
	if len(highAndAbove) != 3 { // critical + 2 high
		t.Errorf("FilterFindingsBySeverity(high) returned %d, want 3", len(highAndAbove))
	}
}

func TestFilterNilSourcesByRisk(t *testing.T) {
	sources := []NilSource{
		{Variable: "a", Risk: "high", Checked: false},
		{Variable: "b", Risk: "low", Checked: true},
		{Variable: "c", Risk: "high", Checked: false},
		{Variable: "d", Risk: "medium", Checked: false},
	}

	highRisk := FilterNilSourcesByRisk(sources, "high")
	if len(highRisk) != 2 {
		t.Errorf("FilterNilSourcesByRisk(high) returned %d, want 2", len(highRisk))
	}
}
```

**Step 2: Run test to verify it fails**

Run: `cd scripts/ring:codereview && go test -v ./internal/context/... 2>&1 | head -20 && cd ../..`

**Expected output:**
```
# github.com/lerianstudio/ring/scripts/ring:codereview/internal/context
./reviewer_mappings_test.go:XX:XX: undefined: GetReviewerNames
FAIL	github.com/lerianstudio/ring/scripts/ring:codereview/internal/context [build failed]
```

**Step 3: Write minimal implementation**

Create file `scripts/ring:codereview/internal/context/reviewer_mappings.go`:

```go
package context

// DataSource represents a data source for a reviewer.
type DataSource struct {
	Name        string // e.g., "static-analysis", "semantic-diff"
	Description string // What this data provides
}

// reviewerDataSources maps each reviewer to their primary data sources.
var reviewerDataSources = map[string][]DataSource{
	"ring:code-reviewer": {
		{Name: "static-analysis", Description: "Lint findings, style issues, deprecations"},
		{Name: "semantic-diff", Description: "Function/type changes, signature modifications"},
	},
	"ring:security-reviewer": {
		{Name: "static-analysis-security", Description: "Security scanner findings (gosec, bandit)"},
		{Name: "security-summary", Description: "Data flow analysis, taint tracking"},
	},
	"ring:business-logic-reviewer": {
		{Name: "semantic-diff", Description: "Business logic changes in functions/methods"},
		{Name: "impact-summary", Description: "Call graph impact, affected callers"},
	},
	"ring:test-reviewer": {
		{Name: "impact-summary", Description: "Test coverage for modified code"},
	},
	"ring:nil-safety-reviewer": {
		{Name: "data-flow", Description: "Nil/None source analysis"},
	},
}

// severityOrder defines severity ranking for filtering.
var severityOrder = map[string]int{
	"critical": 4,
	"high":     3,
	"warning":  2,
	"info":     1,
}

// securityCategories lists categories relevant to security reviewer.
var securityCategories = map[string]bool{
	"security": true,
}

// codeQualityCategories lists categories relevant to code reviewer.
var codeQualityCategories = map[string]bool{
	"bug":         true,
	"style":       true,
	"performance": true,
	"deprecation": true,
	"complexity":  true,
	"type":        true,
	"unused":      true,
	"other":       true,
}

// GetReviewerNames returns the list of all reviewer names in order.
func GetReviewerNames() []string {
	return []string{
		"ring:code-reviewer",
		"ring:security-reviewer",
		"ring:business-logic-reviewer",
		"ring:test-reviewer",
		"ring:nil-safety-reviewer",
	}
}

// GetReviewerDataSources returns the data sources for a specific reviewer.
func GetReviewerDataSources(reviewer string) []DataSource {
	return reviewerDataSources[reviewer]
}

// FilterFindingsByCategory filters findings to only those in the specified category.
func FilterFindingsByCategory(findings []Finding, category string) []Finding {
	var filtered []Finding
	for _, f := range findings {
		if f.Category == category {
			filtered = append(filtered, f)
		}
	}
	return filtered
}

// FilterFindingsBySeverity filters findings at or above the specified severity.
func FilterFindingsBySeverity(findings []Finding, minSeverity string) []Finding {
	minLevel := severityOrder[minSeverity]
	var filtered []Finding
	for _, f := range findings {
		if severityOrder[f.Severity] >= minLevel {
			filtered = append(filtered, f)
		}
	}
	return filtered
}

// FilterFindingsForCodeReviewer filters findings relevant to code quality.
func FilterFindingsForCodeReviewer(findings []Finding) []Finding {
	var filtered []Finding
	for _, f := range findings {
		if codeQualityCategories[f.Category] {
			filtered = append(filtered, f)
		}
	}
	return filtered
}

// FilterFindingsForSecurityReviewer filters findings relevant to security.
func FilterFindingsForSecurityReviewer(findings []Finding) []Finding {
	var filtered []Finding
	for _, f := range findings {
		if securityCategories[f.Category] {
			filtered = append(filtered, f)
		}
	}
	return filtered
}

// FilterNilSourcesByRisk filters nil sources by risk level.
func FilterNilSourcesByRisk(sources []NilSource, risk string) []NilSource {
	var filtered []NilSource
	for _, s := range sources {
		if s.Risk == risk {
			filtered = append(filtered, s)
		}
	}
	return filtered
}

// FilterNilSourcesUnchecked filters nil sources that are not checked.
func FilterNilSourcesUnchecked(sources []NilSource) []NilSource {
	var filtered []NilSource
	for _, s := range sources {
		if !s.Checked {
			filtered = append(filtered, s)
		}
	}
	return filtered
}

// GetUncoveredFunctions returns functions with no test coverage.
func GetUncoveredFunctions(callGraph *CallGraphData) []FunctionCallGraph {
	var uncovered []FunctionCallGraph
	for _, f := range callGraph.ModifiedFunctions {
		if len(f.TestCoverage) == 0 {
			uncovered = append(uncovered, f)
		}
	}
	return uncovered
}

// GetHighImpactFunctions returns functions with many callers.
func GetHighImpactFunctions(callGraph *CallGraphData, threshold int) []FunctionCallGraph {
	var highImpact []FunctionCallGraph
	for _, f := range callGraph.ModifiedFunctions {
		if len(f.Callers) >= threshold {
			highImpact = append(highImpact, f)
		}
	}
	return highImpact
}
```

**Step 4: Run test to verify it passes**

Run: `cd scripts/ring:codereview && go test -v ./internal/context/... && cd ../..`

**Expected output:**
```
=== RUN   TestReviewerNames
--- PASS: TestReviewerNames (0.00s)
=== RUN   TestGetReviewerDataSources
--- PASS: TestGetReviewerDataSources (0.00s)
=== RUN   TestFilterFindingsByCategory
--- PASS: TestFilterFindingsByCategory (0.00s)
=== RUN   TestFilterFindingsBySeverity
--- PASS: TestFilterFindingsBySeverity (0.00s)
=== RUN   TestFilterNilSourcesByRisk
--- PASS: TestFilterNilSourcesByRisk (0.00s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/context
```

**Step 5: Commit**

```bash
git add scripts/ring:codereview/internal/context/reviewer_mappings.go
git add scripts/ring:codereview/internal/context/reviewer_mappings_test.go
git commit -m "feat(ring:codereview): add reviewer data mappings and filters

Maps each reviewer to their primary data sources and provides
filter functions for findings by category, severity, and risk."
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Expected data source counts may need adjustment
   - Fix: Update expected values in tests
   - Rollback: `git checkout -- scripts/ring:codereview/internal/context/`

---

## Task 4: Write Templates for ring:code-reviewer

**Files:**
- Create: `scripts/ring:codereview/internal/context/templates.go`

**Prerequisites:**
- Task 3 completed

**Step 1: Write the templates file**

Create file `scripts/ring:codereview/internal/context/templates.go`:

```go
package context

import (
	"bytes"
	"fmt"
	"strings"
	"text/template"
)

// Template definitions for each reviewer's context file.

const codeReviewerTemplate = `# Pre-Analysis Context: Code Quality

## Static Analysis Findings ({{.FindingCount}} issues)

{{if .Findings}}
| Severity | Tool | File | Line | Message |
|----------|------|------|------|---------|
{{- range .Findings}}
| {{.Severity}} | {{.Tool}} | {{.File}} | {{.Line}} | {{.Message}} |
{{- end}}
{{else}}
No static analysis findings.
{{end}}

## Semantic Changes

{{if .HasSemanticChanges}}
### Functions Modified ({{len .ModifiedFunctions}})
{{range .ModifiedFunctions}}
#### ` + "`{{.Package}}.{{.Name}}`" + `
**File:** ` + "`{{.File}}:{{.After.LineStart}}-{{.After.LineEnd}}`" + `
{{if .Changes}}**Changes:** {{join .Changes ", "}}{{end}}

{{if signatureChanged .}}
` + "```diff" + `
- {{.Before.Signature}}
+ {{.After.Signature}}
` + "```" + `
{{end}}
{{end}}

### Functions Added ({{len .AddedFunctions}})
{{range .AddedFunctions}}
#### ` + "`{{.Package}}.{{.Name}}`" + `
**File:** ` + "`{{.File}}:{{.LineStart}}-{{.LineEnd}}`" + `
**Purpose:** New function (requires review)
{{end}}

### Types Modified ({{len .ModifiedTypes}})
{{range .ModifiedTypes}}
#### ` + "`{{.Name}}`" + `
**File:** ` + "`{{.File}}`" + `

| Field | Before | After |
|-------|--------|-------|
{{- range fieldChanges .}}
| {{.Name}} | {{.Before}} | {{.After}} |
{{- end}}
{{end}}
{{else}}
No semantic changes detected.
{{end}}

## Focus Areas

Based on analysis, pay special attention to:
{{range $i, $area := .FocusAreas}}
{{inc $i}}. **{{$area.Title}}** - {{$area.Description}}
{{- end}}
{{if not .FocusAreas}}
No specific focus areas identified.
{{end}}
`

const securityReviewerTemplate = `# Pre-Analysis Context: Security

## Security Scanner Findings ({{.FindingCount}} issues)

{{if .Findings}}
| Severity | Tool | Rule | File | Line | Message |
|----------|------|------|------|------|---------|
{{- range .Findings}}
| {{.Severity}} | {{.Tool}} | {{.Rule}} | {{.File}} | {{.Line}} | {{.Message}} |
{{- end}}
{{else}}
No security scanner findings.
{{end}}

## Data Flow Analysis

{{if .HasDataFlowAnalysis}}
### High Risk Flows ({{len .HighRiskFlows}})
{{range .HighRiskFlows}}
#### {{.ID}}: {{.Source.Type}} -> {{.Sink.Type}}
**File:** ` + "`{{.Source.File}}:{{.Source.Line}}`" + `
**Risk:** {{.Risk}}
**Notes:** {{.Notes}}

**Source:** ` + "`{{.Source.Expression}}`" + `
**Sink:** ` + "`{{.Sink.Expression}}`" + `
**Sanitized:** {{if .Sanitized}}Yes{{else}}No{{end}}
{{end}}

### Medium Risk Flows ({{len .MediumRiskFlows}})
{{range .MediumRiskFlows}}
- {{.Source.Type}} -> {{.Sink.Type}} at ` + "`{{.Source.File}}:{{.Source.Line}}`" + ` ({{.Notes}})
{{- end}}
{{else}}
No data flow analysis available.
{{end}}

## Focus Areas

Based on analysis, pay special attention to:
{{range $i, $area := .FocusAreas}}
{{inc $i}}. **{{$area.Title}}** - {{$area.Description}}
{{- end}}
{{if not .FocusAreas}}
No specific focus areas identified.
{{end}}
`

const businessLogicReviewerTemplate = `# Pre-Analysis Context: Business Logic

## Impact Analysis

{{if .HasCallGraph}}
### High Impact Changes

{{range .HighImpactFunctions}}
#### ` + "`{{.Function}}`" + `
**File:** ` + "`{{.File}}`" + `
**Risk Level:** {{riskLevel .}} ({{len .Callers}} direct callers)

**Direct Callers (signature change affects these):**
{{range $i, $caller := .Callers}}
{{inc $i}}. ` + "`{{$caller.Function}}`" + ` - ` + "`{{$caller.File}}:{{$caller.Line}}`" + `
{{- end}}

**Callees (this function depends on):**
{{range $i, $callee := .Callees}}
{{inc $i}}. ` + "`{{$callee.Function}}`" + `
{{- end}}
{{end}}
{{else}}
No call graph analysis available.
{{end}}

## Semantic Changes

{{if .HasSemanticChanges}}
### Functions with Logic Changes
{{range $i, $f := .ModifiedFunctions}}
{{inc $i}}. **` + "`{{$f.Package}}.{{$f.Name}}`" + `** - {{join $f.Changes ", "}}
{{- end}}
{{else}}
No semantic changes detected.
{{end}}

## Focus Areas

Based on analysis, pay special attention to:
{{range $i, $area := .FocusAreas}}
{{inc $i}}. **{{$area.Title}}** - {{$area.Description}}
{{- end}}
{{if not .FocusAreas}}
No specific focus areas identified.
{{end}}
`

const testReviewerTemplate = `# Pre-Analysis Context: Testing

## Test Coverage for Modified Code

{{if .HasCallGraph}}
| Function | File | Tests | Status |
|----------|------|-------|--------|
{{- range .ModifiedFunctions}}
| ` + "`{{.Function}}`" + ` | {{.File}} | {{len .TestCoverage}} tests | {{testStatus .}} |
{{- end}}
{{else}}
No call graph analysis available for test coverage.
{{end}}

## Uncovered New Code

{{if .UncoveredFunctions}}
{{range .UncoveredFunctions}}
- ` + "`{{.Function}}`" + ` at ` + "`{{.File}}`" + ` - **No tests found**
{{- end}}
{{else}}
All modified code has test coverage.
{{end}}

## Focus Areas

Based on analysis, pay special attention to:
{{range $i, $area := .FocusAreas}}
{{inc $i}}. **{{$area.Title}}** - {{$area.Description}}
{{- end}}
{{if not .FocusAreas}}
No specific focus areas identified.
{{end}}
`

const nilSafetyReviewerTemplate = `# Pre-Analysis Context: Nil Safety

## Nil Source Analysis

{{if .HasNilSources}}
| Variable | File | Line | Checked? | Risk |
|----------|------|------|----------|------|
{{- range .NilSources}}
| ` + "`{{.Variable}}`" + ` | {{.File}} | {{.Line}} | {{if .Checked}}Yes{{else}}No{{end}} | {{.Risk}} |
{{- end}}
{{else}}
No nil sources detected in changed code.
{{end}}

## High Risk Nil Sources

{{range .HighRiskNilSources}}
### ` + "`{{.Variable}}`" + ` at ` + "`{{.File}}:{{.Line}}`" + `
**Expression:** ` + "`{{.Expression}}`" + `
**Checked:** {{if .Checked}}Yes (line {{.CheckLine}}){{else}}No{{end}}
**Notes:** {{.Notes}}
{{end}}

## Focus Areas

Based on analysis, pay special attention to:
{{range $i, $area := .FocusAreas}}
{{inc $i}}. **{{$area.Title}}** - {{$area.Description}}
{{- end}}
{{if not .FocusAreas}}
No specific focus areas identified.
{{end}}
`

// FocusArea represents a specific area requiring attention.
type FocusArea struct {
	Title       string
	Description string
}

// FieldChange represents a before/after field comparison.
type FieldChange struct {
	Name   string
	Before string
	After  string
}

// TemplateData holds data for template rendering.
type TemplateData struct {
	// Common fields
	FindingCount int
	Findings     []Finding
	FocusAreas   []FocusArea

	// Semantic changes (ring:code-reviewer, ring:business-logic-reviewer)
	HasSemanticChanges bool
	ModifiedFunctions  []FunctionDiff
	AddedFunctions     []FunctionInfo
	ModifiedTypes      []TypeDiff

	// Data flow (ring:security-reviewer)
	HasDataFlowAnalysis bool
	HighRiskFlows       []DataFlow
	MediumRiskFlows     []DataFlow

	// Call graph (ring:business-logic-reviewer, ring:test-reviewer)
	HasCallGraph         bool
	HighImpactFunctions  []FunctionCallGraph
	UncoveredFunctions   []FunctionCallGraph

	// Nil safety (ring:nil-safety-reviewer)
	HasNilSources       bool
	NilSources          []NilSource
	HighRiskNilSources  []NilSource
}

// templateFuncs provides custom functions for templates.
var templateFuncs = template.FuncMap{
	"inc": func(i int) int {
		return i + 1
	},
	"join": func(items []string, sep string) string {
		return strings.Join(items, sep)
	},
	"signatureChanged": func(f FunctionDiff) bool {
		return f.Before.Signature != f.After.Signature
	},
	"fieldChanges": func(t TypeDiff) []FieldChange {
		var changes []FieldChange
		beforeMap := make(map[string]string)
		for _, f := range t.Before.Fields {
			beforeMap[f.Name] = f.Type
		}
		afterMap := make(map[string]string)
		for _, f := range t.After.Fields {
			afterMap[f.Name] = f.Type
		}
		
		// Find modified and added fields
		for _, f := range t.After.Fields {
			if before, ok := beforeMap[f.Name]; ok {
				if before != f.Type {
					changes = append(changes, FieldChange{
						Name:   f.Name,
						Before: before,
						After:  f.Type,
					})
				}
			} else {
				changes = append(changes, FieldChange{
					Name:   f.Name,
					Before: "-",
					After:  f.Type + " (added)",
				})
			}
		}
		
		// Find deleted fields
		for _, f := range t.Before.Fields {
			if _, ok := afterMap[f.Name]; !ok {
				changes = append(changes, FieldChange{
					Name:   f.Name,
					Before: f.Type,
					After:  "(deleted)",
				})
			}
		}
		
		return changes
	},
	"riskLevel": func(f FunctionCallGraph) string {
		callerCount := len(f.Callers)
		if callerCount >= 5 {
			return "HIGH"
		}
		if callerCount >= 2 {
			return "MEDIUM"
		}
		return "LOW"
	},
	"testStatus": func(f FunctionCallGraph) string {
		if len(f.TestCoverage) == 0 {
			return "No tests"
		}
		return fmt.Sprintf("%d tests", len(f.TestCoverage))
	},
}

// RenderTemplate renders a template with the given data.
func RenderTemplate(templateStr string, data *TemplateData) (string, error) {
	tmpl, err := template.New("context").Funcs(templateFuncs).Parse(templateStr)
	if err != nil {
		return "", fmt.Errorf("failed to parse template: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, data); err != nil {
		return "", fmt.Errorf("failed to execute template: %w", err)
	}

	return buf.String(), nil
}

// GetTemplateForReviewer returns the template string for a specific reviewer.
func GetTemplateForReviewer(reviewer string) string {
	switch reviewer {
	case "ring:code-reviewer":
		return codeReviewerTemplate
	case "ring:security-reviewer":
		return securityReviewerTemplate
	case "ring:business-logic-reviewer":
		return businessLogicReviewerTemplate
	case "ring:test-reviewer":
		return testReviewerTemplate
	case "ring:nil-safety-reviewer":
		return nilSafetyReviewerTemplate
	default:
		return ""
	}
}
```

**Step 2: Verify compilation**

Run: `cd scripts/ring:codereview && go build ./internal/context/... && cd ../..`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/internal/context/templates.go
git commit -m "feat(ring:codereview): add markdown templates for all reviewers

Includes templates for ring:code-reviewer, ring:security-reviewer,
ring:business-logic-reviewer, ring:test-reviewer, and ring:nil-safety-reviewer.
Uses text/template with custom functions for rendering."
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Template syntax, especially backticks and escaping
   - Fix: Use raw string literals correctly
   - Rollback: `git checkout -- scripts/ring:codereview/internal/context/templates.go`

---

## Task 5: Add Template Tests

**Files:**
- Create: `scripts/ring:codereview/internal/context/templates_test.go`

**Prerequisites:**
- Task 4 completed

**Step 1: Write template tests**

Create file `scripts/ring:codereview/internal/context/templates_test.go`:

```go
package context

import (
	"strings"
	"testing"
)

func TestRenderTemplate_CodeReviewer(t *testing.T) {
	data := &TemplateData{
		FindingCount: 2,
		Findings: []Finding{
			{Tool: "staticcheck", Rule: "SA1019", Severity: "warning", File: "user.go", Line: 45, Message: "deprecated API"},
			{Tool: "golangci-lint", Rule: "ineffassign", Severity: "info", File: "repo.go", Line: 23, Message: "unused var"},
		},
		HasSemanticChanges: true,
		ModifiedFunctions: []FunctionDiff{
			{
				Name:    "CreateUser",
				Package: "handler",
				File:    "user.go",
				Before:  FunctionInfo{Signature: "func CreateUser(ctx context.Context)", LineStart: 10, LineEnd: 20},
				After:   FunctionInfo{Signature: "func CreateUser(ctx context.Context, opts ...Option)", LineStart: 10, LineEnd: 30},
				Changes: []string{"added_param"},
			},
		},
		FocusAreas: []FocusArea{
			{Title: "Deprecated API", Description: "grpc.Dial needs update"},
		},
	}

	result, err := RenderTemplate(codeReviewerTemplate, data)
	if err != nil {
		t.Fatalf("RenderTemplate failed: %v", err)
	}

	// Verify key sections exist
	if !strings.Contains(result, "# Pre-Analysis Context: Code Quality") {
		t.Error("Missing title section")
	}
	if !strings.Contains(result, "Static Analysis Findings (2 issues)") {
		t.Error("Missing findings count")
	}
	if !strings.Contains(result, "staticcheck") {
		t.Error("Missing tool name in findings")
	}
	if !strings.Contains(result, "handler.CreateUser") {
		t.Error("Missing function name")
	}
	if !strings.Contains(result, "Deprecated API") {
		t.Error("Missing focus area")
	}
}

func TestRenderTemplate_SecurityReviewer(t *testing.T) {
	data := &TemplateData{
		FindingCount: 1,
		Findings: []Finding{
			{Tool: "gosec", Rule: "G401", Severity: "high", File: "crypto.go", Line: 23, Message: "weak crypto"},
		},
		HasDataFlowAnalysis: true,
		HighRiskFlows: []DataFlow{
			{
				ID:   "flow-1",
				Risk: "high",
				Source: FlowSource{
					Type:       "http_request",
					File:       "handler.go",
					Line:       45,
					Expression: "r.URL.Query().Get(\"id\")",
				},
				Sink: FlowSink{
					Type:       "database",
					File:       "repo.go",
					Line:       23,
					Expression: "db.Query(q, id)",
				},
				Sanitized: false,
				Notes:     "Query param without validation",
			},
		},
	}

	result, err := RenderTemplate(securityReviewerTemplate, data)
	if err != nil {
		t.Fatalf("RenderTemplate failed: %v", err)
	}

	if !strings.Contains(result, "# Pre-Analysis Context: Security") {
		t.Error("Missing title section")
	}
	if !strings.Contains(result, "gosec") {
		t.Error("Missing security tool")
	}
	if !strings.Contains(result, "High Risk Flows") {
		t.Error("Missing high risk flows section")
	}
	if !strings.Contains(result, "http_request") {
		t.Error("Missing source type")
	}
}

func TestRenderTemplate_NilSafetyReviewer(t *testing.T) {
	data := &TemplateData{
		HasNilSources: true,
		NilSources: []NilSource{
			{Variable: "user", File: "handler.go", Line: 67, Checked: true, Risk: "low"},
			{Variable: "config", File: "service.go", Line: 23, Checked: false, Risk: "high", Notes: "env var may be empty"},
		},
		HighRiskNilSources: []NilSource{
			{Variable: "config", File: "service.go", Line: 23, Checked: false, Risk: "high", Expression: "os.Getenv(...)", Notes: "env var may be empty"},
		},
	}

	result, err := RenderTemplate(nilSafetyReviewerTemplate, data)
	if err != nil {
		t.Fatalf("RenderTemplate failed: %v", err)
	}

	if !strings.Contains(result, "# Pre-Analysis Context: Nil Safety") {
		t.Error("Missing title section")
	}
	if !strings.Contains(result, "config") {
		t.Error("Missing variable name")
	}
	if !strings.Contains(result, "High Risk Nil Sources") {
		t.Error("Missing high risk section")
	}
}

func TestGetTemplateForReviewer(t *testing.T) {
	tests := []struct {
		reviewer string
		wantLen  int // non-zero means template exists
	}{
		{"ring:code-reviewer", 100},
		{"ring:security-reviewer", 100},
		{"ring:business-logic-reviewer", 100},
		{"ring:test-reviewer", 100},
		{"ring:nil-safety-reviewer", 100},
		{"unknown-reviewer", 0},
	}

	for _, tt := range tests {
		t.Run(tt.reviewer, func(t *testing.T) {
			template := GetTemplateForReviewer(tt.reviewer)
			if (len(template) > 0) != (tt.wantLen > 0) {
				t.Errorf("GetTemplateForReviewer(%q) returned len=%d, want len>0: %v",
					tt.reviewer, len(template), tt.wantLen > 0)
			}
		})
	}
}

func TestRenderTemplate_EmptyData(t *testing.T) {
	data := &TemplateData{
		FindingCount:       0,
		Findings:           nil,
		HasSemanticChanges: false,
		FocusAreas:         nil,
	}

	result, err := RenderTemplate(codeReviewerTemplate, data)
	if err != nil {
		t.Fatalf("RenderTemplate failed with empty data: %v", err)
	}

	if !strings.Contains(result, "No static analysis findings") {
		t.Error("Should show 'No static analysis findings' for empty findings")
	}
	if !strings.Contains(result, "No semantic changes detected") {
		t.Error("Should show 'No semantic changes detected' for empty changes")
	}
}
```

**Step 2: Run tests**

Run: `cd scripts/ring:codereview && go test -v ./internal/context/... && cd ../..`

**Expected output:**
```
=== RUN   TestReviewerNames
--- PASS: TestReviewerNames (0.00s)
...
=== RUN   TestRenderTemplate_CodeReviewer
--- PASS: TestRenderTemplate_CodeReviewer (0.00s)
=== RUN   TestRenderTemplate_SecurityReviewer
--- PASS: TestRenderTemplate_SecurityReviewer (0.00s)
=== RUN   TestRenderTemplate_NilSafetyReviewer
--- PASS: TestRenderTemplate_NilSafetyReviewer (0.00s)
=== RUN   TestGetTemplateForReviewer
--- PASS: TestGetTemplateForReviewer (0.00s)
=== RUN   TestRenderTemplate_EmptyData
--- PASS: TestRenderTemplate_EmptyData (0.00s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/context
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/internal/context/templates_test.go
git commit -m "test(ring:codereview): add template rendering tests

Covers ring:code-reviewer, ring:security-reviewer, ring:nil-safety-reviewer templates
and edge cases with empty data."
```

**If Task Fails:**

1. **Template rendering fails:**
   - Check: Template syntax errors in the error message
   - Fix: Adjust template string escaping
   - Rollback: `git checkout -- scripts/ring:codereview/internal/context/templates_test.go`

---

## Task 6: Implement Compiler Core

**Files:**
- Create: `scripts/ring:codereview/internal/context/compiler.go`

**Prerequisites:**
- Tasks 4-5 completed

**Step 1: Write the compiler implementation**

Create file `scripts/ring:codereview/internal/context/compiler.go`:

```go
package context

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Compiler aggregates phase outputs and generates reviewer context files.
type Compiler struct {
	inputDir  string
	outputDir string
	language  string
}

// NewCompiler creates a new context compiler.
// inputDir: directory containing phase outputs (e.g., .ring/ring:codereview/)
// outputDir: directory to write context files (typically same as inputDir)
func NewCompiler(inputDir, outputDir string) *Compiler {
	return &Compiler{
		inputDir:  inputDir,
		outputDir: outputDir,
	}
}

// Compile reads all phase outputs and generates reviewer context files.
func (c *Compiler) Compile() error {
	// Read all phase outputs
	outputs, err := c.readPhaseOutputs()
	if err != nil {
		return fmt.Errorf("failed to read phase outputs: %w", err)
	}

	// Determine language from scope
	if outputs.Scope != nil {
		c.language = outputs.Scope.Language
	}

	// Generate context for each reviewer
	reviewers := GetReviewerNames()
	for _, reviewer := range reviewers {
		if err := c.generateReviewerContext(reviewer, outputs); err != nil {
			return fmt.Errorf("failed to generate context for %s: %w", reviewer, err)
		}
	}

	return nil
}

// readPhaseOutputs reads all phase outputs from the input directory.
func (c *Compiler) readPhaseOutputs() (*PhaseOutputs, error) {
	outputs := &PhaseOutputs{}

	// Read scope.json (Phase 0)
	scopePath := filepath.Join(c.inputDir, "scope.json")
	if data, err := os.ReadFile(scopePath); err == nil {
		var scope ScopeData
		if err := json.Unmarshal(data, &scope); err == nil {
			outputs.Scope = &scope
		} else {
			outputs.Errors = append(outputs.Errors, fmt.Sprintf("scope.json parse error: %v", err))
		}
	}

	// Read static-analysis.json (Phase 1)
	staticPath := filepath.Join(c.inputDir, "static-analysis.json")
	if data, err := os.ReadFile(staticPath); err == nil {
		var static StaticAnalysisData
		if err := json.Unmarshal(data, &static); err == nil {
			outputs.StaticAnalysis = &static
		} else {
			outputs.Errors = append(outputs.Errors, fmt.Sprintf("static-analysis.json parse error: %v", err))
		}
	}

	// Read language-specific AST (Phase 2)
	// Try each language suffix
	for _, lang := range []string{"go", "ts", "py"} {
		astPath := filepath.Join(c.inputDir, fmt.Sprintf("%s-ast.json", lang))
		if data, err := os.ReadFile(astPath); err == nil {
			var ast ASTData
			if err := json.Unmarshal(data, &ast); err == nil {
				outputs.AST = &ast
				break
			}
		}
	}

	// Read language-specific call graph (Phase 3)
	for _, lang := range []string{"go", "ts", "py"} {
		callsPath := filepath.Join(c.inputDir, fmt.Sprintf("%s-calls.json", lang))
		if data, err := os.ReadFile(callsPath); err == nil {
			var calls CallGraphData
			if err := json.Unmarshal(data, &calls); err == nil {
				outputs.CallGraph = &calls
				break
			}
		}
	}

	// Read language-specific data flow (Phase 4)
	for _, lang := range []string{"go", "ts", "py"} {
		flowPath := filepath.Join(c.inputDir, fmt.Sprintf("%s-flow.json", lang))
		if data, err := os.ReadFile(flowPath); err == nil {
			var flow DataFlowData
			if err := json.Unmarshal(data, &flow); err == nil {
				outputs.DataFlow = &flow
				break
			}
		}
	}

	return outputs, nil
}

// generateReviewerContext generates the context file for a specific reviewer.
func (c *Compiler) generateReviewerContext(reviewer string, outputs *PhaseOutputs) error {
	// Build template data based on reviewer
	data := c.buildTemplateData(reviewer, outputs)

	// Get and render template
	templateStr := GetTemplateForReviewer(reviewer)
	if templateStr == "" {
		return fmt.Errorf("no template found for reviewer: %s", reviewer)
	}

	content, err := RenderTemplate(templateStr, data)
	if err != nil {
		return fmt.Errorf("failed to render template: %w", err)
	}

	// Write context file
	outputPath := filepath.Join(c.outputDir, fmt.Sprintf("context-%s.md", reviewer))
	if err := os.MkdirAll(c.outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	if err := os.WriteFile(outputPath, []byte(content), 0644); err != nil {
		return fmt.Errorf("failed to write context file: %w", err)
	}

	return nil
}

// buildTemplateData constructs the template data for a specific reviewer.
func (c *Compiler) buildTemplateData(reviewer string, outputs *PhaseOutputs) *TemplateData {
	data := &TemplateData{}

	switch reviewer {
	case "ring:code-reviewer":
		c.buildCodeReviewerData(data, outputs)
	case "ring:security-reviewer":
		c.buildSecurityReviewerData(data, outputs)
	case "ring:business-logic-reviewer":
		c.buildBusinessLogicReviewerData(data, outputs)
	case "ring:test-reviewer":
		c.buildTestReviewerData(data, outputs)
	case "ring:nil-safety-reviewer":
		c.buildNilSafetyReviewerData(data, outputs)
	}

	return data
}

// buildCodeReviewerData populates data for the code reviewer.
func (c *Compiler) buildCodeReviewerData(data *TemplateData, outputs *PhaseOutputs) {
	// Static analysis findings (non-security)
	if outputs.StaticAnalysis != nil {
		data.Findings = FilterFindingsForCodeReviewer(outputs.StaticAnalysis.Findings)
		data.FindingCount = len(data.Findings)
	}

	// Semantic changes from AST
	if outputs.AST != nil {
		data.HasSemanticChanges = true
		data.ModifiedFunctions = outputs.AST.Functions.Modified
		data.AddedFunctions = outputs.AST.Functions.Added
		data.ModifiedTypes = outputs.AST.Types.Modified
	}

	// Build focus areas
	data.FocusAreas = c.buildCodeReviewerFocusAreas(outputs)
}

// buildSecurityReviewerData populates data for the security reviewer.
func (c *Compiler) buildSecurityReviewerData(data *TemplateData, outputs *PhaseOutputs) {
	// Security-specific findings
	if outputs.StaticAnalysis != nil {
		data.Findings = FilterFindingsForSecurityReviewer(outputs.StaticAnalysis.Findings)
		data.FindingCount = len(data.Findings)
	}

	// Data flow analysis
	if outputs.DataFlow != nil {
		data.HasDataFlowAnalysis = true
		for _, flow := range outputs.DataFlow.Flows {
			switch flow.Risk {
			case "high":
				data.HighRiskFlows = append(data.HighRiskFlows, flow)
			case "medium":
				data.MediumRiskFlows = append(data.MediumRiskFlows, flow)
			}
		}
	}

	// Build focus areas
	data.FocusAreas = c.buildSecurityReviewerFocusAreas(outputs)
}

// buildBusinessLogicReviewerData populates data for the business logic reviewer.
func (c *Compiler) buildBusinessLogicReviewerData(data *TemplateData, outputs *PhaseOutputs) {
	// Call graph for impact analysis
	if outputs.CallGraph != nil {
		data.HasCallGraph = true
		data.HighImpactFunctions = GetHighImpactFunctions(outputs.CallGraph, 2)
	}

	// Semantic changes
	if outputs.AST != nil {
		data.HasSemanticChanges = true
		data.ModifiedFunctions = outputs.AST.Functions.Modified
	}

	// Build focus areas
	data.FocusAreas = c.buildBusinessLogicReviewerFocusAreas(outputs)
}

// buildTestReviewerData populates data for the test reviewer.
func (c *Compiler) buildTestReviewerData(data *TemplateData, outputs *PhaseOutputs) {
	// Call graph for test coverage
	if outputs.CallGraph != nil {
		data.HasCallGraph = true
		data.ModifiedFunctions = nil // Will use FunctionCallGraph instead
		
		// Convert to the right type for template
		for _, f := range outputs.CallGraph.ModifiedFunctions {
			data.HighImpactFunctions = append(data.HighImpactFunctions, f)
		}
		
		data.UncoveredFunctions = GetUncoveredFunctions(outputs.CallGraph)
	}

	// Build focus areas
	data.FocusAreas = c.buildTestReviewerFocusAreas(outputs)
}

// buildNilSafetyReviewerData populates data for the nil safety reviewer.
func (c *Compiler) buildNilSafetyReviewerData(data *TemplateData, outputs *PhaseOutputs) {
	// Nil sources from data flow
	if outputs.DataFlow != nil && len(outputs.DataFlow.NilSources) > 0 {
		data.HasNilSources = true
		data.NilSources = outputs.DataFlow.NilSources
		data.HighRiskNilSources = FilterNilSourcesByRisk(outputs.DataFlow.NilSources, "high")
	}

	// Build focus areas
	data.FocusAreas = c.buildNilSafetyReviewerFocusAreas(outputs)
}

// Focus area builders

func (c *Compiler) buildCodeReviewerFocusAreas(outputs *PhaseOutputs) []FocusArea {
	var areas []FocusArea

	// Check for deprecation warnings
	if outputs.StaticAnalysis != nil {
		deprecations := FilterFindingsByCategory(outputs.StaticAnalysis.Findings, "deprecation")
		if len(deprecations) > 0 {
			areas = append(areas, FocusArea{
				Title:       "Deprecated API Usage",
				Description: fmt.Sprintf("%d deprecated API calls need updating", len(deprecations)),
			})
		}
	}

	// Check for signature changes
	if outputs.AST != nil {
		for _, f := range outputs.AST.Functions.Modified {
			if f.Before.Signature != f.After.Signature {
				areas = append(areas, FocusArea{
					Title:       fmt.Sprintf("Signature change in %s", f.Name),
					Description: "Function signature modified - verify caller compatibility",
				})
			}
		}
	}

	return areas
}

func (c *Compiler) buildSecurityReviewerFocusAreas(outputs *PhaseOutputs) []FocusArea {
	var areas []FocusArea

	// Check for high-risk data flows
	if outputs.DataFlow != nil {
		highRisk := 0
		for _, flow := range outputs.DataFlow.Flows {
			if flow.Risk == "high" && !flow.Sanitized {
				highRisk++
			}
		}
		if highRisk > 0 {
			areas = append(areas, FocusArea{
				Title:       "Unsanitized High-Risk Flows",
				Description: fmt.Sprintf("%d data flows without sanitization", highRisk),
			})
		}
	}

	// Check for security findings
	if outputs.StaticAnalysis != nil {
		critical := FilterFindingsBySeverity(
			FilterFindingsForSecurityReviewer(outputs.StaticAnalysis.Findings),
			"high",
		)
		if len(critical) > 0 {
			areas = append(areas, FocusArea{
				Title:       "Critical Security Findings",
				Description: fmt.Sprintf("%d high/critical security issues detected", len(critical)),
			})
		}
	}

	return areas
}

func (c *Compiler) buildBusinessLogicReviewerFocusAreas(outputs *PhaseOutputs) []FocusArea {
	var areas []FocusArea

	// Check for high-impact changes
	if outputs.CallGraph != nil {
		highImpact := GetHighImpactFunctions(outputs.CallGraph, 3)
		if len(highImpact) > 0 {
			areas = append(areas, FocusArea{
				Title:       "High-Impact Functions",
				Description: fmt.Sprintf("%d functions with 3+ callers modified", len(highImpact)),
			})
		}
	}

	// Check for new functions
	if outputs.AST != nil && len(outputs.AST.Functions.Added) > 0 {
		areas = append(areas, FocusArea{
			Title:       "New Functions",
			Description: fmt.Sprintf("%d new functions added - verify business requirements", len(outputs.AST.Functions.Added)),
		})
	}

	return areas
}

func (c *Compiler) buildTestReviewerFocusAreas(outputs *PhaseOutputs) []FocusArea {
	var areas []FocusArea

	// Check for uncovered functions
	if outputs.CallGraph != nil {
		uncovered := GetUncoveredFunctions(outputs.CallGraph)
		if len(uncovered) > 0 {
			areas = append(areas, FocusArea{
				Title:       "Uncovered Code",
				Description: fmt.Sprintf("%d modified functions without test coverage", len(uncovered)),
			})
		}
	}

	// Check for new error paths
	if outputs.AST != nil && outputs.AST.ErrorHandling.NewErrorReturns != nil {
		if len(outputs.AST.ErrorHandling.NewErrorReturns) > 0 {
			areas = append(areas, FocusArea{
				Title:       "New Error Paths",
				Description: fmt.Sprintf("%d new error return paths need negative tests", len(outputs.AST.ErrorHandling.NewErrorReturns)),
			})
		}
	}

	return areas
}

func (c *Compiler) buildNilSafetyReviewerFocusAreas(outputs *PhaseOutputs) []FocusArea {
	var areas []FocusArea

	// Check for unchecked nil sources
	if outputs.DataFlow != nil {
		unchecked := FilterNilSourcesUnchecked(outputs.DataFlow.NilSources)
		if len(unchecked) > 0 {
			areas = append(areas, FocusArea{
				Title:       "Unchecked Nil Sources",
				Description: fmt.Sprintf("%d potential nil values without checks", len(unchecked)),
			})
		}

		// Check for high-risk nil sources
		highRisk := FilterNilSourcesByRisk(outputs.DataFlow.NilSources, "high")
		if len(highRisk) > 0 {
			areas = append(areas, FocusArea{
				Title:       "High-Risk Nil Sources",
				Description: fmt.Sprintf("%d high-risk nil sources require immediate attention", len(highRisk)),
			})
		}
	}

	return areas
}
```

**Step 2: Verify compilation**

Run: `cd scripts/ring:codereview && go build ./internal/context/... && cd ../..`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/internal/context/compiler.go
git commit -m "feat(ring:codereview): add context compiler core logic

Implements Compiler struct that reads phase outputs (0-4),
builds template data for each reviewer, and generates
context markdown files."
```

**If Task Fails:**

1. **Compilation fails:**
   - Check: Import paths and type references
   - Fix: Ensure all types are defined in types.go
   - Rollback: `git checkout -- scripts/ring:codereview/internal/context/compiler.go`

---

## Task 7: Add Compiler Tests

**Files:**
- Create: `scripts/ring:codereview/internal/context/compiler_test.go`

**Prerequisites:**
- Task 6 completed

**Step 1: Write compiler tests**

Create file `scripts/ring:codereview/internal/context/compiler_test.go`:

```go
package context

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCompiler_Compile(t *testing.T) {
	// Create temp directories
	inputDir := t.TempDir()
	outputDir := t.TempDir()

	// Create sample phase outputs
	createSamplePhaseOutputs(t, inputDir)

	// Create compiler and run
	compiler := NewCompiler(inputDir, outputDir)
	if err := compiler.Compile(); err != nil {
		t.Fatalf("Compile() error = %v", err)
	}

	// Verify all context files were created
	reviewers := GetReviewerNames()
	for _, reviewer := range reviewers {
		contextPath := filepath.Join(outputDir, "context-"+reviewer+".md")
		if _, err := os.Stat(contextPath); os.IsNotExist(err) {
			t.Errorf("Context file not created for %s", reviewer)
		}

		// Read and verify content
		content, err := os.ReadFile(contextPath)
		if err != nil {
			t.Errorf("Failed to read context file for %s: %v", reviewer, err)
			continue
		}

		// Basic content verification
		if len(content) == 0 {
			t.Errorf("Context file for %s is empty", reviewer)
		}
	}
}

func TestCompiler_CodeReviewerContext(t *testing.T) {
	inputDir := t.TempDir()
	outputDir := t.TempDir()
	createSamplePhaseOutputs(t, inputDir)

	compiler := NewCompiler(inputDir, outputDir)
	if err := compiler.Compile(); err != nil {
		t.Fatalf("Compile() error = %v", err)
	}

	content, err := os.ReadFile(filepath.Join(outputDir, "context-ring:code-reviewer.md"))
	if err != nil {
		t.Fatalf("Failed to read ring:code-reviewer context: %v", err)
	}

	contentStr := string(content)
	if !strings.Contains(contentStr, "Code Quality") {
		t.Error("Missing 'Code Quality' title")
	}
	if !strings.Contains(contentStr, "Static Analysis Findings") {
		t.Error("Missing static analysis section")
	}
}

func TestCompiler_SecurityReviewerContext(t *testing.T) {
	inputDir := t.TempDir()
	outputDir := t.TempDir()
	createSamplePhaseOutputs(t, inputDir)

	compiler := NewCompiler(inputDir, outputDir)
	if err := compiler.Compile(); err != nil {
		t.Fatalf("Compile() error = %v", err)
	}

	content, err := os.ReadFile(filepath.Join(outputDir, "context-ring:security-reviewer.md"))
	if err != nil {
		t.Fatalf("Failed to read ring:security-reviewer context: %v", err)
	}

	contentStr := string(content)
	if !strings.Contains(contentStr, "Security") {
		t.Error("Missing 'Security' title")
	}
}

func TestCompiler_MissingInputs(t *testing.T) {
	// Test with empty input directory
	inputDir := t.TempDir()
	outputDir := t.TempDir()

	compiler := NewCompiler(inputDir, outputDir)
	
	// Should not fail, just produce minimal output
	if err := compiler.Compile(); err != nil {
		t.Fatalf("Compile() should not fail with missing inputs: %v", err)
	}

	// Context files should still be created (with "no data" messages)
	contextPath := filepath.Join(outputDir, "context-ring:code-reviewer.md")
	if _, err := os.Stat(contextPath); os.IsNotExist(err) {
		t.Error("Context file should be created even with missing inputs")
	}
}

func TestCompiler_PartialInputs(t *testing.T) {
	inputDir := t.TempDir()
	outputDir := t.TempDir()

	// Create only scope.json
	scope := ScopeData{
		BaseRef:  "main",
		HeadRef:  "HEAD",
		Language: "go",
	}
	scopeData, _ := json.Marshal(scope)
	os.WriteFile(filepath.Join(inputDir, "scope.json"), scopeData, 0644)

	compiler := NewCompiler(inputDir, outputDir)
	if err := compiler.Compile(); err != nil {
		t.Fatalf("Compile() error with partial inputs: %v", err)
	}

	// Verify files were created
	for _, reviewer := range GetReviewerNames() {
		contextPath := filepath.Join(outputDir, "context-"+reviewer+".md")
		if _, err := os.Stat(contextPath); os.IsNotExist(err) {
			t.Errorf("Context file not created for %s with partial inputs", reviewer)
		}
	}
}

// Helper function to create sample phase outputs for testing
func createSamplePhaseOutputs(t *testing.T, dir string) {
	t.Helper()

	// scope.json
	scope := ScopeData{
		BaseRef:          "main",
		HeadRef:          "HEAD",
		Language:         "go",
		ModifiedFiles:    []string{"internal/handler/user.go"},
		AddedFiles:       []string{"internal/service/notification.go"},
		TotalFiles:       2,
		TotalAdditions:   100,
		TotalDeletions:   10,
		PackagesAffected: []string{"internal/handler", "internal/service"},
	}
	writeJSON(t, dir, "scope.json", scope)

	// static-analysis.json
	static := StaticAnalysisData{
		ToolVersions: map[string]string{"golangci-lint": "1.56.0"},
		Findings: []Finding{
			{Tool: "staticcheck", Rule: "SA1019", Severity: "warning", File: "user.go", Line: 45, Message: "deprecated", Category: "deprecation"},
			{Tool: "gosec", Rule: "G401", Severity: "high", File: "crypto.go", Line: 23, Message: "weak crypto", Category: "security"},
		},
		Summary: FindingSummary{High: 1, Warning: 1},
	}
	writeJSON(t, dir, "static-analysis.json", static)

	// go-ast.json
	ast := ASTData{
		Functions: FunctionChanges{
			Modified: []FunctionDiff{
				{
					Name:    "CreateUser",
					Package: "handler",
					File:    "user.go",
					Before:  FunctionInfo{Signature: "func CreateUser(ctx context.Context)", LineStart: 10, LineEnd: 20},
					After:   FunctionInfo{Signature: "func CreateUser(ctx context.Context, opts ...Option)", LineStart: 10, LineEnd: 30},
					Changes: []string{"added_param"},
				},
			},
			Added: []FunctionInfo{
				{Name: "NotifyUser", Package: "service", File: "notification.go", Signature: "func NotifyUser(ctx context.Context)", LineStart: 10, LineEnd: 40},
			},
		},
	}
	writeJSON(t, dir, "go-ast.json", ast)

	// go-calls.json
	calls := CallGraphData{
		ModifiedFunctions: []FunctionCallGraph{
			{
				Function: "handler.CreateUser",
				File:     "user.go",
				Callers: []CallSite{
					{Function: "router.ServeHTTP", File: "router.go", Line: 89},
				},
				TestCoverage: []TestCoverage{
					{TestFunction: "TestCreateUser", File: "user_test.go", Line: 23},
				},
			},
		},
		ImpactAnalysis: ImpactSummary{DirectCallers: 1, AffectedTests: 1},
	}
	writeJSON(t, dir, "go-calls.json", calls)

	// go-flow.json
	flow := DataFlowData{
		Flows: []DataFlow{
			{
				ID:        "flow-1",
				Risk:      "medium",
				Sanitized: false,
				Source:    FlowSource{Type: "http_request", File: "user.go", Line: 23},
				Sink:      FlowSink{Type: "database", File: "repo.go", Line: 45},
			},
		},
		NilSources: []NilSource{
			{Variable: "user", File: "user.go", Line: 67, Checked: true, Risk: "low"},
			{Variable: "config", File: "service.go", Line: 23, Checked: false, Risk: "high", Notes: "env var"},
		},
		Summary: FlowSummary{TotalFlows: 1, MediumRisk: 1, NilRisks: 1},
	}
	writeJSON(t, dir, "go-flow.json", flow)
}

func writeJSON(t *testing.T, dir, filename string, data interface{}) {
	t.Helper()
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		t.Fatalf("Failed to marshal %s: %v", filename, err)
	}
	if err := os.WriteFile(filepath.Join(dir, filename), jsonData, 0644); err != nil {
		t.Fatalf("Failed to write %s: %v", filename, err)
	}
}
```

**Step 2: Run tests**

Run: `cd scripts/ring:codereview && go test -v ./internal/context/... && cd ../..`

**Expected output:**
```
=== RUN   TestCompiler_Compile
--- PASS: TestCompiler_Compile (0.XX s)
=== RUN   TestCompiler_CodeReviewerContext
--- PASS: TestCompiler_CodeReviewerContext (0.XX s)
=== RUN   TestCompiler_SecurityReviewerContext
--- PASS: TestCompiler_SecurityReviewerContext (0.XX s)
=== RUN   TestCompiler_MissingInputs
--- PASS: TestCompiler_MissingInputs (0.XX s)
=== RUN   TestCompiler_PartialInputs
--- PASS: TestCompiler_PartialInputs (0.XX s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/context
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/internal/context/compiler_test.go
git commit -m "test(ring:codereview): add compiler integration tests

Tests full compilation flow, individual reviewer contexts,
missing inputs handling, and partial inputs scenarios."
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Error messages for file path issues
   - Fix: Ensure temp directories are created correctly
   - Rollback: `git checkout -- scripts/ring:codereview/internal/context/compiler_test.go`

---

## Task 8: Implement compile-context CLI

**Files:**
- Create: `scripts/ring:codereview/cmd/compile-context/main.go`

**Prerequisites:**
- Tasks 6-7 completed

**Step 1: Create CLI binary**

Create file `scripts/ring:codereview/cmd/compile-context/main.go`:

```go
// compile-context aggregates analysis phase outputs into reviewer-specific context files.
//
// Usage:
//
//	compile-context --input=.ring/ring:codereview/ --output=.ring/ring:codereview/
//
// This binary reads all phase outputs (scope.json, static-analysis.json, etc.)
// and generates context files for each reviewer:
//   - context-ring:code-reviewer.md
//   - context-ring:security-reviewer.md
//   - context-ring:business-logic-reviewer.md
//   - context-ring:test-reviewer.md
//   - context-ring:nil-safety-reviewer.md
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/context"
)

func main() {
	inputDir := flag.String("input", ".ring/ring:codereview", "Directory containing phase outputs")
	outputDir := flag.String("output", "", "Directory to write context files (defaults to input dir)")
	verbose := flag.Bool("verbose", false, "Enable verbose output")
	help := flag.Bool("help", false, "Show help message")

	flag.Parse()

	if *help {
		printUsage()
		os.Exit(0)
	}

	// Default output to input directory
	if *outputDir == "" {
		*outputDir = *inputDir
	}

	// Verify input directory exists
	if _, err := os.Stat(*inputDir); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Error: Input directory does not exist: %s\n", *inputDir)
		os.Exit(1)
	}

	if *verbose {
		fmt.Printf("Input directory: %s\n", *inputDir)
		fmt.Printf("Output directory: %s\n", *outputDir)
	}

	// Create compiler and run
	compiler := context.NewCompiler(*inputDir, *outputDir)
	if err := compiler.Compile(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: Compilation failed: %v\n", err)
		os.Exit(1)
	}

	if *verbose {
		fmt.Println("Context files generated:")
		for _, reviewer := range context.GetReviewerNames() {
			fmt.Printf("  - context-%s.md\n", reviewer)
		}
	}

	fmt.Println("Context compilation complete.")
}

func printUsage() {
	fmt.Println(`compile-context - Generate reviewer-specific context files

Usage:
  compile-context [flags]

Flags:
  --input DIR    Directory containing phase outputs (default: .ring/ring:codereview)
  --output DIR   Directory to write context files (default: same as input)
  --verbose      Enable verbose output
  --help         Show this help message

Examples:
  # Compile context from default location
  compile-context

  # Specify custom input/output directories
  compile-context --input=/path/to/analysis --output=/path/to/output

  # Verbose mode
  compile-context --verbose

Phase Outputs Expected (in input directory):
  - scope.json           (Phase 0: Scope detection)
  - static-analysis.json (Phase 1: Static analysis)
  - {go,ts,py}-ast.json  (Phase 2: AST extraction)
  - {go,ts,py}-calls.json (Phase 3: Call graph)
  - {go,ts,py}-flow.json (Phase 4: Data flow)

Context Files Generated (in output directory):
  - context-ring:code-reviewer.md
  - context-ring:security-reviewer.md
  - context-ring:business-logic-reviewer.md
  - context-ring:test-reviewer.md
  - context-ring:nil-safety-reviewer.md
`)
}
```

**Step 2: Verify compilation**

Run: `cd scripts/ring:codereview && go build -o bin/compile-context ./cmd/compile-context && cd ../..`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Test binary**

Run: `scripts/ring:codereview/bin/compile-context --help`

**Expected output:**
```
compile-context - Generate reviewer-specific context files

Usage:
  compile-context [flags]
...
```

**Step 4: Commit**

```bash
git add scripts/ring:codereview/cmd/compile-context/main.go
git commit -m "feat(ring:codereview): add compile-context CLI binary

Phase 5 binary that reads all phase outputs and generates
reviewer-specific context markdown files."
```

**If Task Fails:**

1. **Build fails:**
   - Check: Import path for context package
   - Fix: Ensure module path matches
   - Rollback: `rm -rf scripts/ring:codereview/cmd/compile-context`

---

## Task 9: Implement run-all Orchestrator

**Files:**
- Create: `scripts/ring:codereview/cmd/run-all/main.go`

**Prerequisites:**
- Task 8 completed

**Step 1: Create orchestrator binary**

Create file `scripts/ring:codereview/cmd/run-all/main.go`:

```go
// run-all orchestrates the complete code review pre-analysis pipeline.
//
// Usage:
//
//	run-all --base=main --head=HEAD --output=.ring/ring:codereview/
//
// This binary runs all phases in sequence:
//   - Phase 0: Scope detection
//   - Phase 1: Static analysis
//   - Phase 2: AST extraction
//   - Phase 3: Call graph analysis
//   - Phase 4: Data flow analysis
//   - Phase 5: Context compilation
package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// Phase represents a single analysis phase.
type Phase struct {
	Name    string
	Binary  string
	Args    func(cfg *Config) []string
	Output  string
	Timeout time.Duration
}

// Config holds the configuration for the pipeline run.
type Config struct {
	BaseRef   string
	HeadRef   string
	OutputDir string
	BinDir    string
	Verbose   bool
}

func main() {
	baseRef := flag.String("base", "main", "Base git ref for comparison")
	headRef := flag.String("head", "HEAD", "Head git ref for comparison")
	outputDir := flag.String("output", ".ring/ring:codereview", "Output directory for analysis results")
	binDir := flag.String("bin-dir", "", "Directory containing analysis binaries (auto-detected)")
	verbose := flag.Bool("verbose", false, "Enable verbose output")
	skipPhases := flag.String("skip", "", "Comma-separated phases to skip (e.g., 'ast,callgraph')")
	help := flag.Bool("help", false, "Show help message")

	flag.Parse()

	if *help {
		printUsage()
		os.Exit(0)
	}

	// Auto-detect bin directory
	if *binDir == "" {
		execPath, err := os.Executable()
		if err == nil {
			*binDir = filepath.Dir(execPath)
		} else {
			*binDir = "scripts/ring:codereview/bin"
		}
	}

	cfg := &Config{
		BaseRef:   *baseRef,
		HeadRef:   *headRef,
		OutputDir: *outputDir,
		BinDir:    *binDir,
		Verbose:   *verbose,
	}

	// Create output directory
	if err := os.MkdirAll(cfg.OutputDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to create output directory: %v\n", err)
		os.Exit(1)
	}

	// Parse skip phases
	skipMap := parseSkipPhases(*skipPhases)

	// Define phases
	phases := []Phase{
		{
			Name:   "scope",
			Binary: "scope-detector",
			Args: func(c *Config) []string {
				return []string{"--base", c.BaseRef, "--head", c.HeadRef, "--output", filepath.Join(c.OutputDir, "scope.json")}
			},
			Output:  "scope.json",
			Timeout: 30 * time.Second,
		},
		{
			Name:   "static-analysis",
			Binary: "static-analysis",
			Args: func(c *Config) []string {
				return []string{"--scope", filepath.Join(c.OutputDir, "scope.json"), "--output", c.OutputDir}
			},
			Output:  "static-analysis.json",
			Timeout: 5 * time.Minute,
		},
		{
			Name:   "ast",
			Binary: "ast-extractor",
			Args: func(c *Config) []string {
				return []string{"--scope", filepath.Join(c.OutputDir, "scope.json"), "--output", c.OutputDir}
			},
			Output:  "*-ast.json",
			Timeout: 2 * time.Minute,
		},
		{
			Name:   "callgraph",
			Binary: "call-graph",
			Args: func(c *Config) []string {
				return []string{"--scope", filepath.Join(c.OutputDir, "scope.json"), "--output", c.OutputDir}
			},
			Output:  "*-calls.json",
			Timeout: 3 * time.Minute,
		},
		{
			Name:   "dataflow",
			Binary: "data-flow",
			Args: func(c *Config) []string {
				return []string{"--scope", filepath.Join(c.OutputDir, "scope.json"), "--output", c.OutputDir}
			},
			Output:  "*-flow.json",
			Timeout: 3 * time.Minute,
		},
		{
			Name:   "context",
			Binary: "compile-context",
			Args: func(c *Config) []string {
				return []string{"--input", c.OutputDir, "--output", c.OutputDir}
			},
			Output:  "context-*.md",
			Timeout: 30 * time.Second,
		},
	}

	// Run phases
	startTime := time.Now()
	failedPhases := []string{}

	for _, phase := range phases {
		if skipMap[phase.Name] {
			if cfg.Verbose {
				fmt.Printf("Skipping phase: %s\n", phase.Name)
			}
			continue
		}

		if cfg.Verbose {
			fmt.Printf("Running phase: %s\n", phase.Name)
		}

		if err := runPhase(cfg, phase); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: Phase %s failed: %v\n", phase.Name, err)
			failedPhases = append(failedPhases, phase.Name)
			// Continue with remaining phases for graceful degradation
		}
	}

	elapsed := time.Since(startTime)

	// Summary
	fmt.Println()
	fmt.Println("=== Pre-Analysis Complete ===")
	fmt.Printf("Duration: %v\n", elapsed.Round(time.Millisecond))
	fmt.Printf("Output: %s\n", cfg.OutputDir)

	if len(failedPhases) > 0 {
		fmt.Printf("Failed phases: %v\n", failedPhases)
		fmt.Println("Some context may be incomplete. Reviewers will proceed with available data.")
		os.Exit(1) // Non-zero exit for CI awareness
	}

	fmt.Println("All phases completed successfully.")
}

func runPhase(cfg *Config, phase Phase) error {
	binaryPath := filepath.Join(cfg.BinDir, phase.Binary)

	// Check if binary exists
	if _, err := os.Stat(binaryPath); os.IsNotExist(err) {
		return fmt.Errorf("binary not found: %s", binaryPath)
	}

	args := phase.Args(cfg)
	cmd := exec.Command(binaryPath, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if cfg.Verbose {
		fmt.Printf("  Command: %s %v\n", binaryPath, args)
	}

	// Run with timeout
	done := make(chan error, 1)
	go func() {
		done <- cmd.Run()
	}()

	select {
	case err := <-done:
		return err
	case <-time.After(phase.Timeout):
		if cmd.Process != nil {
			cmd.Process.Kill()
		}
		return fmt.Errorf("timeout after %v", phase.Timeout)
	}
}

func parseSkipPhases(skip string) map[string]bool {
	skipMap := make(map[string]bool)
	if skip == "" {
		return skipMap
	}
	for _, phase := range splitAndTrim(skip, ',') {
		skipMap[phase] = true
	}
	return skipMap
}

func splitAndTrim(s string, sep rune) []string {
	var result []string
	current := ""
	for _, c := range s {
		if c == sep {
			if current != "" {
				result = append(result, current)
				current = ""
			}
		} else if c != ' ' {
			current += string(c)
		}
	}
	if current != "" {
		result = append(result, current)
	}
	return result
}

func printUsage() {
	fmt.Println(`run-all - Orchestrate complete code review pre-analysis pipeline

Usage:
  run-all [flags]

Flags:
  --base REF     Base git ref for comparison (default: main)
  --head REF     Head git ref for comparison (default: HEAD)
  --output DIR   Output directory for results (default: .ring/ring:codereview)
  --bin-dir DIR  Directory containing binaries (auto-detected)
  --skip PHASES  Comma-separated phases to skip
  --verbose      Enable verbose output
  --help         Show this help message

Phases (in order):
  1. scope          - Detect changed files and language
  2. static-analysis - Run linters and static analyzers
  3. ast            - Extract AST and semantic changes
  4. callgraph      - Analyze call graphs and impact
  5. dataflow       - Track data flow and nil sources
  6. context        - Compile reviewer context files

Examples:
  # Run full pipeline
  run-all

  # Compare specific refs
  run-all --base=origin/main --head=feature-branch

  # Skip slow phases
  run-all --skip=callgraph,dataflow

  # Custom output location
  run-all --output=/tmp/ring:codereview-analysis

Graceful Degradation:
  If a phase fails, subsequent phases continue with available data.
  Context files will note missing analysis sections.
`)
}
```

**Step 2: Verify compilation**

Run: `cd scripts/ring:codereview && go build -o bin/run-all ./cmd/run-all && cd ../..`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Test binary**

Run: `scripts/ring:codereview/bin/run-all --help`

**Expected output:**
```
run-all - Orchestrate complete code review pre-analysis pipeline

Usage:
  run-all [flags]
...
```

**Step 4: Commit**

```bash
git add scripts/ring:codereview/cmd/run-all/main.go
git commit -m "feat(ring:codereview): add run-all orchestrator binary

Main entry point that runs all analysis phases (0-5) in sequence
with timeout handling and graceful degradation on failures."
```

**If Task Fails:**

1. **Build fails:**
   - Check: Import paths and command structure
   - Fix: Ensure all packages are importable
   - Rollback: `rm -rf scripts/ring:codereview/cmd/run-all`

---

## Task 10: Update Makefile

**Files:**
- Modify: `scripts/ring:codereview/Makefile`

**Prerequisites:**
- Tasks 8-9 completed

**Step 1: Update Makefile with new targets**

Modify `scripts/ring:codereview/Makefile` to add the new binaries:

```makefile
.PHONY: all build test clean install fmt vet lint

# Binary output directory
BIN_DIR := bin

# All binaries to build
BINARIES := scope-detector static-analysis ast-extractor call-graph data-flow compile-context run-all

all: build

build: $(BINARIES)

scope-detector:
	@echo "Building scope-detector..."
	@go build -o $(BIN_DIR)/scope-detector ./cmd/scope-detector

static-analysis:
	@echo "Building static-analysis..."
	@go build -o $(BIN_DIR)/static-analysis ./cmd/static-analysis

ast-extractor:
	@echo "Building ast-extractor..."
	@go build -o $(BIN_DIR)/ast-extractor ./cmd/ast-extractor

call-graph:
	@echo "Building call-graph..."
	@go build -o $(BIN_DIR)/call-graph ./cmd/call-graph

data-flow:
	@echo "Building data-flow..."
	@go build -o $(BIN_DIR)/data-flow ./cmd/data-flow

compile-context:
	@echo "Building compile-context..."
	@go build -o $(BIN_DIR)/compile-context ./cmd/compile-context

run-all:
	@echo "Building run-all..."
	@go build -o $(BIN_DIR)/run-all ./cmd/run-all

test:
	@echo "Running tests..."
	@go test -v -race ./...

test-coverage:
	@echo "Running tests with coverage..."
	@go test -v -race -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

clean:
	@echo "Cleaning..."
	@rm -rf $(BIN_DIR)
	@rm -f coverage.out coverage.html

install: build
	@echo "Installing binaries to $(BIN_DIR)..."
	@chmod +x $(BIN_DIR)/*

# Development helpers
fmt:
	@go fmt ./...

vet:
	@go vet ./...

lint: fmt vet

# Quick build for development (only context-related)
build-context: compile-context run-all
	@echo "Context binaries built."
```

**Step 2: Verify Makefile**

Run: `cd scripts/ring:codereview && make build-context && cd ../..`

**Expected output:**
```
Building compile-context...
Building run-all...
Context binaries built.
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/Makefile
git commit -m "build(ring:codereview): add compile-context and run-all targets to Makefile

Updates Makefile with Phase 5 binaries and convenience target build-context."
```

**If Task Fails:**

1. **Make fails:**
   - Check: Tab vs spaces in Makefile
   - Fix: Ensure tabs are used for indentation
   - Rollback: `git checkout -- scripts/ring:codereview/Makefile`

---

## Task 11: Update install.sh

**Files:**
- Modify: `scripts/ring:codereview/install.sh`

**Prerequisites:**
- Task 10 completed

**Step 1: Update install.sh with new binaries**

If `scripts/ring:codereview/install.sh` exists, update it. If not, create it:

```bash
#!/bin/bash
set -e

# Installs all required tools for ring:codereview pre-analysis
# Run: ./scripts/ring:codereview/install.sh [go|ts|py|all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_TARGET="${1:-all}"

install_go_tools() {
    echo "=== Installing Go tools ==="
    go install honnef.co/go/tools/cmd/staticcheck@latest
    go install github.com/securego/gosec/v2/cmd/gosec@latest
    go install golang.org/x/tools/cmd/callgraph@latest
    go install golang.org/x/tools/cmd/guru@latest

    # golangci-lint (platform-specific)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install golangci-lint 2>/dev/null || brew upgrade golangci-lint 2>/dev/null || true
    else
        curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b "$(go env GOPATH)/bin"
    fi
    echo "Go tools installed"
}

install_ts_tools() {
    echo "=== Installing TypeScript tools ==="
    npm install -g typescript dependency-cruiser madge
    
    # Install local TS helper deps
    if [ -d "$SCRIPT_DIR/ts" ]; then
        cd "$SCRIPT_DIR/ts"
        npm install
        cd -
    fi
    echo "TypeScript tools installed"
}

install_py_tools() {
    echo "=== Installing Python tools ==="
    pip install --upgrade ruff mypy pylint bandit pyan3
    
    # Verify Python helper has no external deps (uses stdlib ast)
    python3 -c "import ast; print('Python ast module: OK')"
    echo "Python tools installed"
}

build_binaries() {
    echo "=== Building Go analysis binaries ==="
    cd "$SCRIPT_DIR"
    
    # Ensure bin directory exists
    mkdir -p bin
    
    # Build all binaries
    go build -o bin/scope-detector ./cmd/scope-detector
    go build -o bin/static-analysis ./cmd/static-analysis
    go build -o bin/ast-extractor ./cmd/ast-extractor
    go build -o bin/call-graph ./cmd/call-graph
    go build -o bin/data-flow ./cmd/data-flow
    go build -o bin/compile-context ./cmd/compile-context
    go build -o bin/run-all ./cmd/run-all
    
    cd -
    echo "Binaries built"
}

verify_installation() {
    echo "=== Verifying installation ==="
    local missing=""
    
    # Check Go binaries
    for bin in scope-detector static-analysis compile-context run-all; do
        if [ ! -f "$SCRIPT_DIR/bin/$bin" ]; then
            missing="$missing $bin"
        fi
    done
    
    if [ -n "$missing" ]; then
        echo "Warning: Missing binaries:$missing"
        echo "Run './install.sh all' to build all binaries."
    else
        echo "All binaries present."
    fi
}

case "$INSTALL_TARGET" in
    go)
        install_go_tools
        ;;
    ts)
        install_ts_tools
        ;;
    py)
        install_py_tools
        ;;
    build)
        build_binaries
        ;;
    all)
        install_go_tools
        install_ts_tools
        install_py_tools
        build_binaries
        verify_installation
        ;;
    verify)
        verify_installation
        ;;
    *)
        echo "Usage: $0 [go|ts|py|build|all|verify]"
        exit 1
        ;;
esac

echo ""
echo "Installation complete!"
echo "Run '$0 verify' to verify installation."
```

**Step 2: Make script executable**

Run: `chmod +x scripts/ring:codereview/install.sh`

**Step 3: Commit**

```bash
git add scripts/ring:codereview/install.sh
git commit -m "build(ring:codereview): update install.sh with all Phase 5 binaries

Includes compile-context and run-all in build targets, adds verify option."
```

**If Task Fails:**

1. **Script fails:**
   - Check: Bash syntax
   - Fix: Verify shebang and variable expansion
   - Rollback: `git checkout -- scripts/ring:codereview/install.sh`

---

## Task 12: Code Review Checkpoint

**Prerequisites:**
- Tasks 1-11 completed

**Step 1: Run all tests**

Run: `cd scripts/ring:codereview && go test -v -race ./... && cd ../..`

**Expected output:**
```
=== RUN   TestReviewerNames
--- PASS: TestReviewerNames (0.00s)
...
=== RUN   TestCompiler_Compile
--- PASS: TestCompiler_Compile (0.XX s)
...
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/context
```

**Step 2: Build all binaries**

Run: `cd scripts/ring:codereview && make build-context && cd ../..`

**Expected output:**
```
Building compile-context...
Building run-all...
Context binaries built.
```

**Step 3: Dispatch code review**

1. **REQUIRED SUB-SKILL: Use ring:requesting-code-review**
2. All reviewers run simultaneously (ring:code-reviewer, ring:business-logic-reviewer, ring:security-reviewer, ring:test-reviewer, ring:nil-safety-reviewer)
3. Wait for all to complete

**Step 4: Handle findings by severity (MANDATORY):**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 5 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location

**Step 5: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments added
- All Cosmetic issues have FIXME(nitpick): comments added

---

## Task 13: Build and Verify

**Prerequisites:**
- Task 12 completed

**Step 1: Full build**

Run: `cd scripts/ring:codereview && make clean && make build && cd ../..`

**Expected output:**
```
Cleaning...
Building scope-detector...
Building static-analysis...
Building ast-extractor...
Building call-graph...
Building data-flow...
Building compile-context...
Building run-all...
```

**Step 2: Verify binary sizes**

Run: `ls -lh scripts/ring:codereview/bin/`

**Expected output:**
```
total XX
-rwxr-xr-x  1 user  staff  X.XM Jan 13 XX:XX compile-context
-rwxr-xr-x  1 user  staff  X.XM Jan 13 XX:XX run-all
...
```

**Step 3: Test compile-context with sample data**

```bash
# Create test directory
mkdir -p /tmp/test-ring:codereview

# Create minimal scope.json
cat > /tmp/test-ring:codereview/scope.json << 'EOF'
{
  "base_ref": "main",
  "head_ref": "HEAD",
  "language": "go",
  "modified": ["user.go"],
  "added": [],
  "deleted": [],
  "total_files": 1,
  "total_additions": 10,
  "total_deletions": 5,
  "packages_affected": ["internal/handler"]
}
EOF

# Run compile-context
scripts/ring:codereview/bin/compile-context --input=/tmp/test-ring:codereview --output=/tmp/test-ring:codereview --verbose

# Verify output
ls -la /tmp/test-ring:codereview/context-*.md
```

**Expected output:**
```
Input directory: /tmp/test-ring:codereview
Output directory: /tmp/test-ring:codereview
Context files generated:
  - context-ring:code-reviewer.md
  - context-ring:security-reviewer.md
  - context-ring:business-logic-reviewer.md
  - context-ring:test-reviewer.md
  - context-ring:nil-safety-reviewer.md
Context compilation complete.
...
-rw-r--r--  1 user  staff  XXX Jan 13 XX:XX /tmp/test-ring:codereview/context-ring:code-reviewer.md
...
```

**Step 4: Cleanup test data**

Run: `rm -rf /tmp/test-ring:codereview`

**Step 5: Final commit**

```bash
git add .
git commit -m "feat(ring:codereview): complete Phase 5 context compilation

Implements:
- context package with types, templates, and compiler
- compile-context binary for generating reviewer context files
- run-all binary for orchestrating the full analysis pipeline
- Updated Makefile and install.sh

All 5 reviewers get dedicated context files:
- context-ring:code-reviewer.md
- context-ring:security-reviewer.md
- context-ring:business-logic-reviewer.md
- context-ring:test-reviewer.md
- context-ring:nil-safety-reviewer.md"
```

**If Task Fails:**

1. **Build fails:**
   - Check: `go build` error messages
   - Fix: Address compilation errors
   - Rollback: `git reset --hard HEAD~1`

2. **Test run fails:**
   - Check: Binary execution errors
   - Fix: Verify input JSON format
   - Rollback: N/A (test data is temporary)

---

## Plan Checklist

Before executing this plan, verify:

- [ ] **Historical precedent queried** (artifact-query --mode planning)
- [ ] Historical Precedent section included in plan
- [ ] Header with goal, architecture, tech stack, prerequisites
- [ ] Verification commands with expected output
- [ ] Tasks broken into bite-sized steps (2-5 min each)
- [ ] Exact file paths for all files
- [ ] Complete code (no placeholders)
- [ ] Exact commands with expected output
- [ ] Failure recovery steps for each task
- [ ] Code review checkpoints after batches
- [ ] Severity-based issue handling documented
- [ ] Passes Zero-Context Test
- [ ] **Plan avoids known failure patterns** (none found)

---

## After Implementation

After completing all tasks:

1. **Verify all tests pass:**
   ```bash
   cd scripts/ring:codereview && go test -v -race ./... && cd ../..
   ```

2. **Verify all binaries build:**
   ```bash
   cd scripts/ring:codereview && make clean && make build && cd ../..
   ```

3. **Integration test with real project:**
   ```bash
   # In a Go project with changes
   scripts/ring:codereview/bin/run-all --base=main --head=HEAD --verbose
   ```

4. **Review generated context files** in `.ring/ring:codereview/`:
   - Verify each reviewer's context file contains relevant data
   - Check that focus areas are actionable
   - Ensure empty sections show appropriate "no data" messages
