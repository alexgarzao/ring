package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	_ "github.com/mattn/go-sqlite3"
)

// Component represents a Ring component from the database
type Component struct {
	ID           int64    `json:"id"`
	Plugin       string   `json:"plugin"`
	Type         string   `json:"type"`
	Name         string   `json:"name"`
	FQN          string   `json:"fqn"`
	Description  string   `json:"description"`
	UseCases     []string `json:"use_cases"`
	Keywords     []string `json:"keywords"`
	FilePath     string   `json:"file_path"`
	Model        *string  `json:"model,omitempty"`
	Trigger      *string  `json:"trigger,omitempty"`
	SkipWhen     *string  `json:"skip_when,omitempty"`
	ArgumentHint *string  `json:"argument_hint,omitempty"`
	Rank         float64  `json:"rank"`
}

// openDatabase opens the SQLite database
func openDatabase(path string) (*sql.DB, error) {
	db, err := sql.Open("sqlite3", path+"?mode=ro")
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Verify connection
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	return db, nil
}

// searchComponents searches for components matching the query
func searchComponents(db *sql.DB, query, typeFilter string, limit int) ([]Component, error) {
	// Build FTS5 query
	// Convert natural language to FTS5 syntax
	ftsQuery := buildFTSQuery(query)

	// Handle empty/invalid queries gracefully
	if ftsQuery == "" {
		return nil, nil // No valid search terms, return empty results
	}

	// Build SQL query
	sqlQuery := `
		SELECT
			c.id,
			c.plugin,
			c.type,
			c.name,
			c.fqn,
			c.description,
			c.use_cases,
			c.keywords,
			c.file_path,
			c.model,
			c.trigger,
			c.skip_when,
			c.argument_hint,
			bm25(components_fts, 1.0, 2.0, 1.5, 1.0, 1.5) as rank
		FROM components_fts
		JOIN components c ON components_fts.rowid = c.id
		WHERE components_fts MATCH ?
	`

	args := []interface{}{ftsQuery}

	if typeFilter != "" {
		sqlQuery += " AND c.type = ?"
		args = append(args, typeFilter)
	}

	sqlQuery += " ORDER BY rank LIMIT ?"
	args = append(args, limit)

	rows, err := db.Query(sqlQuery, args...)
	if err != nil {
		return nil, fmt.Errorf("search query failed: %w", err)
	}
	defer rows.Close()

	var results []Component
	for rows.Next() {
		var c Component
		var useCasesJSON, keywordsJSON sql.NullString
		var description sql.NullString

		err := rows.Scan(
			&c.ID,
			&c.Plugin,
			&c.Type,
			&c.Name,
			&c.FQN,
			&description,
			&useCasesJSON,
			&keywordsJSON,
			&c.FilePath,
			&c.Model,
			&c.Trigger,
			&c.SkipWhen,
			&c.ArgumentHint,
			&c.Rank,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		// Handle nullable description
		if description.Valid {
			c.Description = description.String
		}

		// Parse JSON arrays (log warnings for malformed data)
		if useCasesJSON.Valid && useCasesJSON.String != "" {
			if err := json.Unmarshal([]byte(useCasesJSON.String), &c.UseCases); err != nil {
				fmt.Fprintf(os.Stderr, "Warning: invalid use_cases JSON for %s: %v\n", c.FQN, err)
			}
		}
		if keywordsJSON.Valid && keywordsJSON.String != "" {
			if err := json.Unmarshal([]byte(keywordsJSON.String), &c.Keywords); err != nil {
				fmt.Fprintf(os.Stderr, "Warning: invalid keywords JSON for %s: %v\n", c.FQN, err)
			}
		}

		results = append(results, c)
	}

	return results, rows.Err()
}

// FTS5 reserved keywords that must be filtered from user queries
var fts5ReservedKeywords = map[string]bool{
	"AND": true, "OR": true, "NOT": true, "NEAR": true,
}

// buildFTSQuery converts natural language to FTS5 query syntax
// Returns empty string if no valid search terms are found
func buildFTSQuery(query string) string {
	// Split into words and handle special characters
	words := strings.Fields(query)
	if len(words) == 0 {
		return "" // Empty/whitespace query returns empty string
	}

	// Join with OR for broader matching
	// FTS5 uses implicit AND, so we use OR to be more permissive
	var parts []string
	for _, word := range words {
		// Remove special characters that could break FTS5
		// Also allow hyphen for compound words but strip leading hyphens
		// (leading hyphen is FTS5 NOT operator)
		cleaned := strings.Map(func(r rune) rune {
			if r >= 'a' && r <= 'z' || r >= 'A' && r <= 'Z' || r >= '0' && r <= '9' || r == '-' || r == '_' {
				return r
			}
			return -1
		}, word)
		// Strip leading hyphens to prevent FTS5 NOT operator injection
		cleaned = strings.TrimLeft(cleaned, "-")
		// Skip FTS5 reserved keywords to prevent syntax errors
		if cleaned != "" && !fts5ReservedKeywords[strings.ToUpper(cleaned)] {
			// Use prefix matching for partial words
			parts = append(parts, cleaned+"*")
		}
	}

	if len(parts) == 0 {
		return "" // No valid terms after sanitization
	}

	// Join with OR for permissive matching
	return strings.Join(parts, " OR ")
}
