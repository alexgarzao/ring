# Phase 3: Call Graph Analysis Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build call graph analysis for Go, TypeScript, and Python that identifies callers, callees, and test coverage for modified functions.

**Architecture:** Multi-language call graph analyzer that wraps external tools (callgraph/guru for Go, dependency-cruiser for TypeScript, pyan3 for Python) with a unified Go binary orchestrator. Consumes AST output from Phase 2, produces structured JSON with impact analysis.

**Tech Stack:**
- Go 1.21+ (main binary, internal packages)
- golang.org/x/tools/go/callgraph (CHA algorithm)
- golang.org/x/tools/go/packages (package loading)
- dependency-cruiser (TypeScript)
- pyan3 + custom Python script (Python)

**Global Prerequisites:**
- Environment: macOS/Linux, Go 1.21+, Node.js 18+, Python 3.10+
- Tools: `go`, `node`, `npm`, `python3`, `pip`
- Access: Write access to `scripts/codereview/` directory
- State: Phase 2 completed (provides `{lang}-ast.json` files)

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
go version          # Expected: go version go1.21+ or higher
node --version      # Expected: v18.0.0 or higher
python3 --version   # Expected: Python 3.10+ or higher
ls scripts/codereview/internal/ast/  # Expected: golang.go, typescript.go, python.go (from Phase 2)
```

## Historical Precedent

**Query:** "call graph analysis static code review"
**Index Status:** Empty (new feature)

No historical data available for call graph analysis. This is a new capability.
Proceeding with standard planning approach.

---

## Task Overview

| Task | Description | Time Est. |
|------|-------------|-----------|
| 1-4 | Go call graph core implementation | 20 min |
| 5-7 | TypeScript call graph wrapper | 15 min |
| 8-11 | Python call graph implementation | 20 min |
| 12-14 | Impact summary renderer | 15 min |
| 15-17 | CLI orchestrator | 15 min |
| 18-20 | Unit tests | 15 min |
| 21 | Integration test | 5 min |
| 22 | Code review checkpoint | 10 min |

**Total estimated time:** 115 minutes

---

## Task 1: Create internal/callgraph/types.go

**Files:**
- Create: `scripts/codereview/internal/callgraph/types.go`

**Prerequisites:**
- Tools: Go 1.21+
- Directory `scripts/codereview/internal/` must exist (from Phase 2)

**Step 1: Write the types file**

```go
// Package callgraph provides call graph analysis for multiple languages.
package callgraph

// CallInfo represents a single caller or callee relationship.
type CallInfo struct {
	Function string `json:"function"`
	File     string `json:"file"`
	Line     int    `json:"line"`
	CallSite string `json:"call_site,omitempty"`
}

// TestCoverage represents a test that covers a function.
type TestCoverage struct {
	TestFunction string `json:"test_function"`
	File         string `json:"file"`
	Line         int    `json:"line"`
}

// FunctionCallGraph represents the call graph for a single modified function.
type FunctionCallGraph struct {
	Function     string         `json:"function"`
	File         string         `json:"file"`
	Callers      []CallInfo     `json:"callers"`
	Callees      []CallInfo     `json:"callees"`
	TestCoverage []TestCoverage `json:"test_coverage"`
}

// ImpactAnalysis summarizes the impact of all changes.
type ImpactAnalysis struct {
	DirectCallers     int      `json:"direct_callers"`
	TransitiveCallers int      `json:"transitive_callers"`
	AffectedTests     int      `json:"affected_tests"`
	AffectedPackages  []string `json:"affected_packages"`
}

// CallGraphResult is the output schema for call graph analysis.
type CallGraphResult struct {
	Language          string              `json:"language"`
	ModifiedFunctions []FunctionCallGraph `json:"modified_functions"`
	ImpactAnalysis    ImpactAnalysis      `json:"impact_analysis"`
	TimeBudgetExceeded bool               `json:"time_budget_exceeded,omitempty"`
	PartialResults    bool                `json:"partial_results,omitempty"`
	Warnings          []string            `json:"warnings,omitempty"`
}

// ModifiedFunction represents a function from AST analysis (input).
type ModifiedFunction struct {
	Name     string `json:"name"`
	File     string `json:"file"`
	Package  string `json:"package"`
	Receiver string `json:"receiver,omitempty"`
}

// Analyzer defines the interface for language-specific call graph analyzers.
type Analyzer interface {
	// Analyze builds call graph for the given modified functions.
	// timeBudgetSec is the maximum time allowed (0 = no limit).
	Analyze(modifiedFuncs []ModifiedFunction, timeBudgetSec int) (*CallGraphResult, error)
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/types.go
git commit -m "feat(codereview): add call graph types for Phase 3"
```

---

## Task 2: Create internal/callgraph/golang.go - Package Loading

**Files:**
- Create: `scripts/codereview/internal/callgraph/golang.go`

**Prerequisites:**
- Task 1 completed
- `go.mod` exists in `scripts/codereview/`

**Step 1: Update go.mod with dependencies**

Run: `cd scripts/codereview && go get golang.org/x/tools/go/packages golang.org/x/tools/go/callgraph/cha golang.org/x/tools/go/ssa golang.org/x/tools/go/ssa/ssautil`

**Expected output:**
```
go: added golang.org/x/tools v0.X.X
```

**Step 2: Write the Go analyzer foundation**

```go
package callgraph

import (
	"context"
	"fmt"
	"go/token"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/tools/go/packages"
	"golang.org/x/tools/go/callgraph"
	"golang.org/x/tools/go/callgraph/cha"
	"golang.org/x/tools/go/ssa"
	"golang.org/x/tools/go/ssa/ssautil"
)

// GoAnalyzer implements call graph analysis for Go code.
type GoAnalyzer struct {
	workDir    string
	testDirs   []string
}

// NewGoAnalyzer creates a new Go call graph analyzer.
func NewGoAnalyzer(workDir string) *GoAnalyzer {
	return &GoAnalyzer{
		workDir:  workDir,
		testDirs: []string{},
	}
}

// loadPackages loads Go packages for the given patterns.
func (g *GoAnalyzer) loadPackages(ctx context.Context, patterns []string) ([]*packages.Package, error) {
	cfg := &packages.Config{
		Mode: packages.NeedName |
			packages.NeedFiles |
			packages.NeedCompiledGoFiles |
			packages.NeedImports |
			packages.NeedDeps |
			packages.NeedTypes |
			packages.NeedSyntax |
			packages.NeedTypesInfo,
		Dir:     g.workDir,
		Context: ctx,
	}

	pkgs, err := packages.Load(cfg, patterns...)
	if err != nil {
		return nil, fmt.Errorf("loading packages: %w", err)
	}

	// Check for package errors
	var errs []string
	for _, pkg := range pkgs {
		for _, e := range pkg.Errors {
			errs = append(errs, e.Error())
		}
	}
	if len(errs) > 0 {
		return pkgs, fmt.Errorf("package errors: %s", strings.Join(errs, "; "))
	}

	return pkgs, nil
}

// buildSSA builds SSA form for the loaded packages.
func (g *GoAnalyzer) buildSSA(pkgs []*packages.Package) (*ssa.Program, []*ssa.Package) {
	prog, ssaPkgs := ssautil.AllPackages(pkgs, ssa.InstantiateGenerics)
	prog.Build()
	return prog, ssaPkgs
}

// getAffectedPackages extracts unique package patterns from modified functions.
func getAffectedPackages(funcs []ModifiedFunction) []string {
	pkgSet := make(map[string]bool)
	for _, f := range funcs {
		if f.Package != "" {
			pkgSet[f.Package] = true
		} else if f.File != "" {
			// Derive package from file path
			dir := filepath.Dir(f.File)
			pkgSet["./"+dir] = true
		}
	}

	patterns := make([]string, 0, len(pkgSet))
	for pkg := range pkgSet {
		patterns = append(patterns, pkg)
	}
	return patterns
}
```

**Step 3: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 4: Commit**

```bash
git add scripts/codereview/internal/callgraph/golang.go scripts/codereview/go.mod scripts/codereview/go.sum
git commit -m "feat(codereview): add Go call graph package loading"
```

---

## Task 3: Implement Go Call Graph Analysis

**Files:**
- Modify: `scripts/codereview/internal/callgraph/golang.go`

**Prerequisites:**
- Task 2 completed

**Step 1: Add the Analyze method**

Append to `golang.go`:

```go
// Analyze implements Analyzer interface for Go.
func (g *GoAnalyzer) Analyze(modifiedFuncs []ModifiedFunction, timeBudgetSec int) (*CallGraphResult, error) {
	result := &CallGraphResult{
		Language:          "go",
		ModifiedFunctions: []FunctionCallGraph{},
		ImpactAnalysis:    ImpactAnalysis{},
	}

	if len(modifiedFuncs) == 0 {
		return result, nil
	}

	// Set up context with timeout
	ctx := context.Background()
	var cancel context.CancelFunc
	if timeBudgetSec > 0 {
		ctx, cancel = context.WithTimeout(ctx, time.Duration(timeBudgetSec)*time.Second)
		defer cancel()
	}

	// Get affected packages
	patterns := getAffectedPackages(modifiedFuncs)
	if len(patterns) == 0 {
		patterns = []string{"./..."}
	}

	// Load packages
	pkgs, err := g.loadPackages(ctx, patterns)
	if err != nil {
		// Return partial results if we can
		result.Warnings = append(result.Warnings, fmt.Sprintf("package loading error: %v", err))
		if len(pkgs) == 0 {
			return result, err
		}
		result.PartialResults = true
	}

	// Check timeout
	select {
	case <-ctx.Done():
		result.TimeBudgetExceeded = true
		result.PartialResults = true
		result.Warnings = append(result.Warnings, "time budget exceeded during package loading")
		return result, nil
	default:
	}

	// Build SSA
	prog, _ := g.buildSSA(pkgs)

	// Build call graph using CHA algorithm (fast, conservative)
	cg := cha.CallGraph(prog)

	// Find callers and callees for each modified function
	affectedPkgs := make(map[string]bool)
	for _, modFunc := range modifiedFuncs {
		funcCG := g.analyzeFunction(cg, prog, modFunc, pkgs)
		result.ModifiedFunctions = append(result.ModifiedFunctions, funcCG)

		// Track affected packages
		for _, caller := range funcCG.Callers {
			pkg := extractPackageFromFile(caller.File)
			if pkg != "" {
				affectedPkgs[pkg] = true
			}
		}

		result.ImpactAnalysis.DirectCallers += len(funcCG.Callers)
		result.ImpactAnalysis.AffectedTests += len(funcCG.TestCoverage)
	}

	// Compile affected packages
	for pkg := range affectedPkgs {
		result.ImpactAnalysis.AffectedPackages = append(result.ImpactAnalysis.AffectedPackages, pkg)
	}

	return result, nil
}

// analyzeFunction builds call graph info for a single function.
func (g *GoAnalyzer) analyzeFunction(cg *callgraph.Graph, prog *ssa.Program, modFunc ModifiedFunction, pkgs []*packages.Package) FunctionCallGraph {
	fcg := FunctionCallGraph{
		Function: modFunc.Name,
		File:     modFunc.File,
		Callers:  []CallInfo{},
		Callees:  []CallInfo{},
		TestCoverage: []TestCoverage{},
	}

	// Find the SSA function
	targetFunc := g.findSSAFunction(prog, modFunc)
	if targetFunc == nil {
		return fcg
	}

	// Get node in call graph
	node := cg.Nodes[targetFunc]
	if node == nil {
		return fcg
	}

	// Find callers (incoming edges)
	for _, edge := range node.In {
		if edge.Caller.Func == nil {
			continue
		}
		caller := edge.Caller.Func
		pos := prog.Fset.Position(edge.Site.Pos())

		callInfo := CallInfo{
			Function: caller.String(),
			File:     pos.Filename,
			Line:     pos.Line,
		}

		// Extract call site text if available
		if edge.Site != nil {
			callInfo.CallSite = edge.Site.String()
		}

		fcg.Callers = append(fcg.Callers, callInfo)

		// Check if caller is a test function
		if isTestFunction(caller.Name()) {
			fcg.TestCoverage = append(fcg.TestCoverage, TestCoverage{
				TestFunction: caller.Name(),
				File:         pos.Filename,
				Line:         int(caller.Pos()),
			})
		}
	}

	// Find callees (outgoing edges)
	for _, edge := range node.Out {
		if edge.Callee.Func == nil {
			continue
		}
		callee := edge.Callee.Func
		pos := prog.Fset.Position(callee.Pos())

		fcg.Callees = append(fcg.Callees, CallInfo{
			Function: callee.String(),
			File:     pos.Filename,
			Line:     pos.Line,
		})
	}

	return fcg
}

// findSSAFunction locates the SSA function matching the modified function.
func (g *GoAnalyzer) findSSAFunction(prog *ssa.Program, modFunc ModifiedFunction) *ssa.Function {
	for fn := range prog.AllFunctions() {
		if fn == nil {
			continue
		}

		// Match by name
		fnName := fn.Name()
		if modFunc.Receiver != "" {
			// Method: check receiver type
			if fn.Signature.Recv() != nil {
				recvType := fn.Signature.Recv().Type().String()
				if strings.Contains(recvType, modFunc.Receiver) && fnName == modFunc.Name {
					return fn
				}
			}
		} else {
			// Function: match by package and name
			if fnName == modFunc.Name {
				pos := prog.Fset.Position(fn.Pos())
				if pos.Filename == modFunc.File || strings.HasSuffix(pos.Filename, modFunc.File) {
					return fn
				}
			}
		}
	}
	return nil
}

// isTestFunction checks if a function name indicates a test function.
func isTestFunction(name string) bool {
	return strings.HasPrefix(name, "Test") ||
		strings.HasPrefix(name, "Benchmark") ||
		strings.HasPrefix(name, "Example")
}

// extractPackageFromFile extracts package name from file path.
func extractPackageFromFile(filePath string) string {
	dir := filepath.Dir(filePath)
	parts := strings.Split(dir, string(filepath.Separator))
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return ""
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/golang.go
git commit -m "feat(codereview): implement Go call graph analysis with CHA"
```

---

## Task 4: Add Transitive Caller Analysis for Go

**Files:**
- Modify: `scripts/codereview/internal/callgraph/golang.go`

**Prerequisites:**
- Task 3 completed

**Step 1: Add transitive caller method**

Add before the closing brace of the file:

```go
// findTransitiveCallers finds all callers up to a certain depth.
func (g *GoAnalyzer) findTransitiveCallers(cg *callgraph.Graph, node *callgraph.Node, maxDepth int) int {
	if node == nil || maxDepth <= 0 {
		return 0
	}

	visited := make(map[*callgraph.Node]bool)
	count := 0

	var visit func(n *callgraph.Node, depth int)
	visit = func(n *callgraph.Node, depth int) {
		if depth > maxDepth || visited[n] {
			return
		}
		visited[n] = true

		for _, edge := range n.In {
			if edge.Caller != nil && !visited[edge.Caller] {
				count++
				visit(edge.Caller, depth+1)
			}
		}
	}

	visit(node, 0)
	return count
}
```

**Step 2: Update Analyze method to use transitive callers**

Find this line in `Analyze`:
```go
result.ImpactAnalysis.DirectCallers += len(funcCG.Callers)
```

Replace with:
```go
result.ImpactAnalysis.DirectCallers += len(funcCG.Callers)

// Count transitive callers
targetFunc := g.findSSAFunction(prog, modFunc)
if targetFunc != nil {
	node := cg.Nodes[targetFunc]
	result.ImpactAnalysis.TransitiveCallers += g.findTransitiveCallers(cg, node, 10)
}
```

**Step 3: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 4: Commit**

```bash
git add scripts/codereview/internal/callgraph/golang.go
git commit -m "feat(codereview): add transitive caller analysis for Go"
```

---

## Task 5: Create internal/callgraph/typescript.go

**Files:**
- Create: `scripts/codereview/internal/callgraph/typescript.go`

**Prerequisites:**
- Task 1 completed
- dependency-cruiser installed globally (`npm install -g dependency-cruiser`)

**Step 1: Write the TypeScript analyzer**

```go
package callgraph

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// TypeScriptAnalyzer implements call graph analysis for TypeScript.
type TypeScriptAnalyzer struct {
	workDir string
}

// NewTypeScriptAnalyzer creates a new TypeScript call graph analyzer.
func NewTypeScriptAnalyzer(workDir string) *TypeScriptAnalyzer {
	return &TypeScriptAnalyzer{workDir: workDir}
}

// depCruiserOutput represents dependency-cruiser JSON output.
type depCruiserOutput struct {
	Modules []depCruiserModule `json:"modules"`
}

type depCruiserModule struct {
	Source       string                  `json:"source"`
	Dependencies []depCruiserDependency  `json:"dependencies"`
}

type depCruiserDependency struct {
	Resolved   string `json:"resolved"`
	ModuleType string `json:"moduleType"`
}

// Analyze implements Analyzer interface for TypeScript.
func (t *TypeScriptAnalyzer) Analyze(modifiedFuncs []ModifiedFunction, timeBudgetSec int) (*CallGraphResult, error) {
	result := &CallGraphResult{
		Language:          "typescript",
		ModifiedFunctions: []FunctionCallGraph{},
		ImpactAnalysis:    ImpactAnalysis{},
	}

	if len(modifiedFuncs) == 0 {
		return result, nil
	}

	// Set up context with timeout
	ctx := context.Background()
	var cancel context.CancelFunc
	if timeBudgetSec > 0 {
		ctx, cancel = context.WithTimeout(ctx, time.Duration(timeBudgetSec)*time.Second)
		defer cancel()
	}

	// Get unique files from modified functions
	files := make(map[string]bool)
	for _, f := range modifiedFuncs {
		files[f.File] = true
	}

	// Run dependency-cruiser for each file
	for file := range files {
		deps, err := t.runDepCruiser(ctx, file)
		if err != nil {
			result.Warnings = append(result.Warnings, fmt.Sprintf("dependency-cruiser error for %s: %v", file, err))
			continue
		}

		// Find functions in this file from modifiedFuncs
		for _, modFunc := range modifiedFuncs {
			if modFunc.File != file {
				continue
			}

			fcg := FunctionCallGraph{
				Function: modFunc.Name,
				File:     modFunc.File,
				Callers:  t.findCallers(deps, file),
				Callees:  t.findCallees(deps, file),
				TestCoverage: t.findTestCoverage(deps, file),
			}

			result.ModifiedFunctions = append(result.ModifiedFunctions, fcg)
			result.ImpactAnalysis.DirectCallers += len(fcg.Callers)
			result.ImpactAnalysis.AffectedTests += len(fcg.TestCoverage)
		}
	}

	// Check if time exceeded
	select {
	case <-ctx.Done():
		result.TimeBudgetExceeded = true
		result.PartialResults = true
	default:
	}

	return result, nil
}

// runDepCruiser runs dependency-cruiser on a file and returns the output.
func (t *TypeScriptAnalyzer) runDepCruiser(ctx context.Context, file string) (*depCruiserOutput, error) {
	// Run dependency-cruiser with JSON output
	cmd := exec.CommandContext(ctx, "npx", "depcruise",
		"--output-type", "json",
		"--include-only", "^src",
		file,
	)
	cmd.Dir = t.workDir

	out, err := cmd.Output()
	if err != nil {
		// Try without npx
		cmd = exec.CommandContext(ctx, "depcruise",
			"--output-type", "json",
			"--include-only", "^src",
			file,
		)
		cmd.Dir = t.workDir
		out, err = cmd.Output()
		if err != nil {
			return nil, fmt.Errorf("running depcruise: %w", err)
		}
	}

	var result depCruiserOutput
	if err := json.Unmarshal(out, &result); err != nil {
		return nil, fmt.Errorf("parsing depcruise output: %w", err)
	}

	return &result, nil
}

// findCallers finds modules that import the given file.
func (t *TypeScriptAnalyzer) findCallers(deps *depCruiserOutput, targetFile string) []CallInfo {
	var callers []CallInfo

	for _, mod := range deps.Modules {
		for _, dep := range mod.Dependencies {
			if dep.Resolved == targetFile || strings.HasSuffix(dep.Resolved, targetFile) {
				callers = append(callers, CallInfo{
					Function: filepath.Base(mod.Source),
					File:     mod.Source,
					Line:     0, // dependency-cruiser doesn't provide line numbers
				})
			}
		}
	}

	return callers
}

// findCallees finds modules that the given file imports.
func (t *TypeScriptAnalyzer) findCallees(deps *depCruiserOutput, sourceFile string) []CallInfo {
	var callees []CallInfo

	for _, mod := range deps.Modules {
		if mod.Source == sourceFile || strings.HasSuffix(mod.Source, sourceFile) {
			for _, dep := range mod.Dependencies {
				callees = append(callees, CallInfo{
					Function: filepath.Base(dep.Resolved),
					File:     dep.Resolved,
					Line:     0,
				})
			}
			break
		}
	}

	return callees
}

// findTestCoverage finds test files that import the given file.
func (t *TypeScriptAnalyzer) findTestCoverage(deps *depCruiserOutput, targetFile string) []TestCoverage {
	var coverage []TestCoverage

	for _, mod := range deps.Modules {
		// Check if this is a test file
		if !isTypeScriptTestFile(mod.Source) {
			continue
		}

		// Check if it imports our target
		for _, dep := range mod.Dependencies {
			if dep.Resolved == targetFile || strings.HasSuffix(dep.Resolved, targetFile) {
				coverage = append(coverage, TestCoverage{
					TestFunction: filepath.Base(mod.Source),
					File:         mod.Source,
					Line:         0,
				})
				break
			}
		}
	}

	return coverage
}

// isTypeScriptTestFile checks if a file is a test file.
func isTypeScriptTestFile(filename string) bool {
	return strings.Contains(filename, ".test.") ||
		strings.Contains(filename, ".spec.") ||
		strings.Contains(filename, "__tests__")
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/typescript.go
git commit -m "feat(codereview): add TypeScript call graph analyzer using dependency-cruiser"
```

---

## Task 6: Create TypeScript Function-Level Call Graph Helper

**Files:**
- Create: `scripts/codereview/ts/call-graph.ts`

**Prerequisites:**
- Task 5 completed
- Node.js 18+ and npm available

**Step 1: Create ts directory and package.json if not exists**

Run: `mkdir -p scripts/codereview/ts`

**Step 2: Write package.json**

Create `scripts/codereview/ts/package.json`:

```json
{
  "name": "codereview-ts-helpers",
  "version": "1.0.0",
  "description": "TypeScript helpers for codereview analysis",
  "main": "call-graph.js",
  "scripts": {
    "build": "tsc",
    "call-graph": "node call-graph.js"
  },
  "dependencies": {
    "typescript": "^5.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0"
  }
}
```

**Step 3: Write call-graph.ts**

Create `scripts/codereview/ts/call-graph.ts`:

```typescript
import * as ts from 'typescript';
import * as fs from 'fs';
import * as path from 'path';

interface CallSite {
  caller: string;
  callee: string;
  file: string;
  line: number;
  column: number;
}

interface FunctionInfo {
  name: string;
  file: string;
  line: number;
  calls: CallSite[];
  calledBy: CallSite[];
}

/**
 * Analyzes TypeScript files to build a function-level call graph.
 */
function analyzeCallGraph(files: string[], targetFunctions: string[]): Map<string, FunctionInfo> {
  const result = new Map<string, FunctionInfo>();
  const program = ts.createProgram(files, {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.CommonJS,
    allowJs: true,
  });

  const checker = program.getTypeChecker();

  for (const sourceFile of program.getSourceFiles()) {
    if (sourceFile.isDeclarationFile) continue;
    
    visitNode(sourceFile, sourceFile, checker, result, targetFunctions);
  }

  return result;
}

function visitNode(
  node: ts.Node,
  sourceFile: ts.SourceFile,
  checker: ts.TypeChecker,
  result: Map<string, FunctionInfo>,
  targetFunctions: string[]
): void {
  // Track function declarations
  if (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) {
    const name = node.name?.getText(sourceFile) || '<anonymous>';
    const { line } = sourceFile.getLineAndCharacterOfPosition(node.getStart());
    
    if (!result.has(name)) {
      result.set(name, {
        name,
        file: sourceFile.fileName,
        line: line + 1,
        calls: [],
        calledBy: [],
      });
    }
  }

  // Track call expressions
  if (ts.isCallExpression(node)) {
    const callee = getCalleeText(node, sourceFile);
    const { line, character } = sourceFile.getLineAndCharacterOfPosition(node.getStart());
    
    // Find the containing function
    const containingFunc = findContainingFunction(node);
    const caller = containingFunc?.name?.getText(sourceFile) || '<module>';
    
    // Update callee info
    if (result.has(callee)) {
      result.get(callee)!.calledBy.push({
        caller,
        callee,
        file: sourceFile.fileName,
        line: line + 1,
        column: character + 1,
      });
    }
    
    // Update caller info
    if (result.has(caller)) {
      result.get(caller)!.calls.push({
        caller,
        callee,
        file: sourceFile.fileName,
        line: line + 1,
        column: character + 1,
      });
    }
  }

  ts.forEachChild(node, child => visitNode(child, sourceFile, checker, result, targetFunctions));
}

function getCalleeText(node: ts.CallExpression, sourceFile: ts.SourceFile): string {
  const expr = node.expression;
  if (ts.isIdentifier(expr)) {
    return expr.getText(sourceFile);
  }
  if (ts.isPropertyAccessExpression(expr)) {
    return expr.name.getText(sourceFile);
  }
  return '<unknown>';
}

function findContainingFunction(node: ts.Node): ts.FunctionDeclaration | ts.MethodDeclaration | undefined {
  let current: ts.Node | undefined = node.parent;
  while (current) {
    if (ts.isFunctionDeclaration(current) || ts.isMethodDeclaration(current)) {
      return current;
    }
    current = current.parent;
  }
  return undefined;
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: call-graph.ts <file1> [file2...] [--functions func1,func2]');
    process.exit(1);
  }

  const funcIndex = args.indexOf('--functions');
  let targetFunctions: string[] = [];
  let files: string[] = args;

  if (funcIndex !== -1) {
    targetFunctions = args[funcIndex + 1]?.split(',') || [];
    files = args.slice(0, funcIndex);
  }

  const result = analyzeCallGraph(files, targetFunctions);
  console.log(JSON.stringify(Object.fromEntries(result), null, 2));
}

export { analyzeCallGraph, FunctionInfo, CallSite };
```

**Step 4: Create tsconfig.json**

Create `scripts/codereview/ts/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "declaration": true
  },
  "include": ["*.ts"],
  "exclude": ["node_modules"]
}
```

**Step 5: Install dependencies and build**

Run: `cd scripts/codereview/ts && npm install && npm run build`

**Expected output:**
```
added X packages...
```

**Step 6: Commit**

```bash
git add scripts/codereview/ts/
git commit -m "feat(codereview): add TypeScript call graph helper script"
```

---

## Task 7: Integrate TypeScript Helper into Go Analyzer

**Files:**
- Modify: `scripts/codereview/internal/callgraph/typescript.go`

**Prerequisites:**
- Task 6 completed

**Step 1: Add function-level analysis using TypeScript helper**

Add to `typescript.go` after the `findTestCoverage` method:

```go
// analyzeWithTSHelper uses the TypeScript helper for function-level analysis.
func (t *TypeScriptAnalyzer) analyzeWithTSHelper(ctx context.Context, files []string, functions []string) (map[string]interface{}, error) {
	args := append(files, "--functions", strings.Join(functions, ","))
	
	cmd := exec.CommandContext(ctx, "node",
		append([]string{filepath.Join(t.workDir, "scripts/codereview/ts/dist/call-graph.js")}, args...)...)
	cmd.Dir = t.workDir

	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("running ts call-graph helper: %w", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(out, &result); err != nil {
		return nil, fmt.Errorf("parsing ts helper output: %w", err)
	}

	return result, nil
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/typescript.go
git commit -m "feat(codereview): integrate TypeScript helper for function-level analysis"
```

---

## Task 8: Create Python Call Graph Script

**Files:**
- Create: `scripts/codereview/py/call_graph.py`

**Prerequisites:**
- Python 3.10+ available
- pyan3 installed (`pip install pyan3`)

**Step 1: Create py directory if not exists**

Run: `mkdir -p scripts/codereview/py`

**Step 2: Write call_graph.py**

```python
#!/usr/bin/env python3
"""
Python call graph analyzer using AST.

This module provides static call graph analysis for Python code,
identifying callers, callees, and test coverage for modified functions.
"""

import ast
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class CallSite:
    """Represents a function call site."""
    caller: str
    callee: str
    file: str
    line: int
    call_site_text: str = ""


@dataclass
class FunctionInfo:
    """Information about a function and its call relationships."""
    name: str
    file: str
    line: int
    module: str = ""
    callers: List[CallSite] = field(default_factory=list)
    callees: List[CallSite] = field(default_factory=list)
    test_coverage: List[Dict] = field(default_factory=list)


class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor that builds call graph information."""

    def __init__(self, filename: str, module_name: str = ""):
        self.filename = filename
        self.module_name = module_name
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
        self.functions: Dict[str, FunctionInfo] = {}
        self.calls: List[CallSite] = []

    def _get_full_name(self, name: str) -> str:
        """Get fully qualified name including class if applicable."""
        if self.current_class:
            return f"{self.current_class}.{name}"
        if self.module_name:
            return f"{self.module_name}.{name}"
        return name

    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class context for method names."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Record function definition and track current function."""
        full_name = self._get_full_name(node.name)
        self.functions[full_name] = FunctionInfo(
            name=node.name,
            file=self.filename,
            line=node.lineno,
            module=self.module_name,
        )

        old_func = self.current_function
        self.current_function = full_name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async functions the same as regular functions."""
        self.visit_FunctionDef(node)  # type: ignore

    def visit_Call(self, node: ast.Call):
        """Record function calls."""
        callee = self._get_callee_name(node)
        if callee and self.current_function:
            self.calls.append(CallSite(
                caller=self.current_function,
                callee=callee,
                file=self.filename,
                line=node.lineno,
                call_site_text=ast.unparse(node) if hasattr(ast, 'unparse') else "",
            ))
        self.generic_visit(node)

    def _get_callee_name(self, node: ast.Call) -> Optional[str]:
        """Extract the callee name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like self.method() or obj.method()
            return node.func.attr
        return None


def analyze_file(filepath: str) -> tuple[Dict[str, FunctionInfo], List[CallSite]]:
    """Analyze a single Python file for call graph information."""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)
        return {}, []

    # Derive module name from file path
    module_name = Path(filepath).stem
    if "/" in filepath:
        parts = filepath.replace("/", ".").replace(".py", "")
        module_name = parts

    visitor = CallGraphVisitor(filepath, module_name)
    visitor.visit(tree)

    return visitor.functions, visitor.calls


def build_call_graph(files: List[str], target_functions: List[str]) -> Dict[str, FunctionInfo]:
    """Build call graph for the given files, focusing on target functions."""
    all_functions: Dict[str, FunctionInfo] = {}
    all_calls: List[CallSite] = []

    # First pass: collect all functions and calls
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}", file=sys.stderr)
            continue
        functions, calls = analyze_file(filepath)
        all_functions.update(functions)
        all_calls.extend(calls)

    # Second pass: associate calls with functions
    for call in all_calls:
        # Add to caller's callees
        if call.caller in all_functions:
            all_functions[call.caller].callees.append(call)

        # Add to callee's callers (if callee is in our functions)
        for func_name, func_info in all_functions.items():
            if call.callee == func_info.name or call.callee in func_name:
                func_info.callers.append(call)

    # Third pass: find test coverage
    for func_name, func_info in all_functions.items():
        for caller in func_info.callers:
            if is_test_function(caller.caller):
                func_info.test_coverage.append({
                    "test_function": caller.caller,
                    "file": caller.file,
                    "line": caller.line,
                })

    # Filter to target functions if specified
    if target_functions:
        filtered = {}
        for target in target_functions:
            for func_name, func_info in all_functions.items():
                if target in func_name or func_name.endswith(target):
                    filtered[func_name] = func_info
        return filtered

    return all_functions


def is_test_function(name: str) -> bool:
    """Check if a function name indicates a test function."""
    return (
        name.startswith("test_") or
        name.startswith("Test") or
        "_test_" in name or
        name.endswith("_test")
    )


def to_json_output(functions: Dict[str, FunctionInfo]) -> dict:
    """Convert function info to JSON-serializable output."""
    result = {
        "modified_functions": [],
        "impact_analysis": {
            "direct_callers": 0,
            "transitive_callers": 0,
            "affected_tests": 0,
            "affected_modules": [],
        }
    }

    affected_modules: Set[str] = set()

    for func_name, func_info in functions.items():
        func_data = {
            "function": func_name,
            "file": func_info.file,
            "callers": [
                {
                    "function": c.caller,
                    "file": c.file,
                    "line": c.line,
                    "call_site": c.call_site_text,
                }
                for c in func_info.callers
            ],
            "callees": [
                {
                    "function": c.callee,
                    "file": c.file,
                    "line": c.line,
                }
                for c in func_info.callees
            ],
            "test_coverage": func_info.test_coverage,
        }
        result["modified_functions"].append(func_data)

        result["impact_analysis"]["direct_callers"] += len(func_info.callers)
        result["impact_analysis"]["affected_tests"] += len(func_info.test_coverage)

        for caller in func_info.callers:
            module = caller.file.replace("/", ".").replace(".py", "")
            affected_modules.add(module)

    result["impact_analysis"]["affected_modules"] = list(affected_modules)

    return result


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Python call graph analyzer")
    parser.add_argument("files", nargs="+", help="Python files to analyze")
    parser.add_argument("--functions", "-f", help="Comma-separated target function names")
    parser.add_argument("--output", "-o", default="-", help="Output file (- for stdout)")

    args = parser.parse_args()

    target_functions = []
    if args.functions:
        target_functions = [f.strip() for f in args.functions.split(",")]

    functions = build_call_graph(args.files, target_functions)
    output = to_json_output(functions)

    json_str = json.dumps(output, indent=2)

    if args.output == "-":
        print(json_str)
    else:
        with open(args.output, "w") as f:
            f.write(json_str)


if __name__ == "__main__":
    main()
```

**Step 3: Make executable**

Run: `chmod +x scripts/codereview/py/call_graph.py`

**Step 4: Verify script works**

Run: `python3 scripts/codereview/py/call_graph.py scripts/codereview/py/call_graph.py --functions main`

**Expected output:**
```json
{
  "modified_functions": [...],
  "impact_analysis": {...}
}
```

**Step 5: Commit**

```bash
git add scripts/codereview/py/call_graph.py
git commit -m "feat(codereview): add Python call graph analyzer script"
```

---

## Task 9: Create internal/callgraph/python.go

**Files:**
- Create: `scripts/codereview/internal/callgraph/python.go`

**Prerequisites:**
- Task 8 completed

**Step 1: Write the Python analyzer wrapper**

```go
package callgraph

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// PythonAnalyzer implements call graph analysis for Python.
type PythonAnalyzer struct {
	workDir string
}

// NewPythonAnalyzer creates a new Python call graph analyzer.
func NewPythonAnalyzer(workDir string) *PythonAnalyzer {
	return &PythonAnalyzer{workDir: workDir}
}

// pythonCallGraphOutput represents the output from call_graph.py.
type pythonCallGraphOutput struct {
	ModifiedFunctions []struct {
		Function     string `json:"function"`
		File         string `json:"file"`
		Callers      []struct {
			Function string `json:"function"`
			File     string `json:"file"`
			Line     int    `json:"line"`
			CallSite string `json:"call_site"`
		} `json:"callers"`
		Callees []struct {
			Function string `json:"function"`
			File     string `json:"file"`
			Line     int    `json:"line"`
		} `json:"callees"`
		TestCoverage []struct {
			TestFunction string `json:"test_function"`
			File         string `json:"file"`
			Line         int    `json:"line"`
		} `json:"test_coverage"`
	} `json:"modified_functions"`
	ImpactAnalysis struct {
		DirectCallers     int      `json:"direct_callers"`
		TransitiveCallers int      `json:"transitive_callers"`
		AffectedTests     int      `json:"affected_tests"`
		AffectedModules   []string `json:"affected_modules"`
	} `json:"impact_analysis"`
}

// Analyze implements Analyzer interface for Python.
func (p *PythonAnalyzer) Analyze(modifiedFuncs []ModifiedFunction, timeBudgetSec int) (*CallGraphResult, error) {
	result := &CallGraphResult{
		Language:          "python",
		ModifiedFunctions: []FunctionCallGraph{},
		ImpactAnalysis:    ImpactAnalysis{},
	}

	if len(modifiedFuncs) == 0 {
		return result, nil
	}

	// Set up context with timeout
	ctx := context.Background()
	var cancel context.CancelFunc
	if timeBudgetSec > 0 {
		ctx, cancel = context.WithTimeout(ctx, time.Duration(timeBudgetSec)*time.Second)
		defer cancel()
	}

	// Collect files and function names
	files := make([]string, 0)
	funcNames := make([]string, 0)
	fileSet := make(map[string]bool)

	for _, f := range modifiedFuncs {
		if !fileSet[f.File] {
			files = append(files, f.File)
			fileSet[f.File] = true
		}
		funcNames = append(funcNames, f.Name)
	}

	// Try using our custom call_graph.py first
	pyOutput, err := p.runCallGraphPy(ctx, files, funcNames)
	if err != nil {
		result.Warnings = append(result.Warnings, fmt.Sprintf("call_graph.py error: %v", err))
		
		// Fall back to pyan3
		pyOutput, err = p.runPyan3(ctx, files)
		if err != nil {
			result.Warnings = append(result.Warnings, fmt.Sprintf("pyan3 error: %v", err))
			result.PartialResults = true
			return result, nil
		}
	}

	// Convert output to result
	result = p.convertOutput(pyOutput)

	// Check if time exceeded
	select {
	case <-ctx.Done():
		result.TimeBudgetExceeded = true
		result.PartialResults = true
	default:
	}

	return result, nil
}

// runCallGraphPy runs our custom Python call graph script.
func (p *PythonAnalyzer) runCallGraphPy(ctx context.Context, files []string, funcNames []string) (*pythonCallGraphOutput, error) {
	scriptPath := filepath.Join(p.workDir, "scripts/codereview/py/call_graph.py")

	args := []string{scriptPath}
	args = append(args, files...)
	if len(funcNames) > 0 {
		args = append(args, "--functions", strings.Join(funcNames, ","))
	}

	cmd := exec.CommandContext(ctx, "python3", args...)
	cmd.Dir = p.workDir

	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("running call_graph.py: %w", err)
	}

	var result pythonCallGraphOutput
	if err := json.Unmarshal(out, &result); err != nil {
		return nil, fmt.Errorf("parsing call_graph.py output: %w", err)
	}

	return &result, nil
}

// runPyan3 runs pyan3 as a fallback for call graph generation.
func (p *PythonAnalyzer) runPyan3(ctx context.Context, files []string) (*pythonCallGraphOutput, error) {
	args := []string{"-m", "pyan3", "--dot"}
	args = append(args, files...)

	cmd := exec.CommandContext(ctx, "python3", args...)
	cmd.Dir = p.workDir

	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("running pyan3: %w", err)
	}

	// pyan3 outputs DOT format, we need to parse it
	// For now, return empty result - full implementation would parse DOT
	_ = out
	return &pythonCallGraphOutput{}, nil
}

// convertOutput converts Python output to CallGraphResult.
func (p *PythonAnalyzer) convertOutput(pyOutput *pythonCallGraphOutput) *CallGraphResult {
	result := &CallGraphResult{
		Language:          "python",
		ModifiedFunctions: []FunctionCallGraph{},
		ImpactAnalysis: ImpactAnalysis{
			DirectCallers:     pyOutput.ImpactAnalysis.DirectCallers,
			TransitiveCallers: pyOutput.ImpactAnalysis.TransitiveCallers,
			AffectedTests:     pyOutput.ImpactAnalysis.AffectedTests,
			AffectedPackages:  pyOutput.ImpactAnalysis.AffectedModules,
		},
	}

	for _, f := range pyOutput.ModifiedFunctions {
		fcg := FunctionCallGraph{
			Function: f.Function,
			File:     f.File,
			Callers:  make([]CallInfo, len(f.Callers)),
			Callees:  make([]CallInfo, len(f.Callees)),
			TestCoverage: make([]TestCoverage, len(f.TestCoverage)),
		}

		for i, c := range f.Callers {
			fcg.Callers[i] = CallInfo{
				Function: c.Function,
				File:     c.File,
				Line:     c.Line,
				CallSite: c.CallSite,
			}
		}

		for i, c := range f.Callees {
			fcg.Callees[i] = CallInfo{
				Function: c.Function,
				File:     c.File,
				Line:     c.Line,
			}
		}

		for i, t := range f.TestCoverage {
			fcg.TestCoverage[i] = TestCoverage{
				TestFunction: t.TestFunction,
				File:         t.File,
				Line:         t.Line,
			}
		}

		result.ModifiedFunctions = append(result.ModifiedFunctions, fcg)
	}

	return result
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/python.go
git commit -m "feat(codereview): add Python call graph analyzer wrapper"
```

---

## Task 10: Add requirements.txt for Python Dependencies

**Files:**
- Create: `scripts/codereview/py/requirements.txt`

**Prerequisites:**
- Task 8 completed

**Step 1: Create requirements.txt**

```text
# Python dependencies for codereview analysis
# Note: ast module is stdlib, no external deps needed for call_graph.py

# Optional: pyan3 for fallback call graph generation
pyan3>=1.2.0
```

**Step 2: Commit**

```bash
git add scripts/codereview/py/requirements.txt
git commit -m "feat(codereview): add Python requirements for call graph analysis"
```

---

## Task 11: Create Analyzer Factory

**Files:**
- Create: `scripts/codereview/internal/callgraph/factory.go`

**Prerequisites:**
- Tasks 3, 5, 9 completed

**Step 1: Write the factory**

```go
package callgraph

import (
	"fmt"
)

// NewAnalyzer creates the appropriate analyzer for the given language.
func NewAnalyzer(language, workDir string) (Analyzer, error) {
	switch language {
	case "go", "golang":
		return NewGoAnalyzer(workDir), nil
	case "typescript", "ts":
		return NewTypeScriptAnalyzer(workDir), nil
	case "python", "py":
		return NewPythonAnalyzer(workDir), nil
	default:
		return nil, fmt.Errorf("unsupported language: %s", language)
	}
}

// SupportedLanguages returns the list of supported languages.
func SupportedLanguages() []string {
	return []string{"go", "typescript", "python"}
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/callgraph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/factory.go
git commit -m "feat(codereview): add call graph analyzer factory"
```

---

## Task 12: Create internal/output/markdown.go (Impact Summary)

**Files:**
- Modify: `scripts/codereview/internal/output/markdown.go` (or create if not exists)

**Prerequisites:**
- Task 1 completed (types available)

**Step 1: Create output directory if needed**

Run: `mkdir -p scripts/codereview/internal/output`

**Step 2: Write the impact summary renderer**

```go
package output

import (
	"fmt"
	"strings"

	"ring/scripts/codereview/internal/callgraph"
)

// RenderImpactSummary generates markdown for the impact analysis.
func RenderImpactSummary(result *callgraph.CallGraphResult) string {
	var sb strings.Builder

	sb.WriteString("# Impact Analysis\n\n")

	if result.TimeBudgetExceeded {
		sb.WriteString("⚠️ **Warning:** Time budget exceeded. Results may be incomplete.\n\n")
	}

	if result.PartialResults {
		sb.WriteString("⚠️ **Warning:** Some analysis failed. Partial results shown.\n\n")
	}

	// Warnings
	if len(result.Warnings) > 0 {
		sb.WriteString("## Warnings\n\n")
		for _, w := range result.Warnings {
			sb.WriteString(fmt.Sprintf("- %s\n", w))
		}
		sb.WriteString("\n")
	}

	// High impact changes
	highImpact := filterHighImpact(result.ModifiedFunctions)
	if len(highImpact) > 0 {
		sb.WriteString("## High Impact Changes\n\n")
		for _, fcg := range highImpact {
			sb.WriteString(renderFunctionImpact(fcg, result.Language, "HIGH"))
		}
	}

	// Medium impact changes
	mediumImpact := filterMediumImpact(result.ModifiedFunctions)
	if len(mediumImpact) > 0 {
		sb.WriteString("## Medium Impact Changes\n\n")
		for _, fcg := range mediumImpact {
			sb.WriteString(renderFunctionImpact(fcg, result.Language, "MEDIUM"))
		}
	}

	// Low impact changes
	lowImpact := filterLowImpact(result.ModifiedFunctions)
	if len(lowImpact) > 0 {
		sb.WriteString("## Low Impact Changes\n\n")
		for _, fcg := range lowImpact {
			sb.WriteString(renderFunctionImpact(fcg, result.Language, "LOW"))
		}
	}

	// Summary table
	sb.WriteString("## Summary\n\n")
	sb.WriteString("| Metric | Count |\n")
	sb.WriteString("|--------|-------|\n")
	sb.WriteString(fmt.Sprintf("| Direct Callers | %d |\n", result.ImpactAnalysis.DirectCallers))
	sb.WriteString(fmt.Sprintf("| Transitive Callers | %d |\n", result.ImpactAnalysis.TransitiveCallers))
	sb.WriteString(fmt.Sprintf("| Affected Tests | %d |\n", result.ImpactAnalysis.AffectedTests))
	sb.WriteString(fmt.Sprintf("| Affected Packages | %d |\n", len(result.ImpactAnalysis.AffectedPackages)))

	if len(result.ImpactAnalysis.AffectedPackages) > 0 {
		sb.WriteString("\n**Affected Packages:**\n")
		for _, pkg := range result.ImpactAnalysis.AffectedPackages {
			sb.WriteString(fmt.Sprintf("- `%s`\n", pkg))
		}
	}

	return sb.String()
}

func renderFunctionImpact(fcg callgraph.FunctionCallGraph, language, riskLevel string) string {
	var sb strings.Builder

	langLabel := strings.Title(language)
	callerCount := len(fcg.Callers)

	sb.WriteString(fmt.Sprintf("### `%s` (%s)\n", fcg.Function, langLabel))
	sb.WriteString(fmt.Sprintf("**Risk Level:** %s (%d direct callers)\n\n", riskLevel, callerCount))

	// Direct callers
	if len(fcg.Callers) > 0 {
		sb.WriteString("**Direct Callers (signature change affects these):**\n")
		for i, caller := range fcg.Callers {
			if i >= 10 {
				sb.WriteString(fmt.Sprintf("- ... and %d more\n", len(fcg.Callers)-10))
				break
			}
			location := fmt.Sprintf("`%s:%d`", caller.File, caller.Line)
			sb.WriteString(fmt.Sprintf("%d. `%s` - %s\n", i+1, caller.Function, location))
		}
		sb.WriteString("\n")
	}

	// Callees (what this function depends on)
	if len(fcg.Callees) > 0 {
		sb.WriteString("**Callees (this function depends on):**\n")
		for i, callee := range fcg.Callees {
			if i >= 5 {
				sb.WriteString(fmt.Sprintf("- ... and %d more\n", len(fcg.Callees)-5))
				break
			}
			sb.WriteString(fmt.Sprintf("%d. `%s`\n", i+1, callee.Function))
		}
		sb.WriteString("\n")
	}

	// Test coverage
	sb.WriteString("**Test Coverage:**\n")
	if len(fcg.TestCoverage) == 0 {
		sb.WriteString("- ⚠️ No tests found covering this function\n")
	} else {
		for _, test := range fcg.TestCoverage {
			location := fmt.Sprintf("`%s:%d`", test.File, test.Line)
			sb.WriteString(fmt.Sprintf("- ✅ `%s` - %s\n", test.TestFunction, location))
		}
	}

	sb.WriteString("\n---\n\n")
	return sb.String()
}

func filterHighImpact(funcs []callgraph.FunctionCallGraph) []callgraph.FunctionCallGraph {
	var result []callgraph.FunctionCallGraph
	for _, f := range funcs {
		if len(f.Callers) >= 3 {
			result = append(result, f)
		}
	}
	return result
}

func filterMediumImpact(funcs []callgraph.FunctionCallGraph) []callgraph.FunctionCallGraph {
	var result []callgraph.FunctionCallGraph
	for _, f := range funcs {
		if len(f.Callers) >= 1 && len(f.Callers) < 3 {
			result = append(result, f)
		}
	}
	return result
}

func filterLowImpact(funcs []callgraph.FunctionCallGraph) []callgraph.FunctionCallGraph {
	var result []callgraph.FunctionCallGraph
	for _, f := range funcs {
		if len(f.Callers) == 0 {
			result = append(result, f)
		}
	}
	return result
}
```

**Step 3: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/output/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 4: Commit**

```bash
git add scripts/codereview/internal/output/markdown.go
git commit -m "feat(codereview): add impact summary markdown renderer"
```

---

## Task 13: Add JSON Output Writer

**Files:**
- Create: `scripts/codereview/internal/output/json.go`

**Prerequisites:**
- Task 1 completed

**Step 1: Write JSON output functions**

```go
package output

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"ring/scripts/codereview/internal/callgraph"
)

// WriteJSON writes the call graph result to a JSON file.
func WriteJSON(result *callgraph.CallGraphResult, outputDir string) error {
	filename := fmt.Sprintf("%s-calls.json", result.Language)
	outputPath := filepath.Join(outputDir, filename)

	data, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return fmt.Errorf("marshaling JSON: %w", err)
	}

	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("creating output directory: %w", err)
	}

	if err := os.WriteFile(outputPath, data, 0644); err != nil {
		return fmt.Errorf("writing JSON file: %w", err)
	}

	return nil
}

// WriteImpactSummary writes the impact summary markdown to a file.
func WriteImpactSummary(result *callgraph.CallGraphResult, outputDir string) error {
	markdown := RenderImpactSummary(result)
	outputPath := filepath.Join(outputDir, "impact-summary.md")

	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("creating output directory: %w", err)
	}

	if err := os.WriteFile(outputPath, []byte(markdown), 0644); err != nil {
		return fmt.Errorf("writing markdown file: %w", err)
	}

	return nil
}
```

**Step 2: Verify file compiles**

Run: `cd scripts/codereview && go build ./internal/output/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/output/json.go
git commit -m "feat(codereview): add JSON and markdown output writers"
```

---

## Task 14: Fix Module Path in Output Package

**Files:**
- Modify: `scripts/codereview/internal/output/markdown.go`
- Modify: `scripts/codereview/internal/output/json.go`

**Prerequisites:**
- Tasks 12, 13 completed

**Step 1: Check go.mod module path**

Run: `head -1 scripts/codereview/go.mod`

**Expected output:** Shows the module name (e.g., `module ring/scripts/codereview` or similar)

**Step 2: Update imports to match module path**

If the module is named differently, update the import in both files. For example, if `go.mod` says:

```
module github.com/lerianstudio/ring/scripts/codereview
```

Then change the import from:
```go
"ring/scripts/codereview/internal/callgraph"
```

To:
```go
"github.com/lerianstudio/ring/scripts/codereview/internal/callgraph"
```

**Step 3: Verify compilation**

Run: `cd scripts/codereview && go build ./internal/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 4: Commit**

```bash
git add scripts/codereview/internal/output/
git commit -m "fix(codereview): fix module path in output package"
```

---

## Task 15: Create cmd/call-graph/main.go

**Files:**
- Create: `scripts/codereview/cmd/call-graph/main.go`

**Prerequisites:**
- Tasks 1-14 completed

**Step 1: Create cmd directory**

Run: `mkdir -p scripts/codereview/cmd/call-graph`

**Step 2: Write the CLI orchestrator**

```go
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"ring/scripts/codereview/internal/callgraph"
	"ring/scripts/codereview/internal/output"
)

// ASTInput represents the input from Phase 2 AST extraction.
type ASTInput struct {
	Functions struct {
		Modified []struct {
			Name     string `json:"name"`
			File     string `json:"file"`
			Package  string `json:"package"`
			Receiver string `json:"receiver,omitempty"`
		} `json:"modified"`
		Added []struct {
			Name    string `json:"name"`
			File    string `json:"file"`
			Package string `json:"package"`
		} `json:"added"`
	} `json:"functions"`
}

func main() {
	// CLI flags
	scopeFile := flag.String("scope", "", "Path to scope.json from Phase 0")
	astFile := flag.String("ast", "", "Path to {lang}-ast.json from Phase 2")
	outputDir := flag.String("output", ".ring/codereview", "Output directory")
	timeBudget := flag.Int("timeout", 30, "Time budget in seconds (0 = no limit)")
	language := flag.String("lang", "", "Language (go, typescript, python) - auto-detected from AST if not specified")
	verbose := flag.Bool("verbose", false, "Enable verbose output")

	flag.Parse()

	// Validate inputs
	if *astFile == "" {
		log.Fatal("--ast flag is required")
	}

	// Read AST input
	astData, err := os.ReadFile(*astFile)
	if err != nil {
		log.Fatalf("Reading AST file: %v", err)
	}

	var ast ASTInput
	if err := json.Unmarshal(astData, &ast); err != nil {
		log.Fatalf("Parsing AST file: %v", err)
	}

	// Detect language from filename if not specified
	lang := *language
	if lang == "" {
		lang = detectLanguage(*astFile)
	}
	if lang == "" {
		log.Fatal("Could not detect language. Please specify --lang")
	}

	if *verbose {
		log.Printf("Language: %s", lang)
		log.Printf("AST file: %s", *astFile)
		log.Printf("Output directory: %s", *outputDir)
		log.Printf("Time budget: %d seconds", *timeBudget)
	}

	// Get working directory
	workDir, err := os.Getwd()
	if err != nil {
		log.Fatalf("Getting working directory: %v", err)
	}

	// If scope file provided, use its directory as workDir
	if *scopeFile != "" {
		workDir = filepath.Dir(*scopeFile)
	}

	// Build modified functions list
	var modifiedFuncs []callgraph.ModifiedFunction

	for _, f := range ast.Functions.Modified {
		modifiedFuncs = append(modifiedFuncs, callgraph.ModifiedFunction{
			Name:     f.Name,
			File:     f.File,
			Package:  f.Package,
			Receiver: f.Receiver,
		})
	}

	for _, f := range ast.Functions.Added {
		modifiedFuncs = append(modifiedFuncs, callgraph.ModifiedFunction{
			Name:    f.Name,
			File:    f.File,
			Package: f.Package,
		})
	}

	if len(modifiedFuncs) == 0 {
		if *verbose {
			log.Println("No modified functions found in AST. Generating empty output.")
		}
		// Generate empty output
		result := &callgraph.CallGraphResult{
			Language:          lang,
			ModifiedFunctions: []callgraph.FunctionCallGraph{},
			ImpactAnalysis:    callgraph.ImpactAnalysis{},
		}
		writeOutput(result, *outputDir)
		return
	}

	if *verbose {
		log.Printf("Found %d modified functions", len(modifiedFuncs))
	}

	// Create analyzer
	analyzer, err := callgraph.NewAnalyzer(lang, workDir)
	if err != nil {
		log.Fatalf("Creating analyzer: %v", err)
	}

	// Run analysis
	result, err := analyzer.Analyze(modifiedFuncs, *timeBudget)
	if err != nil {
		log.Printf("Warning: Analysis error: %v", err)
		// Continue with partial results
	}

	// Write output
	writeOutput(result, *outputDir)

	if *verbose {
		log.Printf("Output written to %s", *outputDir)
		log.Printf("  - %s-calls.json", lang)
		log.Printf("  - impact-summary.md")
	}
}

func detectLanguage(filename string) string {
	base := filepath.Base(filename)
	if strings.HasPrefix(base, "go-") {
		return "go"
	}
	if strings.HasPrefix(base, "ts-") {
		return "typescript"
	}
	if strings.HasPrefix(base, "py-") {
		return "python"
	}
	return ""
}

func writeOutput(result *callgraph.CallGraphResult, outputDir string) {
	// Write JSON
	if err := output.WriteJSON(result, outputDir); err != nil {
		log.Printf("Warning: Could not write JSON: %v", err)
	}

	// Write impact summary markdown
	if err := output.WriteImpactSummary(result, outputDir); err != nil {
		log.Printf("Warning: Could not write impact summary: %v", err)
	}

	// Print summary to stdout
	fmt.Printf("Call graph analysis complete:\n")
	fmt.Printf("  Language: %s\n", result.Language)
	fmt.Printf("  Modified functions: %d\n", len(result.ModifiedFunctions))
	fmt.Printf("  Direct callers: %d\n", result.ImpactAnalysis.DirectCallers)
	fmt.Printf("  Transitive callers: %d\n", result.ImpactAnalysis.TransitiveCallers)
	fmt.Printf("  Affected tests: %d\n", result.ImpactAnalysis.AffectedTests)

	if result.TimeBudgetExceeded {
		fmt.Println("  ⚠️  Time budget exceeded (partial results)")
	}
	if result.PartialResults {
		fmt.Println("  ⚠️  Some analysis failed (partial results)")
	}
}
```

**Step 3: Verify file compiles**

Run: `cd scripts/codereview && go build ./cmd/call-graph/...`

**Expected output:**
```
(no output - successful compilation)
```

**Step 4: Commit**

```bash
git add scripts/codereview/cmd/call-graph/
git commit -m "feat(codereview): add call-graph CLI orchestrator"
```

---

## Task 16: Fix Module Path in CLI

**Files:**
- Modify: `scripts/codereview/cmd/call-graph/main.go`

**Prerequisites:**
- Task 15 completed

**Step 1: Check and update module path**

Run: `head -1 scripts/codereview/go.mod`

Update the imports in `main.go` to match the actual module path. For example, if the module is `github.com/lerianstudio/ring/scripts/codereview`:

```go
import (
	// ... standard library imports ...

	"github.com/lerianstudio/ring/scripts/codereview/internal/callgraph"
	"github.com/lerianstudio/ring/scripts/codereview/internal/output"
)
```

**Step 2: Verify compilation**

Run: `cd scripts/codereview && go build -o bin/call-graph ./cmd/call-graph/`

**Expected output:**
```
(no output - successful build)
```

**Step 3: Commit**

```bash
git add scripts/codereview/cmd/call-graph/main.go
git commit -m "fix(codereview): fix module path in call-graph CLI"
```

---

## Task 17: Build Binary and Verify

**Files:**
- Build: `scripts/codereview/bin/call-graph`

**Prerequisites:**
- Task 16 completed

**Step 1: Build the binary**

Run: `cd scripts/codereview && go build -o bin/call-graph ./cmd/call-graph/`

**Expected output:**
```
(no output - successful build)
```

**Step 2: Verify binary runs**

Run: `scripts/codereview/bin/call-graph --help`

**Expected output:**
```
Usage of call-graph:
  -ast string
    	Path to {lang}-ast.json from Phase 2
  -lang string
    	Language (go, typescript, python) - auto-detected from AST if not specified
  -output string
    	Output directory (default ".ring/codereview")
  -scope string
    	Path to scope.json from Phase 0
  -timeout int
    	Time budget in seconds (0 = no limit) (default 30)
  -verbose
    	Enable verbose output
```

**Step 3: Commit**

```bash
git add scripts/codereview/bin/
echo "scripts/codereview/bin/" >> .gitignore
git add .gitignore
git commit -m "feat(codereview): build call-graph binary"
```

---

## Task 18: Create Unit Tests for Go Analyzer

**Files:**
- Create: `scripts/codereview/internal/callgraph/golang_test.go`

**Prerequisites:**
- Task 4 completed

**Step 1: Write the test file**

```go
package callgraph

import (
	"testing"
)

func TestGetAffectedPackages(t *testing.T) {
	tests := []struct {
		name     string
		funcs    []ModifiedFunction
		expected int // minimum expected packages
	}{
		{
			name:     "empty input",
			funcs:    []ModifiedFunction{},
			expected: 0,
		},
		{
			name: "single package",
			funcs: []ModifiedFunction{
				{Name: "Foo", File: "internal/handler/user.go", Package: "handler"},
			},
			expected: 1,
		},
		{
			name: "multiple packages",
			funcs: []ModifiedFunction{
				{Name: "Foo", File: "internal/handler/user.go", Package: "handler"},
				{Name: "Bar", File: "internal/repo/user.go", Package: "repo"},
			},
			expected: 2,
		},
		{
			name: "duplicate packages",
			funcs: []ModifiedFunction{
				{Name: "Foo", File: "internal/handler/user.go", Package: "handler"},
				{Name: "Bar", File: "internal/handler/admin.go", Package: "handler"},
			},
			expected: 1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := getAffectedPackages(tt.funcs)
			if len(result) < tt.expected {
				t.Errorf("got %d packages, expected at least %d", len(result), tt.expected)
			}
		})
	}
}

func TestIsTestFunction(t *testing.T) {
	tests := []struct {
		name     string
		funcName string
		expected bool
	}{
		{"Test prefix", "TestCreateUser", true},
		{"Benchmark prefix", "BenchmarkSort", true},
		{"Example prefix", "ExampleHandler", true},
		{"Regular function", "CreateUser", false},
		{"Helper function", "setupTest", false},
		{"Internal function", "doTest", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := isTestFunction(tt.funcName)
			if result != tt.expected {
				t.Errorf("isTestFunction(%q) = %v, expected %v", tt.funcName, result, tt.expected)
			}
		})
	}
}

func TestExtractPackageFromFile(t *testing.T) {
	tests := []struct {
		name     string
		filePath string
		expected string
	}{
		{"simple path", "internal/handler/user.go", "handler"},
		{"nested path", "pkg/api/v1/handler/user.go", "handler"},
		{"root file", "main.go", "."},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractPackageFromFile(tt.filePath)
			if result != tt.expected {
				t.Errorf("extractPackageFromFile(%q) = %q, expected %q", tt.filePath, result, tt.expected)
			}
		})
	}
}

func TestNewGoAnalyzer(t *testing.T) {
	analyzer := NewGoAnalyzer("/tmp/test")
	if analyzer == nil {
		t.Error("NewGoAnalyzer returned nil")
	}
	if analyzer.workDir != "/tmp/test" {
		t.Errorf("workDir = %q, expected %q", analyzer.workDir, "/tmp/test")
	}
}
```

**Step 2: Run tests**

Run: `cd scripts/codereview && go test -v ./internal/callgraph/...`

**Expected output:**
```
=== RUN   TestGetAffectedPackages
...
--- PASS: TestGetAffectedPackages (X.XXs)
=== RUN   TestIsTestFunction
...
--- PASS: TestIsTestFunction (X.XXs)
=== RUN   TestExtractPackageFromFile
...
--- PASS: TestExtractPackageFromFile (X.XXs)
=== RUN   TestNewGoAnalyzer
--- PASS: TestNewGoAnalyzer (X.XXs)
PASS
```

**Step 3: Commit**

```bash
git add scripts/codereview/internal/callgraph/golang_test.go
git commit -m "test(codereview): add unit tests for Go call graph analyzer"
```

---

## Task 19: Create Unit Tests for Python Script

**Files:**
- Create: `scripts/codereview/py/test_call_graph.py`

**Prerequisites:**
- Task 8 completed

**Step 1: Write the test file**

```python
#!/usr/bin/env python3
"""Unit tests for call_graph.py"""

import ast
import tempfile
import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path for import
sys.path.insert(0, str(Path(__file__).parent))

from call_graph import (
    CallGraphVisitor,
    analyze_file,
    build_call_graph,
    is_test_function,
    to_json_output,
)


class TestIsTestFunction(unittest.TestCase):
    """Tests for is_test_function()"""

    def test_test_prefix(self):
        self.assertTrue(is_test_function("test_create_user"))

    def test_Test_prefix(self):
        self.assertTrue(is_test_function("TestCreateUser"))

    def test_contains_test(self):
        self.assertTrue(is_test_function("integration_test_user"))

    def test_ends_with_test(self):
        self.assertTrue(is_test_function("user_test"))

    def test_regular_function(self):
        self.assertFalse(is_test_function("create_user"))

    def test_helper_function(self):
        self.assertFalse(is_test_function("setup_database"))


class TestCallGraphVisitor(unittest.TestCase):
    """Tests for CallGraphVisitor"""

    def test_simple_function(self):
        source = """
def foo():
    pass
"""
        tree = ast.parse(source)
        visitor = CallGraphVisitor("test.py", "test")
        visitor.visit(tree)

        self.assertIn("foo", visitor.functions)
        self.assertEqual(visitor.functions["foo"].name, "foo")

    def test_function_call(self):
        source = """
def caller():
    callee()

def callee():
    pass
"""
        tree = ast.parse(source)
        visitor = CallGraphVisitor("test.py", "test")
        visitor.visit(tree)

        self.assertEqual(len(visitor.calls), 1)
        self.assertEqual(visitor.calls[0].caller, "caller")
        self.assertEqual(visitor.calls[0].callee, "callee")

    def test_method_in_class(self):
        source = """
class MyClass:
    def method(self):
        pass
"""
        tree = ast.parse(source)
        visitor = CallGraphVisitor("test.py", "test")
        visitor.visit(tree)

        self.assertIn("MyClass.method", visitor.functions)


class TestAnalyzeFile(unittest.TestCase):
    """Tests for analyze_file()"""

    def test_analyze_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def foo():
    bar()

def bar():
    pass
""")
            f.flush()

            try:
                functions, calls = analyze_file(f.name)
                self.assertIn("foo", functions)
                self.assertIn("bar", functions)
                self.assertEqual(len(calls), 1)
            finally:
                os.unlink(f.name)

    def test_analyze_syntax_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(:\n    pass")
            f.flush()

            try:
                functions, calls = analyze_file(f.name)
                # Should return empty on syntax error
                self.assertEqual(len(functions), 0)
                self.assertEqual(len(calls), 0)
            finally:
                os.unlink(f.name)


class TestToJsonOutput(unittest.TestCase):
    """Tests for to_json_output()"""

    def test_empty_input(self):
        result = to_json_output({})
        self.assertEqual(result["modified_functions"], [])
        self.assertEqual(result["impact_analysis"]["direct_callers"], 0)

    def test_with_functions(self):
        from call_graph import FunctionInfo, CallSite

        functions = {
            "test.foo": FunctionInfo(
                name="foo",
                file="test.py",
                line=1,
                module="test",
                callers=[CallSite("bar", "foo", "test.py", 10, "")],
                callees=[],
                test_coverage=[],
            )
        }

        result = to_json_output(functions)
        self.assertEqual(len(result["modified_functions"]), 1)
        self.assertEqual(result["modified_functions"][0]["function"], "test.foo")
        self.assertEqual(result["impact_analysis"]["direct_callers"], 1)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run tests**

Run: `cd scripts/codereview/py && python3 -m pytest test_call_graph.py -v`

Or without pytest:

Run: `cd scripts/codereview/py && python3 test_call_graph.py -v`

**Expected output:**
```
test_test_prefix ... ok
test_Test_prefix ... ok
...
----------------------------------------------------------------------
Ran X tests in Y.YYYs

OK
```

**Step 3: Commit**

```bash
git add scripts/codereview/py/test_call_graph.py
git commit -m "test(codereview): add unit tests for Python call graph script"
```

---

## Task 20: Create Unit Tests for Output Package

**Files:**
- Create: `scripts/codereview/internal/output/markdown_test.go`

**Prerequisites:**
- Task 12 completed

**Step 1: Write the test file**

```go
package output

import (
	"strings"
	"testing"

	"ring/scripts/codereview/internal/callgraph"
)

func TestRenderImpactSummary_Empty(t *testing.T) {
	result := &callgraph.CallGraphResult{
		Language:          "go",
		ModifiedFunctions: []callgraph.FunctionCallGraph{},
		ImpactAnalysis:    callgraph.ImpactAnalysis{},
	}

	markdown := RenderImpactSummary(result)

	if !strings.Contains(markdown, "# Impact Analysis") {
		t.Error("Missing header")
	}
	if !strings.Contains(markdown, "## Summary") {
		t.Error("Missing summary section")
	}
}

func TestRenderImpactSummary_WithWarnings(t *testing.T) {
	result := &callgraph.CallGraphResult{
		Language:           "go",
		ModifiedFunctions:  []callgraph.FunctionCallGraph{},
		ImpactAnalysis:     callgraph.ImpactAnalysis{},
		TimeBudgetExceeded: true,
		Warnings:           []string{"test warning"},
	}

	markdown := RenderImpactSummary(result)

	if !strings.Contains(markdown, "⚠️") {
		t.Error("Missing warning indicator")
	}
	if !strings.Contains(markdown, "test warning") {
		t.Error("Missing warning text")
	}
}

func TestRenderImpactSummary_HighImpact(t *testing.T) {
	result := &callgraph.CallGraphResult{
		Language: "go",
		ModifiedFunctions: []callgraph.FunctionCallGraph{
			{
				Function: "CreateUser",
				File:     "handler/user.go",
				Callers: []callgraph.CallInfo{
					{Function: "Caller1", File: "a.go", Line: 1},
					{Function: "Caller2", File: "b.go", Line: 2},
					{Function: "Caller3", File: "c.go", Line: 3},
				},
				Callees: []callgraph.CallInfo{
					{Function: "Save", File: "repo.go", Line: 10},
				},
				TestCoverage: []callgraph.TestCoverage{
					{TestFunction: "TestCreateUser", File: "user_test.go", Line: 5},
				},
			},
		},
		ImpactAnalysis: callgraph.ImpactAnalysis{
			DirectCallers: 3,
		},
	}

	markdown := RenderImpactSummary(result)

	if !strings.Contains(markdown, "## High Impact Changes") {
		t.Error("Missing high impact section")
	}
	if !strings.Contains(markdown, "CreateUser") {
		t.Error("Missing function name")
	}
	if !strings.Contains(markdown, "HIGH") {
		t.Error("Missing risk level")
	}
}

func TestFilterHighImpact(t *testing.T) {
	funcs := []callgraph.FunctionCallGraph{
		{Function: "High", Callers: make([]callgraph.CallInfo, 5)},
		{Function: "Medium", Callers: make([]callgraph.CallInfo, 2)},
		{Function: "Low", Callers: make([]callgraph.CallInfo, 0)},
	}

	high := filterHighImpact(funcs)
	if len(high) != 1 {
		t.Errorf("Expected 1 high impact, got %d", len(high))
	}
	if high[0].Function != "High" {
		t.Errorf("Expected 'High', got %q", high[0].Function)
	}
}

func TestFilterMediumImpact(t *testing.T) {
	funcs := []callgraph.FunctionCallGraph{
		{Function: "High", Callers: make([]callgraph.CallInfo, 5)},
		{Function: "Medium", Callers: make([]callgraph.CallInfo, 2)},
		{Function: "Low", Callers: make([]callgraph.CallInfo, 0)},
	}

	medium := filterMediumImpact(funcs)
	if len(medium) != 1 {
		t.Errorf("Expected 1 medium impact, got %d", len(medium))
	}
	if medium[0].Function != "Medium" {
		t.Errorf("Expected 'Medium', got %q", medium[0].Function)
	}
}

func TestFilterLowImpact(t *testing.T) {
	funcs := []callgraph.FunctionCallGraph{
		{Function: "High", Callers: make([]callgraph.CallInfo, 5)},
		{Function: "Medium", Callers: make([]callgraph.CallInfo, 2)},
		{Function: "Low", Callers: make([]callgraph.CallInfo, 0)},
	}

	low := filterLowImpact(funcs)
	if len(low) != 1 {
		t.Errorf("Expected 1 low impact, got %d", len(low))
	}
	if low[0].Function != "Low" {
		t.Errorf("Expected 'Low', got %q", low[0].Function)
	}
}
```

**Step 2: Fix module path in test file**

Update the import to match your actual module path (same as Task 14).

**Step 3: Run tests**

Run: `cd scripts/codereview && go test -v ./internal/output/...`

**Expected output:**
```
=== RUN   TestRenderImpactSummary_Empty
--- PASS: TestRenderImpactSummary_Empty (X.XXs)
=== RUN   TestRenderImpactSummary_WithWarnings
--- PASS: TestRenderImpactSummary_WithWarnings (X.XXs)
...
PASS
```

**Step 4: Commit**

```bash
git add scripts/codereview/internal/output/markdown_test.go
git commit -m "test(codereview): add unit tests for markdown output renderer"
```

---

## Task 21: Integration Test

**Files:**
- Create: `scripts/codereview/test/integration_test.sh`

**Prerequisites:**
- All previous tasks completed

**Step 1: Create test directory**

Run: `mkdir -p scripts/codereview/test`

**Step 2: Write integration test script**

```bash
#!/bin/bash
# Integration test for call-graph binary

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN="$ROOT_DIR/bin/call-graph"
TEST_OUTPUT="$SCRIPT_DIR/test-output"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=== Call Graph Integration Test ==="
echo ""

# Cleanup
rm -rf "$TEST_OUTPUT"
mkdir -p "$TEST_OUTPUT"

# Create test AST input (simulating Phase 2 output)
cat > "$TEST_OUTPUT/go-ast.json" << 'EOF'
{
  "functions": {
    "modified": [
      {
        "name": "CreateUser",
        "file": "internal/handler/user.go",
        "package": "handler",
        "receiver": "*UserHandler"
      }
    ],
    "added": []
  },
  "types": {
    "modified": [],
    "added": []
  }
}
EOF

# Test 1: Help output
echo "Test 1: Help output..."
if $BIN --help 2>&1 | grep -q "Usage"; then
    echo -e "${GREEN}PASS${NC}: Help output works"
else
    echo -e "${RED}FAIL${NC}: Help output missing"
    exit 1
fi

# Test 2: Missing required flag
echo "Test 2: Missing required flag..."
if $BIN 2>&1 | grep -q "required"; then
    echo -e "${GREEN}PASS${NC}: Missing flag error works"
else
    echo -e "${RED}FAIL${NC}: Missing flag error not shown"
    exit 1
fi

# Test 3: Process test AST input
echo "Test 3: Process AST input..."
if $BIN --ast "$TEST_OUTPUT/go-ast.json" --output "$TEST_OUTPUT" --lang go --verbose 2>&1; then
    echo -e "${GREEN}PASS${NC}: AST processing completed"
else
    echo -e "${RED}FAIL${NC}: AST processing failed"
    exit 1
fi

# Test 4: Verify JSON output exists
echo "Test 4: Verify JSON output..."
if [ -f "$TEST_OUTPUT/go-calls.json" ]; then
    echo -e "${GREEN}PASS${NC}: JSON output created"
else
    echo -e "${RED}FAIL${NC}: JSON output missing"
    exit 1
fi

# Test 5: Verify markdown output exists
echo "Test 5: Verify markdown output..."
if [ -f "$TEST_OUTPUT/impact-summary.md" ]; then
    echo -e "${GREEN}PASS${NC}: Markdown output created"
else
    echo -e "${RED}FAIL${NC}: Markdown output missing"
    exit 1
fi

# Test 6: Verify JSON structure
echo "Test 6: Verify JSON structure..."
if cat "$TEST_OUTPUT/go-calls.json" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'language' in d; assert 'modified_functions' in d"; then
    echo -e "${GREEN}PASS${NC}: JSON structure valid"
else
    echo -e "${RED}FAIL${NC}: JSON structure invalid"
    exit 1
fi

# Cleanup
rm -rf "$TEST_OUTPUT"

echo ""
echo "=== All integration tests passed! ==="
```

**Step 3: Make executable**

Run: `chmod +x scripts/codereview/test/integration_test.sh`

**Step 4: Run integration test**

Run: `./scripts/codereview/test/integration_test.sh`

**Expected output:**
```
=== Call Graph Integration Test ===

Test 1: Help output...
PASS: Help output works
Test 2: Missing required flag...
PASS: Missing flag error works
Test 3: Process AST input...
PASS: AST processing completed
Test 4: Verify JSON output...
PASS: JSON output created
Test 5: Verify markdown output...
PASS: Markdown output created
Test 6: Verify JSON structure...
PASS: JSON structure valid

=== All integration tests passed! ===
```

**Step 5: Commit**

```bash
git add scripts/codereview/test/integration_test.sh
git commit -m "test(codereview): add integration test for call-graph binary"
```

---

## Task 22: Code Review Checkpoint

**Prerequisites:**
- All previous tasks completed

**Step 1: Dispatch all 5 reviewers in parallel**

> **REQUIRED SUB-SKILL:** Use `ring:requesting-code-review`

All reviewers run simultaneously:
- code-reviewer
- business-logic-reviewer
- security-reviewer
- test-reviewer
- nil-safety-reviewer

**Step 2: Handle findings by severity**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 5 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on [date], severity: Cosmetic)`

**Step 3: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments added
- All Cosmetic issues have FIXME(nitpick): comments added

---

## If Task Fails

**General recovery steps:**

1. **Compilation fails:**
   - Check: Module path matches `go.mod`
   - Fix: Update imports to match actual module path
   - Rollback: `git checkout -- .`

2. **Tests fail:**
   - Run: Individual test to see detailed error
   - Check: Expected behavior vs actual
   - Fix: Update test or implementation

3. **Binary won't build:**
   - Run: `go mod tidy` to fix dependencies
   - Check: All imports resolve correctly
   - Fix: Missing dependencies with `go get`

4. **Integration test fails:**
   - Check: Binary exists at expected path
   - Check: Required tools installed (dependency-cruiser, pyan3)
   - Run: Individual test step manually

5. **Can't recover:**
   - Document: What failed and why
   - Stop: Return to human partner
   - Don't: Try to fix without understanding

---

## Verification Checklist

Before marking Phase 3 complete:

- [ ] `scripts/codereview/internal/callgraph/types.go` exists with all types
- [ ] `scripts/codereview/internal/callgraph/golang.go` compiles and has tests
- [ ] `scripts/codereview/internal/callgraph/typescript.go` compiles
- [ ] `scripts/codereview/internal/callgraph/python.go` compiles
- [ ] `scripts/codereview/internal/callgraph/factory.go` compiles
- [ ] `scripts/codereview/py/call_graph.py` runs and has tests
- [ ] `scripts/codereview/ts/call-graph.ts` compiles
- [ ] `scripts/codereview/internal/output/markdown.go` compiles and has tests
- [ ] `scripts/codereview/internal/output/json.go` compiles
- [ ] `scripts/codereview/cmd/call-graph/main.go` builds to `bin/call-graph`
- [ ] `bin/call-graph --help` shows usage
- [ ] Unit tests pass: `go test ./internal/...`
- [ ] Python tests pass: `python3 py/test_call_graph.py`
- [ ] Integration test passes: `./test/integration_test.sh`
- [ ] Code review completed with no Critical/High/Medium issues

---

## CLI Interface Summary
## CLI Summary

After implementation, the binary can be invoked as:

```bash
# Basic usage
call-graph --ast .ring/codereview/go-ast.json --output .ring/codereview/

# With all options
call-graph \
  --scope .ring/codereview/scope.json \
  --ast .ring/codereview/go-ast.json \
  --output .ring/codereview/ \
  --lang go \
  --timeout 30 \
  --verbose
```

**Outputs:**
- `{output}/go-calls.json` (or `ts-calls.json`, `py-calls.json`)
- `{output}/impact-summary.md`

---

## Next Phase

After Phase 3 is complete, proceed to **Phase 4: Data Flow Analysis** which will:
- Track data from sources (HTTP input, env vars) to sinks (DB, responses)
- Identify sanitization points
- Generate security-focused analysis
- Build on the call graph to trace data through function calls
