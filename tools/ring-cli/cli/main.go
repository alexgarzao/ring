package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const version = "0.1.0"

func main() {
	// Define flags
	var (
		dbPath      string
		limit       int
		typeFilter  string
		jsonOutput  bool
		showVersion bool
	)

	flag.StringVar(&dbPath, "db", "", "Path to ring-index.db (default: auto-detect)")
	flag.IntVar(&limit, "limit", 5, "Maximum number of results")
	flag.StringVar(&typeFilter, "type", "", "Filter by type: skill, agent, command")
	flag.BoolVar(&jsonOutput, "json", false, "Output results as JSON")
	flag.BoolVar(&showVersion, "version", false, "Show version")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "ring-cli - Discover Ring components\n\n")
		fmt.Fprintf(os.Stderr, "Usage:\n")
		fmt.Fprintf(os.Stderr, "  ring-cli [flags] <query>\n\n")
		fmt.Fprintf(os.Stderr, "Examples:\n")
		fmt.Fprintf(os.Stderr, "  ring-cli \"code review\"\n")
		fmt.Fprintf(os.Stderr, "  ring-cli --type agent \"backend golang\"\n")
		fmt.Fprintf(os.Stderr, "  ring-cli --json \"debugging\"\n\n")
		fmt.Fprintf(os.Stderr, "Flags:\n")
		flag.PrintDefaults()
	}

	flag.Parse()

	if showVersion {
		fmt.Printf("ring-cli version %s\n", version)
		os.Exit(0)
	}

	// Get query from remaining args
	args := flag.Args()
	if len(args) == 0 {
		flag.Usage()
		os.Exit(1)
	}
	query := strings.Join(args, " ")

	// Find database
	dbFile, err := findDatabase(dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		fmt.Fprintf(os.Stderr, "Run 'python build_index.py' to create the index\n")
		os.Exit(1)
	}

	// Open database and search
	db, err := openDatabase(dbFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error opening database: %v\n", err)
		os.Exit(1)
	}
	defer db.Close()

	// Perform search
	results, err := searchComponents(db, query, typeFilter, limit)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error searching: %v\n", err)
		os.Exit(1)
	}

	// Output results
	if jsonOutput {
		outputJSON(results)
	} else {
		outputText(results, query)
	}
}

// findDatabase locates the ring-index.db file
func findDatabase(explicit string) (string, error) {
	// Use explicit path if provided
	if explicit != "" {
		if _, err := os.Stat(explicit); err != nil {
			return "", fmt.Errorf("database not found: %s", explicit)
		}
		return explicit, nil
	}

	// Search in common locations
	searchPaths := []string{
		"ring-index.db",
		"tools/ring-cli/ring-index.db",
		"../ring-index.db",
	}

	// Also search from executable location
	if exe, err := os.Executable(); err == nil {
		exeDir := filepath.Dir(exe)
		searchPaths = append(searchPaths,
			filepath.Join(exeDir, "ring-index.db"),
			filepath.Join(exeDir, "..", "ring-index.db"),
		)
	}

	for _, path := range searchPaths {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}

	return "", fmt.Errorf("ring-index.db not found in common locations")
}
