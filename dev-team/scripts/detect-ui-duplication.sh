#!/usr/bin/env bash
# detect-ui-duplication.sh - Detect component duplication between sindarian-ui and shadcn/radix
#
# Usage: ./detect-ui-duplication.sh [src_dir]
#   src_dir: Directory to scan (default: src/)
#
# Exit codes:
#   0 - No duplication found
#   1 - Duplication detected (CRITICAL)
#   2 - Usage error

set -euo pipefail

SRC_DIR="${1:-src/}"

if [ ! -d "$SRC_DIR" ]; then
    echo "ERROR: Directory '$SRC_DIR' does not exist."
    exit 2
fi

TMPDIR="${TMPDIR:-/tmp}"
SINDARIAN_FILE="$TMPDIR/sindarian-components.txt"
SHADCN_FILE="$TMPDIR/shadcn-components.txt"

# Extract component names imported from each library
grep -rn "from '@lerianstudio/sindarian-ui'" "$SRC_DIR" 2>/dev/null \
    | awk -F'/' '{print $NF}' | sort -u > "$SINDARIAN_FILE" || true

grep -rn "from '@/components/ui'" "$SRC_DIR" 2>/dev/null \
    | awk -F'/' '{print $NF}' | sort -u > "$SHADCN_FILE" || true

# Find components imported from both libraries
DUPLICATES=$(comm -12 "$SINDARIAN_FILE" "$SHADCN_FILE" 2>/dev/null || true)

# Clean up
rm -f "$SINDARIAN_FILE" "$SHADCN_FILE"

if [ -n "$DUPLICATES" ]; then
    echo "CRITICAL: Component duplication detected between sindarian-ui and shadcn/radix:"
    echo ""
    echo "$DUPLICATES"
    echo ""
    echo "Each component MUST have a single source. Remove the shadcn/radix duplicate."
    exit 1
else
    echo "PASS: No component duplication found between sindarian-ui and shadcn/radix."
    exit 0
fi
