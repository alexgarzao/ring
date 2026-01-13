// Package main provides the scope-detector CLI binary for code review scope analysis.
// It analyzes git diffs to detect changed files, determine project language,
// and output structured JSON for downstream code review tools.
package main

import (
	"errors"
	"flag"
	"fmt"
	"os"

	"github.com/lerianstudio/ring/scripts/codereview/internal/output"
	"github.com/lerianstudio/ring/scripts/codereview/internal/scope"
)

// version is set via ldflags during build.
var version = "dev"

func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

// config holds the parsed CLI configuration.
type config struct {
	baseRef     string
	headRef     string
	outputPath  string
	workDir     string
	showVersion bool
}

// parseFlags parses command-line flags and returns the configuration.
func parseFlags() *config {
	cfg := &config{}

	// TODO(review): Clarify help text - when both empty, DetectAllChanges() is used, not HEAD comparison (business-logic-reviewer, 2026-01-13, Low)
	flag.StringVar(&cfg.baseRef, "base", "", "Base reference (commit/branch). Empty = use HEAD for comparison")
	flag.StringVar(&cfg.headRef, "head", "", "Head reference (commit/branch). Empty = use working tree")
	flag.StringVar(&cfg.outputPath, "output", "", "Output file path. Empty = write to stdout")
	flag.StringVar(&cfg.workDir, "workdir", "", "Working directory. Empty = current directory")
	flag.BoolVar(&cfg.showVersion, "version", false, "Show version and exit")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: scope-detector [options]\n\n")
		fmt.Fprintf(os.Stderr, "Analyzes git diff to detect changed files and project language.\n\n")
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
		fmt.Fprintf(os.Stderr, "\nExamples:\n")
		fmt.Fprintf(os.Stderr, "  scope-detector                             # All uncommitted changes\n")
		fmt.Fprintf(os.Stderr, "  scope-detector --base=main --head=HEAD     # Compare branches\n")
		fmt.Fprintf(os.Stderr, "  scope-detector --output=.ring/codereview/scope.json\n")
	}

	flag.Parse()

	return cfg
}

// run executes the main CLI logic.
func run() error {
	cfg := parseFlags()

	// Handle --version flag
	if cfg.showVersion {
		fmt.Printf("scope-detector version %s\n", version)
		return nil
	}

	// Determine working directory
	workDir := cfg.workDir
	if workDir == "" {
		var err error
		workDir, err = os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get current directory: %w", err)
		}
	}

	// Create detector
	detector := scope.NewDetector(workDir)

	// Detect scope based on refs
	var result *scope.ScopeResult
	var err error

	if cfg.baseRef == "" && cfg.headRef == "" {
		// No refs specified: detect all uncommitted changes (staged + unstaged)
		result, err = detector.DetectAllChanges()
	} else {
		// Refs specified: compare specific refs
		result, err = detector.DetectFromRefs(cfg.baseRef, cfg.headRef)
	}

	if err != nil {
		// Check for mixed languages error
		if errors.Is(err, scope.ErrMixedLanguages) {
			return fmt.Errorf("mixed languages detected in changed files: %w", err)
		}
		return fmt.Errorf("failed to detect scope: %w", err)
	}

	// Check for no changes
	if result.TotalFiles == 0 {
		fmt.Fprintln(os.Stderr, "No changes detected")
		// Still output empty result for consistency
	}

	// Create output wrapper
	// Defensive: NewScopeOutput returns nil only if result is nil, which cannot happen here
	// after successful detection. Kept for safety against future refactoring.
	scopeOutput := output.NewScopeOutput(result)
	if scopeOutput == nil {
		return fmt.Errorf("failed to create scope output: nil result")
	}

	// Write output
	if cfg.outputPath != "" {
		// Write to file
		if err := scopeOutput.WriteToFile(cfg.outputPath); err != nil {
			return fmt.Errorf("failed to write output file: %w", err)
		}
		fmt.Fprintf(os.Stderr, "Scope written to %s\n", cfg.outputPath)
	} else {
		// Write to stdout
		if err := scopeOutput.WriteToStdout(); err != nil {
			return fmt.Errorf("failed to write to stdout: %w", err)
		}
	}

	return nil
}
