package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// outputJSON outputs results as JSON
func outputJSON(results []Component) {
	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error encoding JSON: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(string(output))
}

// outputText outputs results in human-readable format
func outputText(results []Component, query string) {
	if len(results) == 0 {
		fmt.Printf("No components found for: %s\n", query)
		fmt.Println("\nTips:")
		fmt.Println("  - Try broader search terms")
		fmt.Println("  - Use --type to filter by component type")
		fmt.Println("  - Check if the index is up to date")
		return
	}

	fmt.Printf("Found %d component(s) for: %s\n\n", len(results), query)

	for i, c := range results {
		// Component header with type badge
		typeBadge := getTypeBadge(c.Type)
		fmt.Printf("%d. %s %s\n", i+1, typeBadge, c.FQN)

		// Description
		if c.Description != "" {
			fmt.Printf("   %s\n", truncate(c.Description, 80))
		}

		// Type-specific info
		switch c.Type {
		case "skill":
			if c.Trigger != nil && *c.Trigger != "" {
				fmt.Printf("   When: %s\n", truncate(*c.Trigger, 60))
			}
		case "agent":
			if c.Model != nil && *c.Model != "" {
				fmt.Printf("   Model: %s\n", *c.Model)
			}
		case "command":
			if c.ArgumentHint != nil && *c.ArgumentHint != "" {
				fmt.Printf("   Args: %s\n", *c.ArgumentHint)
			}
		}

		// Usage hint
		fmt.Printf("   Use:  %s\n", getUsageHint(c))

		fmt.Println()
	}

	// Footer
	fmt.Println("---")
	fmt.Println("Use --json for machine-readable output")
	fmt.Println("Use --type <skill|agent|command> to filter")
}

// getTypeBadge returns a visual badge for the component type
func getTypeBadge(t string) string {
	switch t {
	case "skill":
		return "[SKILL]"
	case "agent":
		return "[AGENT]"
	case "command":
		return "[CMD]  "
	default:
		return "[" + strings.ToUpper(t) + "]"
	}
}

// getUsageHint returns how to use the component
func getUsageHint(c Component) string {
	switch c.Type {
	case "skill":
		return fmt.Sprintf("Skill tool with \"%s\"", c.FQN)
	case "agent":
		model := "sonnet"
		if c.Model != nil && *c.Model != "" {
			model = *c.Model
		}
		return fmt.Sprintf("Task tool with subagent_type=\"%s\", model=\"%s\"", c.FQN, model)
	case "command":
		return fmt.Sprintf("Type: %s", c.FQN)
	default:
		return c.FQN
	}
}

// truncate truncates a string to maxLen and adds ellipsis if needed
func truncate(s string, maxLen int) string {
	// Remove newlines and extra whitespace
	s = strings.Join(strings.Fields(s), " ")

	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
