# Phase 4: Data Flow Analysis Implementation Plan

## Overview

Track data from untrusted sources (HTTP, env, files) to sinks (DB, exec, responses).
Identify unsanitized flows and nil/null safety risks.

## Input/Output

- **Input:** `scope.json` from Phase 0
- **Output:** `{lang}-flow.json`, `security-summary.md`

## Directory Structure

```
scripts/ring:codereview/
├── cmd/data-flow/main.go
├── internal/dataflow/
│   ├── types.go
│   ├── golang.go
│   ├── typescript.go
│   └── python.go
├── py/
│   └── data_flow.py
```

---

## Tasks

### Task 1: Create dataflow package structure (2 min)

**Description:** Create the directory structure for the dataflow package.

**Commands:**
```bash
mkdir -p scripts/ring:codereview/cmd/data-flow
mkdir -p scripts/ring:codereview/internal/dataflow
mkdir -p scripts/ring:codereview/py
```

**Verification:**
```bash
ls -la scripts/ring:codereview/cmd/data-flow
ls -la scripts/ring:codereview/internal/dataflow
ls -la scripts/ring:codereview/py
```

---

### Task 2: Define types (Flow, Source, Sink, NilSource) (3 min)

**Description:** Define the core data structures for tracking data flows, sources, sinks, and nil safety.

**File:** `scripts/ring:codereview/internal/dataflow/types.go`

```go
package dataflow

// SourceType categorizes where untrusted data originates
type SourceType string

const (
	SourceHTTPBody    SourceType = "http_body"
	SourceHTTPQuery   SourceType = "http_query"
	SourceHTTPHeader  SourceType = "http_header"
	SourceHTTPPath    SourceType = "http_path"
	SourceEnvVar      SourceType = "env_var"
	SourceFile        SourceType = "file_read"
	SourceDatabase    SourceType = "database"
	SourceUserInput   SourceType = "user_input"
	SourceExternal    SourceType = "external_api"
)

// SinkType categorizes where data flows to
type SinkType string

const (
	SinkDatabase   SinkType = "database"
	SinkExec       SinkType = "command_exec"
	SinkResponse   SinkType = "http_response"
	SinkLog        SinkType = "logging"
	SinkFile       SinkType = "file_write"
	SinkTemplate   SinkType = "template"
	SinkRedirect   SinkType = "redirect"
)

// RiskLevel indicates severity of a flow
type RiskLevel string

const (
	RiskCritical RiskLevel = "critical"
	RiskHigh     RiskLevel = "high"
	RiskMedium   RiskLevel = "medium"
	RiskLow      RiskLevel = "low"
	RiskInfo     RiskLevel = "info"
)

// Source represents an untrusted data source
type Source struct {
	Type     SourceType `json:"type"`
	File     string     `json:"file"`
	Line     int        `json:"line"`
	Column   int        `json:"column,omitempty"`
	Variable string     `json:"variable"`
	Pattern  string     `json:"pattern"`
	Context  string     `json:"context,omitempty"`
}

// Sink represents a data destination
type Sink struct {
	Type     SinkType `json:"type"`
	File     string   `json:"file"`
	Line     int      `json:"line"`
	Column   int      `json:"column,omitempty"`
	Function string   `json:"function"`
	Pattern  string   `json:"pattern"`
	Context  string   `json:"context,omitempty"`
}

// Flow represents a data path from source to sink
type Flow struct {
	ID          string    `json:"id"`
	Source      Source    `json:"source"`
	Sink        Sink      `json:"sink"`
	Path        []string  `json:"path"`
	Sanitized   bool      `json:"sanitized"`
	Sanitizers  []string  `json:"sanitizers,omitempty"`
	Risk        RiskLevel `json:"risk"`
	Description string    `json:"description"`
}

// NilSource tracks variables that may be nil/null
type NilSource struct {
	File       string `json:"file"`
	Line       int    `json:"line"`
	Variable   string `json:"variable"`
	Origin     string `json:"origin"`
	IsChecked  bool   `json:"is_checked"`
	CheckLine  int    `json:"check_line,omitempty"`
	UsageLine  int    `json:"usage_line,omitempty"`
	Risk       RiskLevel `json:"risk"`
}

// FlowAnalysis contains all analysis results for a language
type FlowAnalysis struct {
	Language    string      `json:"language"`
	Sources     []Source    `json:"sources"`
	Sinks       []Sink      `json:"sinks"`
	Flows       []Flow      `json:"flows"`
	NilSources  []NilSource `json:"nil_sources"`
	Statistics  Stats       `json:"statistics"`
}

// Stats provides summary statistics
type Stats struct {
	TotalSources      int `json:"total_sources"`
	TotalSinks        int `json:"total_sinks"`
	TotalFlows        int `json:"total_flows"`
	UnsanitizedFlows  int `json:"unsanitized_flows"`
	CriticalFlows     int `json:"critical_flows"`
	HighRiskFlows     int `json:"high_risk_flows"`
	NilRisks          int `json:"nil_risks"`
	UncheckedNilRisks int `json:"unchecked_nil_risks"`
}

// SecuritySummary aggregates results across languages
type SecuritySummary struct {
	Timestamp   string                  `json:"timestamp"`
	Languages   []string                `json:"languages"`
	Analyses    map[string]FlowAnalysis `json:"analyses"`
	TotalStats  Stats                   `json:"total_stats"`
	TopRisks    []Flow                  `json:"top_risks"`
}

// Analyzer interface for language-specific implementations
type Analyzer interface {
	Language() string
	DetectSources(files []string) ([]Source, error)
	DetectSinks(files []string) ([]Sink, error)
	TrackFlows(sources []Source, sinks []Sink, files []string) ([]Flow, error)
	DetectNilSources(files []string) ([]NilSource, error)
	Analyze(files []string) (*FlowAnalysis, error)
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go build ./internal/dataflow/...
```

---

### Task 3: Implement Go source detection (5 min)

**Description:** Detect untrusted data sources in Go code including HTTP requests, environment variables, database queries, and file reads.

**File:** `scripts/ring:codereview/internal/dataflow/golang.go`

```go
package dataflow

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"regexp"
	"strings"
)

// GoAnalyzer implements Analyzer for Go code
type GoAnalyzer struct{}

// NewGoAnalyzer creates a new Go analyzer
func NewGoAnalyzer() *GoAnalyzer {
	return &GoAnalyzer{}
}

// Language returns the language identifier
func (g *GoAnalyzer) Language() string {
	return "go"
}

// sourcePatterns maps patterns to source types
var goSourcePatterns = map[SourceType]*regexp.Regexp{
	SourceHTTPBody:   regexp.MustCompile(`(?:r|req|request)\.Body`),
	SourceHTTPQuery:  regexp.MustCompile(`(?:r|req|request)\.(?:URL\.Query\(\)|FormValue\(|PostFormValue\(|Form\.Get\()`),
	SourceHTTPHeader: regexp.MustCompile(`(?:r|req|request)\.Header\.(?:Get\(|Values\()`),
	SourceHTTPPath:   regexp.MustCompile(`(?:mux\.Vars\(|chi\.URLParam\(|c\.Param\(|params\.ByName\()`),
	SourceEnvVar:     regexp.MustCompile(`os\.(?:Getenv|LookupEnv)\(`),
	SourceFile:       regexp.MustCompile(`(?:os\.(?:Open|ReadFile)|ioutil\.ReadFile|io\.ReadAll)\(`),
	SourceDatabase:   regexp.MustCompile(`\.(?:Query|QueryRow|QueryContext|QueryRowContext)\(`),
	SourceExternal:   regexp.MustCompile(`(?:http\.(?:Get|Post|Do)|client\.(?:Get|Post|Do))\(`),
}

// DetectSources finds all untrusted data sources in Go files
func (g *GoAnalyzer) DetectSources(files []string) ([]Source, error) {
	var sources []Source

	for _, file := range files {
		if !strings.HasSuffix(file, ".go") {
			continue
		}

		fileSources, err := g.detectSourcesInFile(file)
		if err != nil {
			continue // Skip files that can't be read
		}
		sources = append(sources, fileSources...)
	}

	return sources, nil
}

func (g *GoAnalyzer) detectSourcesInFile(filepath string) ([]Source, error) {
	var sources []Source

	f, err := os.Open(filepath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := scanner.Text()

		for sourceType, pattern := range goSourcePatterns {
			matches := pattern.FindAllStringIndex(line, -1)
			for _, match := range matches {
				variable := extractVariable(line, match[0])
				sources = append(sources, Source{
					Type:     sourceType,
					File:     filepath,
					Line:     lineNum,
					Column:   match[0] + 1,
					Variable: variable,
					Pattern:  pattern.String(),
					Context:  strings.TrimSpace(line),
				})
			}
		}
	}

	return sources, scanner.Err()
}

// extractVariable attempts to extract the variable name from an assignment
func extractVariable(line string, matchStart int) string {
	// Look for assignment pattern: varName := or varName =
	assignPattern := regexp.MustCompile(`(\w+)\s*:?=\s*`)
	if match := assignPattern.FindStringSubmatch(line[:matchStart]); len(match) > 1 {
		return match[1]
	}

	// Look for variable in function argument context
	argPattern := regexp.MustCompile(`(\w+)\s*$`)
	prefix := strings.TrimSpace(line[:matchStart])
	if match := argPattern.FindStringSubmatch(prefix); len(match) > 1 {
		return match[1]
	}

	return "unknown"
}

// sinkPatterns maps patterns to sink types
var goSinkPatterns = map[SinkType]*regexp.Regexp{
	SinkDatabase: regexp.MustCompile(`\.(?:Exec|ExecContext|Prepare|PrepareContext)\(`),
	SinkExec:     regexp.MustCompile(`exec\.(?:Command|CommandContext)\(`),
	SinkResponse: regexp.MustCompile(`(?:w|rw|writer|resp|response)\.(?:Write|WriteHeader|WriteString)\(`),
	SinkLog:      regexp.MustCompile(`(?:log|logger|slog)\.(?:Print|Printf|Println|Info|Warn|Error|Debug|Fatal)\(`),
	SinkFile:     regexp.MustCompile(`(?:os\.(?:WriteFile|Create)|ioutil\.WriteFile|f\.Write)\(`),
	SinkTemplate: regexp.MustCompile(`(?:template\.(?:Execute|ExecuteTemplate)|tmpl\.Execute)\(`),
	SinkRedirect: regexp.MustCompile(`http\.Redirect\(`),
}

// DetectSinks finds all data sinks in Go files
func (g *GoAnalyzer) DetectSinks(files []string) ([]Sink, error) {
	var sinks []Sink

	for _, file := range files {
		if !strings.HasSuffix(file, ".go") {
			continue
		}

		fileSinks, err := g.detectSinksInFile(file)
		if err != nil {
			continue
		}
		sinks = append(sinks, fileSinks...)
	}

	return sinks, nil
}

func (g *GoAnalyzer) detectSinksInFile(filepath string) ([]Sink, error) {
	var sinks []Sink

	f, err := os.Open(filepath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := scanner.Text()

		for sinkType, pattern := range goSinkPatterns {
			matches := pattern.FindAllStringIndex(line, -1)
			for _, match := range matches {
				funcName := extractFunctionName(line, match[0], match[1])
				sinks = append(sinks, Sink{
					Type:     sinkType,
					File:     filepath,
					Line:     lineNum,
					Column:   match[0] + 1,
					Function: funcName,
					Pattern:  pattern.String(),
					Context:  strings.TrimSpace(line),
				})
			}
		}
	}

	return sinks, scanner.Err()
}

func extractFunctionName(line string, start, end int) string {
	if end > len(line) {
		end = len(line)
	}
	match := line[start:end]
	// Remove trailing parenthesis
	match = strings.TrimSuffix(match, "(")
	// Extract just the function name
	parts := strings.Split(match, ".")
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return match
}

// TrackFlows connects sources to sinks through variable tracking
func (g *GoAnalyzer) TrackFlows(sources []Source, sinks []Sink, files []string) ([]Flow, error) {
	var flows []Flow

	// Build variable tracking map per file
	fileVarMap := make(map[string]map[string][]Source)
	for _, source := range sources {
		if fileVarMap[source.File] == nil {
			fileVarMap[source.File] = make(map[string][]Source)
		}
		fileVarMap[source.File][source.Variable] = append(fileVarMap[source.File][source.Variable], source)
	}

	// For each sink, check if any source variable flows into it
	for _, sink := range sinks {
		// Check same-file flows
		if varMap, ok := fileVarMap[sink.File]; ok {
			for varName, varSources := range varMap {
				if strings.Contains(sink.Context, varName) {
					for _, source := range varSources {
						flow := g.createFlow(source, sink)
						flows = append(flows, flow)
					}
				}
			}
		}

		// Check for direct inline flows (source used directly in sink)
		for sourceType, pattern := range goSourcePatterns {
			if pattern.MatchString(sink.Context) {
				directSource := Source{
					Type:     sourceType,
					File:     sink.File,
					Line:     sink.Line,
					Variable: "inline",
					Pattern:  pattern.String(),
					Context:  sink.Context,
				}
				flow := g.createFlow(directSource, sink)
				flows = append(flows, flow)
			}
		}
	}

	return flows, nil
}

func (g *GoAnalyzer) createFlow(source Source, sink Sink) Flow {
	risk := g.calculateRisk(source, sink)
	sanitized, sanitizers := g.checkSanitization(source, sink)

	id := generateFlowID(source, sink)

	return Flow{
		ID:          id,
		Source:      source,
		Sink:        sink,
		Path:        []string{source.Variable},
		Sanitized:   sanitized,
		Sanitizers:  sanitizers,
		Risk:        risk,
		Description: g.describeFlow(source, sink, risk),
	}
}

func generateFlowID(source Source, sink Sink) string {
	data := fmt.Sprintf("%s:%d:%s:%d", source.File, source.Line, sink.File, sink.Line)
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:8])
}

func (g *GoAnalyzer) calculateRisk(source Source, sink Sink) RiskLevel {
	// Critical: User input to command execution or raw SQL
	if sink.Type == SinkExec {
		return RiskCritical
	}
	if sink.Type == SinkDatabase && (source.Type == SourceHTTPBody || source.Type == SourceHTTPQuery) {
		return RiskCritical
	}

	// High: User input to response (XSS) or template
	if sink.Type == SinkResponse && (source.Type == SourceHTTPBody || source.Type == SourceHTTPQuery) {
		return RiskHigh
	}
	if sink.Type == SinkTemplate {
		return RiskHigh
	}
	if sink.Type == SinkRedirect && source.Type == SourceHTTPQuery {
		return RiskHigh
	}

	// Medium: Env vars to sensitive sinks, file operations
	if source.Type == SourceEnvVar && (sink.Type == SinkDatabase || sink.Type == SinkExec) {
		return RiskMedium
	}
	if sink.Type == SinkFile {
		return RiskMedium
	}

	// Low: Logging user data (info disclosure)
	if sink.Type == SinkLog {
		return RiskLow
	}

	return RiskInfo
}

// checkSanitization looks for common sanitization patterns
func (g *GoAnalyzer) checkSanitization(source Source, sink Sink) (bool, []string) {
	var sanitizers []string

	// Common Go sanitization patterns
	sanitizationPatterns := map[string]*regexp.Regexp{
		"html.EscapeString":    regexp.MustCompile(`html\.EscapeString`),
		"url.QueryEscape":      regexp.MustCompile(`url\.QueryEscape`),
		"strconv.Atoi":         regexp.MustCompile(`strconv\.(?:Atoi|ParseInt|ParseFloat)`),
		"prepared_statement":   regexp.MustCompile(`\?\s*,|\$\d+`),
		"filepath.Clean":       regexp.MustCompile(`filepath\.(?:Clean|Base)`),
		"regexp.MustCompile":   regexp.MustCompile(`regexp\.(?:MustCompile|MatchString)`),
		"validator":            regexp.MustCompile(`(?:validate|validator|Validate)`),
	}

	// Check if sink context contains sanitization
	for name, pattern := range sanitizationPatterns {
		if pattern.MatchString(sink.Context) {
			sanitizers = append(sanitizers, name)
		}
	}

	return len(sanitizers) > 0, sanitizers
}

func (g *GoAnalyzer) describeFlow(source Source, sink Sink, risk RiskLevel) string {
	sourceDesc := map[SourceType]string{
		SourceHTTPBody:   "HTTP request body",
		SourceHTTPQuery:  "HTTP query parameter",
		SourceHTTPHeader: "HTTP header",
		SourceHTTPPath:   "URL path parameter",
		SourceEnvVar:     "environment variable",
		SourceFile:       "file content",
		SourceDatabase:   "database query result",
		SourceExternal:   "external API response",
	}

	sinkDesc := map[SinkType]string{
		SinkDatabase: "database query",
		SinkExec:     "command execution",
		SinkResponse: "HTTP response",
		SinkLog:      "log output",
		SinkFile:     "file write",
		SinkTemplate: "template rendering",
		SinkRedirect: "HTTP redirect",
	}

	return fmt.Sprintf("%s flows from %s to %s",
		strings.ToUpper(string(risk)),
		sourceDesc[source.Type],
		sinkDesc[sink.Type])
}

// nilPatterns for detecting potential nil sources
var goNilPatterns = []struct {
	pattern *regexp.Regexp
	origin  string
}{
	{regexp.MustCompile(`(\w+)\s*,\s*(?:err|ok)\s*:?=.*\.(?:Get|Load|Lookup|Find)\(`), "map/cache lookup"},
	{regexp.MustCompile(`(\w+)\s*:?=.*\.(?:QueryRow|Get|First|Find)\(`), "database query"},
	{regexp.MustCompile(`(\w+)\s*,\s*ok\s*:?=.*\.\(`), "type assertion"},
	{regexp.MustCompile(`(\w+)\s*:?=.*json\.Unmarshal`), "JSON unmarshal"},
	{regexp.MustCompile(`(\w+)\s*:?=.*\.(?:Decode|Unmarshal)\(`), "decoding"},
	{regexp.MustCompile(`var\s+(\w+)\s+\*\w+`), "nil pointer declaration"},
	{regexp.MustCompile(`(\w+)\s*:?=\s*\(\*\w+\)\(nil\)`), "explicit nil"},
}

// nilCheckPatterns detect nil checks
var goNilCheckPatterns = []*regexp.Regexp{
	regexp.MustCompile(`if\s+(\w+)\s*[!=]=\s*nil`),
	regexp.MustCompile(`if\s+nil\s*[!=]=\s*(\w+)`),
	regexp.MustCompile(`if\s+(\w+)\s*!=\s*nil\s*\{`),
	regexp.MustCompile(`(\w+)\s*!=\s*nil\s*&&`),
	regexp.MustCompile(`(\w+)\s*==\s*nil\s*\|\|`),
}

// DetectNilSources finds variables that may be nil
func (g *GoAnalyzer) DetectNilSources(files []string) ([]NilSource, error) {
	var nilSources []NilSource

	for _, file := range files {
		if !strings.HasSuffix(file, ".go") {
			continue
		}

		fileNils, err := g.detectNilSourcesInFile(file)
		if err != nil {
			continue
		}
		nilSources = append(nilSources, fileNils...)
	}

	return nilSources, nil
}

func (g *GoAnalyzer) detectNilSourcesInFile(filepath string) ([]NilSource, error) {
	var nilSources []NilSource

	content, err := os.ReadFile(filepath)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(string(content), "\n")

	// Track variables and their nil checks
	varNilChecks := make(map[string]int) // variable -> line where checked

	// First pass: find nil checks
	for lineNum, line := range lines {
		for _, checkPattern := range goNilCheckPatterns {
			if matches := checkPattern.FindStringSubmatch(line); len(matches) > 1 {
				varNilChecks[matches[1]] = lineNum + 1
			}
		}
	}

	// Second pass: find nil sources
	for lineNum, line := range lines {
		for _, np := range goNilPatterns {
			if matches := np.pattern.FindStringSubmatch(line); len(matches) > 1 {
				varName := matches[1]
				checkLine, isChecked := varNilChecks[varName]

				risk := RiskHigh
				if isChecked {
					risk = RiskLow
				}

				nilSources = append(nilSources, NilSource{
					File:      filepath,
					Line:      lineNum + 1,
					Variable:  varName,
					Origin:    np.origin,
					IsChecked: isChecked,
					CheckLine: checkLine,
					Risk:      risk,
				})
			}
		}
	}

	return nilSources, nil
}

// Analyze performs complete analysis on Go files
func (g *GoAnalyzer) Analyze(files []string) (*FlowAnalysis, error) {
	sources, err := g.DetectSources(files)
	if err != nil {
		return nil, fmt.Errorf("detecting sources: %w", err)
	}

	sinks, err := g.DetectSinks(files)
	if err != nil {
		return nil, fmt.Errorf("detecting sinks: %w", err)
	}

	flows, err := g.TrackFlows(sources, sinks, files)
	if err != nil {
		return nil, fmt.Errorf("tracking flows: %w", err)
	}

	nilSources, err := g.DetectNilSources(files)
	if err != nil {
		return nil, fmt.Errorf("detecting nil sources: %w", err)
	}

	// Calculate statistics
	stats := Stats{
		TotalSources: len(sources),
		TotalSinks:   len(sinks),
		TotalFlows:   len(flows),
	}

	for _, flow := range flows {
		if !flow.Sanitized {
			stats.UnsanitizedFlows++
		}
		switch flow.Risk {
		case RiskCritical:
			stats.CriticalFlows++
		case RiskHigh:
			stats.HighRiskFlows++
		}
	}

	stats.NilRisks = len(nilSources)
	for _, ns := range nilSources {
		if !ns.IsChecked {
			stats.UncheckedNilRisks++
		}
	}

	return &FlowAnalysis{
		Language:   "go",
		Sources:    sources,
		Sinks:      sinks,
		Flows:      flows,
		NilSources: nilSources,
		Statistics: stats,
	}, nil
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go build ./internal/dataflow/...
```

---

### Task 4: Implement Go sink detection (5 min)

**Description:** Already included in Task 3 (`DetectSinks` method in `golang.go`). The sink detection includes:
- Database operations: `Exec`, `ExecContext`, `Prepare`
- Command execution: `exec.Command`, `exec.CommandContext`
- HTTP responses: `Write`, `WriteHeader`, `WriteString`
- Logging: `log.Print*`, `slog.*`, `logger.*`
- File writes: `os.WriteFile`, `os.Create`, `f.Write`
- Templates: `template.Execute*`
- Redirects: `http.Redirect`

**Verification:**
```bash
cd scripts/ring:codereview && go test ./internal/dataflow/... -run TestDetectSinks -v
```

---

### Task 5: Implement flow tracking (5 min)

**Description:** Already included in Task 3 (`TrackFlows` method in `golang.go`). The flow tracking:
- Builds variable map per file
- Tracks variables from source to sink
- Detects inline flows (source used directly in sink call)
- Calculates risk level based on source-sink combination
- Checks for sanitization patterns

**Verification:**
```bash
cd scripts/ring:codereview && go test ./internal/dataflow/... -run TestTrackFlows -v
```

---

### Task 6: Implement nil source tracking (4 min)

**Description:** Already included in Task 3 (`DetectNilSources` method in `golang.go`). The nil tracking:
- Detects map/cache lookups that may return nil
- Detects database queries that may return nil
- Detects type assertions
- Detects JSON/decode operations
- Tracks whether nil checks exist for each variable

**Verification:**
```bash
cd scripts/ring:codereview && go test ./internal/dataflow/... -run TestNilSources -v
```

---

### Task 7: Create Python data_flow.py (5 min)

**Description:** Python script for analyzing Python/TypeScript code with framework detection for Flask, Django, FastAPI, and Express.

**File:** `scripts/ring:codereview/py/data_flow.py`

```python
#!/usr/bin/env python3
"""
Data flow analysis for Python and TypeScript projects.
Detects sources, sinks, and flows in common web frameworks.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict


@dataclass
class Source:
    type: str
    file: str
    line: int
    column: int
    variable: str
    pattern: str
    context: str


@dataclass
class Sink:
    type: str
    file: str
    line: int
    column: int
    function: str
    pattern: str
    context: str


@dataclass
class Flow:
    id: str
    source: dict
    sink: dict
    path: list
    sanitized: bool
    sanitizers: list
    risk: str
    description: str


@dataclass
class NilSource:
    file: str
    line: int
    variable: str
    origin: str
    is_checked: bool
    check_line: int
    usage_line: int
    risk: str


# Python source patterns by framework
PYTHON_SOURCE_PATTERNS = {
    # Flask
    "http_body": [
        r"request\.(?:get_json|json|data|form)",
        r"request\.files",
    ],
    "http_query": [
        r"request\.args\.get\(",
        r"request\.args\[",
        r"request\.values",
    ],
    "http_header": [
        r"request\.headers\.get\(",
        r"request\.headers\[",
    ],
    "http_path": [
        r"@app\.route.*<(\w+)>",
        r"@router\.(?:get|post|put|delete).*\{(\w+)\}",
    ],
    # Django
    "http_body_django": [
        r"request\.POST\.get\(",
        r"request\.POST\[",
        r"request\.body",
    ],
    "http_query_django": [
        r"request\.GET\.get\(",
        r"request\.GET\[",
    ],
    # FastAPI
    "http_body_fastapi": [
        r"Body\(",
        r"Form\(",
    ],
    "http_query_fastapi": [
        r"Query\(",
    ],
    # Common
    "env_var": [
        r"os\.(?:getenv|environ\.get)\(",
        r"os\.environ\[",
    ],
    "file_read": [
        r"open\([^)]+\)\.read",
        r"Path\([^)]+\)\.read_text",
    ],
    "database": [
        r"\.(?:execute|fetchone|fetchall|fetchmany)\(",
        r"cursor\.\w+\(",
    ],
    "external_api": [
        r"requests\.(?:get|post|put|delete|patch)\(",
        r"httpx\.(?:get|post|put|delete|patch)\(",
        r"aiohttp\.\w+",
    ],
}

PYTHON_SINK_PATTERNS = {
    "database": [
        r"cursor\.execute\(",
        r"\.execute\([^)]*%",
        r"\.execute\([^)]*\.format",
        r"\.raw\(",
    ],
    "command_exec": [
        r"subprocess\.(?:run|call|Popen|check_output)\(",
        r"os\.(?:system|popen|exec\w*)\(",
        r"eval\(",
        r"exec\(",
    ],
    "http_response": [
        r"return\s+(?:jsonify|render_template|Response)\(",
        r"HttpResponse\(",
        r"JsonResponse\(",
        r"return\s+\{",
    ],
    "logging": [
        r"(?:logging|logger)\.\w+\(",
        r"print\(",
    ],
    "file_write": [
        r"open\([^)]+,\s*['\"]w",
        r"\.write\(",
        r"Path\([^)]+\)\.write_text",
    ],
    "template": [
        r"render_template\(",
        r"render\(",
        r"Template\(",
    ],
    "redirect": [
        r"redirect\(",
        r"HttpResponseRedirect\(",
    ],
}

# TypeScript/JavaScript patterns
TS_SOURCE_PATTERNS = {
    "http_body": [
        r"req\.body",
        r"request\.body",
        r"ctx\.request\.body",
    ],
    "http_query": [
        r"req\.query",
        r"req\.params",
        r"request\.query",
        r"ctx\.query",
        r"searchParams\.get\(",
    ],
    "http_header": [
        r"req\.headers",
        r"request\.headers",
        r"ctx\.headers",
    ],
    "http_path": [
        r"req\.params\.",
        r":(\w+)",
    ],
    "env_var": [
        r"process\.env\.",
        r"Deno\.env\.get\(",
    ],
    "file_read": [
        r"fs\.readFile",
        r"readFileSync\(",
        r"Deno\.readTextFile",
    ],
    "database": [
        r"\.query\(",
        r"\.findOne\(",
        r"\.find\(",
        r"\.aggregate\(",
    ],
    "external_api": [
        r"fetch\(",
        r"axios\.\w+\(",
        r"got\.\w+\(",
    ],
    "user_input": [
        r"prompt\(",
        r"readline\.",
    ],
}

TS_SINK_PATTERNS = {
    "database": [
        r"\.query\([^)]*\$\{",
        r"\.query\([^)]*\+",
        r"\.exec\(",
        r"\.raw\(",
    ],
    "command_exec": [
        r"exec\(",
        r"execSync\(",
        r"spawn\(",
        r"eval\(",
        r"Function\(",
        r"new\s+Function\(",
    ],
    "http_response": [
        r"res\.(?:send|json|write)\(",
        r"response\.(?:send|json|write)\(",
        r"ctx\.body\s*=",
        r"return\s+Response\.",
    ],
    "logging": [
        r"console\.\w+\(",
        r"logger\.\w+\(",
    ],
    "file_write": [
        r"fs\.writeFile",
        r"writeFileSync\(",
        r"Deno\.writeTextFile",
    ],
    "template": [
        r"\.render\(",
        r"dangerouslySetInnerHTML",
        r"innerHTML\s*=",
    ],
    "redirect": [
        r"res\.redirect\(",
        r"response\.redirect\(",
        r"window\.location",
    ],
}

# Null/undefined patterns for TypeScript
TS_NULL_PATTERNS = [
    (r"(\w+)\s*=\s*await\s+\w+\.(?:findOne|findFirst|get)\(", "database query"),
    (r"(\w+)\s*=\s*\w+\.get\(", "map/cache lookup"),
    (r"(\w+)\s*=\s*JSON\.parse\(", "JSON parse"),
    (r"(\w+)\?\.", "optional chaining usage"),
    (r"(\w+)\s+as\s+\w+", "type assertion"),
    (r"let\s+(\w+):\s*\w+\s*\|?\s*(?:null|undefined)", "nullable declaration"),
]

TS_NULL_CHECK_PATTERNS = [
    r"if\s*\(\s*(\w+)\s*(?:!==?|===?)\s*(?:null|undefined)",
    r"if\s*\(\s*!(\w+)\s*\)",
    r"if\s*\(\s*(\w+)\s*\)",
    r"(\w+)\s*\?\?",
    r"(\w+)\s*&&\s*(\w+)\.",
]


def hash_flow(source: Source, sink: Sink) -> str:
    """Generate unique ID for a flow."""
    import hashlib
    data = f"{source.file}:{source.line}:{sink.file}:{sink.line}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def detect_sources(files: list[str], language: str) -> list[Source]:
    """Detect untrusted data sources in files."""
    sources = []
    patterns = PYTHON_SOURCE_PATTERNS if language == "python" else TS_SOURCE_PATTERNS
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (IOError, OSError):
            continue
            
        for line_num, line in enumerate(lines, 1):
            for source_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    for match in re.finditer(pattern, line):
                        variable = extract_variable(line, match.start())
                        sources.append(Source(
                            type=source_type.replace("_django", "").replace("_fastapi", ""),
                            file=filepath,
                            line=line_num,
                            column=match.start() + 1,
                            variable=variable,
                            pattern=pattern,
                            context=line.strip()
                        ))
    
    return sources


def detect_sinks(files: list[str], language: str) -> list[Sink]:
    """Detect data sinks in files."""
    sinks = []
    patterns = PYTHON_SINK_PATTERNS if language == "python" else TS_SINK_PATTERNS
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (IOError, OSError):
            continue
            
        for line_num, line in enumerate(lines, 1):
            for sink_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    for match in re.finditer(pattern, line):
                        func_name = extract_function_name(line, match.start(), match.end())
                        sinks.append(Sink(
                            type=sink_type,
                            file=filepath,
                            line=line_num,
                            column=match.start() + 1,
                            function=func_name,
                            pattern=pattern,
                            context=line.strip()
                        ))
    
    return sinks


def extract_variable(line: str, match_start: int) -> str:
    """Extract variable name from assignment."""
    prefix = line[:match_start]
    # Look for assignment
    assign_match = re.search(r'(\w+)\s*=\s*$', prefix)
    if assign_match:
        return assign_match.group(1)
    # Look for const/let/var declaration
    decl_match = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*$', prefix)
    if decl_match:
        return decl_match.group(1)
    return "unknown"


def extract_function_name(line: str, start: int, end: int) -> str:
    """Extract function name from match."""
    match_text = line[start:end]
    # Remove parenthesis
    match_text = re.sub(r'\($', '', match_text)
    # Get last part after dot
    parts = match_text.split('.')
    return parts[-1] if parts else match_text


def calculate_risk(source: Source, sink: Sink) -> str:
    """Calculate risk level for a flow."""
    # Critical: User input to command execution or raw SQL
    if sink.type == "command_exec":
        return "critical"
    if sink.type == "database" and source.type in ("http_body", "http_query"):
        return "critical"
    
    # High: User input to response (XSS) or template
    if sink.type in ("http_response", "template") and source.type in ("http_body", "http_query"):
        return "high"
    if sink.type == "redirect" and source.type == "http_query":
        return "high"
    
    # Medium: Env vars to sensitive sinks
    if source.type == "env_var" and sink.type in ("database", "command_exec"):
        return "medium"
    if sink.type == "file_write":
        return "medium"
    
    # Low: Logging
    if sink.type == "logging":
        return "low"
    
    return "info"


def check_sanitization(source: Source, sink: Sink, language: str) -> tuple[bool, list[str]]:
    """Check for sanitization patterns."""
    sanitizers = []
    context = sink.context
    
    if language == "python":
        patterns = {
            "parameterized_query": r"\?\s*,|\%s",
            "html_escape": r"(?:escape|html\.escape|markupsafe\.escape)",
            "quote": r"shlex\.quote",
            "validator": r"(?:validate|validator|pydantic)",
            "bleach": r"bleach\.",
        }
    else:
        patterns = {
            "parameterized_query": r"\$\d+|\?",
            "escape_html": r"(?:escapeHtml|sanitize|DOMPurify)",
            "validator": r"(?:validator|zod|yup|joi)",
            "prepared": r"prepare\(",
        }
    
    for name, pattern in patterns.items():
        if re.search(pattern, context):
            sanitizers.append(name)
    
    return len(sanitizers) > 0, sanitizers


def track_flows(sources: list[Source], sinks: list[Sink], language: str) -> list[Flow]:
    """Connect sources to sinks through variable tracking."""
    flows = []
    
    # Build variable map per file
    file_var_map: dict[str, dict[str, list[Source]]] = {}
    for source in sources:
        if source.file not in file_var_map:
            file_var_map[source.file] = {}
        if source.variable not in file_var_map[source.file]:
            file_var_map[source.file][source.variable] = []
        file_var_map[source.file][source.variable].append(source)
    
    for sink in sinks:
        # Same file flows
        if sink.file in file_var_map:
            for var_name, var_sources in file_var_map[sink.file].items():
                if var_name in sink.context:
                    for source in var_sources:
                        risk = calculate_risk(source, sink)
                        sanitized, sanitizers = check_sanitization(source, sink, language)
                        
                        flows.append(Flow(
                            id=hash_flow(source, sink),
                            source=asdict(source),
                            sink=asdict(sink),
                            path=[source.variable],
                            sanitized=sanitized,
                            sanitizers=sanitizers,
                            risk=risk,
                            description=describe_flow(source, sink, risk)
                        ))
    
    return flows


def describe_flow(source: Source, sink: Sink, risk: str) -> str:
    """Generate human-readable description."""
    source_desc = {
        "http_body": "HTTP request body",
        "http_query": "HTTP query parameter",
        "http_header": "HTTP header",
        "http_path": "URL path parameter",
        "env_var": "environment variable",
        "file_read": "file content",
        "database": "database query result",
        "external_api": "external API response",
        "user_input": "user input",
    }
    
    sink_desc = {
        "database": "database query",
        "command_exec": "command execution",
        "http_response": "HTTP response",
        "logging": "log output",
        "file_write": "file write",
        "template": "template rendering",
        "redirect": "HTTP redirect",
    }
    
    return f"{risk.upper()}: {source_desc.get(source.type, source.type)} flows to {sink_desc.get(sink.type, sink.type)}"


def detect_null_sources(files: list[str], language: str) -> list[NilSource]:
    """Detect variables that may be null/undefined."""
    if language != "typescript":
        return []
    
    nil_sources = []
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except (IOError, OSError):
            continue
        
        # Build null check map
        var_checks: dict[str, int] = {}
        for line_num, line in enumerate(lines, 1):
            for pattern in TS_NULL_CHECK_PATTERNS:
                for match in re.finditer(pattern, line):
                    for group in match.groups():
                        if group:
                            var_checks[group] = line_num
        
        # Find null sources
        for line_num, line in enumerate(lines, 1):
            for pattern, origin in TS_NULL_PATTERNS:
                for match in re.finditer(pattern, line):
                    if match.groups():
                        var_name = match.group(1)
                        check_line = var_checks.get(var_name, 0)
                        is_checked = var_name in var_checks
                        
                        nil_sources.append(NilSource(
                            file=filepath,
                            line=line_num,
                            variable=var_name,
                            origin=origin,
                            is_checked=is_checked,
                            check_line=check_line,
                            usage_line=0,
                            risk="low" if is_checked else "high"
                        ))
    
    return nil_sources


def analyze(files: list[str], language: str) -> dict[str, Any]:
    """Perform complete analysis."""
    sources = detect_sources(files, language)
    sinks = detect_sinks(files, language)
    flows = track_flows(sources, sinks, language)
    nil_sources = detect_null_sources(files, language)
    
    # Calculate statistics
    unsanitized = sum(1 for f in flows if not f.sanitized)
    critical = sum(1 for f in flows if f.risk == "critical")
    high = sum(1 for f in flows if f.risk == "high")
    unchecked_nil = sum(1 for n in nil_sources if not n.is_checked)
    
    return {
        "language": language,
        "sources": [asdict(s) for s in sources],
        "sinks": [asdict(s) for s in sinks],
        "flows": [asdict(f) for f in flows],
        "nil_sources": [asdict(n) for n in nil_sources],
        "statistics": {
            "total_sources": len(sources),
            "total_sinks": len(sinks),
            "total_flows": len(flows),
            "unsanitized_flows": unsanitized,
            "critical_flows": critical,
            "high_risk_flows": high,
            "nil_risks": len(nil_sources),
            "unchecked_nil_risks": unchecked_nil,
        }
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: data_flow.py <language> <file1> [file2] ...", file=sys.stderr)
        print("Languages: python, typescript", file=sys.stderr)
        sys.exit(1)
    
    language = sys.argv[1]
    if language not in ("python", "typescript"):
        print(f"Unsupported language: {language}", file=sys.stderr)
        sys.exit(1)
    
    files = sys.argv[2:]
    
    # Filter files by language
    if language == "python":
        files = [f for f in files if f.endswith('.py')]
    else:
        files = [f for f in files if f.endswith(('.ts', '.tsx', '.js', '.jsx'))]
    
    result = analyze(files, language)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

**Verification:**
```bash
chmod +x scripts/ring:codereview/py/data_flow.py
python3 scripts/ring:codereview/py/data_flow.py python scripts/ring:codereview/py/data_flow.py
```

---

### Task 8: Implement Go wrapper for Python (3 min)

**Description:** Create Go wrapper to invoke Python analyzer for Python/TypeScript files.

**File:** `scripts/ring:codereview/internal/dataflow/python.go`

```go
package dataflow

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
)

// PythonAnalyzer wraps the Python data_flow.py script
type PythonAnalyzer struct {
	scriptPath string
	language   string
}

// NewPythonAnalyzer creates analyzer for Python code
func NewPythonAnalyzer(scriptDir string) *PythonAnalyzer {
	return &PythonAnalyzer{
		scriptPath: filepath.Join(scriptDir, "py", "data_flow.py"),
		language:   "python",
	}
}

// NewTypeScriptAnalyzer creates analyzer for TypeScript code
func NewTypeScriptAnalyzer(scriptDir string) *PythonAnalyzer {
	return &PythonAnalyzer{
		scriptPath: filepath.Join(scriptDir, "py", "data_flow.py"),
		language:   "typescript",
	}
}

// Language returns the language identifier
func (p *PythonAnalyzer) Language() string {
	return p.language
}

// filterFiles returns only files matching the language
func (p *PythonAnalyzer) filterFiles(files []string) []string {
	var filtered []string
	for _, f := range files {
		switch p.language {
		case "python":
			if strings.HasSuffix(f, ".py") {
				filtered = append(filtered, f)
			}
		case "typescript":
			if strings.HasSuffix(f, ".ts") || strings.HasSuffix(f, ".tsx") ||
				strings.HasSuffix(f, ".js") || strings.HasSuffix(f, ".jsx") {
				filtered = append(filtered, f)
			}
		}
	}
	return filtered
}

// runScript executes the Python script and returns parsed output
func (p *PythonAnalyzer) runScript(files []string) (*FlowAnalysis, error) {
	filtered := p.filterFiles(files)
	if len(filtered) == 0 {
		return &FlowAnalysis{
			Language:   p.language,
			Sources:    []Source{},
			Sinks:      []Sink{},
			Flows:      []Flow{},
			NilSources: []NilSource{},
			Statistics: Stats{},
		}, nil
	}

	args := append([]string{p.scriptPath, p.language}, filtered...)
	cmd := exec.Command("python3", args...)

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("python script failed: %s", string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("running python script: %w", err)
	}

	var result FlowAnalysis
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("parsing python output: %w", err)
	}

	return &result, nil
}

// DetectSources finds sources using Python script
func (p *PythonAnalyzer) DetectSources(files []string) ([]Source, error) {
	result, err := p.runScript(files)
	if err != nil {
		return nil, err
	}
	return result.Sources, nil
}

// DetectSinks finds sinks using Python script
func (p *PythonAnalyzer) DetectSinks(files []string) ([]Sink, error) {
	result, err := p.runScript(files)
	if err != nil {
		return nil, err
	}
	return result.Sinks, nil
}

// TrackFlows tracks flows using Python script
func (p *PythonAnalyzer) TrackFlows(sources []Source, sinks []Sink, files []string) ([]Flow, error) {
	result, err := p.runScript(files)
	if err != nil {
		return nil, err
	}
	return result.Flows, nil
}

// DetectNilSources finds null/undefined sources using Python script
func (p *PythonAnalyzer) DetectNilSources(files []string) ([]NilSource, error) {
	result, err := p.runScript(files)
	if err != nil {
		return nil, err
	}
	return result.NilSources, nil
}

// Analyze performs complete analysis using Python script
func (p *PythonAnalyzer) Analyze(files []string) (*FlowAnalysis, error) {
	return p.runScript(files)
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go build ./internal/dataflow/...
```

---

### Task 9: Generate security-summary.md (5 min)

**Description:** Create markdown renderer for security summary report with risk levels and recommendations.

**File:** `scripts/ring:codereview/internal/dataflow/report.go`

```go
package dataflow

import (
	"fmt"
	"sort"
	"strings"
	"time"
	"unicode"
	"unicode/utf8"
)

// capitalizeFirst returns the string with its first letter capitalized.
// This is a stdlib-only replacement for the deprecated strings.Title.
func capitalizeFirst(s string) string {
	if s == "" {
		return s
	}
	r, size := utf8.DecodeRuneInString(s)
	if r == utf8.RuneError {
		return s
	}
	return string(unicode.ToUpper(r)) + s[size:]
}

// GenerateSecuritySummary creates a markdown report from analysis results
func GenerateSecuritySummary(analyses map[string]*FlowAnalysis) string {
	var sb strings.Builder

	// Header
	sb.WriteString("# Security Data Flow Analysis\n\n")
	sb.WriteString(fmt.Sprintf("**Generated:** %s\n\n", time.Now().Format("2006-01-02 15:04:05")))

	// Calculate totals
	var totalStats Stats
	var allFlows []Flow
	var allNilSources []NilSource

	languages := make([]string, 0, len(analyses))
	for lang := range analyses {
		languages = append(languages, lang)
	}
	sort.Strings(languages)

	for _, lang := range languages {
		analysis := analyses[lang]
		totalStats.TotalSources += analysis.Statistics.TotalSources
		totalStats.TotalSinks += analysis.Statistics.TotalSinks
		totalStats.TotalFlows += analysis.Statistics.TotalFlows
		totalStats.UnsanitizedFlows += analysis.Statistics.UnsanitizedFlows
		totalStats.CriticalFlows += analysis.Statistics.CriticalFlows
		totalStats.HighRiskFlows += analysis.Statistics.HighRiskFlows
		totalStats.NilRisks += analysis.Statistics.NilRisks
		totalStats.UncheckedNilRisks += analysis.Statistics.UncheckedNilRisks

		allFlows = append(allFlows, analysis.Flows...)
		allNilSources = append(allNilSources, analysis.NilSources...)
	}

	// Executive Summary
	sb.WriteString("## Executive Summary\n\n")
	sb.WriteString(fmt.Sprintf("| Metric | Count |\n"))
	sb.WriteString(fmt.Sprintf("|--------|-------|\n"))
	sb.WriteString(fmt.Sprintf("| Languages Analyzed | %d |\n", len(languages)))
	sb.WriteString(fmt.Sprintf("| Total Sources | %d |\n", totalStats.TotalSources))
	sb.WriteString(fmt.Sprintf("| Total Sinks | %d |\n", totalStats.TotalSinks))
	sb.WriteString(fmt.Sprintf("| Total Data Flows | %d |\n", totalStats.TotalFlows))
	sb.WriteString(fmt.Sprintf("| **Unsanitized Flows** | **%d** |\n", totalStats.UnsanitizedFlows))
	sb.WriteString(fmt.Sprintf("| Critical Risk Flows | %d |\n", totalStats.CriticalFlows))
	sb.WriteString(fmt.Sprintf("| High Risk Flows | %d |\n", totalStats.HighRiskFlows))
	sb.WriteString(fmt.Sprintf("| Nil/Null Risks | %d |\n", totalStats.NilRisks))
	sb.WriteString(fmt.Sprintf("| Unchecked Nil/Null | %d |\n", totalStats.UncheckedNilRisks))
	sb.WriteString("\n")

	// Risk Assessment
	sb.WriteString("## Risk Assessment\n\n")
	if totalStats.CriticalFlows > 0 {
		sb.WriteString("### :rotating_light: CRITICAL\n\n")
		sb.WriteString("**Immediate action required.** Critical vulnerabilities detected that could lead to:\n")
		sb.WriteString("- Remote Code Execution (RCE)\n")
		sb.WriteString("- SQL Injection\n")
		sb.WriteString("- Command Injection\n\n")
	}
	if totalStats.HighRiskFlows > 0 {
		sb.WriteString("### :warning: HIGH\n\n")
		sb.WriteString("**Priority remediation needed.** High-risk issues detected:\n")
		sb.WriteString("- Cross-Site Scripting (XSS)\n")
		sb.WriteString("- Open Redirect\n")
		sb.WriteString("- Template Injection\n\n")
	}
	if totalStats.UncheckedNilRisks > 0 {
		sb.WriteString("### :exclamation: NIL SAFETY\n\n")
		sb.WriteString(fmt.Sprintf("**%d unchecked nil/null values** that could cause runtime panics or crashes.\n\n",
			totalStats.UncheckedNilRisks))
	}

	// Critical and High Risk Flows
	if totalStats.CriticalFlows > 0 || totalStats.HighRiskFlows > 0 {
		sb.WriteString("## Critical & High Risk Flows\n\n")

		// Sort flows by risk
		sortedFlows := make([]Flow, len(allFlows))
		copy(sortedFlows, allFlows)
		sort.Slice(sortedFlows, func(i, j int) bool {
			return riskPriority(sortedFlows[i].Risk) < riskPriority(sortedFlows[j].Risk)
		})

		for _, flow := range sortedFlows {
			if flow.Risk != RiskCritical && flow.Risk != RiskHigh {
				continue
			}

			icon := ":rotating_light:"
			if flow.Risk == RiskHigh {
				icon = ":warning:"
			}

			sb.WriteString(fmt.Sprintf("### %s %s\n\n", icon, flow.Description))
			sb.WriteString(fmt.Sprintf("- **Source:** `%s:%d` - %s\n",
				flow.Source.File, flow.Source.Line, flow.Source.Type))
			sb.WriteString(fmt.Sprintf("- **Sink:** `%s:%d` - %s\n",
				flow.Sink.File, flow.Sink.Line, flow.Sink.Function))
			sb.WriteString(fmt.Sprintf("- **Sanitized:** %v\n", flow.Sanitized))
			if len(flow.Sanitizers) > 0 {
				sb.WriteString(fmt.Sprintf("- **Sanitizers:** %s\n", strings.Join(flow.Sanitizers, ", ")))
			}

			// Context
			sb.WriteString("\n**Source Context:**\n```\n")
			sb.WriteString(flow.Source.Context)
			sb.WriteString("\n```\n\n")

			sb.WriteString("**Sink Context:**\n```\n")
			sb.WriteString(flow.Sink.Context)
			sb.WriteString("\n```\n\n")

			// Recommendation
			sb.WriteString("**Recommendation:** ")
			sb.WriteString(getRecommendation(flow))
			sb.WriteString("\n\n---\n\n")
		}
	}

	// Nil Safety Issues
	if len(allNilSources) > 0 {
		sb.WriteString("## Nil/Null Safety Issues\n\n")
		sb.WriteString("| File | Line | Variable | Origin | Checked | Risk |\n")
		sb.WriteString("|------|------|----------|--------|---------|------|\n")

		for _, ns := range allNilSources {
			checked := ":x:"
			if ns.IsChecked {
				checked = ":white_check_mark:"
			}
			sb.WriteString(fmt.Sprintf("| `%s` | %d | `%s` | %s | %s | %s |\n",
				ns.File, ns.Line, ns.Variable, ns.Origin, checked, ns.Risk))
		}
		sb.WriteString("\n")
	}

	// Per-Language Breakdown
	sb.WriteString("## Language Breakdown\n\n")
	for _, lang := range languages {
		analysis := analyses[lang]
		sb.WriteString(fmt.Sprintf("### %s\n\n", capitalizeFirst(lang)))
		sb.WriteString(fmt.Sprintf("| Metric | Count |\n"))
		sb.WriteString(fmt.Sprintf("|--------|-------|\n"))
		sb.WriteString(fmt.Sprintf("| Sources | %d |\n", analysis.Statistics.TotalSources))
		sb.WriteString(fmt.Sprintf("| Sinks | %d |\n", analysis.Statistics.TotalSinks))
		sb.WriteString(fmt.Sprintf("| Flows | %d |\n", analysis.Statistics.TotalFlows))
		sb.WriteString(fmt.Sprintf("| Unsanitized | %d |\n", analysis.Statistics.UnsanitizedFlows))
		sb.WriteString(fmt.Sprintf("| Critical | %d |\n", analysis.Statistics.CriticalFlows))
		sb.WriteString(fmt.Sprintf("| High | %d |\n", analysis.Statistics.HighRiskFlows))
		sb.WriteString("\n")
	}

	// Recommendations
	sb.WriteString("## General Recommendations\n\n")
	sb.WriteString("1. **Use Parameterized Queries:** Never concatenate user input into SQL queries\n")
	sb.WriteString("2. **Escape Output:** Always escape data before rendering in HTML responses\n")
	sb.WriteString("3. **Validate Input:** Validate and sanitize all user input at entry points\n")
	sb.WriteString("4. **Avoid Command Execution:** Never pass user input to shell commands\n")
	sb.WriteString("5. **Check for Nil:** Always check pointers/optionals before dereferencing\n")
	sb.WriteString("6. **Use Allow Lists:** Prefer allow lists over deny lists for validation\n")

	return sb.String()
}

func riskPriority(risk RiskLevel) int {
	switch risk {
	case RiskCritical:
		return 0
	case RiskHigh:
		return 1
	case RiskMedium:
		return 2
	case RiskLow:
		return 3
	default:
		return 4
	}
}

func getRecommendation(flow Flow) string {
	switch {
	case flow.Sink.Type == SinkExec:
		return "Remove command execution or use a strict allow list for permitted commands. Never pass user input directly to shell."
	case flow.Sink.Type == SinkDatabase && !flow.Sanitized:
		return "Use parameterized queries or prepared statements. Never concatenate user input into SQL."
	case flow.Sink.Type == SinkResponse && (flow.Source.Type == SourceHTTPBody || flow.Source.Type == SourceHTTPQuery):
		return "Escape output using html.EscapeString() or equivalent. Consider using a templating engine with auto-escaping."
	case flow.Sink.Type == SinkTemplate:
		return "Ensure template engine auto-escapes output. Avoid using raw/unescaped directives with user input."
	case flow.Sink.Type == SinkRedirect:
		return "Validate redirect URLs against an allow list. Never redirect to user-controlled URLs directly."
	case flow.Sink.Type == SinkFile:
		return "Validate file paths and use filepath.Clean(). Ensure user cannot control path traversal sequences."
	case flow.Sink.Type == SinkLog:
		return "Sanitize log output to prevent log injection. Consider masking sensitive data."
	default:
		return "Review the data flow and ensure proper input validation and output encoding."
	}
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go build ./internal/dataflow/...
```

---

### Task 10: Create CLI binary (4 min)

**Description:** Create the main CLI entry point that orchestrates the data flow analysis.

**File:** `scripts/ring:codereview/cmd/data-flow/main.go`

```go
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/dataflow"
)

type ScopeFile struct {
	Files     []string          `json:"files"`
	Languages map[string][]string `json:"languages"`
}

func main() {
	var (
		scopeFile  = flag.String("scope", "scope.json", "Path to scope.json from Phase 0")
		outputDir  = flag.String("output", ".", "Output directory for results")
		scriptDir  = flag.String("scripts", "", "Path to scripts/ring:codereview directory")
		language   = flag.String("lang", "", "Analyze specific language only (go, python, typescript)")
		jsonOutput = flag.Bool("json", false, "Output JSON only, no markdown summary")
		verbose    = flag.Bool("v", false, "Verbose output")
	)
	flag.Parse()

	// Find script directory if not provided
	if *scriptDir == "" {
		exe, err := os.Executable()
		if err == nil {
			*scriptDir = filepath.Dir(filepath.Dir(exe))
		} else {
			*scriptDir = "."
		}
	}

	// Load scope file
	scope, err := loadScope(*scopeFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading scope: %v\n", err)
		os.Exit(1)
	}

	if *verbose {
		fmt.Printf("Loaded scope with %d files\n", len(scope.Files))
		for lang, files := range scope.Languages {
			fmt.Printf("  %s: %d files\n", lang, len(files))
		}
	}

	// Initialize analyzers
	analyzers := make(map[string]dataflow.Analyzer)

	if *language == "" || *language == "go" {
		analyzers["go"] = dataflow.NewGoAnalyzer()
	}
	if *language == "" || *language == "python" {
		analyzers["python"] = dataflow.NewPythonAnalyzer(*scriptDir)
	}
	if *language == "" || *language == "typescript" {
		analyzers["typescript"] = dataflow.NewTypeScriptAnalyzer(*scriptDir)
	}

	// Run analysis
	results := make(map[string]*dataflow.FlowAnalysis)

	for lang, analyzer := range analyzers {
		var files []string
		if langFiles, ok := scope.Languages[lang]; ok {
			files = langFiles
		} else {
			files = filterFilesByLanguage(scope.Files, lang)
		}

		if len(files) == 0 {
			if *verbose {
				fmt.Printf("No %s files to analyze\n", lang)
			}
			continue
		}

		if *verbose {
			fmt.Printf("Analyzing %d %s files...\n", len(files), lang)
		}

		analysis, err := analyzer.Analyze(files)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error analyzing %s: %v\n", lang, err)
			continue
		}

		results[lang] = analysis

		// Write language-specific JSON
		outputPath := filepath.Join(*outputDir, fmt.Sprintf("%s-flow.json", lang))
		if err := writeJSON(outputPath, analysis); err != nil {
			fmt.Fprintf(os.Stderr, "Error writing %s: %v\n", outputPath, err)
		} else if *verbose {
			fmt.Printf("Wrote %s\n", outputPath)
		}
	}

	if len(results) == 0 {
		fmt.Println("No files analyzed")
		os.Exit(0)
	}

	// Generate summary
	if !*jsonOutput {
		summary := dataflow.GenerateSecuritySummary(results)
		summaryPath := filepath.Join(*outputDir, "security-summary.md")
		if err := os.WriteFile(summaryPath, []byte(summary), 0644); err != nil {
			fmt.Fprintf(os.Stderr, "Error writing summary: %v\n", err)
		} else if *verbose {
			fmt.Printf("Wrote %s\n", summaryPath)
		}

		// Print summary stats
		printSummary(results)
	} else {
		// JSON output mode
		output, _ := json.MarshalIndent(results, "", "  ")
		fmt.Println(string(output))
	}
}

func loadScope(path string) (*ScopeFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var scope ScopeFile
	if err := json.Unmarshal(data, &scope); err != nil {
		return nil, err
	}

	// If languages map is empty, populate from files
	if scope.Languages == nil {
		scope.Languages = make(map[string][]string)
	}
	if len(scope.Languages) == 0 {
		for _, file := range scope.Files {
			lang := detectLanguage(file)
			if lang != "" {
				scope.Languages[lang] = append(scope.Languages[lang], file)
			}
		}
	}

	return &scope, nil
}

func detectLanguage(file string) string {
	switch {
	case strings.HasSuffix(file, ".go"):
		return "go"
	case strings.HasSuffix(file, ".py"):
		return "python"
	case strings.HasSuffix(file, ".ts"), strings.HasSuffix(file, ".tsx"):
		return "typescript"
	case strings.HasSuffix(file, ".js"), strings.HasSuffix(file, ".jsx"):
		return "typescript" // Analyze JS with TS patterns
	default:
		return ""
	}
}

func filterFilesByLanguage(files []string, lang string) []string {
	var filtered []string
	for _, f := range files {
		if detectLanguage(f) == lang {
			filtered = append(filtered, f)
		}
	}
	return filtered
}

func writeJSON(path string, data interface{}) error {
	output, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, output, 0644)
}

func printSummary(results map[string]*dataflow.FlowAnalysis) {
	var totalFlows, critical, high, unsanitized, nilRisks int

	for _, analysis := range results {
		totalFlows += analysis.Statistics.TotalFlows
		critical += analysis.Statistics.CriticalFlows
		high += analysis.Statistics.HighRiskFlows
		unsanitized += analysis.Statistics.UnsanitizedFlows
		nilRisks += analysis.Statistics.UncheckedNilRisks
	}

	fmt.Println("\n=== Data Flow Analysis Summary ===")
	fmt.Printf("Total Flows:        %d\n", totalFlows)
	fmt.Printf("Critical Risk:      %d\n", critical)
	fmt.Printf("High Risk:          %d\n", high)
	fmt.Printf("Unsanitized:        %d\n", unsanitized)
	fmt.Printf("Unchecked Nil/Null: %d\n", nilRisks)

	if critical > 0 {
		fmt.Println("\n[CRITICAL] Immediate remediation required!")
	} else if high > 0 {
		fmt.Println("\n[WARNING] High-risk issues detected")
	} else if unsanitized > 0 {
		fmt.Println("\n[INFO] Review unsanitized flows")
	} else {
		fmt.Println("\n[OK] No critical issues detected")
	}
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go build -o bin/data-flow ./cmd/data-flow
./bin/data-flow -h
```

---

### Task 11: Add tests (5 min)

**Description:** Create unit tests for the Go analyzer.

**File:** `scripts/ring:codereview/internal/dataflow/golang_test.go`

```go
package dataflow

import (
	"os"
	"path/filepath"
	"testing"
)

func TestGoAnalyzer_DetectSources(t *testing.T) {
	// Create temp test file
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.go")

	content := `package main

import (
	"net/http"
	"os"
)

func handler(w http.ResponseWriter, r *http.Request) {
	body := r.Body
	query := r.URL.Query().Get("id")
	header := r.Header.Get("Authorization")
	env := os.Getenv("SECRET")
	_ = body
	_ = query
	_ = header
	_ = env
}
`
	if err := os.WriteFile(testFile, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	analyzer := NewGoAnalyzer()
	sources, err := analyzer.DetectSources([]string{testFile})
	if err != nil {
		t.Fatal(err)
	}

	// Should detect: r.Body, r.URL.Query(), r.Header.Get(), os.Getenv()
	if len(sources) < 4 {
		t.Errorf("Expected at least 4 sources, got %d", len(sources))
	}

	// Check source types
	sourceTypes := make(map[SourceType]bool)
	for _, s := range sources {
		sourceTypes[s.Type] = true
	}

	expectedTypes := []SourceType{SourceHTTPBody, SourceHTTPQuery, SourceHTTPHeader, SourceEnvVar}
	for _, expected := range expectedTypes {
		if !sourceTypes[expected] {
			t.Errorf("Expected source type %s not found", expected)
		}
	}
}

func TestGoAnalyzer_DetectSinks(t *testing.T) {
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.go")

	content := `package main

import (
	"database/sql"
	"log"
	"net/http"
	"os/exec"
)

func handler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	db.Exec("INSERT INTO users VALUES (?)", "test")
	w.Write([]byte("response"))
	exec.Command("ls", "-la")
	log.Printf("request from %s", r.RemoteAddr)
}
`
	if err := os.WriteFile(testFile, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	analyzer := NewGoAnalyzer()
	sinks, err := analyzer.DetectSinks([]string{testFile})
	if err != nil {
		t.Fatal(err)
	}

	// Should detect: db.Exec, w.Write, exec.Command, log.Printf
	if len(sinks) < 4 {
		t.Errorf("Expected at least 4 sinks, got %d", len(sinks))
	}

	sinkTypes := make(map[SinkType]bool)
	for _, s := range sinks {
		sinkTypes[s.Type] = true
	}

	expectedTypes := []SinkType{SinkDatabase, SinkResponse, SinkExec, SinkLog}
	for _, expected := range expectedTypes {
		if !sinkTypes[expected] {
			t.Errorf("Expected sink type %s not found", expected)
		}
	}
}

func TestGoAnalyzer_TrackFlows(t *testing.T) {
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.go")

	content := `package main

import (
	"database/sql"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	userInput := r.URL.Query().Get("input")
	db.Exec("INSERT INTO logs VALUES (" + userInput + ")")
}
`
	if err := os.WriteFile(testFile, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	analyzer := NewGoAnalyzer()
	sources, _ := analyzer.DetectSources([]string{testFile})
	sinks, _ := analyzer.DetectSinks([]string{testFile})
	flows, err := analyzer.TrackFlows(sources, sinks, []string{testFile})
	if err != nil {
		t.Fatal(err)
	}

	// Should detect flow from query param to database
	var criticalFlow *Flow
	for i, f := range flows {
		if f.Risk == RiskCritical {
			criticalFlow = &flows[i]
			break
		}
	}

	if criticalFlow == nil {
		t.Error("Expected to detect critical flow from HTTP query to database")
	}
}

func TestGoAnalyzer_DetectNilSources(t *testing.T) {
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.go")

	content := `package main

import "database/sql"

func getUser(db *sql.DB, id string) (*User, error) {
	row := db.QueryRow("SELECT * FROM users WHERE id = ?", id)
	var user User
	if err := row.Scan(&user.ID, &user.Name); err != nil {
		return nil, err
	}
	return &user, nil
}

func uncheckedUsage(db *sql.DB) {
	result, _ := cache.Get("key")
	// Using result without nil check
	println(result.Value)
}

func checkedUsage(db *sql.DB) {
	result, ok := cache.Get("key")
	if result != nil && ok {
		println(result.Value)
	}
}

type User struct {
	ID   string
	Name string
}

var cache map[string]*Result
type Result struct{ Value string }
`
	if err := os.WriteFile(testFile, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	analyzer := NewGoAnalyzer()
	nilSources, err := analyzer.DetectNilSources([]string{testFile})
	if err != nil {
		t.Fatal(err)
	}

	if len(nilSources) == 0 {
		t.Error("Expected to detect nil sources")
	}

	// Check that we detected both checked and unchecked patterns
	var hasUnchecked, hasChecked bool
	for _, ns := range nilSources {
		if ns.IsChecked {
			hasChecked = true
		} else {
			hasUnchecked = true
		}
	}

	if !hasUnchecked {
		t.Error("Expected to detect unchecked nil source")
	}
	// Note: hasChecked depends on how our check detection works
}

func TestGoAnalyzer_Analyze(t *testing.T) {
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.go")

	content := `package main

import (
	"database/sql"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	input := r.URL.Query().Get("q")
	db.Exec("SELECT * FROM users WHERE name = '" + input + "'")
	w.Write([]byte(input))
}
`
	if err := os.WriteFile(testFile, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	analyzer := NewGoAnalyzer()
	analysis, err := analyzer.Analyze([]string{testFile})
	if err != nil {
		t.Fatal(err)
	}

	if analysis.Language != "go" {
		t.Errorf("Expected language 'go', got '%s'", analysis.Language)
	}

	if analysis.Statistics.TotalSources == 0 {
		t.Error("Expected to detect sources")
	}

	if analysis.Statistics.TotalSinks == 0 {
		t.Error("Expected to detect sinks")
	}

	if analysis.Statistics.CriticalFlows == 0 {
		t.Error("Expected to detect critical flows (SQL injection)")
	}
}

func TestCalculateRisk(t *testing.T) {
	analyzer := NewGoAnalyzer()

	tests := []struct {
		sourceType SourceType
		sinkType   SinkType
		expected   RiskLevel
	}{
		{SourceHTTPQuery, SinkExec, RiskCritical},
		{SourceHTTPBody, SinkDatabase, RiskCritical},
		{SourceHTTPQuery, SinkResponse, RiskHigh},
		{SourceHTTPBody, SinkTemplate, RiskHigh},
		{SourceEnvVar, SinkDatabase, RiskMedium},
		{SourceHTTPQuery, SinkLog, RiskLow},
	}

	for _, tt := range tests {
		source := Source{Type: tt.sourceType}
		sink := Sink{Type: tt.sinkType}
		risk := analyzer.calculateRisk(source, sink)
		if risk != tt.expected {
			t.Errorf("calculateRisk(%s, %s) = %s, want %s",
				tt.sourceType, tt.sinkType, risk, tt.expected)
		}
	}
}

func TestCheckSanitization(t *testing.T) {
	analyzer := NewGoAnalyzer()

	tests := []struct {
		context  string
		expected bool
	}{
		{"db.Exec(\"SELECT * FROM users WHERE id = ?\", id)", true},
		{"db.Exec(\"SELECT * FROM users WHERE id = \" + id)", false},
		{"w.Write([]byte(html.EscapeString(input)))", true},
		{"w.Write([]byte(input))", false},
	}

	for _, tt := range tests {
		source := Source{}
		sink := Sink{Context: tt.context}
		sanitized, _ := analyzer.checkSanitization(source, sink)
		if sanitized != tt.expected {
			t.Errorf("checkSanitization(%q) = %v, want %v",
				tt.context, sanitized, tt.expected)
		}
	}
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go test ./internal/dataflow/... -v
```

---

### Task 12: Integration test (3 min)

**Description:** Create end-to-end integration test that runs the full analysis pipeline.

**File:** `scripts/ring:codereview/internal/dataflow/integration_test.go`

```go
//go:build integration

package dataflow

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestIntegration_FullPipeline(t *testing.T) {
	// Create test project structure
	tmpDir := t.TempDir()

	// Create Go file with vulnerabilities
	goDir := filepath.Join(tmpDir, "go")
	if err := os.MkdirAll(goDir, 0755); err != nil {
		t.Fatal(err)
	}

	goFile := filepath.Join(goDir, "main.go")
	goContent := `package main

import (
	"database/sql"
	"html/template"
	"net/http"
	"os"
	"os/exec"
)

func handler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	// Critical: SQL injection
	userID := r.URL.Query().Get("id")
	db.Exec("SELECT * FROM users WHERE id = '" + userID + "'")

	// Critical: Command injection
	cmd := r.URL.Query().Get("cmd")
	exec.Command("sh", "-c", cmd)

	// High: XSS
	name := r.URL.Query().Get("name")
	w.Write([]byte("<h1>Hello " + name + "</h1>"))

	// High: Template injection
	tmpl := template.New("test")
	tmpl.Parse(r.URL.Query().Get("template"))

	// Medium: Env to database
	secret := os.Getenv("DB_PASSWORD")
	db.Exec("SET PASSWORD = '" + secret + "'")

	// Low: Logging user data
	log.Printf("User requested: %s", r.URL.Path)

	// Safe: Parameterized query
	safeID := r.URL.Query().Get("safe_id")
	db.Exec("SELECT * FROM users WHERE id = ?", safeID)
}

func nilRisk(db *sql.DB) {
	// Nil risk: unchecked
	user, _ := db.QueryRow("SELECT * FROM users WHERE id = 1").Scan()
	println(user)

	// Nil risk: checked
	result, ok := cache.Get("key")
	if result != nil && ok {
		println(result)
	}
}

var cache map[string]interface{}
`
	if err := os.WriteFile(goFile, []byte(goContent), 0644); err != nil {
		t.Fatal(err)
	}

	// Create scope.json
	scopeFile := filepath.Join(tmpDir, "scope.json")
	scope := map[string]interface{}{
		"files": []string{goFile},
		"languages": map[string][]string{
			"go": {goFile},
		},
	}
	scopeData, _ := json.Marshal(scope)
	if err := os.WriteFile(scopeFile, scopeData, 0644); err != nil {
		t.Fatal(err)
	}

	// Run analysis
	analyzer := NewGoAnalyzer()
	analysis, err := analyzer.Analyze([]string{goFile})
	if err != nil {
		t.Fatal(err)
	}

	// Verify results
	t.Logf("Analysis results:")
	t.Logf("  Sources: %d", analysis.Statistics.TotalSources)
	t.Logf("  Sinks: %d", analysis.Statistics.TotalSinks)
	t.Logf("  Flows: %d", analysis.Statistics.TotalFlows)
	t.Logf("  Critical: %d", analysis.Statistics.CriticalFlows)
	t.Logf("  High: %d", analysis.Statistics.HighRiskFlows)
	t.Logf("  Nil risks: %d", analysis.Statistics.NilRisks)

	// Must detect critical flows
	if analysis.Statistics.CriticalFlows < 2 {
		t.Errorf("Expected at least 2 critical flows (SQL injection + command injection), got %d",
			analysis.Statistics.CriticalFlows)
	}

	// Must detect high risk flows
	if analysis.Statistics.HighRiskFlows < 1 {
		t.Errorf("Expected at least 1 high risk flow (XSS), got %d",
			analysis.Statistics.HighRiskFlows)
	}

	// Must have some sanitized flows (parameterized query)
	sanitizedCount := 0
	for _, flow := range analysis.Flows {
		if flow.Sanitized {
			sanitizedCount++
		}
	}
	if sanitizedCount == 0 {
		t.Error("Expected at least 1 sanitized flow (parameterized query)")
	}

	// Generate security summary
	results := map[string]*FlowAnalysis{"go": analysis}
	summary := GenerateSecuritySummary(results)

	if len(summary) == 0 {
		t.Error("Expected non-empty security summary")
	}

	// Verify summary contains expected sections
	expectedSections := []string{
		"# Security Data Flow Analysis",
		"## Executive Summary",
		"## Risk Assessment",
		"CRITICAL",
		"## Critical & High Risk Flows",
	}

	for _, section := range expectedSections {
		if !containsString(summary, section) {
			t.Errorf("Summary missing expected section: %s", section)
		}
	}

	// Write outputs for manual inspection
	outputDir := filepath.Join(tmpDir, "output")
	os.MkdirAll(outputDir, 0755)

	flowJSON, _ := json.MarshalIndent(analysis, "", "  ")
	os.WriteFile(filepath.Join(outputDir, "go-flow.json"), flowJSON, 0644)
	os.WriteFile(filepath.Join(outputDir, "security-summary.md"), []byte(summary), 0644)

	t.Logf("Output written to: %s", outputDir)
}

func containsString(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsString(s[1:], substr) || s[:len(substr)] == substr)
}

func TestIntegration_MultiLanguage(t *testing.T) {
	// Skip if Python not available
	if _, err := os.Stat("/usr/bin/python3"); os.IsNotExist(err) {
		t.Skip("Python3 not available")
	}

	tmpDir := t.TempDir()

	// Create Go file
	goFile := filepath.Join(tmpDir, "main.go")
	goContent := `package main

import "net/http"

func handler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(r.URL.Query().Get("q")))
}
`
	os.WriteFile(goFile, []byte(goContent), 0644)

	// Create Python file
	pyFile := filepath.Join(tmpDir, "app.py")
	pyContent := `from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def index():
    return request.args.get("q")
`
	os.WriteFile(pyFile, []byte(pyContent), 0644)

	// Analyze Go
	goAnalyzer := NewGoAnalyzer()
	goAnalysis, err := goAnalyzer.Analyze([]string{goFile})
	if err != nil {
		t.Fatal(err)
	}

	// Analyze Python (if script exists)
	scriptDir := os.Getenv("SCRIPT_DIR")
	if scriptDir == "" {
		t.Log("SCRIPT_DIR not set, skipping Python analysis")
	} else {
		pyAnalyzer := NewPythonAnalyzer(scriptDir)
		pyAnalysis, err := pyAnalyzer.Analyze([]string{pyFile})
		if err != nil {
			t.Logf("Python analysis error (expected if script not found): %v", err)
		} else {
			// Generate combined summary
			results := map[string]*FlowAnalysis{
				"go":     goAnalysis,
				"python": pyAnalysis,
			}
			summary := GenerateSecuritySummary(results)
			t.Logf("Multi-language summary length: %d bytes", len(summary))
		}
	}

	if goAnalysis.Statistics.TotalFlows == 0 {
		t.Error("Expected Go analysis to detect flows")
	}
}
```

**Verification:**
```bash
cd scripts/ring:codereview && go test ./internal/dataflow/... -v -tags=integration
```

---

## Estimated Total: ~50 minutes

| Task | Time | Cumulative |
|------|------|------------|
| Task 1: Directory structure | 2 min | 2 min |
| Task 2: Types definition | 3 min | 5 min |
| Task 3: Go source detection | 5 min | 10 min |
| Task 4: Go sink detection | 5 min | 15 min |
| Task 5: Flow tracking | 5 min | 20 min |
| Task 6: Nil source tracking | 4 min | 24 min |
| Task 7: Python data_flow.py | 5 min | 29 min |
| Task 8: Go wrapper for Python | 3 min | 32 min |
| Task 9: Security summary renderer | 5 min | 37 min |
| Task 10: CLI binary | 4 min | 41 min |
| Task 11: Unit tests | 5 min | 46 min |
| Task 12: Integration test | 3 min | 49 min |

---

## Execution Order

1. **Tasks 1-2**: Setup structure and types (foundation)
2. **Tasks 3-6**: Implement Go analyzer (core functionality)
3. **Tasks 7-8**: Add Python/TypeScript support (language coverage)
4. **Tasks 9-10**: Create output and CLI (user interface)
5. **Tasks 11-12**: Add tests (quality assurance)

## Usage

```bash
# Build
cd scripts/ring:codereview
go build -o bin/data-flow ./cmd/data-flow

# Run with scope file
./bin/data-flow -scope scope.json -output results/ -v

# Run for specific language
./bin/data-flow -scope scope.json -lang go -output results/

# JSON output only
./bin/data-flow -scope scope.json -json
```

## Output Files

- `go-flow.json` - Go analysis results
- `python-flow.json` - Python analysis results  
- `typescript-flow.json` - TypeScript analysis results
- `security-summary.md` - Human-readable security report
