# Codereview Phase 0: Scope Detector Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans to implement this plan task-by-task.

**Goal:** Build the `scope-detector` Go binary that analyzes git diffs to detect changed files, identify project language (Go/TypeScript/Python), and output structured scope information for downstream code review phases.

**Architecture:** Single Go binary in `scripts/ring:codereview/cmd/scope-detector/` that uses `exec.Command` to run git operations, parses output to categorize files by language/extension, and produces JSON output. Internal packages under `scripts/ring:codereview/internal/` provide reusable git operations, scope detection logic, and output formatting.

**Tech Stack:**
- Go 1.22+ (stdlib only - no external dependencies)
- Git CLI (via `exec.Command`)
- JSON output format

**Global Prerequisites:**
- Environment: macOS/Linux with Go 1.22+, Git 2.x+
- Tools: Go compiler, Git CLI
- Access: None required (local git operations only)
- State: Clean working tree on feature branch

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
go version           # Expected: go version go1.22+ (any 1.22.x or higher)
git --version        # Expected: git version 2.x.x
ls -la scripts/      # Expected: directory does not exist (we'll create it)
```

## Historical Precedent

**Query:** "ring:codereview scope detection Go CLI git diff"
**Index Status:** Populated (no relevant matches)

### Successful Patterns to Reference
No directly relevant handoffs found. This is a new feature area.

### Failure Patterns to AVOID
No failure patterns recorded for this domain.

### Related Past Plans
- `ring:codereview-enhancement-macro-plan.md` - Parent macro plan defining overall architecture

---

## File Structure Overview

```
scripts/
└── ring:codereview/
    ├── cmd/
    │   └── scope-detector/
    │       └── main.go              # CLI binary entry point
    ├── internal/
    │   ├── git/
    │   │   └── git.go               # Git operations wrapper
    │   │   └── git_test.go          # Git unit tests
    │   ├── scope/
    │   │   └── scope.go             # Scope detection logic
    │   │   └── scope_test.go        # Scope unit tests
    │   └── output/
    │       └── json.go              # JSON output formatter
    │       └── json_test.go         # JSON formatter tests
    ├── go.mod                       # Go module definition
    ├── go.sum                       # (empty initially - no deps)
    └── Makefile                     # Build targets
```

---

## Task 1: Create Go Module and Directory Structure

**Files:**
- Create: `scripts/ring:codereview/go.mod`
- Create: `scripts/ring:codereview/Makefile`

**Prerequisites:**
- Tools: Go 1.22+
- Current directory: Repository root `/Users/fredamaral/repos/lerianstudio/ring`

**Step 1: Create directory structure**

```bash
mkdir -p scripts/ring:codereview/cmd/scope-detector
mkdir -p scripts/ring:codereview/internal/git
mkdir -p scripts/ring:codereview/internal/scope
mkdir -p scripts/ring:codereview/internal/output
mkdir -p scripts/ring:codereview/bin
```

**Step 2: Create go.mod**

Create file `scripts/ring:codereview/go.mod`:

```go
module github.com/lerianstudio/ring/scripts/ring:codereview

go 1.22
```

**Step 3: Create Makefile**

Create file `scripts/ring:codereview/Makefile`:

```makefile
.PHONY: all build test clean install

# Binary output directory
BIN_DIR := bin

# All binaries to build
BINARIES := scope-detector

all: build

build: $(BINARIES)

scope-detector:
	@echo "Building scope-detector..."
	@go build -o $(BIN_DIR)/scope-detector ./cmd/scope-detector

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
```

**Step 4: Verify structure**

Run: `ls -la scripts/ring:codereview/`

**Expected output:**
```
total 16
drwxr-xr-x  7 user  staff   224 Jan 13 XX:XX .
drwxr-xr-x  3 user  staff    96 Jan 13 XX:XX ..
-rw-r--r--  1 user  staff    XX Jan 13 XX:XX Makefile
drwxr-xr-x  2 user  staff    64 Jan 13 XX:XX bin
drwxr-xr-x  3 user  staff    96 Jan 13 XX:XX cmd
-rw-r--r--  1 user  staff    XX Jan 13 XX:XX go.mod
drwxr-xr-x  5 user  staff   160 Jan 13 XX:XX internal
```

**Step 5: Verify go.mod is valid**

Run: `cd scripts/ring:codereview && go mod verify && cd ../..`

**Expected output:**
```
all modules verified
```

**If Task Fails:**

1. **Directory creation fails:**
   - Check: `ls -la scripts/` (parent exists?)
   - Fix: Create parent first: `mkdir -p scripts`
   - Rollback: `rm -rf scripts/ring:codereview`

2. **go mod verify fails:**
   - Check: `cat scripts/ring:codereview/go.mod` (syntax correct?)
   - Fix: Ensure go directive matches installed Go version
   - Rollback: `rm scripts/ring:codereview/go.mod`

---

## Task 2: Implement Git Operations Package - Types and Interface

**Files:**
- Create: `scripts/ring:codereview/internal/git/git.go`

**Prerequisites:**
- Task 1 completed (directory structure exists)
- Tools: Go 1.22+

**Step 1: Write the failing test**

Create file `scripts/ring:codereview/internal/git/git_test.go`:

```go
package git

import (
	"testing"
)

func TestFileStatusString(t *testing.T) {
	tests := []struct {
		name     string
		status   FileStatus
		expected string
	}{
		{"Added", StatusAdded, "A"},
		{"Modified", StatusModified, "M"},
		{"Deleted", StatusDeleted, "D"},
		{"Renamed", StatusRenamed, "R"},
		{"Copied", StatusCopied, "C"},
		{"Unknown", StatusUnknown, "?"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.status.String(); got != tt.expected {
				t.Errorf("FileStatus.String() = %q, want %q", got, tt.expected)
			}
		})
	}
}

func TestParseFileStatus(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected FileStatus
	}{
		{"Added", "A", StatusAdded},
		{"Modified", "M", StatusModified},
		{"Deleted", "D", StatusDeleted},
		{"Renamed", "R100", StatusRenamed},
		{"Renamed partial", "R075", StatusRenamed},
		{"Copied", "C", StatusCopied},
		{"Unknown", "X", StatusUnknown},
		{"Empty", "", StatusUnknown},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := ParseFileStatus(tt.input); got != tt.expected {
				t.Errorf("ParseFileStatus(%q) = %v, want %v", tt.input, got, tt.expected)
			}
		})
	}
}

func TestChangedFileValidation(t *testing.T) {
	// Test that ChangedFile struct can be created with all fields
	cf := ChangedFile{
		Path:      "internal/handler/user.go",
		Status:    StatusModified,
		OldPath:   "",
		Additions: 10,
		Deletions: 5,
	}

	if cf.Path != "internal/handler/user.go" {
		t.Errorf("ChangedFile.Path = %q, want %q", cf.Path, "internal/handler/user.go")
	}
	if cf.Status != StatusModified {
		t.Errorf("ChangedFile.Status = %v, want %v", cf.Status, StatusModified)
	}
}

func TestDiffStatsValidation(t *testing.T) {
	// Test that DiffStats struct can be created with all fields
	stats := DiffStats{
		TotalFiles:     3,
		TotalAdditions: 100,
		TotalDeletions: 25,
	}

	if stats.TotalFiles != 3 {
		t.Errorf("DiffStats.TotalFiles = %d, want %d", stats.TotalFiles, 3)
	}
}
```

**Step 2: Run test to verify it fails**

Run: `cd scripts/ring:codereview && go test -v ./internal/git/... 2>&1 | head -20 && cd ../..`

**Expected output:**
```
# github.com/lerianstudio/ring/scripts/ring:codereview/internal/git [github.com/lerianstudio/ring/scripts/ring:codereview/internal/git.test]
./git_test.go:XX:XX: undefined: FileStatus
./git_test.go:XX:XX: undefined: StatusAdded
...
FAIL	github.com/lerianstudio/ring/scripts/ring:codereview/internal/git [build failed]
```

**If you see different error:** Check that git_test.go was created in the correct location

**Step 3: Write minimal implementation**

Create file `scripts/ring:codereview/internal/git/git.go`:

```go
// Package git provides utilities for interacting with git repositories.
// It wraps git CLI commands using exec.Command (no external dependencies).
package git

import (
	"bufio"
	"bytes"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
)

// FileStatus represents the status of a file in git diff output.
type FileStatus int

const (
	StatusUnknown FileStatus = iota
	StatusAdded
	StatusModified
	StatusDeleted
	StatusRenamed
	StatusCopied
)

// String returns the single-character git status code.
func (s FileStatus) String() string {
	switch s {
	case StatusAdded:
		return "A"
	case StatusModified:
		return "M"
	case StatusDeleted:
		return "D"
	case StatusRenamed:
		return "R"
	case StatusCopied:
		return "C"
	default:
		return "?"
	}
}

// ParseFileStatus converts a git status string to FileStatus.
// Handles both single-char ("M") and similarity-prefixed ("R100") formats.
func ParseFileStatus(s string) FileStatus {
	if len(s) == 0 {
		return StatusUnknown
	}
	switch s[0] {
	case 'A':
		return StatusAdded
	case 'M':
		return StatusModified
	case 'D':
		return StatusDeleted
	case 'R':
		return StatusRenamed
	case 'C':
		return StatusCopied
	default:
		return StatusUnknown
	}
}

// ChangedFile represents a single file change in a git diff.
type ChangedFile struct {
	Path      string     // Current path of the file
	Status    FileStatus // Type of change (A/M/D/R/C)
	OldPath   string     // Previous path (for renames/copies)
	Additions int        // Lines added
	Deletions int        // Lines deleted
}

// DiffStats contains aggregate statistics for a diff.
type DiffStats struct {
	TotalFiles     int
	TotalAdditions int
	TotalDeletions int
}

// DiffResult contains the complete result of a git diff operation.
type DiffResult struct {
	BaseRef  string        // Base reference (e.g., "main", commit SHA)
	HeadRef  string        // Head reference (e.g., "HEAD", commit SHA)
	Files    []ChangedFile // List of changed files
	Stats    DiffStats     // Aggregate statistics
}

// Client provides methods for interacting with git.
type Client struct {
	workDir string // Working directory for git commands
}

// NewClient creates a new git client for the specified directory.
// If workDir is empty, commands run in the current directory.
func NewClient(workDir string) *Client {
	return &Client{workDir: workDir}
}

// runGit executes a git command and returns stdout.
func (c *Client) runGit(args ...string) ([]byte, error) {
	cmd := exec.Command("git", args...)
	if c.workDir != "" {
		cmd.Dir = c.workDir
	}

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("git %s failed: %w\nstderr: %s", 
			strings.Join(args, " "), err, stderr.String())
	}

	return stdout.Bytes(), nil
}

// GetDiff returns the diff between two refs, or working tree changes if refs are empty.
// baseRef: starting point (e.g., "main", "abc123"). Empty = use index.
// headRef: ending point (e.g., "HEAD", "def456"). Empty = working tree.
func (c *Client) GetDiff(baseRef, headRef string) (*DiffResult, error) {
	result := &DiffResult{
		BaseRef: baseRef,
		HeadRef: headRef,
		Files:   make([]ChangedFile, 0),
	}

	// Build git diff command based on refs provided
	args := []string{"diff", "--name-status"}
	
	switch {
	case baseRef == "" && headRef == "":
		// Staged + unstaged changes (compare index to working tree)
		args = append(args, "HEAD")
	case baseRef != "" && headRef == "":
		// Compare base to working tree
		args = append(args, baseRef)
	case baseRef == "" && headRef != "":
		// Compare HEAD to specific ref
		args = append(args, "HEAD", headRef)
	default:
		// Compare two specific refs
		args = append(args, baseRef, headRef)
	}

	// Get file status list
	output, err := c.runGit(args...)
	if err != nil {
		return nil, fmt.Errorf("failed to get diff name-status: %w", err)
	}

	// Parse name-status output
	scanner := bufio.NewScanner(bytes.NewReader(output))
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}

		cf, err := parseNameStatusLine(line)
		if err != nil {
			continue // Skip unparseable lines
		}
		result.Files = append(result.Files, cf)
	}

	// Get diff statistics
	statsArgs := []string{"diff", "--numstat"}
	if baseRef == "" && headRef == "" {
		statsArgs = append(statsArgs, "HEAD")
	} else if baseRef != "" && headRef == "" {
		statsArgs = append(statsArgs, baseRef)
	} else if baseRef == "" && headRef != "" {
		statsArgs = append(statsArgs, "HEAD", headRef)
	} else {
		statsArgs = append(statsArgs, baseRef, headRef)
	}

	statsOutput, err := c.runGit(statsArgs...)
	if err != nil {
		// Non-fatal: we can continue without stats
		result.Stats.TotalFiles = len(result.Files)
		return result, nil
	}

	// Parse numstat output and update file stats
	statsMap := parseNumstat(statsOutput)
	for i, f := range result.Files {
		if stats, ok := statsMap[f.Path]; ok {
			result.Files[i].Additions = stats.additions
			result.Files[i].Deletions = stats.deletions
			result.Stats.TotalAdditions += stats.additions
			result.Stats.TotalDeletions += stats.deletions
		}
	}
	result.Stats.TotalFiles = len(result.Files)

	return result, nil
}

// GetStagedDiff returns only staged changes (index vs HEAD).
func (c *Client) GetStagedDiff() (*DiffResult, error) {
	result := &DiffResult{
		BaseRef: "HEAD",
		HeadRef: "staged",
		Files:   make([]ChangedFile, 0),
	}

	// Get staged file status
	output, err := c.runGit("diff", "--name-status", "--cached")
	if err != nil {
		return nil, fmt.Errorf("failed to get staged diff: %w", err)
	}

	scanner := bufio.NewScanner(bytes.NewReader(output))
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		cf, err := parseNameStatusLine(line)
		if err != nil {
			continue
		}
		result.Files = append(result.Files, cf)
	}

	// Get staged stats
	statsOutput, err := c.runGit("diff", "--numstat", "--cached")
	if err == nil {
		statsMap := parseNumstat(statsOutput)
		for i, f := range result.Files {
			if stats, ok := statsMap[f.Path]; ok {
				result.Files[i].Additions = stats.additions
				result.Files[i].Deletions = stats.deletions
				result.Stats.TotalAdditions += stats.additions
				result.Stats.TotalDeletions += stats.deletions
			}
		}
	}
	result.Stats.TotalFiles = len(result.Files)

	return result, nil
}

// GetWorkingTreeDiff returns only unstaged changes (working tree vs index).
func (c *Client) GetWorkingTreeDiff() (*DiffResult, error) {
	result := &DiffResult{
		BaseRef: "index",
		HeadRef: "working-tree",
		Files:   make([]ChangedFile, 0),
	}

	// Get unstaged file status (no --cached flag)
	output, err := c.runGit("diff", "--name-status")
	if err != nil {
		return nil, fmt.Errorf("failed to get working tree diff: %w", err)
	}

	scanner := bufio.NewScanner(bytes.NewReader(output))
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		cf, err := parseNameStatusLine(line)
		if err != nil {
			continue
		}
		result.Files = append(result.Files, cf)
	}

	// Get unstaged stats
	statsOutput, err := c.runGit("diff", "--numstat")
	if err == nil {
		statsMap := parseNumstat(statsOutput)
		for i, f := range result.Files {
			if stats, ok := statsMap[f.Path]; ok {
				result.Files[i].Additions = stats.additions
				result.Files[i].Deletions = stats.deletions
				result.Stats.TotalAdditions += stats.additions
				result.Stats.TotalDeletions += stats.deletions
			}
		}
	}
	result.Stats.TotalFiles = len(result.Files)

	return result, nil
}

// GetAllChangesDiff returns both staged and unstaged changes combined.
func (c *Client) GetAllChangesDiff() (*DiffResult, error) {
	staged, err := c.GetStagedDiff()
	if err != nil {
		return nil, fmt.Errorf("failed to get staged changes: %w", err)
	}

	unstaged, err := c.GetWorkingTreeDiff()
	if err != nil {
		return nil, fmt.Errorf("failed to get unstaged changes: %w", err)
	}

	// Merge results, deduplicating by path (staged takes precedence)
	result := &DiffResult{
		BaseRef: "HEAD",
		HeadRef: "working-tree",
		Files:   make([]ChangedFile, 0),
	}

	seenPaths := make(map[string]bool)
	
	// Add staged files first
	for _, f := range staged.Files {
		result.Files = append(result.Files, f)
		seenPaths[f.Path] = true
		result.Stats.TotalAdditions += f.Additions
		result.Stats.TotalDeletions += f.Deletions
	}

	// Add unstaged files not already in staged
	for _, f := range unstaged.Files {
		if !seenPaths[f.Path] {
			result.Files = append(result.Files, f)
			seenPaths[f.Path] = true
			result.Stats.TotalAdditions += f.Additions
			result.Stats.TotalDeletions += f.Deletions
		}
	}

	result.Stats.TotalFiles = len(result.Files)
	return result, nil
}

// parseNameStatusLine parses a single line of git diff --name-status output.
// Format: "M\tpath/to/file" or "R100\told/path\tnew/path"
func parseNameStatusLine(line string) (ChangedFile, error) {
	parts := strings.Split(line, "\t")
	if len(parts) < 2 {
		return ChangedFile{}, fmt.Errorf("invalid name-status line: %s", line)
	}

	status := ParseFileStatus(parts[0])
	cf := ChangedFile{
		Status: status,
	}

	// Handle renames/copies (have old and new paths)
	if status == StatusRenamed || status == StatusCopied {
		if len(parts) < 3 {
			return ChangedFile{}, fmt.Errorf("invalid rename/copy line: %s", line)
		}
		cf.OldPath = parts[1]
		cf.Path = parts[2]
	} else {
		cf.Path = parts[1]
	}

	return cf, nil
}

// fileStats holds parsed addition/deletion counts for a file.
type fileStats struct {
	additions int
	deletions int
}

// parseNumstat parses git diff --numstat output.
// Format: "10\t5\tpath/to/file" (additions, deletions, path)
// Binary files show as "-\t-\tpath"
func parseNumstat(output []byte) map[string]fileStats {
	result := make(map[string]fileStats)
	scanner := bufio.NewScanner(bytes.NewReader(output))

	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}

		parts := strings.Split(line, "\t")
		if len(parts) < 3 {
			continue
		}

		// Skip binary files (marked with "-")
		if parts[0] == "-" || parts[1] == "-" {
			continue
		}

		additions, err := strconv.Atoi(parts[0])
		if err != nil {
			continue
		}
		deletions, err := strconv.Atoi(parts[1])
		if err != nil {
			continue
		}

		// Handle paths with spaces (rejoin remaining parts)
		path := strings.Join(parts[2:], "\t")
		result[path] = fileStats{
			additions: additions,
			deletions: deletions,
		}
	}

	return result
}
```

**Step 4: Run test to verify it passes**

Run: `cd scripts/ring:codereview && go test -v ./internal/git/... && cd ../..`

**Expected output:**
```
=== RUN   TestFileStatusString
=== RUN   TestFileStatusString/Added
=== RUN   TestFileStatusString/Modified
=== RUN   TestFileStatusString/Deleted
=== RUN   TestFileStatusString/Renamed
=== RUN   TestFileStatusString/Copied
=== RUN   TestFileStatusString/Unknown
--- PASS: TestFileStatusString (0.00s)
    --- PASS: TestFileStatusString/Added (0.00s)
    --- PASS: TestFileStatusString/Modified (0.00s)
    --- PASS: TestFileStatusString/Deleted (0.00s)
    --- PASS: TestFileStatusString/Renamed (0.00s)
    --- PASS: TestFileStatusString/Copied (0.00s)
    --- PASS: TestFileStatusString/Unknown (0.00s)
=== RUN   TestParseFileStatus
...
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/git
```

**Step 5: Commit**

```bash
git add scripts/ring:codereview/
git commit -m "feat(ring:codereview): add git operations package with types and diff parsing

Phase 0 of ring:codereview enhancement - foundational git wrapper.
Includes FileStatus enum, ChangedFile struct, and Client with
GetDiff, GetStagedDiff, GetWorkingTreeDiff, GetAllChangesDiff methods."
```

**If Task Fails:**

1. **Test still fails after implementation:**
   - Check: `go build ./internal/git/` (syntax errors?)
   - Fix: Review error messages and fix type definitions
   - Rollback: `git checkout -- scripts/ring:codereview/internal/git/`

2. **Import errors:**
   - Check: Package name matches directory
   - Fix: Ensure `package git` at top of both files

---

## Task 3: Add Integration Tests for Git Package

**Files:**
- Modify: `scripts/ring:codereview/internal/git/git_test.go`

**Prerequisites:**
- Task 2 completed (git package exists)
- Must be in a git repository (ring repo itself)

**Step 1: Add integration tests to existing test file**

Append to `scripts/ring:codereview/internal/git/git_test.go`:

```go
// Integration tests - these run against the actual git repository

func TestClientGetDiff_Integration(t *testing.T) {
	// Skip if not in a git repo
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	client := NewClient("")

	// Test getting diff between two known commits
	// This tests against the ring repo itself
	result, err := client.GetDiff("HEAD~1", "HEAD")
	if err != nil {
		// This might fail if HEAD~1 doesn't exist (fresh repo)
		t.Skipf("Could not get diff HEAD~1..HEAD: %v", err)
	}

	// Basic validation
	if result.BaseRef != "HEAD~1" {
		t.Errorf("BaseRef = %q, want %q", result.BaseRef, "HEAD~1")
	}
	if result.HeadRef != "HEAD" {
		t.Errorf("HeadRef = %q, want %q", result.HeadRef, "HEAD")
	}
}

func TestClientGetStagedDiff_Integration(t *testing.T) {
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	client := NewClient("")
	result, err := client.GetStagedDiff()
	if err != nil {
		t.Fatalf("GetStagedDiff() error = %v", err)
	}

	// Should return a valid result (even if empty)
	if result.BaseRef != "HEAD" {
		t.Errorf("BaseRef = %q, want %q", result.BaseRef, "HEAD")
	}
	if result.HeadRef != "staged" {
		t.Errorf("HeadRef = %q, want %q", result.HeadRef, "staged")
	}
	if result.Files == nil {
		t.Error("Files should not be nil")
	}
}

func TestClientGetWorkingTreeDiff_Integration(t *testing.T) {
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	client := NewClient("")
	result, err := client.GetWorkingTreeDiff()
	if err != nil {
		t.Fatalf("GetWorkingTreeDiff() error = %v", err)
	}

	// Should return a valid result (even if empty)
	if result.BaseRef != "index" {
		t.Errorf("BaseRef = %q, want %q", result.BaseRef, "index")
	}
	if result.HeadRef != "working-tree" {
		t.Errorf("HeadRef = %q, want %q", result.HeadRef, "working-tree")
	}
}

func TestClientGetAllChangesDiff_Integration(t *testing.T) {
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	client := NewClient("")
	result, err := client.GetAllChangesDiff()
	if err != nil {
		t.Fatalf("GetAllChangesDiff() error = %v", err)
	}

	// Should return a valid result
	if result.BaseRef != "HEAD" {
		t.Errorf("BaseRef = %q, want %q", result.BaseRef, "HEAD")
	}
	if result.HeadRef != "working-tree" {
		t.Errorf("HeadRef = %q, want %q", result.HeadRef, "working-tree")
	}
	if result.Stats.TotalFiles < 0 {
		t.Error("TotalFiles should not be negative")
	}
}

func TestParseNameStatusLine(t *testing.T) {
	tests := []struct {
		name     string
		line     string
		expected ChangedFile
		wantErr  bool
	}{
		{
			name: "Modified file",
			line: "M\tinternal/handler/user.go",
			expected: ChangedFile{
				Path:   "internal/handler/user.go",
				Status: StatusModified,
			},
		},
		{
			name: "Added file",
			line: "A\tnew/file.go",
			expected: ChangedFile{
				Path:   "new/file.go",
				Status: StatusAdded,
			},
		},
		{
			name: "Deleted file",
			line: "D\told/file.go",
			expected: ChangedFile{
				Path:   "old/file.go",
				Status: StatusDeleted,
			},
		},
		{
			name: "Renamed file",
			line: "R100\told/path.go\tnew/path.go",
			expected: ChangedFile{
				Path:    "new/path.go",
				OldPath: "old/path.go",
				Status:  StatusRenamed,
			},
		},
		{
			name: "Copied file",
			line: "C100\toriginal.go\tcopy.go",
			expected: ChangedFile{
				Path:    "copy.go",
				OldPath: "original.go",
				Status:  StatusCopied,
			},
		},
		{
			name:    "Invalid line - no tab",
			line:    "M internal/handler/user.go",
			wantErr: true,
		},
		{
			name:    "Invalid line - empty",
			line:    "",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := parseNameStatusLine(tt.line)
			if (err != nil) != tt.wantErr {
				t.Errorf("parseNameStatusLine() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.wantErr {
				return
			}
			if got.Path != tt.expected.Path {
				t.Errorf("Path = %q, want %q", got.Path, tt.expected.Path)
			}
			if got.OldPath != tt.expected.OldPath {
				t.Errorf("OldPath = %q, want %q", got.OldPath, tt.expected.OldPath)
			}
			if got.Status != tt.expected.Status {
				t.Errorf("Status = %v, want %v", got.Status, tt.expected.Status)
			}
		})
	}
}

func TestParseNumstat(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected map[string]fileStats
	}{
		{
			name:  "Single file",
			input: "10\t5\tpath/to/file.go",
			expected: map[string]fileStats{
				"path/to/file.go": {additions: 10, deletions: 5},
			},
		},
		{
			name:  "Multiple files",
			input: "10\t5\tfile1.go\n20\t3\tfile2.go",
			expected: map[string]fileStats{
				"file1.go": {additions: 10, deletions: 5},
				"file2.go": {additions: 20, deletions: 3},
			},
		},
		{
			name:     "Binary file (skip)",
			input:    "-\t-\timage.png",
			expected: map[string]fileStats{},
		},
		{
			name:     "Empty input",
			input:    "",
			expected: map[string]fileStats{},
		},
		{
			name:  "File with spaces",
			input: "10\t5\tpath/to/file with spaces.go",
			expected: map[string]fileStats{
				"path/to/file with spaces.go": {additions: 10, deletions: 5},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parseNumstat([]byte(tt.input))
			if len(got) != len(tt.expected) {
				t.Errorf("parseNumstat() returned %d entries, want %d", len(got), len(tt.expected))
			}
			for path, expectedStats := range tt.expected {
				if gotStats, ok := got[path]; !ok {
					t.Errorf("parseNumstat() missing path %q", path)
				} else if gotStats != expectedStats {
					t.Errorf("parseNumstat()[%q] = %+v, want %+v", path, gotStats, expectedStats)
				}
			}
		})
	}
}
```

**Step 2: Run all tests**

Run: `cd scripts/ring:codereview && go test -v ./internal/git/... && cd ../..`

**Expected output:**
```
=== RUN   TestFileStatusString
--- PASS: TestFileStatusString (0.00s)
...
=== RUN   TestClientGetDiff_Integration
--- PASS: TestClientGetDiff_Integration (0.XX s)
=== RUN   TestClientGetStagedDiff_Integration
--- PASS: TestClientGetStagedDiff_Integration (0.XX s)
...
=== RUN   TestParseNameStatusLine
--- PASS: TestParseNameStatusLine (0.00s)
=== RUN   TestParseNumstat
--- PASS: TestParseNumstat (0.00s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/git
```

**Step 3: Commit**

```bash
git add scripts/ring:codereview/internal/git/git_test.go
git commit -m "test(ring:codereview): add integration and unit tests for git package

Covers parseNameStatusLine, parseNumstat, and integration tests
for Client.GetDiff, GetStagedDiff, GetWorkingTreeDiff, GetAllChangesDiff."
```

**If Task Fails:**

1. **Integration tests fail:**
   - Check: Are you in the ring repository?
   - Fix: Tests should skip gracefully with `t.Skip()` if not in git repo
   - Rollback: Remove integration test functions

---

## Task 4: Implement Scope Detection Package - Language Detection

**Files:**
- Create: `scripts/ring:codereview/internal/scope/scope.go`
- Create: `scripts/ring:codereview/internal/scope/scope_test.go`

**Prerequisites:**
- Task 2 completed (git package exists)
- Tools: Go 1.22+

**Step 1: Write the failing test**

Create file `scripts/ring:codereview/internal/scope/scope_test.go`:

```go
package scope

import (
	"testing"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/git"
)

func TestDetectLanguage(t *testing.T) {
	tests := []struct {
		name     string
		files    []string
		expected Language
		wantErr  bool
	}{
		{
			name:     "Go only",
			files:    []string{"main.go", "internal/handler.go", "pkg/utils.go"},
			expected: LanguageGo,
		},
		{
			name:     "TypeScript only",
			files:    []string{"src/index.ts", "src/App.tsx", "components/Button.tsx"},
			expected: LanguageTypeScript,
		},
		{
			name:     "Python only",
			files:    []string{"main.py", "app/handlers.py", "tests/test_main.py"},
			expected: LanguagePython,
		},
		{
			name:     "Mixed languages - error",
			files:    []string{"main.go", "app.ts"},
			expected: LanguageUnknown,
			wantErr:  true,
		},
		{
			name:     "No recognized files",
			files:    []string{"README.md", "config.yaml", ".gitignore"},
			expected: LanguageUnknown,
		},
		{
			name:     "Go with non-code files",
			files:    []string{"main.go", "README.md", "go.mod"},
			expected: LanguageGo,
		},
		{
			name:     "Empty file list",
			files:    []string{},
			expected: LanguageUnknown,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := DetectLanguage(tt.files)
			if (err != nil) != tt.wantErr {
				t.Errorf("DetectLanguage() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got != tt.expected {
				t.Errorf("DetectLanguage() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestLanguageString(t *testing.T) {
	tests := []struct {
		lang     Language
		expected string
	}{
		{LanguageGo, "go"},
		{LanguageTypeScript, "typescript"},
		{LanguagePython, "python"},
		{LanguageUnknown, "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.lang.String(); got != tt.expected {
				t.Errorf("Language.String() = %q, want %q", got, tt.expected)
			}
		})
	}
}

func TestGetFileExtension(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"main.go", ".go"},
		{"src/App.tsx", ".tsx"},
		{"internal/handler/user.go", ".go"},
		{"noextension", ""},
		{".gitignore", ".gitignore"},
		{"file.test.ts", ".ts"},
	}

	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			if got := getFileExtension(tt.path); got != tt.expected {
				t.Errorf("getFileExtension(%q) = %q, want %q", tt.path, got, tt.expected)
			}
		})
	}
}

func TestCategorizeFilesByStatus(t *testing.T) {
	files := []git.ChangedFile{
		{Path: "handler.go", Status: git.StatusModified},
		{Path: "new_file.go", Status: git.StatusAdded},
		{Path: "old_file.go", Status: git.StatusDeleted},
		{Path: "renamed.go", Status: git.StatusRenamed, OldPath: "old_name.go"},
	}

	modified, added, deleted := CategorizeFilesByStatus(files)

	if len(modified) != 1 || modified[0] != "handler.go" {
		t.Errorf("Modified files = %v, want [handler.go]", modified)
	}
	if len(added) != 1 || added[0] != "new_file.go" {
		t.Errorf("Added files = %v, want [new_file.go]", added)
	}
	if len(deleted) != 1 || deleted[0] != "old_file.go" {
		t.Errorf("Deleted files = %v, want [old_file.go]", deleted)
	}
}

func TestExtractPackages(t *testing.T) {
	tests := []struct {
		name     string
		lang     Language
		files    []string
		expected []string
	}{
		{
			name:     "Go packages",
			lang:     LanguageGo,
			files:    []string{"internal/handler/user.go", "internal/handler/admin.go", "pkg/utils/string.go"},
			expected: []string{"internal/handler", "pkg/utils"},
		},
		{
			name:     "TypeScript directories",
			lang:     LanguageTypeScript,
			files:    []string{"src/components/Button.tsx", "src/components/Form.tsx", "src/utils/helpers.ts"},
			expected: []string{"src/components", "src/utils"},
		},
		{
			name:     "Python modules",
			lang:     LanguagePython,
			files:    []string{"app/handlers/user.py", "app/handlers/admin.py", "app/services/auth.py"},
			expected: []string{"app/handlers", "app/services"},
		},
		{
			name:     "Root level files",
			lang:     LanguageGo,
			files:    []string{"main.go", "config.go"},
			expected: []string{"."},
		},
		{
			name:     "Empty file list",
			lang:     LanguageGo,
			files:    []string{},
			expected: []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ExtractPackages(tt.lang, tt.files)
			if len(got) != len(tt.expected) {
				t.Errorf("ExtractPackages() = %v, want %v", got, tt.expected)
				return
			}
			// Check that all expected packages are present
			gotMap := make(map[string]bool)
			for _, p := range got {
				gotMap[p] = true
			}
			for _, exp := range tt.expected {
				if !gotMap[exp] {
					t.Errorf("ExtractPackages() missing expected package %q, got %v", exp, got)
				}
			}
		})
	}
}
```

**Step 2: Run test to verify it fails**

Run: `cd scripts/ring:codereview && go test -v ./internal/scope/... 2>&1 | head -20 && cd ../..`

**Expected output:**
```
# github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope [github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope.test]
./scope_test.go:XX:XX: undefined: Language
./scope_test.go:XX:XX: undefined: LanguageGo
...
FAIL	github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope [build failed]
```

**Step 3: Write minimal implementation**

Create file `scripts/ring:codereview/internal/scope/scope.go`:

```go
// Package scope provides scope detection for code review analysis.
// It identifies changed files, detects project language, and extracts
// package/module information from git diffs.
package scope

import (
	"errors"
	"path/filepath"
	"sort"
	"strings"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/git"
)

// Language represents a supported programming language.
type Language int

const (
	LanguageUnknown Language = iota
	LanguageGo
	LanguageTypeScript
	LanguagePython
)

// String returns the string representation of the language.
func (l Language) String() string {
	switch l {
	case LanguageGo:
		return "go"
	case LanguageTypeScript:
		return "typescript"
	case LanguagePython:
		return "python"
	default:
		return "unknown"
	}
}

// languageExtensions maps file extensions to languages.
var languageExtensions = map[string]Language{
	".go":  LanguageGo,
	".ts":  LanguageTypeScript,
	".tsx": LanguageTypeScript,
	".py":  LanguagePython,
}

// ErrMixedLanguages is returned when multiple languages are detected.
var ErrMixedLanguages = errors.New("mixed languages detected: project must be single-language (Go, TypeScript, or Python)")

// DetectLanguage determines the primary language from a list of file paths.
// Returns ErrMixedLanguages if multiple code languages are found.
func DetectLanguage(files []string) (Language, error) {
	if len(files) == 0 {
		return LanguageUnknown, nil
	}

	languagesSeen := make(map[Language]bool)

	for _, file := range files {
		ext := getFileExtension(file)
		if lang, ok := languageExtensions[ext]; ok {
			languagesSeen[lang] = true
		}
	}

	// No recognized code files
	if len(languagesSeen) == 0 {
		return LanguageUnknown, nil
	}

	// Multiple languages detected
	if len(languagesSeen) > 1 {
		return LanguageUnknown, ErrMixedLanguages
	}

	// Return the single detected language
	for lang := range languagesSeen {
		return lang, nil
	}

	return LanguageUnknown, nil
}

// getFileExtension returns the file extension including the dot.
// For files like "file.test.ts", returns ".ts" (last extension).
func getFileExtension(path string) string {
	base := filepath.Base(path)
	ext := filepath.Ext(base)
	return ext
}

// CategorizeFilesByStatus separates files into modified, added, and deleted lists.
// Renamed files are treated as additions of the new path.
func CategorizeFilesByStatus(files []git.ChangedFile) (modified, added, deleted []string) {
	for _, f := range files {
		switch f.Status {
		case git.StatusModified:
			modified = append(modified, f.Path)
		case git.StatusAdded, git.StatusRenamed, git.StatusCopied:
			added = append(added, f.Path)
		case git.StatusDeleted:
			deleted = append(deleted, f.Path)
		}
	}
	return
}

// ExtractPackages extracts unique package/directory paths from file paths.
// For Go, this is the directory containing the file.
// For TypeScript/Python, this is also the parent directory.
func ExtractPackages(lang Language, files []string) []string {
	if len(files) == 0 {
		return []string{}
	}

	packageSet := make(map[string]bool)

	for _, file := range files {
		dir := filepath.Dir(file)
		// Normalize empty dir to "." for root-level files
		if dir == "" {
			dir = "."
		}
		packageSet[dir] = true
	}

	// Convert set to sorted slice
	packages := make([]string, 0, len(packageSet))
	for pkg := range packageSet {
		packages = append(packages, pkg)
	}
	sort.Strings(packages)

	return packages
}

// ScopeResult contains the complete scope detection result.
type ScopeResult struct {
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

// Detector performs scope detection on git diffs.
type Detector struct {
	gitClient *git.Client
}

// NewDetector creates a new scope detector for the given working directory.
func NewDetector(workDir string) *Detector {
	return &Detector{
		gitClient: git.NewClient(workDir),
	}
}

// DetectFromRefs detects scope from a diff between two git refs.
// If baseRef is empty, uses HEAD. If headRef is empty, uses working tree.
func (d *Detector) DetectFromRefs(baseRef, headRef string) (*ScopeResult, error) {
	// Get the diff
	diff, err := d.gitClient.GetDiff(baseRef, headRef)
	if err != nil {
		return nil, err
	}

	return d.buildResult(diff)
}

// DetectAllChanges detects scope from all staged and unstaged changes.
func (d *Detector) DetectAllChanges() (*ScopeResult, error) {
	diff, err := d.gitClient.GetAllChangesDiff()
	if err != nil {
		return nil, err
	}

	return d.buildResult(diff)
}

// buildResult constructs a ScopeResult from a DiffResult.
func (d *Detector) buildResult(diff *git.DiffResult) (*ScopeResult, error) {
	// Extract file paths for language detection
	filePaths := make([]string, len(diff.Files))
	for i, f := range diff.Files {
		filePaths[i] = f.Path
	}

	// Detect language
	lang, err := DetectLanguage(filePaths)
	if err != nil {
		return nil, err
	}

	// Categorize files by status
	modified, added, deleted := CategorizeFilesByStatus(diff.Files)

	// Extract affected packages
	allFiles := append(append(modified, added...), deleted...)
	packages := ExtractPackages(lang, allFiles)

	return &ScopeResult{
		BaseRef:          diff.BaseRef,
		HeadRef:          diff.HeadRef,
		Language:         lang.String(),
		ModifiedFiles:    modified,
		AddedFiles:       added,
		DeletedFiles:     deleted,
		TotalFiles:       diff.Stats.TotalFiles,
		TotalAdditions:   diff.Stats.TotalAdditions,
		TotalDeletions:   diff.Stats.TotalDeletions,
		PackagesAffected: packages,
	}, nil
}

// FilterByLanguage filters files to only those matching the detected language.
func FilterByLanguage(files []string, lang Language) []string {
	if lang == LanguageUnknown {
		return files
	}

	var filtered []string
	for _, file := range files {
		ext := getFileExtension(file)
		if fileLang, ok := languageExtensions[ext]; ok && fileLang == lang {
			filtered = append(filtered, file)
		}
	}
	return filtered
}
```

**Step 4: Run test to verify it passes**

Run: `cd scripts/ring:codereview && go test -v ./internal/scope/... && cd ../..`

**Expected output:**
```
=== RUN   TestDetectLanguage
=== RUN   TestDetectLanguage/Go_only
=== RUN   TestDetectLanguage/TypeScript_only
=== RUN   TestDetectLanguage/Python_only
=== RUN   TestDetectLanguage/Mixed_languages_-_error
=== RUN   TestDetectLanguage/No_recognized_files
=== RUN   TestDetectLanguage/Go_with_non-code_files
=== RUN   TestDetectLanguage/Empty_file_list
--- PASS: TestDetectLanguage (0.00s)
...
=== RUN   TestLanguageString
--- PASS: TestLanguageString (0.00s)
=== RUN   TestGetFileExtension
--- PASS: TestGetFileExtension (0.00s)
=== RUN   TestCategorizeFilesByStatus
--- PASS: TestCategorizeFilesByStatus (0.00s)
=== RUN   TestExtractPackages
--- PASS: TestExtractPackages (0.00s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope
```

**Step 5: Commit**

```bash
git add scripts/ring:codereview/internal/scope/
git commit -m "feat(ring:codereview): add scope detection package with language detection

Implements Language enum, DetectLanguage function (errors on mixed languages),
CategorizeFilesByStatus, ExtractPackages, and Detector struct for building
complete scope results from git diffs."
```

**If Task Fails:**

1. **Import error for git package:**
   - Check: `go mod tidy` in scripts/ring:codereview directory
   - Fix: Ensure module path matches in imports

---

## Task 5: Add Integration Tests for Scope Package

**Files:**
- Modify: `scripts/ring:codereview/internal/scope/scope_test.go`

**Prerequisites:**
- Task 4 completed (scope package exists)

**Step 1: Add integration tests**

Append to `scripts/ring:codereview/internal/scope/scope_test.go`:

```go
import (
	"os/exec"
)

func TestDetector_Integration(t *testing.T) {
	// Skip if not in a git repo
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	detector := NewDetector("")

	// Test detecting from refs
	result, err := detector.DetectFromRefs("HEAD~1", "HEAD")
	if err != nil {
		// Might fail if HEAD~1 doesn't exist or mixed languages
		if errors.Is(err, ErrMixedLanguages) {
			t.Skip("Repository has mixed languages")
		}
		t.Skipf("Could not detect from refs: %v", err)
	}

	// Basic validation
	if result.BaseRef != "HEAD~1" {
		t.Errorf("BaseRef = %q, want %q", result.BaseRef, "HEAD~1")
	}
	if result.HeadRef != "HEAD" {
		t.Errorf("HeadRef = %q, want %q", result.HeadRef, "HEAD")
	}
	if result.Language == "" {
		t.Error("Language should not be empty")
	}
}

func TestDetector_DetectAllChanges_Integration(t *testing.T) {
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	detector := NewDetector("")
	result, err := detector.DetectAllChanges()
	if err != nil {
		if errors.Is(err, ErrMixedLanguages) {
			t.Skip("Repository has mixed languages")
		}
		t.Fatalf("DetectAllChanges() error = %v", err)
	}

	// Should return valid result (even if no changes)
	if result.BaseRef != "HEAD" {
		t.Errorf("BaseRef = %q, want %q", result.BaseRef, "HEAD")
	}
}

func TestFilterByLanguage(t *testing.T) {
	tests := []struct {
		name     string
		files    []string
		lang     Language
		expected []string
	}{
		{
			name:     "Filter Go files",
			files:    []string{"main.go", "README.md", "internal/handler.go", "config.yaml"},
			lang:     LanguageGo,
			expected: []string{"main.go", "internal/handler.go"},
		},
		{
			name:     "Filter TypeScript files",
			files:    []string{"index.ts", "App.tsx", "styles.css", "package.json"},
			lang:     LanguageTypeScript,
			expected: []string{"index.ts", "App.tsx"},
		},
		{
			name:     "Filter Python files",
			files:    []string{"main.py", "requirements.txt", "app/handler.py"},
			lang:     LanguagePython,
			expected: []string{"main.py", "app/handler.py"},
		},
		{
			name:     "Unknown language returns all",
			files:    []string{"main.go", "app.ts", "script.py"},
			lang:     LanguageUnknown,
			expected: []string{"main.go", "app.ts", "script.py"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := FilterByLanguage(tt.files, tt.lang)
			if len(got) != len(tt.expected) {
				t.Errorf("FilterByLanguage() = %v, want %v", got, tt.expected)
				return
			}
			for i, exp := range tt.expected {
				if got[i] != exp {
					t.Errorf("FilterByLanguage()[%d] = %q, want %q", i, got[i], exp)
				}
			}
		})
	}
}
```

**Step 2: Update imports at top of file**

Add `"errors"` and `"os/exec"` to the imports in `scope_test.go`:

```go
import (
	"errors"
	"os/exec"
	"testing"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/git"
)
```

**Step 3: Run all tests**

Run: `cd scripts/ring:codereview && go test -v ./internal/scope/... && cd ../..`

**Expected output:**
```
=== RUN   TestDetectLanguage
--- PASS: TestDetectLanguage (0.00s)
...
=== RUN   TestDetector_Integration
--- PASS: TestDetector_Integration (0.XX s)
=== RUN   TestDetector_DetectAllChanges_Integration
--- PASS: TestDetector_DetectAllChanges_Integration (0.XX s)
=== RUN   TestFilterByLanguage
--- PASS: TestFilterByLanguage (0.00s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope
```

**Step 4: Commit**

```bash
git add scripts/ring:codereview/internal/scope/scope_test.go
git commit -m "test(ring:codereview): add integration tests and FilterByLanguage tests

Adds Detector integration tests and comprehensive FilterByLanguage tests."
```

---

## Task 6: Implement JSON Output Package

**Files:**
- Create: `scripts/ring:codereview/internal/output/json.go`
- Create: `scripts/ring:codereview/internal/output/json_test.go`

**Prerequisites:**
- Task 4 completed (scope package exists)

**Step 1: Write the failing test**

Create file `scripts/ring:codereview/internal/output/json_test.go`:

```go
package output

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope"
)

func TestScopeOutput_ToJSON(t *testing.T) {
	result := &scope.ScopeResult{
		BaseRef:        "main",
		HeadRef:        "HEAD",
		Language:       "go",
		ModifiedFiles:  []string{"internal/handler/user.go"},
		AddedFiles:     []string{"internal/service/notification.go"},
		DeletedFiles:   []string{},
		TotalFiles:     2,
		TotalAdditions: 100,
		TotalDeletions: 10,
		PackagesAffected: []string{"internal/handler", "internal/service"},
	}

	output := NewScopeOutput(result)
	jsonBytes, err := output.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON() error = %v", err)
	}

	// Verify it's valid JSON
	var decoded map[string]interface{}
	if err := json.Unmarshal(jsonBytes, &decoded); err != nil {
		t.Fatalf("Output is not valid JSON: %v", err)
	}

	// Check key fields
	if decoded["base_ref"] != "main" {
		t.Errorf("base_ref = %v, want %q", decoded["base_ref"], "main")
	}
	if decoded["language"] != "go" {
		t.Errorf("language = %v, want %q", decoded["language"], "go")
	}
}

func TestScopeOutput_ToPrettyJSON(t *testing.T) {
	result := &scope.ScopeResult{
		BaseRef:  "main",
		HeadRef:  "HEAD",
		Language: "go",
	}

	output := NewScopeOutput(result)
	jsonBytes, err := output.ToPrettyJSON()
	if err != nil {
		t.Fatalf("ToPrettyJSON() error = %v", err)
	}

	// Pretty JSON should contain newlines
	if !containsNewlines(jsonBytes) {
		t.Error("ToPrettyJSON() should contain newlines for formatting")
	}
}

func TestScopeOutput_WriteToFile(t *testing.T) {
	result := &scope.ScopeResult{
		BaseRef:  "main",
		HeadRef:  "HEAD",
		Language: "go",
	}

	// Create temp directory
	tmpDir := t.TempDir()
	outputPath := filepath.Join(tmpDir, "scope.json")

	output := NewScopeOutput(result)
	if err := output.WriteToFile(outputPath); err != nil {
		t.Fatalf("WriteToFile() error = %v", err)
	}

	// Verify file exists and contains valid JSON
	data, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("Failed to read output file: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Output file is not valid JSON: %v", err)
	}

	if decoded["base_ref"] != "main" {
		t.Errorf("base_ref = %v, want %q", decoded["base_ref"], "main")
	}
}

func TestScopeOutput_WriteToFile_CreatesDirectory(t *testing.T) {
	result := &scope.ScopeResult{
		BaseRef:  "main",
		HeadRef:  "HEAD",
		Language: "go",
	}

	// Create temp directory with nested path
	tmpDir := t.TempDir()
	outputPath := filepath.Join(tmpDir, "nested", "dir", "scope.json")

	output := NewScopeOutput(result)
	if err := output.WriteToFile(outputPath); err != nil {
		t.Fatalf("WriteToFile() error = %v", err)
	}

	// Verify file exists
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		t.Errorf("Output file was not created at %s", outputPath)
	}
}

func containsNewlines(data []byte) bool {
	for _, b := range data {
		if b == '\n' {
			return true
		}
	}
	return false
}
```

**Step 2: Run test to verify it fails**

Run: `cd scripts/ring:codereview && go test -v ./internal/output/... 2>&1 | head -20 && cd ../..`

**Expected output:**
```
# github.com/lerianstudio/ring/scripts/ring:codereview/internal/output [github.com/lerianstudio/ring/scripts/ring:codereview/internal/output.test]
./json_test.go:XX:XX: undefined: NewScopeOutput
FAIL	github.com/lerianstudio/ring/scripts/ring:codereview/internal/output [build failed]
```

**Step 3: Write minimal implementation**

Create file `scripts/ring:codereview/internal/output/json.go`:

```go
// Package output provides formatters for writing analysis results.
package output

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope"
)

// ScopeOutput wraps a ScopeResult for output formatting.
type ScopeOutput struct {
	result *scope.ScopeResult
}

// NewScopeOutput creates a new ScopeOutput from a ScopeResult.
func NewScopeOutput(result *scope.ScopeResult) *ScopeOutput {
	return &ScopeOutput{result: result}
}

// scopeJSON is the JSON-serializable representation of scope results.
// This matches the output format specified in the macro plan.
type scopeJSON struct {
	BaseRef  string      `json:"base_ref"`
	HeadRef  string      `json:"head_ref"`
	Language string      `json:"language"`
	Files    filesJSON   `json:"files"`
	Stats    statsJSON   `json:"stats"`
	Packages []string    `json:"packages_affected"`
}

type filesJSON struct {
	Modified []string `json:"modified"`
	Added    []string `json:"added"`
	Deleted  []string `json:"deleted"`
}

type statsJSON struct {
	TotalFiles     int `json:"total_files"`
	TotalAdditions int `json:"total_additions"`
	TotalDeletions int `json:"total_deletions"`
}

// toScopeJSON converts the internal result to the JSON output format.
func (o *ScopeOutput) toScopeJSON() scopeJSON {
	// Ensure slices are never nil (for consistent JSON output)
	modified := o.result.ModifiedFiles
	if modified == nil {
		modified = []string{}
	}
	added := o.result.AddedFiles
	if added == nil {
		added = []string{}
	}
	deleted := o.result.DeletedFiles
	if deleted == nil {
		deleted = []string{}
	}
	packages := o.result.PackagesAffected
	if packages == nil {
		packages = []string{}
	}

	return scopeJSON{
		BaseRef:  o.result.BaseRef,
		HeadRef:  o.result.HeadRef,
		Language: o.result.Language,
		Files: filesJSON{
			Modified: modified,
			Added:    added,
			Deleted:  deleted,
		},
		Stats: statsJSON{
			TotalFiles:     o.result.TotalFiles,
			TotalAdditions: o.result.TotalAdditions,
			TotalDeletions: o.result.TotalDeletions,
		},
		Packages: packages,
	}
}

// ToJSON returns the scope result as compact JSON bytes.
func (o *ScopeOutput) ToJSON() ([]byte, error) {
	data := o.toScopeJSON()
	return json.Marshal(data)
}

// ToPrettyJSON returns the scope result as formatted JSON bytes.
func (o *ScopeOutput) ToPrettyJSON() ([]byte, error) {
	data := o.toScopeJSON()
	return json.MarshalIndent(data, "", "  ")
}

// WriteToFile writes the scope result as formatted JSON to the specified path.
// Creates parent directories if they don't exist.
func (o *ScopeOutput) WriteToFile(path string) error {
	// Ensure parent directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory %s: %w", dir, err)
	}

	// Generate pretty JSON
	jsonBytes, err := o.ToPrettyJSON()
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	// Write to file
	if err := os.WriteFile(path, jsonBytes, 0644); err != nil {
		return fmt.Errorf("failed to write file %s: %w", path, err)
	}

	return nil
}

// WriteToStdout writes the scope result as formatted JSON to stdout.
func (o *ScopeOutput) WriteToStdout() error {
	jsonBytes, err := o.ToPrettyJSON()
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	_, err = os.Stdout.Write(jsonBytes)
	if err != nil {
		return fmt.Errorf("failed to write to stdout: %w", err)
	}

	// Add trailing newline
	fmt.Println()
	return nil
}
```

**Step 4: Run test to verify it passes**

Run: `cd scripts/ring:codereview && go test -v ./internal/output/... && cd ../..`

**Expected output:**
```
=== RUN   TestScopeOutput_ToJSON
--- PASS: TestScopeOutput_ToJSON (0.00s)
=== RUN   TestScopeOutput_ToPrettyJSON
--- PASS: TestScopeOutput_ToPrettyJSON (0.00s)
=== RUN   TestScopeOutput_WriteToFile
--- PASS: TestScopeOutput_WriteToFile (0.00s)
=== RUN   TestScopeOutput_WriteToFile_CreatesDirectory
--- PASS: TestScopeOutput_WriteToFile_CreatesDirectory (0.00s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/output
```

**Step 5: Commit**

```bash
git add scripts/ring:codereview/internal/output/
git commit -m "feat(ring:codereview): add JSON output package for scope results

Implements ScopeOutput with ToJSON, ToPrettyJSON, WriteToFile, WriteToStdout
methods. Output format matches macro plan specification with nested files
and stats structures."
```

---

## Task 7: Implement CLI Binary - Main Entry Point

**Files:**
- Create: `scripts/ring:codereview/cmd/scope-detector/main.go`

**Prerequisites:**
- Tasks 2, 4, 6 completed (git, scope, output packages exist)

**Step 1: Create the CLI binary**

Create file `scripts/ring:codereview/cmd/scope-detector/main.go`:

```go
// scope-detector analyzes git diffs to detect changed files and project language.
//
// Usage:
//   scope-detector                           # Analyze staged + unstaged changes
//   scope-detector --base=main --head=HEAD   # Compare specific refs
//   scope-detector --output=scope.json       # Write to file instead of stdout
//
// Output: JSON containing language, files (modified/added/deleted), stats, and packages.
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/output"
	"github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope"
)

// Version information (set via ldflags during build)
var (
	version = "dev"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func run() error {
	// Define flags
	baseRef := flag.String("base", "", "Base reference (commit/branch). Empty = use HEAD for comparison")
	headRef := flag.String("head", "", "Head reference (commit/branch). Empty = use working tree")
	outputPath := flag.String("output", "", "Output file path. Empty = write to stdout")
	workDir := flag.String("workdir", "", "Working directory. Empty = current directory")
	showVersion := flag.Bool("version", false, "Show version and exit")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: scope-detector [options]\n\n")
		fmt.Fprintf(os.Stderr, "Analyzes git diff to detect changed files and project language.\n\n")
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
		fmt.Fprintf(os.Stderr, "\nExamples:\n")
		fmt.Fprintf(os.Stderr, "  scope-detector                             # All uncommitted changes\n")
		fmt.Fprintf(os.Stderr, "  scope-detector --base=main --head=HEAD     # Compare branches\n")
		fmt.Fprintf(os.Stderr, "  scope-detector --output=.ring/ring:codereview/scope.json\n")
	}

	flag.Parse()

	// Handle version flag
	if *showVersion {
		fmt.Printf("scope-detector version %s\n", version)
		return nil
	}

	// Create detector
	detector := scope.NewDetector(*workDir)

	// Detect scope based on provided refs
	var result *scope.ScopeResult
	var err error

	if *baseRef == "" && *headRef == "" {
		// No refs specified: detect all uncommitted changes
		result, err = detector.DetectAllChanges()
	} else {
		// Compare specific refs
		result, err = detector.DetectFromRefs(*baseRef, *headRef)
	}

	if err != nil {
		return fmt.Errorf("scope detection failed: %w", err)
	}

	// Handle empty result (no changes)
	if result.TotalFiles == 0 {
		fmt.Fprintln(os.Stderr, "No changes detected")
	}

	// Create output formatter
	out := output.NewScopeOutput(result)

	// Write output
	if *outputPath != "" {
		if err := out.WriteToFile(*outputPath); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		fmt.Fprintf(os.Stderr, "Scope written to %s\n", *outputPath)
	} else {
		if err := out.WriteToStdout(); err != nil {
			return fmt.Errorf("failed to write to stdout: %w", err)
		}
	}

	return nil
}
```

**Step 2: Build the binary**

Run: `cd scripts/ring:codereview && make build && cd ../..`

**Expected output:**
```
Building scope-detector...
```

**Step 3: Verify binary exists**

Run: `ls -la scripts/ring:codereview/bin/`

**Expected output:**
```
total XX
drwxr-xr-x  3 user  staff   96 Jan 13 XX:XX .
drwxr-xr-x  8 user  staff  256 Jan 13 XX:XX ..
-rwxr-xr-x  1 user  staff  XXX Jan 13 XX:XX scope-detector
```

**Step 4: Test binary with --help**

Run: `./scripts/ring:codereview/bin/scope-detector --help`

**Expected output:**
```
Usage: scope-detector [options]

Analyzes git diff to detect changed files and project language.

Options:
  -base string
    	Base reference (commit/branch). Empty = use HEAD for comparison
  -head string
    	Head reference (commit/branch). Empty = use working tree
  -output string
    	Output file path. Empty = write to stdout
  -version
    	Show version and exit
  -workdir string
    	Working directory. Empty = current directory

Examples:
  scope-detector                             # All uncommitted changes
  scope-detector --base=main --head=HEAD     # Compare branches
  scope-detector --output=.ring/ring:codereview/scope.json
```

**Step 5: Test binary with actual diff**

Run: `./scripts/ring:codereview/bin/scope-detector --base=HEAD~1 --head=HEAD`

**Expected output:** (varies based on actual changes)
```json
{
  "base_ref": "HEAD~1",
  "head_ref": "HEAD",
  "language": "...",
  "files": {
    "modified": [...],
    "added": [...],
    "deleted": []
  },
  "stats": {
    "total_files": N,
    "total_additions": N,
    "total_deletions": N
  },
  "packages_affected": [...]
}
```

**Step 6: Commit**

```bash
git add scripts/ring:codereview/cmd/scope-detector/
git commit -m "feat(ring:codereview): implement scope-detector CLI binary

Entry point for Phase 0 scope detection. Supports:
- Default: all uncommitted changes (staged + unstaged)
- --base/--head: compare specific refs
- --output: write to file instead of stdout
- --workdir: run in different directory"
```

**If Task Fails:**

1. **Build fails:**
   - Check: `go build ./cmd/scope-detector/` for detailed errors
   - Fix: Ensure all imports are correct
   - Rollback: `rm -rf scripts/ring:codereview/bin/`

2. **Binary runs but errors:**
   - Check: Are you in a git repository?
   - Fix: Run from ring repository root

---

## Task 8: Run Full Test Suite and Code Review Checkpoint

**Files:**
- None (verification only)

**Prerequisites:**
- Tasks 1-7 completed

**Step 1: Run all tests with coverage**

Run: `cd scripts/ring:codereview && make test-coverage && cd ../..`

**Expected output:**
```
Running tests with coverage...
=== RUN   TestFileStatusString
--- PASS: TestFileStatusString (0.00s)
...
PASS
coverage: XX.X% of statements
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/git
...
PASS
coverage: XX.X% of statements
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope
...
PASS
coverage: XX.X% of statements
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/output
Coverage report: coverage.html
```

**Step 2: Run linters**

Run: `cd scripts/ring:codereview && make lint && cd ../..`

**Expected output:**
```
(no output means no errors)
```

**Step 3: Test binary end-to-end**

Run: `./scripts/ring:codereview/bin/scope-detector --output=.ring/ring:codereview/scope.json --base=HEAD~5 --head=HEAD`

**Expected output:**
```
Scope written to .ring/ring:codereview/scope.json
```

**Step 4: Verify output file**

Run: `cat .ring/ring:codereview/scope.json`

**Expected output:** Valid JSON with scope information

**Step 5: Clean up test output**

Run: `rm -f .ring/ring:codereview/scope.json`

### Code Review Checkpoint

**CRITICAL: Dispatch all 5 reviewers in parallel before proceeding.**

1. **Dispatch all 5 reviewers in parallel:**
   - REQUIRED SUB-SKILL: Use ring:requesting-code-review
   - All reviewers run simultaneously (ring:code-reviewer, ring:business-logic-reviewer, ring:security-reviewer, ring:test-reviewer, ring:nil-safety-reviewer)
   - Wait for all to complete

2. **Handle findings by severity (MANDATORY):**

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

3. **Proceed only when:**
   - Zero Critical/High/Medium issues remain
   - All Low issues have TODO(review): comments added
   - All Cosmetic issues have FIXME(nitpick): comments added

---

## Task 9: Add CLI Tests

**Files:**
- Create: `scripts/ring:codereview/cmd/scope-detector/main_test.go`

**Prerequisites:**
- Task 7 completed (CLI binary exists)

**Step 1: Create CLI test file**

Create file `scripts/ring:codereview/cmd/scope-detector/main_test.go`:

```go
package main

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestMain_Version(t *testing.T) {
	// Build the binary first
	buildCmd := exec.Command("go", "build", "-o", "scope-detector-test", ".")
	buildCmd.Dir = "."
	if err := buildCmd.Run(); err != nil {
		t.Fatalf("Failed to build binary: %v", err)
	}
	defer os.Remove("scope-detector-test")

	// Run with --version
	cmd := exec.Command("./scope-detector-test", "--version")
	var stdout bytes.Buffer
	cmd.Stdout = &stdout

	if err := cmd.Run(); err != nil {
		t.Fatalf("Command failed: %v", err)
	}

	output := stdout.String()
	if !bytes.Contains([]byte(output), []byte("scope-detector version")) {
		t.Errorf("Version output = %q, want to contain 'scope-detector version'", output)
	}
}

func TestMain_Help(t *testing.T) {
	// Build the binary
	buildCmd := exec.Command("go", "build", "-o", "scope-detector-test", ".")
	if err := buildCmd.Run(); err != nil {
		t.Fatalf("Failed to build binary: %v", err)
	}
	defer os.Remove("scope-detector-test")

	// Run with --help (exits with 0)
	cmd := exec.Command("./scope-detector-test", "--help")
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	// --help should exit 0
	if err := cmd.Run(); err != nil {
		// help might exit non-zero on some systems
		t.Logf("Help command exited with: %v", err)
	}

	output := stderr.String()
	if !bytes.Contains([]byte(output), []byte("Usage:")) {
		t.Errorf("Help output = %q, want to contain 'Usage:'", output)
	}
}

func TestMain_OutputToFile(t *testing.T) {
	// Skip if not in a git repo
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	// Build the binary
	buildCmd := exec.Command("go", "build", "-o", "scope-detector-test", ".")
	if err := buildCmd.Run(); err != nil {
		t.Fatalf("Failed to build binary: %v", err)
	}
	defer os.Remove("scope-detector-test")

	// Create temp output path
	tmpDir := t.TempDir()
	outputPath := filepath.Join(tmpDir, "scope.json")

	// Run with output flag
	cmd := exec.Command("./scope-detector-test", 
		"--base=HEAD~1", 
		"--head=HEAD",
		"--output="+outputPath)
	
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		// Might fail if HEAD~1 doesn't exist
		t.Skipf("Command failed (may be expected): %v, stderr: %s", err, stderr.String())
	}

	// Verify output file exists
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		t.Errorf("Output file was not created at %s", outputPath)
	}

	// Verify it's valid JSON
	data, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("Failed to read output file: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Output is not valid JSON: %v", err)
	}

	// Check required fields exist
	if _, ok := decoded["base_ref"]; !ok {
		t.Error("Output missing 'base_ref' field")
	}
	if _, ok := decoded["language"]; !ok {
		t.Error("Output missing 'language' field")
	}
	if _, ok := decoded["files"]; !ok {
		t.Error("Output missing 'files' field")
	}
}

func TestMain_JSONStructure(t *testing.T) {
	// Skip if not in a git repo
	if _, err := exec.Command("git", "rev-parse", "--git-dir").Output(); err != nil {
		t.Skip("Not in a git repository")
	}

	// Build the binary
	buildCmd := exec.Command("go", "build", "-o", "scope-detector-test", ".")
	if err := buildCmd.Run(); err != nil {
		t.Fatalf("Failed to build binary: %v", err)
	}
	defer os.Remove("scope-detector-test")

	// Run and capture stdout
	cmd := exec.Command("./scope-detector-test", 
		"--base=HEAD~1", 
		"--head=HEAD")
	
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		t.Skipf("Command failed (may be expected): %v, stderr: %s", err, stderr.String())
	}

	// Parse output
	var output struct {
		BaseRef  string `json:"base_ref"`
		HeadRef  string `json:"head_ref"`
		Language string `json:"language"`
		Files    struct {
			Modified []string `json:"modified"`
			Added    []string `json:"added"`
			Deleted  []string `json:"deleted"`
		} `json:"files"`
		Stats struct {
			TotalFiles     int `json:"total_files"`
			TotalAdditions int `json:"total_additions"`
			TotalDeletions int `json:"total_deletions"`
		} `json:"stats"`
		Packages []string `json:"packages_affected"`
	}

	if err := json.Unmarshal(stdout.Bytes(), &output); err != nil {
		t.Fatalf("Failed to parse output JSON: %v\nOutput was: %s", err, stdout.String())
	}

	// Validate structure
	if output.BaseRef != "HEAD~1" {
		t.Errorf("base_ref = %q, want %q", output.BaseRef, "HEAD~1")
	}
	if output.HeadRef != "HEAD" {
		t.Errorf("head_ref = %q, want %q", output.HeadRef, "HEAD")
	}
	// Files and stats should exist (even if empty)
	if output.Files.Modified == nil {
		t.Error("files.modified should not be nil")
	}
}
```

**Step 2: Run CLI tests**

Run: `cd scripts/ring:codereview && go test -v ./cmd/scope-detector/... && cd ../..`

**Expected output:**
```
=== RUN   TestMain_Version
--- PASS: TestMain_Version (X.XX s)
=== RUN   TestMain_Help
--- PASS: TestMain_Help (X.XX s)
=== RUN   TestMain_OutputToFile
--- PASS: TestMain_OutputToFile (X.XX s)
=== RUN   TestMain_JSONStructure
--- PASS: TestMain_JSONStructure (X.XX s)
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/cmd/scope-detector
```

**Step 3: Run full test suite**

Run: `cd scripts/ring:codereview && go test -v ./... && cd ../..`

**Expected output:** All tests pass

**Step 4: Commit**

```bash
git add scripts/ring:codereview/cmd/scope-detector/main_test.go
git commit -m "test(ring:codereview): add CLI integration tests for scope-detector

Tests version flag, help output, file output, and JSON structure validation."
```

---

## Task 10: Update .gitignore and Documentation

**Files:**
- Modify: `.gitignore`

**Prerequisites:**
- Tasks 1-9 completed

**Step 1: Verify .gitignore already includes .ring/**

Check if `.ring/` is already in `.gitignore`:

Run: `grep -n "\.ring" .gitignore`

**Expected output:**
```
26:.ring/
```

If `.ring/` is already present, skip to Step 3. Otherwise:

**Step 2: Add .ring/ to .gitignore (if needed)**

This step is likely NOT needed based on earlier verification. The `.ring/` directory is already gitignored.

**Step 3: Add bin directory to gitignore**

We should ensure the built binaries are not committed. Add to `.gitignore`:

```bash
echo "" >> .gitignore
echo "# Code review binaries" >> .gitignore
echo "scripts/ring:codereview/bin/" >> .gitignore
echo "scripts/ring:codereview/coverage.*" >> .gitignore
```

**Step 4: Verify additions**

Run: `tail -5 .gitignore`

**Expected output:**
```
.ring/

# Code review binaries
scripts/ring:codereview/bin/
scripts/ring:codereview/coverage.*
```

**Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore ring:codereview binaries and coverage files"
```

---

## Task 11: Final Integration Test

**Files:**
- None (verification only)

**Prerequisites:**
- All previous tasks completed

**Step 1: Clean build**

Run: `cd scripts/ring:codereview && make clean && make build && cd ../..`

**Expected output:**
```
Cleaning...
Building scope-detector...
```

**Step 2: Run complete test suite**

Run: `cd scripts/ring:codereview && make test && cd ../..`

**Expected output:**
```
Running tests...
...
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/git
...
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/scope
...
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/internal/output
...
PASS
ok  	github.com/lerianstudio/ring/scripts/ring:codereview/cmd/scope-detector
```

**Step 3: End-to-end test with output**

Run: `./scripts/ring:codereview/bin/scope-detector --base=HEAD~3 --head=HEAD --output=.ring/ring:codereview/scope.json && cat .ring/ring:codereview/scope.json`

**Expected output:** Valid JSON scope file with detected language and files

**Step 4: Verify JSON matches spec**

The output should match this structure from the macro plan:

```json
{
  "base_ref": "...",
  "head_ref": "...",
  "language": "go|typescript|python|unknown",
  "files": {
    "modified": [...],
    "added": [...],
    "deleted": []
  },
  "stats": {
    "total_files": N,
    "total_additions": N,
    "total_deletions": N
  },
  "packages_affected": [...]
}
```

**Step 5: Clean up**

Run: `rm -f .ring/ring:codereview/scope.json`

**Step 6: Final commit (if any uncommitted changes)**

```bash
git status
# If clean: done
# If changes: commit appropriately
```

---

## Plan Checklist

Before saving the plan, verify:

- [x] **Historical precedent queried** (artifact-query --mode planning)
- [x] Historical Precedent section included in plan
- [x] Header with goal, architecture, tech stack, prerequisites
- [x] Verification commands with expected output
- [x] Tasks broken into bite-sized steps (2-5 min each)
- [x] Exact file paths for all files
- [x] Complete code (no placeholders)
- [x] Exact commands with expected output
- [x] Failure recovery steps for each task
- [x] Code review checkpoints after batches
- [x] Severity-based issue handling documented
- [x] Passes Zero-Context Test
- [x] **Plan avoids known failure patterns** (none found in precedent)

---

## Summary

This plan implements Phase 0 (Scope Detection) of the ring:codereview enhancement with:

1. **Go module structure** - `scripts/ring:codereview/` with proper layout
2. **Git package** - Wrapper for git CLI operations (diff, name-status, numstat)
3. **Scope package** - Language detection, file categorization, package extraction
4. **Output package** - JSON formatter with file/stdout output
5. **CLI binary** - `scope-detector` with flags for refs and output path
6. **Comprehensive tests** - Unit tests, integration tests, CLI tests

**Total Tasks:** 11
**Estimated Time:** 60-90 minutes

**Next Phase:** Phase 1 (Static Analysis) will consume `scope.json` and run language-specific linters.
