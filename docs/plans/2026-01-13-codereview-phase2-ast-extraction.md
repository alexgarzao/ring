# Phase 2: AST Extraction Implementation Plan

## Overview

Extract semantic changes from code (not line-level diffs) for Go, TypeScript, and Python. This phase enables reviewers to understand **what** changed semantically (functions added/modified, types changed, signatures altered) rather than just which lines differ.

## Goals

1. Parse code files into AST representations
2. Compare before/after ASTs to detect semantic changes
3. Generate structured JSON output for downstream consumers
4. Support Go, TypeScript, and Python as primary languages

## Directory Structure

```
scripts/codereview/
├── cmd/ast-extractor/
│   └── main.go                 # CLI entry point
├── internal/ast/
│   ├── types.go                # Shared types (FunctionDiff, TypeDiff, etc.)
│   ├── extractor.go            # Common interface and orchestration
│   ├── golang.go               # Go AST extraction
│   ├── typescript.go           # TypeScript extraction (calls ts/ subprocess)
│   └── python.go               # Python extraction (calls py/ subprocess)
├── ts/
│   ├── ast-extractor.ts        # TypeScript AST extraction
│   ├── package.json            # Dependencies (typescript)
│   └── tsconfig.json           # TypeScript config
├── py/
│   └── ast_extractor.py        # Python AST extraction
└── testdata/
    ├── go/                     # Go test fixtures
    ├── ts/                     # TypeScript test fixtures
    └── py/                     # Python test fixtures
```

## Shared Types Schema

```go
// Output JSON schema for all languages
type SemanticDiff struct {
    Language   string         `json:"language"`
    FilePath   string         `json:"file_path"`
    Functions  []FunctionDiff `json:"functions"`
    Types      []TypeDiff     `json:"types"`
    Imports    []ImportDiff   `json:"imports"`
    Summary    ChangeSummary  `json:"summary"`
}

type FunctionDiff struct {
    Name       string   `json:"name"`
    ChangeType string   `json:"change_type"` // added, removed, modified, renamed
    Before     *FuncSig `json:"before,omitempty"`
    After      *FuncSig `json:"after,omitempty"`
    BodyDiff   string   `json:"body_diff,omitempty"` // semantic description
}

type FuncSig struct {
    Params     []Param  `json:"params"`
    Returns    []string `json:"returns"`
    Receiver   string   `json:"receiver,omitempty"` // Go methods
    IsAsync    bool     `json:"is_async,omitempty"` // Python/TS
    Decorators []string `json:"decorators,omitempty"` // Python
    IsExported bool     `json:"is_exported"`
}

type TypeDiff struct {
    Name       string   `json:"name"`
    Kind       string   `json:"kind"` // struct, interface, class, type alias
    ChangeType string   `json:"change_type"`
    Fields     []FieldDiff `json:"fields,omitempty"`
}

type ChangeSummary struct {
    FunctionsAdded    int `json:"functions_added"`
    FunctionsRemoved  int `json:"functions_removed"`
    FunctionsModified int `json:"functions_modified"`
    TypesAdded        int `json:"types_added"`
    TypesRemoved      int `json:"types_removed"`
    TypesModified     int `json:"types_modified"`
}
```

---

## Tasks

### Task 1: Create Directory Structure
**Time:** 2 min

Create the base directory structure for the AST extraction system.

```bash
mkdir -p scripts/codereview/cmd/ast-extractor
mkdir -p scripts/codereview/internal/ast
mkdir -p scripts/codereview/ts
mkdir -p scripts/codereview/py
mkdir -p scripts/codereview/testdata/{go,ts,py}
```

**Verification:**
```bash
ls -la scripts/codereview/
# Should show: cmd/, internal/, ts/, py/, testdata/
```

---

### Task 2: Define Shared Types (types.go)
**Time:** 5 min

Create the shared type definitions used by all language extractors.

**File:** `scripts/codereview/internal/ast/types.go`

```go
package ast

// ChangeType represents the kind of change detected
type ChangeType string

const (
    ChangeAdded    ChangeType = "added"
    ChangeRemoved  ChangeType = "removed"
    ChangeModified ChangeType = "modified"
    ChangeRenamed  ChangeType = "renamed"
)

// Param represents a function parameter
type Param struct {
    Name string `json:"name"`
    Type string `json:"type"`
}

// FieldDiff represents a change in a struct/class field
type FieldDiff struct {
    Name       string     `json:"name"`
    ChangeType ChangeType `json:"change_type"`
    OldType    string     `json:"old_type,omitempty"`
    NewType    string     `json:"new_type,omitempty"`
}

// FuncSig represents a function signature
type FuncSig struct {
    Params     []Param  `json:"params"`
    Returns    []string `json:"returns"`
    Receiver   string   `json:"receiver,omitempty"`
    IsAsync    bool     `json:"is_async,omitempty"`
    Decorators []string `json:"decorators,omitempty"`
    IsExported bool     `json:"is_exported"`
    StartLine  int      `json:"start_line"`
    EndLine    int      `json:"end_line"`
}

// FunctionDiff represents a change in a function
type FunctionDiff struct {
    Name       string     `json:"name"`
    ChangeType ChangeType `json:"change_type"`
    Before     *FuncSig   `json:"before,omitempty"`
    After      *FuncSig   `json:"after,omitempty"`
    BodyDiff   string     `json:"body_diff,omitempty"`
}

// TypeDiff represents a change in a type definition
type TypeDiff struct {
    Name       string      `json:"name"`
    Kind       string      `json:"kind"`
    ChangeType ChangeType  `json:"change_type"`
    Fields     []FieldDiff `json:"fields,omitempty"`
    StartLine  int         `json:"start_line"`
    EndLine    int         `json:"end_line"`
}

// ImportDiff represents a change in imports
type ImportDiff struct {
    Path       string     `json:"path"`
    Alias      string     `json:"alias,omitempty"`
    ChangeType ChangeType `json:"change_type"`
}

// ChangeSummary provides counts of changes
type ChangeSummary struct {
    FunctionsAdded    int `json:"functions_added"`
    FunctionsRemoved  int `json:"functions_removed"`
    FunctionsModified int `json:"functions_modified"`
    TypesAdded        int `json:"types_added"`
    TypesRemoved      int `json:"types_removed"`
    TypesModified     int `json:"types_modified"`
    ImportsAdded      int `json:"imports_added"`
    ImportsRemoved    int `json:"imports_removed"`
}

// SemanticDiff represents the complete semantic diff for a file
type SemanticDiff struct {
    Language  string         `json:"language"`
    FilePath  string         `json:"file_path"`
    Functions []FunctionDiff `json:"functions"`
    Types     []TypeDiff     `json:"types"`
    Imports   []ImportDiff   `json:"imports"`
    Summary   ChangeSummary  `json:"summary"`
    Error     string         `json:"error,omitempty"`
}

// FilePair represents before/after versions of a file
type FilePair struct {
    BeforePath string
    AfterPath  string
    Language   string
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 3: Create Extractor Interface (extractor.go)
**Time:** 5 min

Define the common interface that all language-specific extractors implement.

**File:** `scripts/codereview/internal/ast/extractor.go`

```go
package ast

import (
    "context"
    "fmt"
    "path/filepath"
    "strings"
)

// Extractor defines the interface for language-specific AST extractors
type Extractor interface {
    // ExtractDiff compares two file versions and returns semantic differences
    ExtractDiff(ctx context.Context, beforePath, afterPath string) (*SemanticDiff, error)
    
    // SupportedExtensions returns file extensions this extractor handles
    SupportedExtensions() []string
    
    // Language returns the language name
    Language() string
}

// Registry holds all registered extractors
type Registry struct {
    extractors map[string]Extractor
}

// NewRegistry creates a new extractor registry
func NewRegistry() *Registry {
    return &Registry{
        extractors: make(map[string]Extractor),
    }
}

// Register adds an extractor to the registry
func (r *Registry) Register(e Extractor) {
    for _, ext := range e.SupportedExtensions() {
        r.extractors[ext] = e
    }
}

// GetExtractor returns the appropriate extractor for a file
func (r *Registry) GetExtractor(filePath string) (Extractor, error) {
    ext := strings.ToLower(filepath.Ext(filePath))
    if e, ok := r.extractors[ext]; ok {
        return e, nil
    }
    return nil, fmt.Errorf("no extractor registered for extension: %s", ext)
}

// ExtractAll processes multiple file pairs and returns semantic diffs
func (r *Registry) ExtractAll(ctx context.Context, pairs []FilePair) ([]SemanticDiff, error) {
    results := make([]SemanticDiff, 0, len(pairs))
    
    for _, pair := range pairs {
        path := pair.AfterPath
        if path == "" {
            path = pair.BeforePath
        }
        
        extractor, err := r.GetExtractor(path)
        if err != nil {
            results = append(results, SemanticDiff{
                FilePath: path,
                Error:    err.Error(),
            })
            continue
        }
        
        diff, err := extractor.ExtractDiff(ctx, pair.BeforePath, pair.AfterPath)
        if err != nil {
            results = append(results, SemanticDiff{
                FilePath: path,
                Language: extractor.Language(),
                Error:    err.Error(),
            })
            continue
        }
        
        results = append(results, *diff)
    }
    
    return results, nil
}

// ComputeSummary calculates the change summary from diffs
func ComputeSummary(funcs []FunctionDiff, types []TypeDiff, imports []ImportDiff) ChangeSummary {
    summary := ChangeSummary{}
    
    for _, f := range funcs {
        switch f.ChangeType {
        case ChangeAdded:
            summary.FunctionsAdded++
        case ChangeRemoved:
            summary.FunctionsRemoved++
        case ChangeModified, ChangeRenamed:
            summary.FunctionsModified++
        }
    }
    
    for _, t := range types {
        switch t.ChangeType {
        case ChangeAdded:
            summary.TypesAdded++
        case ChangeRemoved:
            summary.TypesRemoved++
        case ChangeModified, ChangeRenamed:
            summary.TypesModified++
        }
    }
    
    for _, i := range imports {
        switch i.ChangeType {
        case ChangeAdded:
            summary.ImportsAdded++
        case ChangeRemoved:
            summary.ImportsRemoved++
        }
    }
    
    return summary
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 4: Implement Go AST Parser - Core Parsing (golang.go part 1)
**Time:** 5 min

Create the Go AST extractor with core parsing functionality.

**File:** `scripts/codereview/internal/ast/golang.go`

```go
package ast

import (
    "bytes"
    "context"
    "fmt"
    "go/ast"
    "go/parser"
    "go/printer"
    "go/token"
    "os"
    "strings"
    "unicode"
)

// GoExtractor implements AST extraction for Go files
type GoExtractor struct{}

// NewGoExtractor creates a new Go AST extractor
func NewGoExtractor() *GoExtractor {
    return &GoExtractor{}
}

func (g *GoExtractor) Language() string {
    return "go"
}

func (g *GoExtractor) SupportedExtensions() []string {
    return []string{".go"}
}

// ParsedFile holds parsed AST information for a Go file
type ParsedFile struct {
    Fset      *token.FileSet
    File      *ast.File
    Functions map[string]*GoFunc
    Types     map[string]*GoType
    Imports   map[string]string // path -> alias
}

// GoFunc represents a parsed Go function
type GoFunc struct {
    Name       string
    Receiver   string
    Params     []Param
    Returns    []string
    IsExported bool
    StartLine  int
    EndLine    int
    BodyHash   string
}

// GoType represents a parsed Go type
type GoType struct {
    Name       string
    Kind       string // struct, interface, alias
    Fields     []GoField
    Methods    []string // interface methods
    IsExported bool
    StartLine  int
    EndLine    int
}

// GoField represents a struct field
type GoField struct {
    Name string
    Type string
    Tag  string
}

func (g *GoExtractor) parseFile(path string) (*ParsedFile, error) {
    if path == "" {
        return &ParsedFile{
            Functions: make(map[string]*GoFunc),
            Types:     make(map[string]*GoType),
            Imports:   make(map[string]string),
        }, nil
    }
    
    content, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("failed to read file: %w", err)
    }
    
    fset := token.NewFileSet()
    file, err := parser.ParseFile(fset, path, content, parser.ParseComments)
    if err != nil {
        return nil, fmt.Errorf("failed to parse Go file: %w", err)
    }
    
    parsed := &ParsedFile{
        Fset:      fset,
        File:      file,
        Functions: make(map[string]*GoFunc),
        Types:     make(map[string]*GoType),
        Imports:   make(map[string]string),
    }
    
    // Extract imports
    for _, imp := range file.Imports {
        path := strings.Trim(imp.Path.Value, `"`)
        alias := ""
        if imp.Name != nil {
            alias = imp.Name.Name
        }
        parsed.Imports[path] = alias
    }
    
    // Extract functions and types
    ast.Inspect(file, func(n ast.Node) bool {
        switch node := n.(type) {
        case *ast.FuncDecl:
            fn := g.extractFunc(fset, node)
            key := fn.Name
            if fn.Receiver != "" {
                key = fn.Receiver + "." + fn.Name
            }
            parsed.Functions[key] = fn
            
        case *ast.GenDecl:
            if node.Tok == token.TYPE {
                for _, spec := range node.Specs {
                    if ts, ok := spec.(*ast.TypeSpec); ok {
                        t := g.extractType(fset, ts)
                        parsed.Types[t.Name] = t
                    }
                }
            }
        }
        return true
    })
    
    return parsed, nil
}

func (g *GoExtractor) extractFunc(fset *token.FileSet, fn *ast.FuncDecl) *GoFunc {
    goFn := &GoFunc{
        Name:       fn.Name.Name,
        IsExported: unicode.IsUpper(rune(fn.Name.Name[0])),
        StartLine:  fset.Position(fn.Pos()).Line,
        EndLine:    fset.Position(fn.End()).Line,
    }
    
    // Extract receiver
    if fn.Recv != nil && len(fn.Recv.List) > 0 {
        goFn.Receiver = g.typeToString(fn.Recv.List[0].Type)
    }
    
    // Extract parameters
    if fn.Type.Params != nil {
        for _, field := range fn.Type.Params.List {
            typeStr := g.typeToString(field.Type)
            if len(field.Names) == 0 {
                goFn.Params = append(goFn.Params, Param{Type: typeStr})
            } else {
                for _, name := range field.Names {
                    goFn.Params = append(goFn.Params, Param{
                        Name: name.Name,
                        Type: typeStr,
                    })
                }
            }
        }
    }
    
    // Extract return types
    if fn.Type.Results != nil {
        for _, field := range fn.Type.Results.List {
            goFn.Returns = append(goFn.Returns, g.typeToString(field.Type))
        }
    }
    
    // Hash the body for change detection
    if fn.Body != nil {
        var buf bytes.Buffer
        printer.Fprint(&buf, fset, fn.Body)
        goFn.BodyHash = fmt.Sprintf("%x", buf.Bytes())
    }
    
    return goFn
}

func (g *GoExtractor) extractType(fset *token.FileSet, ts *ast.TypeSpec) *GoType {
    goType := &GoType{
        Name:       ts.Name.Name,
        IsExported: unicode.IsUpper(rune(ts.Name.Name[0])),
        StartLine:  fset.Position(ts.Pos()).Line,
        EndLine:    fset.Position(ts.End()).Line,
    }
    
    switch t := ts.Type.(type) {
    case *ast.StructType:
        goType.Kind = "struct"
        if t.Fields != nil {
            for _, field := range t.Fields.List {
                typeStr := g.typeToString(field.Type)
                tag := ""
                if field.Tag != nil {
                    tag = field.Tag.Value
                }
                if len(field.Names) == 0 {
                    // Embedded field
                    goType.Fields = append(goType.Fields, GoField{
                        Name: typeStr,
                        Type: typeStr,
                        Tag:  tag,
                    })
                } else {
                    for _, name := range field.Names {
                        goType.Fields = append(goType.Fields, GoField{
                            Name: name.Name,
                            Type: typeStr,
                            Tag:  tag,
                        })
                    }
                }
            }
        }
        
    case *ast.InterfaceType:
        goType.Kind = "interface"
        if t.Methods != nil {
            for _, method := range t.Methods.List {
                if len(method.Names) > 0 {
                    goType.Methods = append(goType.Methods, method.Names[0].Name)
                }
            }
        }
        
    default:
        goType.Kind = "alias"
    }
    
    return goType
}

func (g *GoExtractor) typeToString(expr ast.Expr) string {
    var buf bytes.Buffer
    printer.Fprint(&buf, token.NewFileSet(), expr)
    return buf.String()
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 5: Implement Go AST Diff Comparison (golang.go part 2)
**Time:** 5 min

Add the diff comparison logic to the Go extractor.

**Append to file:** `scripts/codereview/internal/ast/golang.go`

```go
// ExtractDiff compares two Go files and returns semantic differences
func (g *GoExtractor) ExtractDiff(ctx context.Context, beforePath, afterPath string) (*SemanticDiff, error) {
    before, err := g.parseFile(beforePath)
    if err != nil {
        return nil, fmt.Errorf("parsing before file: %w", err)
    }
    
    after, err := g.parseFile(afterPath)
    if err != nil {
        return nil, fmt.Errorf("parsing after file: %w", err)
    }
    
    diff := &SemanticDiff{
        Language: "go",
        FilePath: afterPath,
    }
    
    if afterPath == "" {
        diff.FilePath = beforePath
    }
    
    // Compare functions
    diff.Functions = g.compareFunctions(before.Functions, after.Functions)
    
    // Compare types
    diff.Types = g.compareTypes(before.Types, after.Types)
    
    // Compare imports
    diff.Imports = g.compareImports(before.Imports, after.Imports)
    
    // Compute summary
    diff.Summary = ComputeSummary(diff.Functions, diff.Types, diff.Imports)
    
    return diff, nil
}

func (g *GoExtractor) compareFunctions(before, after map[string]*GoFunc) []FunctionDiff {
    var diffs []FunctionDiff
    
    // Find removed and modified functions
    for name, beforeFn := range before {
        afterFn, exists := after[name]
        if !exists {
            diffs = append(diffs, FunctionDiff{
                Name:       name,
                ChangeType: ChangeRemoved,
                Before:     g.funcToSig(beforeFn),
            })
            continue
        }
        
        // Check if modified
        if g.funcChanged(beforeFn, afterFn) {
            diff := FunctionDiff{
                Name:       name,
                ChangeType: ChangeModified,
                Before:     g.funcToSig(beforeFn),
                After:      g.funcToSig(afterFn),
            }
            diff.BodyDiff = g.describeFuncChange(beforeFn, afterFn)
            diffs = append(diffs, diff)
        }
    }
    
    // Find added functions
    for name, afterFn := range after {
        if _, exists := before[name]; !exists {
            diffs = append(diffs, FunctionDiff{
                Name:       name,
                ChangeType: ChangeAdded,
                After:      g.funcToSig(afterFn),
            })
        }
    }
    
    return diffs
}

func (g *GoExtractor) funcToSig(fn *GoFunc) *FuncSig {
    return &FuncSig{
        Params:     fn.Params,
        Returns:    fn.Returns,
        Receiver:   fn.Receiver,
        IsExported: fn.IsExported,
        StartLine:  fn.StartLine,
        EndLine:    fn.EndLine,
    }
}

func (g *GoExtractor) funcChanged(before, after *GoFunc) bool {
    // Check signature changes
    if !g.paramsEqual(before.Params, after.Params) {
        return true
    }
    if !g.stringsEqual(before.Returns, after.Returns) {
        return true
    }
    if before.Receiver != after.Receiver {
        return true
    }
    // Check body changes
    if before.BodyHash != after.BodyHash {
        return true
    }
    return false
}

func (g *GoExtractor) describeFuncChange(before, after *GoFunc) string {
    var changes []string
    
    if !g.paramsEqual(before.Params, after.Params) {
        changes = append(changes, "parameters changed")
    }
    if !g.stringsEqual(before.Returns, after.Returns) {
        changes = append(changes, "return types changed")
    }
    if before.Receiver != after.Receiver {
        changes = append(changes, "receiver changed")
    }
    if before.BodyHash != after.BodyHash {
        changes = append(changes, "implementation changed")
    }
    
    return strings.Join(changes, ", ")
}

func (g *GoExtractor) compareTypes(before, after map[string]*GoType) []TypeDiff {
    var diffs []TypeDiff
    
    // Find removed and modified types
    for name, beforeType := range before {
        afterType, exists := after[name]
        if !exists {
            diffs = append(diffs, TypeDiff{
                Name:       name,
                Kind:       beforeType.Kind,
                ChangeType: ChangeRemoved,
                StartLine:  beforeType.StartLine,
                EndLine:    beforeType.EndLine,
            })
            continue
        }
        
        // Check if modified
        fieldDiffs := g.compareFields(beforeType.Fields, afterType.Fields)
        if len(fieldDiffs) > 0 || beforeType.Kind != afterType.Kind {
            diffs = append(diffs, TypeDiff{
                Name:       name,
                Kind:       afterType.Kind,
                ChangeType: ChangeModified,
                Fields:     fieldDiffs,
                StartLine:  afterType.StartLine,
                EndLine:    afterType.EndLine,
            })
        }
    }
    
    // Find added types
    for name, afterType := range after {
        if _, exists := before[name]; !exists {
            diffs = append(diffs, TypeDiff{
                Name:       name,
                Kind:       afterType.Kind,
                ChangeType: ChangeAdded,
                StartLine:  afterType.StartLine,
                EndLine:    afterType.EndLine,
            })
        }
    }
    
    return diffs
}

func (g *GoExtractor) compareFields(before, after []GoField) []FieldDiff {
    var diffs []FieldDiff
    
    beforeMap := make(map[string]GoField)
    for _, f := range before {
        beforeMap[f.Name] = f
    }
    
    afterMap := make(map[string]GoField)
    for _, f := range after {
        afterMap[f.Name] = f
    }
    
    // Find removed and modified fields
    for name, beforeField := range beforeMap {
        afterField, exists := afterMap[name]
        if !exists {
            diffs = append(diffs, FieldDiff{
                Name:       name,
                ChangeType: ChangeRemoved,
                OldType:    beforeField.Type,
            })
            continue
        }
        
        if beforeField.Type != afterField.Type {
            diffs = append(diffs, FieldDiff{
                Name:       name,
                ChangeType: ChangeModified,
                OldType:    beforeField.Type,
                NewType:    afterField.Type,
            })
        }
    }
    
    // Find added fields
    for name, afterField := range afterMap {
        if _, exists := beforeMap[name]; !exists {
            diffs = append(diffs, FieldDiff{
                Name:       name,
                ChangeType: ChangeAdded,
                NewType:    afterField.Type,
            })
        }
    }
    
    return diffs
}

func (g *GoExtractor) compareImports(before, after map[string]string) []ImportDiff {
    var diffs []ImportDiff
    
    for path, alias := range before {
        if _, exists := after[path]; !exists {
            diffs = append(diffs, ImportDiff{
                Path:       path,
                Alias:      alias,
                ChangeType: ChangeRemoved,
            })
        }
    }
    
    for path, alias := range after {
        if _, exists := before[path]; !exists {
            diffs = append(diffs, ImportDiff{
                Path:       path,
                Alias:      alias,
                ChangeType: ChangeAdded,
            })
        }
    }
    
    return diffs
}

func (g *GoExtractor) paramsEqual(a, b []Param) bool {
    if len(a) != len(b) {
        return false
    }
    for i := range a {
        if a[i].Name != b[i].Name || a[i].Type != b[i].Type {
            return false
        }
    }
    return true
}

func (g *GoExtractor) stringsEqual(a, b []string) bool {
    if len(a) != len(b) {
        return false
    }
    for i := range a {
        if a[i] != b[i] {
            return false
        }
    }
    return true
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 6: Create Go Test Fixtures
**Time:** 3 min

Create test fixtures for the Go AST extractor.

**File:** `scripts/codereview/testdata/go/before.go`

```go
package example

import (
    "fmt"
    "strings"
)

// User represents a user in the system
type User struct {
    ID   int
    Name string
}

// Greeter interface for greeting
type Greeter interface {
    Greet() string
}

// Hello returns a greeting message
func Hello(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}

// (u *User) GetName returns the user's name
func (u *User) GetName() string {
    return u.Name
}

// FormatName formats a name with optional prefix
func FormatName(name string) string {
    return strings.Title(name)
}
```

**File:** `scripts/codereview/testdata/go/after.go`

```go
package example

import (
    "context"
    "fmt"
)

// User represents a user in the system
type User struct {
    ID       int
    Name     string
    Email    string  // Added field
    IsActive bool    // Added field
}

// Greeter interface for greeting
type Greeter interface {
    Greet() string
    GreetWithContext(ctx context.Context) string // Added method
}

// Config is a new type
type Config struct {
    Debug   bool
    Timeout int
}

// Hello returns a greeting message (signature changed)
func Hello(ctx context.Context, name string) (string, error) {
    if name == "" {
        return "", fmt.Errorf("name is required")
    }
    return fmt.Sprintf("Hello, %s!", name), nil
}

// (u *User) GetName returns the user's name
func (u *User) GetName() string {
    return u.Name
}

// (u *User) GetEmail is a new method
func (u *User) GetEmail() string {
    return u.Email
}

// NewGreeting is a new function
func NewGreeting(prefix, name string) string {
    return fmt.Sprintf("%s, %s!", prefix, name)
}
```

**Verification:**
```bash
ls scripts/codereview/testdata/go/
# Should show: before.go, after.go
```

---

### Task 7: Add Go Extractor Unit Tests
**Time:** 5 min

Create unit tests for the Go AST extractor.

**File:** `scripts/codereview/internal/ast/golang_test.go`

```go
package ast

import (
    "context"
    "path/filepath"
    "testing"
)

func TestGoExtractor_ExtractDiff(t *testing.T) {
    extractor := NewGoExtractor()
    
    beforePath := filepath.Join("..", "..", "testdata", "go", "before.go")
    afterPath := filepath.Join("..", "..", "testdata", "go", "after.go")
    
    diff, err := extractor.ExtractDiff(context.Background(), beforePath, afterPath)
    if err != nil {
        t.Fatalf("ExtractDiff failed: %v", err)
    }
    
    // Verify language
    if diff.Language != "go" {
        t.Errorf("expected language 'go', got '%s'", diff.Language)
    }
    
    // Verify function changes
    funcChanges := make(map[string]ChangeType)
    for _, f := range diff.Functions {
        funcChanges[f.Name] = f.ChangeType
    }
    
    // Hello should be modified (signature changed)
    if ct, ok := funcChanges["Hello"]; !ok || ct != ChangeModified {
        t.Errorf("expected Hello to be modified, got %v", funcChanges["Hello"])
    }
    
    // FormatName should be removed
    if ct, ok := funcChanges["FormatName"]; !ok || ct != ChangeRemoved {
        t.Errorf("expected FormatName to be removed, got %v", funcChanges["FormatName"])
    }
    
    // NewGreeting should be added
    if ct, ok := funcChanges["NewGreeting"]; !ok || ct != ChangeAdded {
        t.Errorf("expected NewGreeting to be added, got %v", funcChanges["NewGreeting"])
    }
    
    // User.GetEmail should be added
    if ct, ok := funcChanges["*User.GetEmail"]; !ok || ct != ChangeAdded {
        t.Errorf("expected *User.GetEmail to be added, got %v", funcChanges["*User.GetEmail"])
    }
    
    // Verify type changes
    typeChanges := make(map[string]ChangeType)
    for _, ty := range diff.Types {
        typeChanges[ty.Name] = ty.ChangeType
    }
    
    // User should be modified (fields added)
    if ct, ok := typeChanges["User"]; !ok || ct != ChangeModified {
        t.Errorf("expected User to be modified, got %v", typeChanges["User"])
    }
    
    // Config should be added
    if ct, ok := typeChanges["Config"]; !ok || ct != ChangeAdded {
        t.Errorf("expected Config to be added, got %v", typeChanges["Config"])
    }
    
    // Verify import changes
    importChanges := make(map[string]ChangeType)
    for _, imp := range diff.Imports {
        importChanges[imp.Path] = imp.ChangeType
    }
    
    // strings should be removed
    if ct, ok := importChanges["strings"]; !ok || ct != ChangeRemoved {
        t.Errorf("expected 'strings' import to be removed, got %v", importChanges["strings"])
    }
    
    // context should be added
    if ct, ok := importChanges["context"]; !ok || ct != ChangeAdded {
        t.Errorf("expected 'context' import to be added, got %v", importChanges["context"])
    }
    
    // Verify summary
    if diff.Summary.FunctionsAdded < 2 {
        t.Errorf("expected at least 2 functions added, got %d", diff.Summary.FunctionsAdded)
    }
    if diff.Summary.FunctionsRemoved < 1 {
        t.Errorf("expected at least 1 function removed, got %d", diff.Summary.FunctionsRemoved)
    }
    if diff.Summary.TypesAdded < 1 {
        t.Errorf("expected at least 1 type added, got %d", diff.Summary.TypesAdded)
    }
}

func TestGoExtractor_NewFile(t *testing.T) {
    extractor := NewGoExtractor()
    
    afterPath := filepath.Join("..", "..", "testdata", "go", "after.go")
    
    diff, err := extractor.ExtractDiff(context.Background(), "", afterPath)
    if err != nil {
        t.Fatalf("ExtractDiff failed: %v", err)
    }
    
    // All functions should be added
    for _, f := range diff.Functions {
        if f.ChangeType != ChangeAdded {
            t.Errorf("expected function %s to be added, got %s", f.Name, f.ChangeType)
        }
    }
}

func TestGoExtractor_DeletedFile(t *testing.T) {
    extractor := NewGoExtractor()
    
    beforePath := filepath.Join("..", "..", "testdata", "go", "before.go")
    
    diff, err := extractor.ExtractDiff(context.Background(), beforePath, "")
    if err != nil {
        t.Fatalf("ExtractDiff failed: %v", err)
    }
    
    // All functions should be removed
    for _, f := range diff.Functions {
        if f.ChangeType != ChangeRemoved {
            t.Errorf("expected function %s to be removed, got %s", f.Name, f.ChangeType)
        }
    }
}
```

**Verification:**
```bash
cd scripts/codereview && go test ./internal/ast/ -v -run TestGoExtractor
```

---

### Task 8: Create TypeScript AST Extractor Package
**Time:** 3 min

Set up the TypeScript package for AST extraction.

**File:** `scripts/codereview/ts/package.json`

```json
{
  "name": "ast-extractor-ts",
  "version": "1.0.0",
  "description": "TypeScript AST extraction for semantic diffs",
  "main": "dist/ast-extractor.js",
  "scripts": {
    "build": "tsc",
    "extract": "node dist/ast-extractor.js"
  },
  "dependencies": {
    "typescript": "^5.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0"
  }
}
```

**File:** `scripts/codereview/ts/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "resolveJsonModule": true
  },
  "include": ["*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

**Verification:**
```bash
cd scripts/codereview/ts && npm install && npm run build
```

---

### Task 9: Implement TypeScript AST Extractor
**Time:** 5 min

Create the TypeScript AST extraction logic using the TypeScript Compiler API.

**File:** `scripts/codereview/ts/ast-extractor.ts`

```typescript
import * as ts from 'typescript';
import * as fs from 'fs';
import * as path from 'path';

interface Param {
  name: string;
  type: string;
}

interface FuncSig {
  params: Param[];
  returns: string[];
  is_async: boolean;
  is_exported: boolean;
  start_line: number;
  end_line: number;
}

interface FunctionDiff {
  name: string;
  change_type: 'added' | 'removed' | 'modified' | 'renamed';
  before?: FuncSig;
  after?: FuncSig;
  body_diff?: string;
}

interface FieldDiff {
  name: string;
  change_type: 'added' | 'removed' | 'modified';
  old_type?: string;
  new_type?: string;
}

interface TypeDiff {
  name: string;
  kind: string;
  change_type: 'added' | 'removed' | 'modified' | 'renamed';
  fields?: FieldDiff[];
  start_line: number;
  end_line: number;
}

interface ImportDiff {
  path: string;
  alias?: string;
  change_type: 'added' | 'removed';
}

interface ChangeSummary {
  functions_added: number;
  functions_removed: number;
  functions_modified: number;
  types_added: number;
  types_removed: number;
  types_modified: number;
  imports_added: number;
  imports_removed: number;
}

interface SemanticDiff {
  language: string;
  file_path: string;
  functions: FunctionDiff[];
  types: TypeDiff[];
  imports: ImportDiff[];
  summary: ChangeSummary;
  error?: string;
}

interface ParsedFunc {
  name: string;
  params: Param[];
  returns: string[];
  isAsync: boolean;
  isExported: boolean;
  startLine: number;
  endLine: number;
  bodyText: string;
}

interface ParsedType {
  name: string;
  kind: string;
  fields: Map<string, string>;
  isExported: boolean;
  startLine: number;
  endLine: number;
}

interface ParsedFile {
  functions: Map<string, ParsedFunc>;
  types: Map<string, ParsedType>;
  imports: Map<string, string>;
}

function parseFile(filePath: string): ParsedFile {
  const result: ParsedFile = {
    functions: new Map(),
    types: new Map(),
    imports: new Map(),
  };

  if (!filePath || !fs.existsSync(filePath)) {
    return result;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  const sourceFile = ts.createSourceFile(
    filePath,
    content,
    ts.ScriptTarget.Latest,
    true
  );

  function getLineNumber(pos: number): number {
    return sourceFile.getLineAndCharacterOfPosition(pos).line + 1;
  }

  function typeToString(type: ts.TypeNode | undefined): string {
    if (!type) return 'any';
    return content.substring(type.pos, type.end).trim();
  }

  function isExported(node: ts.Node): boolean {
    return (
      ts.canHaveModifiers(node) &&
      ts.getModifiers(node)?.some(
        (m) => m.kind === ts.SyntaxKind.ExportKeyword
      ) || false
    );
  }

  function visit(node: ts.Node) {
    // Extract imports
    if (ts.isImportDeclaration(node)) {
      const moduleSpecifier = node.moduleSpecifier;
      if (ts.isStringLiteral(moduleSpecifier)) {
        const importPath = moduleSpecifier.text;
        let alias = '';
        if (node.importClause?.name) {
          alias = node.importClause.name.text;
        }
        result.imports.set(importPath, alias);
      }
    }

    // Extract functions
    if (ts.isFunctionDeclaration(node) && node.name) {
      const func: ParsedFunc = {
        name: node.name.text,
        params: [],
        returns: [],
        isAsync: node.modifiers?.some(
          (m) => m.kind === ts.SyntaxKind.AsyncKeyword
        ) || false,
        isExported: isExported(node),
        startLine: getLineNumber(node.pos),
        endLine: getLineNumber(node.end),
        bodyText: node.body ? content.substring(node.body.pos, node.body.end) : '',
      };

      node.parameters.forEach((param) => {
        func.params.push({
          name: param.name.getText(sourceFile),
          type: typeToString(param.type),
        });
      });

      if (node.type) {
        func.returns.push(typeToString(node.type));
      }

      result.functions.set(func.name, func);
    }

    // Extract arrow functions assigned to const
    if (ts.isVariableStatement(node)) {
      const exported = isExported(node);
      node.declarationList.declarations.forEach((decl) => {
        if (
          ts.isIdentifier(decl.name) &&
          decl.initializer &&
          ts.isArrowFunction(decl.initializer)
        ) {
          const arrow = decl.initializer;
          const func: ParsedFunc = {
            name: decl.name.text,
            params: [],
            returns: [],
            isAsync: arrow.modifiers?.some(
              (m) => m.kind === ts.SyntaxKind.AsyncKeyword
            ) || false,
            isExported: exported,
            startLine: getLineNumber(node.pos),
            endLine: getLineNumber(node.end),
            bodyText: content.substring(arrow.body.pos, arrow.body.end),
          };

          arrow.parameters.forEach((param) => {
            func.params.push({
              name: param.name.getText(sourceFile),
              type: typeToString(param.type),
            });
          });

          if (arrow.type) {
            func.returns.push(typeToString(arrow.type));
          }

          result.functions.set(func.name, func);
        }
      });
    }

    // Extract interfaces
    if (ts.isInterfaceDeclaration(node)) {
      const parsedType: ParsedType = {
        name: node.name.text,
        kind: 'interface',
        fields: new Map(),
        isExported: isExported(node),
        startLine: getLineNumber(node.pos),
        endLine: getLineNumber(node.end),
      };

      node.members.forEach((member) => {
        if (ts.isPropertySignature(member) && member.name) {
          const name = member.name.getText(sourceFile);
          const type = typeToString(member.type);
          parsedType.fields.set(name, type);
        }
      });

      result.types.set(parsedType.name, parsedType);
    }

    // Extract type aliases
    if (ts.isTypeAliasDeclaration(node)) {
      const parsedType: ParsedType = {
        name: node.name.text,
        kind: 'type',
        fields: new Map(),
        isExported: isExported(node),
        startLine: getLineNumber(node.pos),
        endLine: getLineNumber(node.end),
      };

      if (ts.isTypeLiteralNode(node.type)) {
        node.type.members.forEach((member) => {
          if (ts.isPropertySignature(member) && member.name) {
            const name = member.name.getText(sourceFile);
            const type = typeToString(member.type);
            parsedType.fields.set(name, type);
          }
        });
      }

      result.types.set(parsedType.name, parsedType);
    }

    // Extract classes
    if (ts.isClassDeclaration(node) && node.name) {
      const parsedType: ParsedType = {
        name: node.name.text,
        kind: 'class',
        fields: new Map(),
        isExported: isExported(node),
        startLine: getLineNumber(node.pos),
        endLine: getLineNumber(node.end),
      };

      node.members.forEach((member) => {
        if (ts.isPropertyDeclaration(member) && member.name) {
          const name = member.name.getText(sourceFile);
          const type = typeToString(member.type);
          parsedType.fields.set(name, type);
        }
        // Extract class methods as functions
        if (ts.isMethodDeclaration(member) && member.name) {
          const methodName = `${node.name!.text}.${member.name.getText(sourceFile)}`;
          const func: ParsedFunc = {
            name: methodName,
            params: [],
            returns: [],
            isAsync: member.modifiers?.some(
              (m) => m.kind === ts.SyntaxKind.AsyncKeyword
            ) || false,
            isExported: isExported(node),
            startLine: getLineNumber(member.pos),
            endLine: getLineNumber(member.end),
            bodyText: member.body ? content.substring(member.body.pos, member.body.end) : '',
          };

          member.parameters.forEach((param) => {
            func.params.push({
              name: param.name.getText(sourceFile),
              type: typeToString(param.type),
            });
          });

          if (member.type) {
            func.returns.push(typeToString(member.type));
          }

          result.functions.set(func.name, func);
        }
      });

      result.types.set(parsedType.name, parsedType);
    }

    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return result;
}

function compareFunctions(
  before: Map<string, ParsedFunc>,
  after: Map<string, ParsedFunc>
): FunctionDiff[] {
  const diffs: FunctionDiff[] = [];

  // Find removed and modified
  before.forEach((beforeFunc, name) => {
    const afterFunc = after.get(name);
    if (!afterFunc) {
      diffs.push({
        name,
        change_type: 'removed',
        before: {
          params: beforeFunc.params,
          returns: beforeFunc.returns,
          is_async: beforeFunc.isAsync,
          is_exported: beforeFunc.isExported,
          start_line: beforeFunc.startLine,
          end_line: beforeFunc.endLine,
        },
      });
      return;
    }

    // Check for modifications
    const sigChanged =
      JSON.stringify(beforeFunc.params) !== JSON.stringify(afterFunc.params) ||
      JSON.stringify(beforeFunc.returns) !== JSON.stringify(afterFunc.returns) ||
      beforeFunc.isAsync !== afterFunc.isAsync;

    const bodyChanged = beforeFunc.bodyText !== afterFunc.bodyText;

    if (sigChanged || bodyChanged) {
      const changes: string[] = [];
      if (JSON.stringify(beforeFunc.params) !== JSON.stringify(afterFunc.params)) {
        changes.push('parameters changed');
      }
      if (JSON.stringify(beforeFunc.returns) !== JSON.stringify(afterFunc.returns)) {
        changes.push('return type changed');
      }
      if (beforeFunc.isAsync !== afterFunc.isAsync) {
        changes.push('async modifier changed');
      }
      if (bodyChanged) {
        changes.push('implementation changed');
      }

      diffs.push({
        name,
        change_type: 'modified',
        before: {
          params: beforeFunc.params,
          returns: beforeFunc.returns,
          is_async: beforeFunc.isAsync,
          is_exported: beforeFunc.isExported,
          start_line: beforeFunc.startLine,
          end_line: beforeFunc.endLine,
        },
        after: {
          params: afterFunc.params,
          returns: afterFunc.returns,
          is_async: afterFunc.isAsync,
          is_exported: afterFunc.isExported,
          start_line: afterFunc.startLine,
          end_line: afterFunc.endLine,
        },
        body_diff: changes.join(', '),
      });
    }
  });

  // Find added
  after.forEach((afterFunc, name) => {
    if (!before.has(name)) {
      diffs.push({
        name,
        change_type: 'added',
        after: {
          params: afterFunc.params,
          returns: afterFunc.returns,
          is_async: afterFunc.isAsync,
          is_exported: afterFunc.isExported,
          start_line: afterFunc.startLine,
          end_line: afterFunc.endLine,
        },
      });
    }
  });

  return diffs;
}

function compareTypes(
  before: Map<string, ParsedType>,
  after: Map<string, ParsedType>
): TypeDiff[] {
  const diffs: TypeDiff[] = [];

  before.forEach((beforeType, name) => {
    const afterType = after.get(name);
    if (!afterType) {
      diffs.push({
        name,
        kind: beforeType.kind,
        change_type: 'removed',
        start_line: beforeType.startLine,
        end_line: beforeType.endLine,
      });
      return;
    }

    // Compare fields
    const fieldDiffs: FieldDiff[] = [];
    beforeType.fields.forEach((type, fieldName) => {
      const afterFieldType = afterType.fields.get(fieldName);
      if (!afterFieldType) {
        fieldDiffs.push({
          name: fieldName,
          change_type: 'removed',
          old_type: type,
        });
      } else if (afterFieldType !== type) {
        fieldDiffs.push({
          name: fieldName,
          change_type: 'modified',
          old_type: type,
          new_type: afterFieldType,
        });
      }
    });

    afterType.fields.forEach((type, fieldName) => {
      if (!beforeType.fields.has(fieldName)) {
        fieldDiffs.push({
          name: fieldName,
          change_type: 'added',
          new_type: type,
        });
      }
    });

    if (fieldDiffs.length > 0 || beforeType.kind !== afterType.kind) {
      diffs.push({
        name,
        kind: afterType.kind,
        change_type: 'modified',
        fields: fieldDiffs,
        start_line: afterType.startLine,
        end_line: afterType.endLine,
      });
    }
  });

  after.forEach((afterType, name) => {
    if (!before.has(name)) {
      diffs.push({
        name,
        kind: afterType.kind,
        change_type: 'added',
        start_line: afterType.startLine,
        end_line: afterType.endLine,
      });
    }
  });

  return diffs;
}

function compareImports(
  before: Map<string, string>,
  after: Map<string, string>
): ImportDiff[] {
  const diffs: ImportDiff[] = [];

  before.forEach((alias, importPath) => {
    if (!after.has(importPath)) {
      diffs.push({
        path: importPath,
        alias: alias || undefined,
        change_type: 'removed',
      });
    }
  });

  after.forEach((alias, importPath) => {
    if (!before.has(importPath)) {
      diffs.push({
        path: importPath,
        alias: alias || undefined,
        change_type: 'added',
      });
    }
  });

  return diffs;
}

function extractDiff(beforePath: string, afterPath: string): SemanticDiff {
  const before = parseFile(beforePath);
  const after = parseFile(afterPath);

  const functions = compareFunctions(before.functions, after.functions);
  const types = compareTypes(before.types, after.types);
  const imports = compareImports(before.imports, after.imports);

  const summary: ChangeSummary = {
    functions_added: functions.filter((f) => f.change_type === 'added').length,
    functions_removed: functions.filter((f) => f.change_type === 'removed').length,
    functions_modified: functions.filter((f) => f.change_type === 'modified').length,
    types_added: types.filter((t) => t.change_type === 'added').length,
    types_removed: types.filter((t) => t.change_type === 'removed').length,
    types_modified: types.filter((t) => t.change_type === 'modified').length,
    imports_added: imports.filter((i) => i.change_type === 'added').length,
    imports_removed: imports.filter((i) => i.change_type === 'removed').length,
  };

  return {
    language: 'typescript',
    file_path: afterPath || beforePath,
    functions,
    types,
    imports,
    summary,
  };
}

// CLI entry point
function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: ast-extractor.ts <before-path> <after-path>');
    console.error('Use empty string "" for new/deleted files');
    process.exit(1);
  }

  const beforePath = args[0] === '""' || args[0] === '' ? '' : args[0];
  const afterPath = args[1] === '""' || args[1] === '' ? '' : args[1];

  try {
    const diff = extractDiff(beforePath, afterPath);
    console.log(JSON.stringify(diff, null, 2));
  } catch (error) {
    const diff: SemanticDiff = {
      language: 'typescript',
      file_path: afterPath || beforePath,
      functions: [],
      types: [],
      imports: [],
      summary: {
        functions_added: 0,
        functions_removed: 0,
        functions_modified: 0,
        types_added: 0,
        types_removed: 0,
        types_modified: 0,
        imports_added: 0,
        imports_removed: 0,
      },
      error: error instanceof Error ? error.message : String(error),
    };
    console.log(JSON.stringify(diff, null, 2));
    process.exit(1);
  }
}

main();
```

**Verification:**
```bash
cd scripts/codereview/ts && npm run build
```

---

### Task 10: Create TypeScript Test Fixtures
**Time:** 3 min

Create test fixtures for the TypeScript AST extractor.

**File:** `scripts/codereview/testdata/ts/before.ts`

```typescript
import { useState } from 'react';
import axios from 'axios';

export interface User {
  id: number;
  name: string;
}

export type Status = 'active' | 'inactive';

export function greet(name: string): string {
  return `Hello, ${name}!`;
}

export async function fetchUser(id: number): Promise<User> {
  const response = await axios.get(`/users/${id}`);
  return response.data;
}

export const formatName = (name: string): string => {
  return name.trim().toUpperCase();
};

export class UserService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getUser(id: number): Promise<User> {
    const response = await axios.get(`${this.baseUrl}/users/${id}`);
    return response.data;
  }
}
```

**File:** `scripts/codereview/testdata/ts/after.ts`

```typescript
import { useState, useEffect } from 'react';
import { api } from './api';

export interface User {
  id: number;
  name: string;
  email: string;  // Added field
  isActive: boolean;  // Added field
}

export type Status = 'active' | 'inactive' | 'pending';  // Added 'pending'

export interface Config {  // New interface
  debug: boolean;
  timeout: number;
}

export function greet(name: string, greeting?: string): string {  // Added parameter
  return `${greeting || 'Hello'}, ${name}!`;
}

export async function fetchUser(id: number, options?: Config): Promise<User> {  // Added parameter
  const response = await api.get(`/users/${id}`, options);
  return response.data;
}

// formatName removed

export const validateEmail = (email: string): boolean => {  // New function
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

export class UserService {
  private baseUrl: string;
  private config: Config;  // Added field

  constructor(baseUrl: string, config: Config) {  // Changed signature
    this.baseUrl = baseUrl;
    this.config = config;
  }

  async getUser(id: number): Promise<User> {
    const response = await api.get(`${this.baseUrl}/users/${id}`);
    return response.data;
  }

  async updateUser(id: number, data: Partial<User>): Promise<User> {  // New method
    const response = await api.put(`${this.baseUrl}/users/${id}`, data);
    return response.data;
  }
}
```

**Verification:**
```bash
ls scripts/codereview/testdata/ts/
# Should show: before.ts, after.ts
```

---

### Task 11: Implement Python AST Extractor
**Time:** 5 min

Create the Python AST extraction script.

**File:** `scripts/codereview/py/ast_extractor.py`

```python
#!/usr/bin/env python3
"""
Python AST Extractor for Semantic Diffs.

Extracts functions, classes, and imports from Python files
and compares before/after versions to generate semantic diffs.
"""

import ast
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Param:
    name: str
    type: str = ""


@dataclass
class FuncSig:
    params: list[Param]
    returns: list[str]
    is_async: bool = False
    decorators: list[str] = field(default_factory=list)
    is_exported: bool = True
    start_line: int = 0
    end_line: int = 0


@dataclass
class FunctionDiff:
    name: str
    change_type: str  # added, removed, modified, renamed
    before: Optional[FuncSig] = None
    after: Optional[FuncSig] = None
    body_diff: str = ""


@dataclass
class FieldDiff:
    name: str
    change_type: str
    old_type: str = ""
    new_type: str = ""


@dataclass
class TypeDiff:
    name: str
    kind: str  # class, dataclass
    change_type: str
    fields: list[FieldDiff] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0


@dataclass
class ImportDiff:
    path: str
    alias: str = ""
    change_type: str = ""


@dataclass
class ChangeSummary:
    functions_added: int = 0
    functions_removed: int = 0
    functions_modified: int = 0
    types_added: int = 0
    types_removed: int = 0
    types_modified: int = 0
    imports_added: int = 0
    imports_removed: int = 0


@dataclass
class SemanticDiff:
    language: str
    file_path: str
    functions: list[FunctionDiff]
    types: list[TypeDiff]
    imports: list[ImportDiff]
    summary: ChangeSummary
    error: str = ""


@dataclass
class ParsedFunc:
    name: str
    params: list[Param]
    returns: list[str]
    is_async: bool
    decorators: list[str]
    is_exported: bool
    start_line: int
    end_line: int
    body_hash: str


@dataclass
class ParsedClass:
    name: str
    is_dataclass: bool
    fields: dict[str, str]  # name -> type
    methods: list[str]
    is_exported: bool
    start_line: int
    end_line: int


@dataclass
class ParsedFile:
    functions: dict[str, ParsedFunc]
    classes: dict[str, ParsedClass]
    imports: dict[str, str]  # module -> alias


def get_annotation_str(node: Optional[ast.expr]) -> str:
    """Convert an annotation AST node to string."""
    if node is None:
        return ""
    return ast.unparse(node)


def parse_file(file_path: str) -> ParsedFile:
    """Parse a Python file and extract semantic information."""
    result = ParsedFile(functions={}, classes={}, imports={})
    
    if not file_path or not Path(file_path).exists():
        return result
    
    content = Path(file_path).read_text()
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return result
    
    for node in ast.walk(tree):
        # Extract imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports[alias.name] = alias.asname or ""
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                key = f"{module}.{alias.name}" if module else alias.name
                result.imports[key] = alias.asname or ""
    
    # Process top-level definitions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func = _parse_function(node, content)
            result.functions[func.name] = func
        
        elif isinstance(node, ast.ClassDef):
            cls = _parse_class(node, content)
            result.classes[cls.name] = cls
            
            # Extract methods as functions
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method = _parse_function(item, content)
                    method.name = f"{cls.name}.{method.name}"
                    result.functions[method.name] = method
    
    return result


def _parse_function(node: ast.FunctionDef | ast.AsyncFunctionDef, content: str) -> ParsedFunc:
    """Parse a function definition."""
    params = []
    for arg in node.args.args:
        params.append(Param(
            name=arg.arg,
            type=get_annotation_str(arg.annotation)
        ))
    
    returns = []
    if node.returns:
        returns.append(get_annotation_str(node.returns))
    
    decorators = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
            decorators.append(dec.func.id)
        elif isinstance(dec, ast.Attribute):
            decorators.append(ast.unparse(dec))
    
    # Hash the body for change detection
    body_lines = content.split('\n')[node.lineno - 1:node.end_lineno]
    body_hash = str(hash('\n'.join(body_lines)))
    
    return ParsedFunc(
        name=node.name,
        params=params,
        returns=returns,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        decorators=decorators,
        is_exported=not node.name.startswith('_'),
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        body_hash=body_hash,
    )


def _parse_class(node: ast.ClassDef, content: str) -> ParsedClass:
    """Parse a class definition."""
    is_dataclass = any(
        (isinstance(d, ast.Name) and d.id == 'dataclass') or
        (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == 'dataclass')
        for d in node.decorator_list
    )
    
    fields: dict[str, str] = {}
    methods: list[str] = []
    
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fields[item.target.id] = get_annotation_str(item.annotation)
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(item.name)
    
    return ParsedClass(
        name=node.name,
        is_dataclass=is_dataclass,
        fields=fields,
        methods=methods,
        is_exported=not node.name.startswith('_'),
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
    )


def compare_functions(
    before: dict[str, ParsedFunc],
    after: dict[str, ParsedFunc]
) -> list[FunctionDiff]:
    """Compare functions between before and after versions."""
    diffs = []
    
    # Find removed and modified
    for name, before_func in before.items():
        after_func = after.get(name)
        if after_func is None:
            diffs.append(FunctionDiff(
                name=name,
                change_type="removed",
                before=FuncSig(
                    params=before_func.params,
                    returns=before_func.returns,
                    is_async=before_func.is_async,
                    decorators=before_func.decorators,
                    is_exported=before_func.is_exported,
                    start_line=before_func.start_line,
                    end_line=before_func.end_line,
                ),
            ))
            continue
        
        # Check for modifications
        changes = []
        if before_func.params != after_func.params:
            changes.append("parameters changed")
        if before_func.returns != after_func.returns:
            changes.append("return type changed")
        if before_func.is_async != after_func.is_async:
            changes.append("async modifier changed")
        if before_func.decorators != after_func.decorators:
            changes.append("decorators changed")
        if before_func.body_hash != after_func.body_hash:
            changes.append("implementation changed")
        
        if changes:
            diffs.append(FunctionDiff(
                name=name,
                change_type="modified",
                before=FuncSig(
                    params=before_func.params,
                    returns=before_func.returns,
                    is_async=before_func.is_async,
                    decorators=before_func.decorators,
                    is_exported=before_func.is_exported,
                    start_line=before_func.start_line,
                    end_line=before_func.end_line,
                ),
                after=FuncSig(
                    params=after_func.params,
                    returns=after_func.returns,
                    is_async=after_func.is_async,
                    decorators=after_func.decorators,
                    is_exported=after_func.is_exported,
                    start_line=after_func.start_line,
                    end_line=after_func.end_line,
                ),
                body_diff=", ".join(changes),
            ))
    
    # Find added
    for name, after_func in after.items():
        if name not in before:
            diffs.append(FunctionDiff(
                name=name,
                change_type="added",
                after=FuncSig(
                    params=after_func.params,
                    returns=after_func.returns,
                    is_async=after_func.is_async,
                    decorators=after_func.decorators,
                    is_exported=after_func.is_exported,
                    start_line=after_func.start_line,
                    end_line=after_func.end_line,
                ),
            ))
    
    return diffs


def compare_classes(
    before: dict[str, ParsedClass],
    after: dict[str, ParsedClass]
) -> list[TypeDiff]:
    """Compare classes between before and after versions."""
    diffs = []
    
    for name, before_cls in before.items():
        after_cls = after.get(name)
        if after_cls is None:
            diffs.append(TypeDiff(
                name=name,
                kind="dataclass" if before_cls.is_dataclass else "class",
                change_type="removed",
                start_line=before_cls.start_line,
                end_line=before_cls.end_line,
            ))
            continue
        
        # Compare fields
        field_diffs = []
        for field_name, field_type in before_cls.fields.items():
            after_type = after_cls.fields.get(field_name)
            if after_type is None:
                field_diffs.append(FieldDiff(
                    name=field_name,
                    change_type="removed",
                    old_type=field_type,
                ))
            elif after_type != field_type:
                field_diffs.append(FieldDiff(
                    name=field_name,
                    change_type="modified",
                    old_type=field_type,
                    new_type=after_type,
                ))
        
        for field_name, field_type in after_cls.fields.items():
            if field_name not in before_cls.fields:
                field_diffs.append(FieldDiff(
                    name=field_name,
                    change_type="added",
                    new_type=field_type,
                ))
        
        if field_diffs or before_cls.is_dataclass != after_cls.is_dataclass:
            diffs.append(TypeDiff(
                name=name,
                kind="dataclass" if after_cls.is_dataclass else "class",
                change_type="modified",
                fields=field_diffs,
                start_line=after_cls.start_line,
                end_line=after_cls.end_line,
            ))
    
    for name, after_cls in after.items():
        if name not in before:
            diffs.append(TypeDiff(
                name=name,
                kind="dataclass" if after_cls.is_dataclass else "class",
                change_type="added",
                start_line=after_cls.start_line,
                end_line=after_cls.end_line,
            ))
    
    return diffs


def compare_imports(
    before: dict[str, str],
    after: dict[str, str]
) -> list[ImportDiff]:
    """Compare imports between before and after versions."""
    diffs = []
    
    for path, alias in before.items():
        if path not in after:
            diffs.append(ImportDiff(path=path, alias=alias, change_type="removed"))
    
    for path, alias in after.items():
        if path not in before:
            diffs.append(ImportDiff(path=path, alias=alias, change_type="added"))
    
    return diffs


def extract_diff(before_path: str, after_path: str) -> SemanticDiff:
    """Extract semantic diff between two Python files."""
    before = parse_file(before_path)
    after = parse_file(after_path)
    
    functions = compare_functions(before.functions, after.functions)
    types = compare_classes(before.classes, after.classes)
    imports = compare_imports(before.imports, after.imports)
    
    summary = ChangeSummary(
        functions_added=sum(1 for f in functions if f.change_type == "added"),
        functions_removed=sum(1 for f in functions if f.change_type == "removed"),
        functions_modified=sum(1 for f in functions if f.change_type == "modified"),
        types_added=sum(1 for t in types if t.change_type == "added"),
        types_removed=sum(1 for t in types if t.change_type == "removed"),
        types_modified=sum(1 for t in types if t.change_type == "modified"),
        imports_added=sum(1 for i in imports if i.change_type == "added"),
        imports_removed=sum(1 for i in imports if i.change_type == "removed"),
    )
    
    return SemanticDiff(
        language="python",
        file_path=after_path or before_path,
        functions=functions,
        types=types,
        imports=imports,
        summary=summary,
    )


def dataclass_to_dict(obj):
    """Recursively convert dataclass to dict."""
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for key, value in asdict(obj).items():
            if value is None:
                continue
            if isinstance(value, list) and not value:
                continue
            if isinstance(value, str) and not value:
                continue
            result[key] = value
        return result
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    return obj


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: ast_extractor.py <before-path> <after-path>", file=sys.stderr)
        print('Use empty string "" for new/deleted files', file=sys.stderr)
        sys.exit(1)
    
    before_path = sys.argv[1] if sys.argv[1] not in ('""', '') else ''
    after_path = sys.argv[2] if sys.argv[2] not in ('""', '') else ''
    
    try:
        diff = extract_diff(before_path, after_path)
        output = dataclass_to_dict(diff)
        print(json.dumps(output, indent=2))
    except Exception as e:
        error_diff = SemanticDiff(
            language="python",
            file_path=after_path or before_path,
            functions=[],
            types=[],
            imports=[],
            summary=ChangeSummary(),
            error=str(e),
        )
        print(json.dumps(dataclass_to_dict(error_diff), indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Verification:**
```bash
python3 scripts/codereview/py/ast_extractor.py --help 2>&1 || true
# Should show usage message
```

---

### Task 12: Create Python Test Fixtures
**Time:** 3 min

Create test fixtures for the Python AST extractor.

**File:** `scripts/codereview/testdata/py/before.py`

```python
"""Example module for testing AST extraction."""

import os
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str


class UserService:
    """Service for managing users."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return None
    
    def list_users(self) -> List[User]:
        """List all users."""
        return []


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


async def fetch_data(url: str) -> dict:
    """Fetch data from a URL."""
    return {}


def format_name(name: str) -> str:
    """Format a name."""
    return name.strip().title()
```

**File:** `scripts/codereview/testdata/py/after.py`

```python
"""Example module for testing AST extraction."""

import logging
from typing import Optional, List, Dict
from dataclasses import dataclass, field

@dataclass
class User:
    id: int
    name: str
    email: str  # Added field
    is_active: bool = True  # Added field with default


@dataclass
class Config:  # New dataclass
    debug: bool = False
    timeout: int = 30


class UserService:
    """Service for managing users."""
    
    def __init__(self, db_url: str, config: Config):  # Changed signature
        self.db_url = db_url
        self.config = config
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        logging.info(f"Fetching user {user_id}")  # Changed implementation
        return None
    
    def list_users(self, active_only: bool = False) -> List[User]:  # Changed signature
        """List all users."""
        return []
    
    async def update_user(self, user_id: int, data: Dict) -> User:  # New async method
        """Update a user."""
        return User(id=user_id, name="", email="")


def greet(name: str, greeting: str = "Hello") -> str:  # Added parameter
    """Return a greeting message."""
    return f"{greeting}, {name}!"


async def fetch_data(url: str, timeout: int = 30) -> dict:  # Added parameter
    """Fetch data from a URL."""
    return {}


# format_name removed


def validate_email(email: str) -> bool:  # New function
    """Validate an email address."""
    return "@" in email
```

**Verification:**
```bash
ls scripts/codereview/testdata/py/
# Should show: before.py, after.py
```

---

### Task 13: Implement TypeScript Bridge for Go (typescript.go)
**Time:** 4 min

Create the Go bridge that calls the TypeScript extractor.

**File:** `scripts/codereview/internal/ast/typescript.go`

```go
package ast

import (
    "context"
    "encoding/json"
    "fmt"
    "os/exec"
    "path/filepath"
)

// TypeScriptExtractor implements AST extraction for TypeScript files
type TypeScriptExtractor struct {
    nodeExecutable string
    scriptPath     string
}

// NewTypeScriptExtractor creates a new TypeScript AST extractor
func NewTypeScriptExtractor(scriptDir string) *TypeScriptExtractor {
    return &TypeScriptExtractor{
        nodeExecutable: "node",
        scriptPath:     filepath.Join(scriptDir, "ts", "dist", "ast-extractor.js"),
    }
}

func (t *TypeScriptExtractor) Language() string {
    return "typescript"
}

func (t *TypeScriptExtractor) SupportedExtensions() []string {
    return []string{".ts", ".tsx", ".js", ".jsx"}
}

func (t *TypeScriptExtractor) ExtractDiff(ctx context.Context, beforePath, afterPath string) (*SemanticDiff, error) {
    before := beforePath
    if before == "" {
        before = `""`
    }
    after := afterPath
    if after == "" {
        after = `""`
    }
    
    cmd := exec.CommandContext(ctx, t.nodeExecutable, t.scriptPath, before, after)
    output, err := cmd.Output()
    if err != nil {
        if exitErr, ok := err.(*exec.ExitError); ok {
            return nil, fmt.Errorf("typescript extractor failed: %s", string(exitErr.Stderr))
        }
        return nil, fmt.Errorf("failed to run typescript extractor: %w", err)
    }
    
    var diff SemanticDiff
    if err := json.Unmarshal(output, &diff); err != nil {
        return nil, fmt.Errorf("failed to parse typescript extractor output: %w", err)
    }
    
    return &diff, nil
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 14: Implement Python Bridge for Go (python.go)
**Time:** 4 min

Create the Go bridge that calls the Python extractor.

**File:** `scripts/codereview/internal/ast/python.go`

```go
package ast

import (
    "context"
    "encoding/json"
    "fmt"
    "os/exec"
    "path/filepath"
)

// PythonExtractor implements AST extraction for Python files
type PythonExtractor struct {
    pythonExecutable string
    scriptPath       string
}

// NewPythonExtractor creates a new Python AST extractor
func NewPythonExtractor(scriptDir string) *PythonExtractor {
    return &PythonExtractor{
        pythonExecutable: "python3",
        scriptPath:       filepath.Join(scriptDir, "py", "ast_extractor.py"),
    }
}

func (p *PythonExtractor) Language() string {
    return "python"
}

func (p *PythonExtractor) SupportedExtensions() []string {
    return []string{".py", ".pyi"}
}

func (p *PythonExtractor) ExtractDiff(ctx context.Context, beforePath, afterPath string) (*SemanticDiff, error) {
    before := beforePath
    if before == "" {
        before = `""`
    }
    after := afterPath
    if after == "" {
        after = `""`
    }
    
    cmd := exec.CommandContext(ctx, p.pythonExecutable, p.scriptPath, before, after)
    output, err := cmd.Output()
    if err != nil {
        if exitErr, ok := err.(*exec.ExitError); ok {
            return nil, fmt.Errorf("python extractor failed: %s", string(exitErr.Stderr))
        }
        return nil, fmt.Errorf("failed to run python extractor: %w", err)
    }
    
    var diff SemanticDiff
    if err := json.Unmarshal(output, &diff); err != nil {
        return nil, fmt.Errorf("failed to parse python extractor output: %w", err)
    }
    
    return &diff, nil
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 15: Implement Semantic Diff Renderer
**Time:** 5 min

Create a renderer that converts AST JSON to human-readable markdown.

**File:** `scripts/codereview/internal/ast/renderer.go`

```go
package ast

import (
    "encoding/json"
    "fmt"
    "strings"
)

// RenderMarkdown converts a SemanticDiff to markdown format
func RenderMarkdown(diff *SemanticDiff) string {
    var sb strings.Builder
    
    sb.WriteString(fmt.Sprintf("# Semantic Changes: %s\n\n", diff.FilePath))
    sb.WriteString(fmt.Sprintf("**Language:** %s\n\n", diff.Language))
    
    // Summary section
    sb.WriteString("## Summary\n\n")
    sb.WriteString("| Category | Added | Removed | Modified |\n")
    sb.WriteString("|----------|-------|---------|----------|\n")
    sb.WriteString(fmt.Sprintf("| Functions | %d | %d | %d |\n",
        diff.Summary.FunctionsAdded,
        diff.Summary.FunctionsRemoved,
        diff.Summary.FunctionsModified))
    sb.WriteString(fmt.Sprintf("| Types | %d | %d | %d |\n",
        diff.Summary.TypesAdded,
        diff.Summary.TypesRemoved,
        diff.Summary.TypesModified))
    sb.WriteString(fmt.Sprintf("| Imports | %d | %d | - |\n\n",
        diff.Summary.ImportsAdded,
        diff.Summary.ImportsRemoved))
    
    // Functions section
    if len(diff.Functions) > 0 {
        sb.WriteString("## Functions\n\n")
        for _, fn := range diff.Functions {
            sb.WriteString(renderFunction(fn))
        }
    }
    
    // Types section
    if len(diff.Types) > 0 {
        sb.WriteString("## Types\n\n")
        for _, t := range diff.Types {
            sb.WriteString(renderType(t))
        }
    }
    
    // Imports section
    if len(diff.Imports) > 0 {
        sb.WriteString("## Imports\n\n")
        for _, imp := range diff.Imports {
            sb.WriteString(renderImport(imp))
        }
    }
    
    return sb.String()
}

func renderFunction(fn FunctionDiff) string {
    var sb strings.Builder
    
    icon := getChangeIcon(fn.ChangeType)
    sb.WriteString(fmt.Sprintf("### %s `%s`\n\n", icon, fn.Name))
    
    switch fn.ChangeType {
    case ChangeAdded:
        sb.WriteString("**Status:** Added\n\n")
        if fn.After != nil {
            sb.WriteString("```\n")
            sb.WriteString(formatSignature(fn.Name, fn.After))
            sb.WriteString("```\n\n")
        }
        
    case ChangeRemoved:
        sb.WriteString("**Status:** Removed\n\n")
        if fn.Before != nil {
            sb.WriteString("```\n")
            sb.WriteString(formatSignature(fn.Name, fn.Before))
            sb.WriteString("```\n\n")
        }
        
    case ChangeModified:
        sb.WriteString("**Status:** Modified\n\n")
        if fn.BodyDiff != "" {
            sb.WriteString(fmt.Sprintf("**Changes:** %s\n\n", fn.BodyDiff))
        }
        
        if fn.Before != nil && fn.After != nil {
            sb.WriteString("**Before:**\n```\n")
            sb.WriteString(formatSignature(fn.Name, fn.Before))
            sb.WriteString("```\n\n")
            sb.WriteString("**After:**\n```\n")
            sb.WriteString(formatSignature(fn.Name, fn.After))
            sb.WriteString("```\n\n")
        }
    }
    
    return sb.String()
}

func renderType(t TypeDiff) string {
    var sb strings.Builder
    
    icon := getChangeIcon(t.ChangeType)
    sb.WriteString(fmt.Sprintf("### %s `%s` (%s)\n\n", icon, t.Name, t.Kind))
    sb.WriteString(fmt.Sprintf("**Status:** %s\n", capitalizeFirst(string(t.ChangeType))))
    sb.WriteString(fmt.Sprintf("**Lines:** %d-%d\n\n", t.StartLine, t.EndLine))
    
    if len(t.Fields) > 0 {
        sb.WriteString("**Field Changes:**\n\n")
        sb.WriteString("| Field | Change | Old Type | New Type |\n")
        sb.WriteString("|-------|--------|----------|----------|\n")
        for _, f := range t.Fields {
            sb.WriteString(fmt.Sprintf("| %s | %s | %s | %s |\n",
                f.Name, f.ChangeType, f.OldType, f.NewType))
        }
        sb.WriteString("\n")
    }
    
    return sb.String()
}

func renderImport(imp ImportDiff) string {
    icon := getChangeIcon(imp.ChangeType)
    alias := ""
    if imp.Alias != "" {
        alias = fmt.Sprintf(" as %s", imp.Alias)
    }
    return fmt.Sprintf("- %s `%s`%s\n", icon, imp.Path, alias)
}

func formatSignature(name string, sig *FuncSig) string {
    var params []string
    for _, p := range sig.Params {
        if p.Type != "" {
            params = append(params, fmt.Sprintf("%s: %s", p.Name, p.Type))
        } else {
            params = append(params, p.Name)
        }
    }
    
    returns := strings.Join(sig.Returns, ", ")
    if returns == "" {
        returns = "void"
    }
    
    prefix := ""
    if sig.IsAsync {
        prefix = "async "
    }
    if sig.Receiver != "" {
        prefix += fmt.Sprintf("(%s) ", sig.Receiver)
    }
    
    return fmt.Sprintf("%sfunc %s(%s) -> %s\n", prefix, name, strings.Join(params, ", "), returns)
}

func getChangeIcon(changeType ChangeType) string {
    switch changeType {
    case ChangeAdded:
        return "+"
    case ChangeRemoved:
        return "-"
    case ChangeModified:
        return "~"
    case ChangeRenamed:
        return ">"
    default:
        return "?"
    }
}

func capitalizeFirst(s string) string {
    if s == "" {
        return s
    }
    return strings.ToUpper(s[:1]) + s[1:]
}

// RenderJSON returns the diff as formatted JSON
func RenderJSON(diff *SemanticDiff) ([]byte, error) {
    return json.MarshalIndent(diff, "", "  ")
}
```

**Verification:**
```bash
cd scripts/codereview && go build ./internal/ast/
```

---

### Task 16: Implement CLI Entry Point (main.go)
**Time:** 5 min

Create the main CLI tool that orchestrates AST extraction.

**File:** `scripts/codereview/cmd/ast-extractor/main.go`

```go
package main

import (
    "context"
    "encoding/json"
    "flag"
    "fmt"
    "os"
    "path/filepath"
    "strings"
    "time"

    "codereview/internal/ast"
)

var (
    beforeFile  = flag.String("before", "", "Path to the before version of the file")
    afterFile   = flag.String("after", "", "Path to the after version of the file")
    language    = flag.String("lang", "", "Force language (go, typescript, python)")
    outputFmt   = flag.String("output", "json", "Output format: json or markdown")
    scriptDir   = flag.String("scripts", "", "Directory containing language scripts (ts/, py/)")
    timeout     = flag.Duration("timeout", 30*time.Second, "Extraction timeout")
    batchFile   = flag.String("batch", "", "JSON file with batch of file pairs to process")
)

func main() {
    flag.Parse()
    
    if err := run(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}

func run() error {
    // Determine script directory
    scriptsPath := *scriptDir
    if scriptsPath == "" {
        // Default to relative path from executable
        exe, err := os.Executable()
        if err == nil {
            scriptsPath = filepath.Join(filepath.Dir(exe), "..", "..")
        } else {
            scriptsPath = "."
        }
    }
    
    // Create registry with all extractors
    registry := ast.NewRegistry()
    registry.Register(ast.NewGoExtractor())
    registry.Register(ast.NewTypeScriptExtractor(scriptsPath))
    registry.Register(ast.NewPythonExtractor(scriptsPath))
    
    ctx, cancel := context.WithTimeout(context.Background(), *timeout)
    defer cancel()
    
    // Handle batch mode
    if *batchFile != "" {
        return processBatch(ctx, registry, *batchFile)
    }
    
    // Single file mode
    if *beforeFile == "" && *afterFile == "" {
        return fmt.Errorf("either -before, -after, or -batch must be specified")
    }
    
    // Determine file path for language detection
    filePath := *afterFile
    if filePath == "" {
        filePath = *beforeFile
    }
    
    // Get extractor
    var extractor ast.Extractor
    var err error
    
    if *language != "" {
        extractor, err = getExtractorByLanguage(registry, *language, scriptsPath)
    } else {
        extractor, err = registry.GetExtractor(filePath)
    }
    
    if err != nil {
        return fmt.Errorf("failed to get extractor: %w", err)
    }
    
    // Extract diff
    diff, err := extractor.ExtractDiff(ctx, *beforeFile, *afterFile)
    if err != nil {
        return fmt.Errorf("extraction failed: %w", err)
    }
    
    // Output result
    return outputDiff(diff)
}

func getExtractorByLanguage(registry *ast.Registry, lang string, scriptsPath string) (ast.Extractor, error) {
    switch strings.ToLower(lang) {
    case "go", "golang":
        return ast.NewGoExtractor(), nil
    case "ts", "typescript", "javascript", "js":
        return ast.NewTypeScriptExtractor(scriptsPath), nil
    case "py", "python":
        return ast.NewPythonExtractor(scriptsPath), nil
    default:
        return nil, fmt.Errorf("unknown language: %s", lang)
    }
}

func processBatch(ctx context.Context, registry *ast.Registry, batchPath string) error {
    data, err := os.ReadFile(batchPath)
    if err != nil {
        return fmt.Errorf("failed to read batch file: %w", err)
    }
    
    var pairs []ast.FilePair
    if err := json.Unmarshal(data, &pairs); err != nil {
        return fmt.Errorf("failed to parse batch file: %w", err)
    }
    
    diffs, err := registry.ExtractAll(ctx, pairs)
    if err != nil {
        return fmt.Errorf("batch extraction failed: %w", err)
    }
    
    // Output all diffs
    if *outputFmt == "markdown" {
        for _, diff := range diffs {
            fmt.Println(ast.RenderMarkdown(&diff))
            fmt.Println("---\n")
        }
    } else {
        output, err := json.MarshalIndent(diffs, "", "  ")
        if err != nil {
            return fmt.Errorf("failed to marshal output: %w", err)
        }
        fmt.Println(string(output))
    }
    
    return nil
}

func outputDiff(diff *ast.SemanticDiff) error {
    if *outputFmt == "markdown" {
        fmt.Println(ast.RenderMarkdown(diff))
        return nil
    }
    
    output, err := ast.RenderJSON(diff)
    if err != nil {
        return fmt.Errorf("failed to marshal output: %w", err)
    }
    
    fmt.Println(string(output))
    return nil
}
```

**Verification:**
```bash
cd scripts/codereview && go build -o bin/ast-extractor ./cmd/ast-extractor/
```

---

### Task 17: Create go.mod for the Module
**Time:** 2 min

Initialize the Go module.

**File:** `scripts/codereview/go.mod`

```
module codereview

go 1.21
```

**Verification:**
```bash
cd scripts/codereview && go mod tidy
```

---

### Task 18: Add Integration Test
**Time:** 5 min

Create an integration test that exercises all extractors.

**File:** `scripts/codereview/internal/ast/integration_test.go`

```go
//go:build integration

package ast

import (
    "context"
    "os"
    "path/filepath"
    "testing"
    "time"
)

func TestIntegration_AllExtractors(t *testing.T) {
    // Skip if testdata doesn't exist
    testdataDir := filepath.Join("..", "..", "testdata")
    if _, err := os.Stat(testdataDir); os.IsNotExist(err) {
        t.Skip("testdata directory not found")
    }
    
    scriptsDir := filepath.Join("..", "..")
    
    tests := []struct {
        name       string
        extractor  Extractor
        beforePath string
        afterPath  string
        wantAdded  int
        wantRemoved int
    }{
        {
            name:       "Go",
            extractor:  NewGoExtractor(),
            beforePath: filepath.Join(testdataDir, "go", "before.go"),
            afterPath:  filepath.Join(testdataDir, "go", "after.go"),
            wantAdded:  2, // At least NewGreeting, User.GetEmail
            wantRemoved: 1, // FormatName
        },
        {
            name:       "TypeScript",
            extractor:  NewTypeScriptExtractor(scriptsDir),
            beforePath: filepath.Join(testdataDir, "ts", "before.ts"),
            afterPath:  filepath.Join(testdataDir, "ts", "after.ts"),
            wantAdded:  2, // validateEmail, UserService.updateUser
            wantRemoved: 1, // formatName
        },
        {
            name:       "Python",
            extractor:  NewPythonExtractor(scriptsDir),
            beforePath: filepath.Join(testdataDir, "py", "before.py"),
            afterPath:  filepath.Join(testdataDir, "py", "after.py"),
            wantAdded:  2, // validate_email, UserService.update_user
            wantRemoved: 1, // format_name
        },
    }
    
    ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
    defer cancel()
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Skip if files don't exist
            if _, err := os.Stat(tt.beforePath); os.IsNotExist(err) {
                t.Skipf("before file not found: %s", tt.beforePath)
            }
            if _, err := os.Stat(tt.afterPath); os.IsNotExist(err) {
                t.Skipf("after file not found: %s", tt.afterPath)
            }
            
            diff, err := tt.extractor.ExtractDiff(ctx, tt.beforePath, tt.afterPath)
            if err != nil {
                t.Fatalf("ExtractDiff failed: %v", err)
            }
            
            if diff.Error != "" {
                t.Fatalf("diff contains error: %s", diff.Error)
            }
            
            if diff.Summary.FunctionsAdded < tt.wantAdded {
                t.Errorf("expected at least %d functions added, got %d",
                    tt.wantAdded, diff.Summary.FunctionsAdded)
            }
            
            if diff.Summary.FunctionsRemoved < tt.wantRemoved {
                t.Errorf("expected at least %d functions removed, got %d",
                    tt.wantRemoved, diff.Summary.FunctionsRemoved)
            }
            
            // Verify markdown rendering doesn't panic
            md := RenderMarkdown(diff)
            if md == "" {
                t.Error("markdown render returned empty string")
            }
            
            // Verify JSON rendering
            jsonBytes, err := RenderJSON(diff)
            if err != nil {
                t.Errorf("JSON render failed: %v", err)
            }
            if len(jsonBytes) == 0 {
                t.Error("JSON render returned empty bytes")
            }
        })
    }
}

func TestIntegration_Registry(t *testing.T) {
    scriptsDir := filepath.Join("..", "..")
    
    registry := NewRegistry()
    registry.Register(NewGoExtractor())
    registry.Register(NewTypeScriptExtractor(scriptsDir))
    registry.Register(NewPythonExtractor(scriptsDir))
    
    tests := []struct {
        ext      string
        wantLang string
    }{
        {".go", "go"},
        {".ts", "typescript"},
        {".tsx", "typescript"},
        {".js", "typescript"},
        {".py", "python"},
        {".pyi", "python"},
    }
    
    for _, tt := range tests {
        t.Run(tt.ext, func(t *testing.T) {
            extractor, err := registry.GetExtractor("test" + tt.ext)
            if err != nil {
                t.Fatalf("GetExtractor failed: %v", err)
            }
            if extractor.Language() != tt.wantLang {
                t.Errorf("expected language %s, got %s", tt.wantLang, extractor.Language())
            }
        })
    }
    
    // Test unknown extension
    _, err := registry.GetExtractor("test.unknown")
    if err == nil {
        t.Error("expected error for unknown extension")
    }
}
```

**Verification:**
```bash
cd scripts/codereview && go test -tags=integration ./internal/ast/ -v
```

---

## Execution Order

Execute tasks in this order for minimal context switching:

1. **Setup Phase (Tasks 1-3):** ~10 min
   - Create directories
   - Define types
   - Create extractor interface

2. **Go Extractor (Tasks 4-7):** ~18 min
   - Implement parser
   - Implement diff comparison
   - Create test fixtures
   - Add unit tests

3. **TypeScript Extractor (Tasks 8-10):** ~11 min
   - Create package
   - Implement extractor
   - Create test fixtures

4. **Python Extractor (Tasks 11-12):** ~8 min
   - Implement extractor
   - Create test fixtures

5. **Bridges and Renderer (Tasks 13-15):** ~13 min
   - TypeScript bridge
   - Python bridge
   - Markdown renderer

6. **CLI and Tests (Tasks 16-18):** ~12 min
   - CLI entry point
   - go.mod setup
   - Integration tests

**Total estimated time:** ~72 min (actual may vary)

---

## Verification Commands

After completing all tasks:

```bash
# Build everything
cd scripts/codereview
go mod tidy
go build ./...

# Build TypeScript extractor
cd ts && npm install && npm run build && cd ..

# Run unit tests
go test ./internal/ast/ -v

# Run integration tests (requires Node.js and Python)
go test -tags=integration ./internal/ast/ -v

# Test CLI
./bin/ast-extractor -before testdata/go/before.go -after testdata/go/after.go
./bin/ast-extractor -before testdata/go/before.go -after testdata/go/after.go -output markdown

# Test TypeScript directly
node ts/dist/ast-extractor.js testdata/ts/before.ts testdata/ts/after.ts

# Test Python directly
python3 py/ast_extractor.py testdata/py/before.py testdata/py/after.py
```

---

## Dependencies

- **Go:** 1.21+ (for go/ast, go/parser)
- **Node.js:** 18+ (for TypeScript Compiler API)
- **Python:** 3.10+ (for ast module with match statements)
- **npm packages:** typescript ^5.3.0

---

## Output Schema Reference

All extractors produce JSON conforming to this schema:

```json
{
  "language": "go|typescript|python",
  "file_path": "/path/to/file",
  "functions": [
    {
      "name": "FunctionName",
      "change_type": "added|removed|modified|renamed",
      "before": { /* FuncSig or null */ },
      "after": { /* FuncSig or null */ },
      "body_diff": "description of changes"
    }
  ],
  "types": [
    {
      "name": "TypeName",
      "kind": "struct|interface|class|type",
      "change_type": "added|removed|modified",
      "fields": [
        {
          "name": "fieldName",
          "change_type": "added|removed|modified",
          "old_type": "OldType",
          "new_type": "NewType"
        }
      ]
    }
  ],
  "imports": [
    {
      "path": "module/path",
      "alias": "optionalAlias",
      "change_type": "added|removed"
    }
  ],
  "summary": {
    "functions_added": 0,
    "functions_removed": 0,
    "functions_modified": 0,
    "types_added": 0,
    "types_removed": 0,
    "types_modified": 0,
    "imports_added": 0,
    "imports_removed": 0
  },
  "error": "optional error message"
}
```
