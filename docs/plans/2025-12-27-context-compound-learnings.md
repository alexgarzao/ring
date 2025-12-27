# Compound Learnings Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Create a self-improving learning loop that extracts insights from sessions, detects patterns across multiple sessions, and generates new rules/skills with user approval.

**Architecture:** SessionEnd hook extracts learnings from session outcomes and handoffs into `.ring/cache/learnings/`. A skill analyzes accumulated learnings to find patterns (3+ occurrences). A command presents proposals to users who approve/reject. Approved patterns become permanent rules or skills in the Ring plugin.

**Tech Stack:**
- Python 3.8+ (learning extraction, pattern detection, rule generation)
- Bash shell scripts (hook wrappers)
- JSON (hook configuration, proposal storage)
- SQLite3 with FTS5 (artifact index querying - from dependency)

**Global Prerequisites:**
- Environment: macOS/Linux, Python 3.8+
- Tools: `python3 --version` (3.8+), `sqlite3 --version` (3.x)
- Access: Write access to `default/` plugin directory
- State: On feature branch, clean working tree
- **CRITICAL DEPENDENCY:** Artifact Index (Phase 1) and Outcome Tracking (Phase 2) MUST be implemented first

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python3 --version                    # Expected: Python 3.8+
sqlite3 --version                    # Expected: 3.x
ls -la default/lib/artifact-index/   # Expected: artifact_query.py exists (from Phase 1)
ls -la .ring/cache/                  # Expected: artifact-index/ exists (from Phase 1)
git status                           # Expected: clean working tree on feature branch
```

---

## Dependencies

This feature is **Phase 4** of the Context Management System. It depends on:

| Dependency | Status Check | Required For |
|------------|-------------|--------------|
| Artifact Index (Phase 1) | `ls default/lib/artifact-index/artifact_query.py` | Querying historical outcomes |
| Outcome Tracking (Phase 2) | `ls default/hooks/session-outcome.sh` | Success/failure context |
| Handoff Tracking (Phase 2) | `ls default/skills/handoff-tracking/SKILL.md` | Key decisions |

**If any dependency is missing:** STOP. Implement missing dependencies first.

---

## Directory Structure

**New files in `default/` plugin:**

```
default/
  hooks/
    hooks.json                           # UPDATE: Add learning-extract hook
    learning-extract.sh                  # NEW: SessionEnd learning extraction wrapper
    learning-extract.py                  # NEW: Python extraction logic

  lib/
    compound-learnings/                  # NEW: Shared learning utilities
      pattern_detector.py                # Pattern detection across learnings
      rule_generator.py                  # Generate rules/skills from patterns
      learning_parser.py                 # Parse learning markdown files

  skills/
    compound-learnings/                  # NEW: Analysis and proposal skill
      SKILL.md

  commands/
    compound-learnings.md                # NEW: /compound-learnings command

  rules/                                 # NEW: Generated rules directory
    .gitkeep                             # Placeholder for generated rules
```

**State files (project-specific):**

```
$PROJECT_ROOT/
  .ring/
    cache/
      learnings/                         # Extracted learnings per session
        YYYY-MM-DD-<session-id>.md
        YYYY-MM-DD-<session-id>.md
      proposals/                         # Pending pattern proposals
        pending.json                     # Current proposals awaiting approval
        history.json                     # Approved/rejected history
```

---

## Task 1: Create Learning Cache Directory Structure

**Files:**
- Create: `default/lib/compound-learnings/.gitkeep`
- Create: `default/rules/.gitkeep`

**Prerequisites:**
- Tools: bash
- Files must exist: `default/` directory
- Environment: None

**Step 1: Create directory structure**

```bash
mkdir -p default/lib/compound-learnings
mkdir -p default/rules
touch default/lib/compound-learnings/.gitkeep
touch default/rules/.gitkeep
```

**Step 2: Verify creation**

Run: `ls -la default/lib/compound-learnings/ default/rules/`

**Expected output:**
```
default/lib/compound-learnings/:
total 0
-rw-r--r--  1 user  staff  0 Dec 27 10:00 .gitkeep

default/rules/:
total 0
-rw-r--r--  1 user  staff  0 Dec 27 10:00 .gitkeep
```

**Step 3: Commit**

```bash
git add default/lib/compound-learnings/.gitkeep default/rules/.gitkeep
git commit -m "chore: add compound-learnings directory structure"
```

**If Task Fails:**

1. **Directory already exists:**
   - Check: `ls -la default/lib/`
   - Fix: Skip creation, proceed to next step
   - Rollback: Not needed

2. **Permission denied:**
   - Check: `ls -la default/`
   - Fix: Check file permissions
   - Rollback: `rm -rf default/lib/compound-learnings default/rules`

---

## Task 2: Create Learning Parser Library

**Files:**
- Create: `default/lib/compound-learnings/learning_parser.py`

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `default/lib/compound-learnings/`
- Environment: None

**Step 1: Write the failing test**

Create test file first:

```python
# default/lib/compound-learnings/test_learning_parser.py
"""Tests for learning_parser.py"""
import unittest
from pathlib import Path
import tempfile
import os

# Will fail until learning_parser.py exists
from learning_parser import (
    parse_learning_file,
    extract_patterns,
    extract_what_worked,
    extract_what_failed,
    extract_key_decisions,
)


class TestLearningParser(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_learning = """# Learnings from Session abc123

**Date:** 2025-12-27 10:00:00

## What Worked

- Using TDD approach for the implementation
- Breaking down tasks into small commits
- Running tests after each change

## What Failed

- Trying to implement everything at once
- Skipping the planning phase

## Key Decisions

- Chose SQLite over PostgreSQL for simplicity
- Used Python instead of TypeScript for portability

## Patterns

- Always run tests before committing
- Use explicit file paths in plans
"""
        self.learning_path = Path(self.test_dir) / "2025-12-27-abc123.md"
        self.learning_path.write_text(self.sample_learning)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_learning_file(self):
        """Test parsing a complete learning file"""
        result = parse_learning_file(self.learning_path)
        self.assertEqual(result["session_id"], "abc123")
        self.assertEqual(result["date"], "2025-12-27 10:00:00")
        self.assertIn("Using TDD approach", result["what_worked"][0])

    def test_extract_what_worked(self):
        """Test extracting What Worked section"""
        items = extract_what_worked(self.sample_learning)
        self.assertEqual(len(items), 3)
        self.assertIn("TDD", items[0])

    def test_extract_what_failed(self):
        """Test extracting What Failed section"""
        items = extract_what_failed(self.sample_learning)
        self.assertEqual(len(items), 2)
        self.assertIn("everything at once", items[0])

    def test_extract_key_decisions(self):
        """Test extracting Key Decisions section"""
        items = extract_key_decisions(self.sample_learning)
        self.assertEqual(len(items), 2)
        self.assertIn("SQLite", items[0])

    def test_extract_patterns(self):
        """Test extracting Patterns section"""
        items = extract_patterns(self.sample_learning)
        self.assertEqual(len(items), 2)
        self.assertIn("tests before committing", items[0])


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `cd default/lib/compound-learnings && python3 -m pytest test_learning_parser.py -v 2>&1 || python3 -m unittest test_learning_parser -v`

**Expected output:**
```
ModuleNotFoundError: No module named 'learning_parser'
```

**If you see different error:** Check file paths and ensure test file exists

**Step 3: Write minimal implementation**

```python
# default/lib/compound-learnings/learning_parser.py
"""Parse learning markdown files into structured data.

This module extracts structured information from session learning files
stored in .ring/cache/learnings/.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def parse_learning_file(file_path: Path) -> Dict:
    """Parse a learning markdown file into structured data.

    Args:
        file_path: Path to the learning markdown file

    Returns:
        Dictionary with session_id, date, what_worked, what_failed,
        key_decisions, and patterns
    """
    content = file_path.read_text()

    # Extract session ID from filename: YYYY-MM-DD-<session-id>.md
    filename = file_path.stem  # e.g., "2025-12-27-abc123"
    session_id = filename.split("-", 3)[-1] if "-" in filename else filename

    # Extract date from content
    date_match = re.search(r'\*\*Date:\*\*\s*(.+)', content)
    date = date_match.group(1).strip() if date_match else ""

    return {
        "session_id": session_id,
        "date": date,
        "file_path": str(file_path),
        "what_worked": extract_what_worked(content),
        "what_failed": extract_what_failed(content),
        "key_decisions": extract_key_decisions(content),
        "patterns": extract_patterns(content),
    }


def _extract_section_items(content: str, section_name: str) -> List[str]:
    """Extract bullet items from a markdown section.

    Args:
        content: Full markdown content
        section_name: Name of section (e.g., "What Worked")

    Returns:
        List of bullet point items (without the leading "- ")
    """
    # Match section header and capture until next ## or end
    pattern = rf'##\s*{re.escape(section_name)}\s*\n(.*?)(?=\n##|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if not match:
        return []

    section_content = match.group(1)

    # Extract bullet points (lines starting with "- ")
    items = []
    for line in section_content.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            items.append(line[2:].strip())

    return items


def extract_what_worked(content: str) -> List[str]:
    """Extract items from 'What Worked' section."""
    return _extract_section_items(content, "What Worked")


def extract_what_failed(content: str) -> List[str]:
    """Extract items from 'What Failed' section."""
    return _extract_section_items(content, "What Failed")


def extract_key_decisions(content: str) -> List[str]:
    """Extract items from 'Key Decisions' section."""
    return _extract_section_items(content, "Key Decisions")


def extract_patterns(content: str) -> List[str]:
    """Extract items from 'Patterns' section."""
    return _extract_section_items(content, "Patterns")


def load_all_learnings(learnings_dir: Path) -> List[Dict]:
    """Load all learning files from a directory.

    Args:
        learnings_dir: Path to .ring/cache/learnings/ directory

    Returns:
        List of parsed learning dictionaries, sorted by date (newest first)
    """
    if not learnings_dir.exists():
        return []

    learnings = []
    for file_path in learnings_dir.glob("*.md"):
        try:
            learning = parse_learning_file(file_path)
            learnings.append(learning)
        except Exception as e:
            # Log but continue processing other files
            print(f"Warning: Failed to parse {file_path}: {e}")

    # Sort by date (newest first)
    learnings.sort(key=lambda x: x.get("date", ""), reverse=True)
    return learnings
```

**Step 4: Run test to verify it passes**

Run: `cd default/lib/compound-learnings && python3 -m pytest test_learning_parser.py -v 2>&1 || python3 -m unittest test_learning_parser -v`

**Expected output:**
```
test_extract_key_decisions ... ok
test_extract_patterns ... ok
test_extract_what_failed ... ok
test_extract_what_worked ... ok
test_parse_learning_file ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.XXXs

OK
```

**Step 5: Commit**

```bash
git add default/lib/compound-learnings/learning_parser.py default/lib/compound-learnings/test_learning_parser.py
git commit -m "feat(compound-learnings): add learning file parser"
```

**If Task Fails:**

1. **Test won't run:**
   - Check: `ls default/lib/compound-learnings/` (files exist?)
   - Fix: Create missing directories first
   - Rollback: `git checkout -- .`

2. **Import errors:**
   - Check: `python3 -c "import re, pathlib"` (standard library available?)
   - Fix: Ensure Python 3.8+
   - Rollback: `git checkout -- .`

---

## Task 3: Create Pattern Detector Library

**Files:**
- Create: `default/lib/compound-learnings/pattern_detector.py`
- Create: `default/lib/compound-learnings/test_pattern_detector.py`

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `default/lib/compound-learnings/learning_parser.py`
- Environment: None

**Step 1: Write the failing test**

```python
# default/lib/compound-learnings/test_pattern_detector.py
"""Tests for pattern_detector.py"""
import unittest
from pathlib import Path
import tempfile

from pattern_detector import (
    normalize_pattern,
    find_similar_patterns,
    aggregate_patterns,
    detect_recurring_patterns,
    categorize_pattern,
)


class TestPatternDetector(unittest.TestCase):
    def test_normalize_pattern(self):
        """Test pattern normalization"""
        # Should lowercase and remove extra whitespace
        self.assertEqual(
            normalize_pattern("  Use TDD   Approach  "),
            "use tdd approach"
        )

    def test_find_similar_patterns(self):
        """Test finding similar patterns using fuzzy matching"""
        patterns = [
            "always run tests before committing",
            "run tests before commit",
            "test before committing changes",
            "use explicit file paths",
        ]
        similar = find_similar_patterns("run tests before commit", patterns)
        # Should find the similar patterns
        self.assertGreaterEqual(len(similar), 2)

    def test_aggregate_patterns(self):
        """Test aggregating similar patterns into groups"""
        patterns = [
            {"text": "run tests before commit", "session": "abc"},
            {"text": "always run tests before committing", "session": "def"},
            {"text": "test before committing changes", "session": "ghi"},
            {"text": "use explicit file paths", "session": "jkl"},
        ]
        groups = aggregate_patterns(patterns)
        # Should group similar patterns together
        self.assertGreaterEqual(len(groups), 1)
        # At least one group should have 3 items
        has_large_group = any(len(g["items"]) >= 3 for g in groups)
        self.assertTrue(has_large_group)

    def test_detect_recurring_patterns(self):
        """Test detecting patterns that appear 3+ times"""
        learnings = [
            {
                "session_id": "abc",
                "patterns": ["run tests before commit", "use explicit paths"],
                "what_worked": ["TDD approach"],
            },
            {
                "session_id": "def",
                "patterns": ["always run tests before committing"],
                "what_worked": ["TDD workflow"],
            },
            {
                "session_id": "ghi",
                "patterns": ["test before committing changes"],
                "what_worked": ["test-driven development"],
            },
        ]
        recurring = detect_recurring_patterns(learnings, min_occurrences=3)
        # Should detect "run tests before commit" pattern (appears in 3 sessions)
        self.assertGreaterEqual(len(recurring), 1)

    def test_categorize_pattern(self):
        """Test categorizing patterns into rule/skill/hook"""
        # Heuristic patterns -> rules
        self.assertEqual(
            categorize_pattern("always run tests before committing"),
            "rule"
        )
        # Sequences/processes -> skills
        self.assertEqual(
            categorize_pattern("step by step debugging process"),
            "skill"
        )
        # Event triggers -> hooks
        self.assertEqual(
            categorize_pattern("on session end, save the state"),
            "hook"
        )


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `cd default/lib/compound-learnings && python3 -m pytest test_pattern_detector.py -v 2>&1 || python3 -m unittest test_pattern_detector -v`

**Expected output:**
```
ModuleNotFoundError: No module named 'pattern_detector'
```

**Step 3: Write minimal implementation**

```python
# default/lib/compound-learnings/pattern_detector.py
"""Detect recurring patterns across session learnings.

This module analyzes learning files to find patterns that appear frequently
enough to warrant becoming permanent rules, skills, or hooks.
"""
import re
from typing import Dict, List, Tuple, Set
from difflib import SequenceCore two


def normalize_pattern(text: str) -> str:
    """Normalize pattern text for comparison.

    Args:
        text: Raw pattern text

    Returns:
        Lowercase, whitespace-normalized text
    """
    # Lowercase and collapse whitespace
    return " ".join(text.lower().split())


def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity between two strings.

    Uses SequenceCore two for fuzzy matching.

    Args:
        text1: First string
        text2: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    return SequenceCore two(None, normalize_pattern(text1), normalize_pattern(text2)).ratio()


def find_similar_patterns(pattern: str, patterns: List[str], threshold: float = 0.6) -> List[str]:
    """Find patterns similar to the given pattern.

    Args:
        pattern: Pattern to match against
        patterns: List of patterns to search
        threshold: Minimum similarity score (0.0 to 1.0)

    Returns:
        List of similar patterns
    """
    similar = []
    normalized_pattern = normalize_pattern(pattern)

    for p in patterns:
        if similarity_score(normalized_pattern, p) >= threshold:
            similar.append(p)

    return similar


def aggregate_patterns(patterns: List[Dict]) -> List[Dict]:
    """Aggregate similar patterns into groups.

    Args:
        patterns: List of {"text": str, "session": str} dictionaries

    Returns:
        List of pattern groups with canonical text and items
    """
    if not patterns:
        return []

    groups = []
    used = set()

    for i, p in enumerate(patterns):
        if i in used:
            continue

        # Start a new group with this pattern
        group = {
            "canonical": p["text"],
            "items": [p],
            "sessions": {p["session"]},
        }
        used.add(i)

        # Find similar patterns
        for j, other in enumerate(patterns):
            if j in used:
                continue

            if similarity_score(p["text"], other["text"]) >= 0.6:
                group["items"].append(other)
                group["sessions"].add(other["session"])
                used.add(j)

        groups.append(group)

    # Sort by number of items (most common first)
    groups.sort(key=lambda g: len(g["items"]), reverse=True)
    return groups


def detect_recurring_patterns(learnings: List[Dict], min_occurrences: int = 3) -> List[Dict]:
    """Detect patterns that appear in multiple sessions.

    Args:
        learnings: List of parsed learning dictionaries
        min_occurrences: Minimum number of sessions for a pattern

    Returns:
        List of recurring patterns with metadata
    """
    # Collect all patterns with their sources
    all_patterns = []

    for learning in learnings:
        session_id = learning.get("session_id", "unknown")

        # Collect from explicit patterns section
        for pattern in learning.get("patterns", []):
            all_patterns.append({"text": pattern, "session": session_id, "source": "patterns"})

        # Collect from what_worked (success patterns)
        for item in learning.get("what_worked", []):
            all_patterns.append({"text": item, "session": session_id, "source": "what_worked"})

        # Collect from what_failed (inverted to anti-patterns)
        for item in learning.get("what_failed", []):
            all_patterns.append({"text": f"Avoid: {item}", "session": session_id, "source": "what_failed"})

    # Aggregate similar patterns
    groups = aggregate_patterns(all_patterns)

    # Filter to those appearing in min_occurrences or more sessions
    recurring = []
    for group in groups:
        if len(group["sessions"]) >= min_occurrences:
            recurring.append({
                "canonical": group["canonical"],
                "occurrences": len(group["items"]),
                "sessions": list(group["sessions"]),
                "category": categorize_pattern(group["canonical"]),
                "sources": [item["source"] for item in group["items"]],
            })

    return recurring


def categorize_pattern(pattern: str) -> str:
    """Categorize a pattern as rule, skill, or hook candidate.

    Decision tree:
    - Contains sequence/process keywords -> skill
    - Contains event trigger keywords -> hook
    - Otherwise -> rule (behavioral heuristic)

    Args:
        pattern: Pattern text

    Returns:
        Category: "rule", "skill", or "hook"
    """
    pattern_lower = pattern.lower()

    # Skill indicators: sequences, processes, step-by-step
    skill_keywords = [
        "step by step", "process", "workflow", "procedure",
        "first", "then", "finally", "sequence", "follow these",
    ]
    for keyword in skill_keywords:
        if keyword in pattern_lower:
            return "skill"

    # Hook indicators: event triggers, automatic actions
    hook_keywords = [
        "on session", "when", "after", "before", "automatically",
        "trigger", "event", "at the end", "at the start",
    ]
    for keyword in hook_keywords:
        if keyword in pattern_lower:
            return "hook"

    # Default: behavioral rule
    return "rule"


def generate_pattern_summary(recurring_patterns: List[Dict]) -> str:
    """Generate a human-readable summary of recurring patterns.

    Args:
        recurring_patterns: Output from detect_recurring_patterns

    Returns:
        Markdown-formatted summary
    """
    if not recurring_patterns:
        return "No recurring patterns found (patterns need 3+ occurrences)."

    lines = ["# Recurring Patterns Analysis", ""]

    # Group by category
    by_category = {"rule": [], "skill": [], "hook": []}
    for pattern in recurring_patterns:
        category = pattern.get("category", "rule")
        by_category[category].append(pattern)

    for category, patterns in by_category.items():
        if not patterns:
            continue

        lines.append(f"## {category.title()} Candidates ({len(patterns)})")
        lines.append("")

        for p in patterns:
            lines.append(f"### {p['canonical'][:60]}...")
            lines.append(f"- **Occurrences:** {p['occurrences']} sessions")
            lines.append(f"- **Sessions:** {', '.join(p['sessions'][:5])}...")
            lines.append(f"- **Sources:** {', '.join(set(p['sources']))}")
            lines.append("")

    return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `cd default/lib/compound-learnings && python3 -m pytest test_pattern_detector.py -v 2>&1 || python3 -m unittest test_pattern_detector -v`

**Expected output:**
```
test_aggregate_patterns ... ok
test_categorize_pattern ... ok
test_detect_recurring_patterns ... ok
test_find_similar_patterns ... ok
test_normalize_pattern ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.XXXs

OK
```

**Step 5: Commit**

```bash
git add default/lib/compound-learnings/pattern_detector.py default/lib/compound-learnings/test_pattern_detector.py
git commit -m "feat(compound-learnings): add pattern detector for recurring learnings"
```

**If Task Fails:**

1. **Similarity scores too strict/loose:**
   - Check: Adjust threshold in `find_similar_patterns`
   - Fix: Lower to 0.5 for more matches, raise to 0.7 for stricter
   - Rollback: `git checkout -- .`

2. **Tests fail on edge cases:**
   - Check: Review test data format
   - Fix: Ensure test data matches expected structure
   - Rollback: `git checkout -- .`

---

## Task 4: Create Rule Generator Library

**Files:**
- Create: `default/lib/compound-learnings/rule_generator.py`
- Create: `default/lib/compound-learnings/test_rule_generator.py`

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `default/lib/compound-learnings/pattern_detector.py`
- Environment: None

**Step 1: Write the failing test**

```python
# default/lib/compound-learnings/test_rule_generator.py
"""Tests for rule_generator.py"""
import unittest
from pathlib import Path
import tempfile
import shutil

from rule_generator import (
    generate_rule_content,
    generate_skill_content,
    create_rule_file,
    create_skill_file,
    generate_proposal,
)


class TestRuleGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.rules_dir = self.test_dir / "rules"
        self.skills_dir = self.test_dir / "skills"
        self.rules_dir.mkdir()
        self.skills_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_rule_content(self):
        """Test generating rule markdown content"""
        pattern = {
            "canonical": "Always run tests before committing",
            "occurrences": 5,
            "sessions": ["abc", "def", "ghi", "jkl", "mno"],
            "sources": ["patterns", "what_worked"],
        }
        content = generate_rule_content(pattern)
        self.assertIn("# Always run tests before committing", content)
        self.assertIn("5 sessions", content)
        self.assertIn("## Pattern", content)
        self.assertIn("## DO", content)
        self.assertIn("## DON'T", content)

    def test_generate_skill_content(self):
        """Test generating skill markdown content"""
        pattern = {
            "canonical": "Step by step debugging process",
            "occurrences": 4,
            "sessions": ["abc", "def", "ghi", "jkl"],
            "sources": ["patterns"],
        }
        content = generate_skill_content(pattern)
        self.assertIn("---", content)  # YAML frontmatter
        self.assertIn("name:", content)
        self.assertIn("description:", content)
        self.assertIn("## Overview", content)
        self.assertIn("## When to Use", content)

    def test_create_rule_file(self):
        """Test creating a rule file on disk"""
        pattern = {
            "canonical": "Use explicit file paths",
            "occurrences": 3,
            "sessions": ["abc", "def", "ghi"],
            "sources": ["patterns"],
        }
        file_path = create_rule_file(pattern, self.rules_dir)
        self.assertTrue(file_path.exists())
        self.assertIn("use-explicit-file-paths", file_path.name)
        content = file_path.read_text()
        self.assertIn("Use explicit file paths", content)

    def test_create_skill_file(self):
        """Test creating a skill directory and SKILL.md"""
        pattern = {
            "canonical": "Systematic debugging workflow",
            "occurrences": 4,
            "sessions": ["abc", "def", "ghi", "jkl"],
            "sources": ["patterns"],
        }
        skill_dir = create_skill_file(pattern, self.skills_dir)
        self.assertTrue(skill_dir.exists())
        skill_file = skill_dir / "SKILL.md"
        self.assertTrue(skill_file.exists())

    def test_generate_proposal(self):
        """Test generating a proposal document"""
        patterns = [
            {
                "canonical": "Always run tests",
                "occurrences": 3,
                "sessions": ["abc", "def", "ghi"],
                "category": "rule",
                "sources": ["patterns"],
            },
            {
                "canonical": "Step by step debug",
                "occurrences": 4,
                "sessions": ["abc", "def", "ghi", "jkl"],
                "category": "skill",
                "sources": ["what_worked"],
            },
        ]
        proposal = generate_proposal(patterns)
        self.assertIn("proposals", proposal)
        self.assertEqual(len(proposal["proposals"]), 2)
        self.assertEqual(proposal["proposals"][0]["category"], "rule")


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `cd default/lib/compound-learnings && python3 -m pytest test_rule_generator.py -v 2>&1 || python3 -m unittest test_rule_generator -v`

**Expected output:**
```
ModuleNotFoundError: No module named 'rule_generator'
```

**Step 3: Write minimal implementation**

```python
# default/lib/compound-learnings/rule_generator.py
"""Generate rules and skills from detected patterns.

This module creates the actual rule/skill files that will be added
to the Ring plugin based on user-approved patterns.
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Input text

    Returns:
        Lowercase, hyphen-separated slug
    """
    # Lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower())
    # Remove leading/trailing hyphens
    return slug.strip('-')


def generate_rule_content(pattern: Dict) -> str:
    """Generate markdown content for a rule.

    Args:
        pattern: Pattern dictionary with canonical, occurrences, sessions

    Returns:
        Markdown content for the rule file
    """
    canonical = pattern["canonical"]
    occurrences = pattern.get("occurrences", 0)
    sessions = pattern.get("sessions", [])
    sources = pattern.get("sources", [])

    # Generate DO/DON'T based on pattern text
    if canonical.lower().startswith("avoid"):
        dont_text = canonical.replace("Avoid: ", "").replace("avoid ", "")
        do_text = f"Do the opposite of: {dont_text}"
    else:
        do_text = canonical
        dont_text = f"Skip or ignore: {canonical}"

    content = f"""# {canonical}

**Context:** This rule emerged from {occurrences} sessions where this pattern appeared.

## Pattern

{canonical}

## DO

- {do_text}

## DON'T

- {dont_text}

## Source Sessions

This rule was automatically generated from learnings in these sessions:

"""
    for session in sessions[:10]:  # Show first 10
        content += f"- `{session}`\n"

    if len(sessions) > 10:
        content += f"- ... and {len(sessions) - 10} more sessions\n"

    content += f"""
## Evidence

- **Occurrences:** {occurrences} times across {len(sessions)} sessions
- **Sources:** {', '.join(set(sources))}
- **Generated:** {datetime.now().strftime('%Y-%m-%d')}
"""

    return content


def generate_skill_content(pattern: Dict) -> str:
    """Generate markdown content for a skill.

    Args:
        pattern: Pattern dictionary with canonical, occurrences, sessions

    Returns:
        Markdown content for SKILL.md file
    """
    canonical = pattern["canonical"]
    occurrences = pattern.get("occurrences", 0)
    sessions = pattern.get("sessions", [])
    slug = slugify(canonical)

    # Create description for frontmatter
    description = f"Use when {canonical.lower()} - emerged from {occurrences} sessions"
    if len(description) > 200:
        description = description[:197] + "..."

    content = f"""---
name: {slug}
description: |
  {description}
---

# {canonical}

## Overview

This skill emerged from patterns observed across {occurrences} sessions.

{canonical}

## When to Use

- When you encounter situations similar to those in the source sessions
- When the pattern would apply to your current task

## When NOT to Use

- When the context is significantly different from the source sessions
- When project-specific conventions override this pattern

## Process

1. [Step 1 - TO BE FILLED: Review and customize this skill]
2. [Step 2 - TO BE FILLED: Add specific steps for your use case]
3. [Step 3 - TO BE FILLED: Include verification steps]

## Source Sessions

This skill was automatically generated from learnings in these sessions:

"""
    for session in sessions[:10]:
        content += f"- `{session}`\n"

    content += f"""
## Notes

- **Generated:** {datetime.now().strftime('%Y-%m-%d')}
- **IMPORTANT:** This skill needs human review and customization before use
- Edit the Process section to add specific, actionable steps
"""

    return content


def create_rule_file(pattern: Dict, rules_dir: Path) -> Path:
    """Create a rule file on disk.

    Args:
        pattern: Pattern dictionary
        rules_dir: Path to rules directory

    Returns:
        Path to created rule file
    """
    slug = slugify(pattern["canonical"])
    file_path = rules_dir / f"{slug}.md"

    content = generate_rule_content(pattern)
    file_path.write_text(content)

    return file_path


def create_skill_file(pattern: Dict, skills_dir: Path) -> Path:
    """Create a skill directory and SKILL.md file.

    Args:
        pattern: Pattern dictionary
        skills_dir: Path to skills directory

    Returns:
        Path to created skill directory
    """
    slug = slugify(pattern["canonical"])
    skill_dir = skills_dir / slug
    skill_dir.mkdir(exist_ok=True)

    skill_file = skill_dir / "SKILL.md"
    content = generate_skill_content(pattern)
    skill_file.write_text(content)

    return skill_dir


def generate_proposal(patterns: List[Dict]) -> Dict:
    """Generate a proposal document for user review.

    Args:
        patterns: List of recurring patterns from pattern_detector

    Returns:
        Proposal dictionary with proposals list and metadata
    """
    proposals = []

    for i, pattern in enumerate(patterns):
        category = pattern.get("category", "rule")

        proposal = {
            "id": f"proposal-{i+1}",
            "canonical": pattern["canonical"],
            "category": category,
            "occurrences": pattern.get("occurrences", 0),
            "sessions": pattern.get("sessions", []),
            "sources": pattern.get("sources", []),
            "status": "pending",
            "preview": generate_rule_content(pattern) if category == "rule" else generate_skill_content(pattern),
        }
        proposals.append(proposal)

    return {
        "generated": datetime.now().isoformat(),
        "total_proposals": len(proposals),
        "proposals": proposals,
    }


def save_proposal(proposal: Dict, proposals_dir: Path) -> Path:
    """Save proposal to pending.json file.

    Args:
        proposal: Proposal dictionary from generate_proposal
        proposals_dir: Path to .ring/cache/proposals/

    Returns:
        Path to saved proposals file
    """
    proposals_dir.mkdir(parents=True, exist_ok=True)
    pending_file = proposals_dir / "pending.json"

    with open(pending_file, 'w') as f:
        json.dump(proposal, f, indent=2)

    return pending_file


def approve_proposal(proposal_id: str, proposals_dir: Path) -> Optional[Dict]:
    """Mark a proposal as approved.

    Args:
        proposal_id: ID of proposal to approve
        proposals_dir: Path to proposals directory

    Returns:
        Approved proposal dictionary, or None if not found
    """
    pending_file = proposals_dir / "pending.json"
    history_file = proposals_dir / "history.json"

    if not pending_file.exists():
        return None

    with open(pending_file) as f:
        data = json.load(f)

    # Find and update proposal
    approved = None
    for proposal in data.get("proposals", []):
        if proposal["id"] == proposal_id:
            proposal["status"] = "approved"
            proposal["approved_at"] = datetime.now().isoformat()
            approved = proposal
            break

    if approved:
        # Save updated pending file
        with open(pending_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Append to history
        history = []
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
        history.append(approved)
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    return approved


def reject_proposal(proposal_id: str, proposals_dir: Path, reason: str = "") -> Optional[Dict]:
    """Mark a proposal as rejected.

    Args:
        proposal_id: ID of proposal to reject
        proposals_dir: Path to proposals directory
        reason: Optional rejection reason

    Returns:
        Rejected proposal dictionary, or None if not found
    """
    pending_file = proposals_dir / "pending.json"
    history_file = proposals_dir / "history.json"

    if not pending_file.exists():
        return None

    with open(pending_file) as f:
        data = json.load(f)

    # Find and update proposal
    rejected = None
    for proposal in data.get("proposals", []):
        if proposal["id"] == proposal_id:
            proposal["status"] = "rejected"
            proposal["rejected_at"] = datetime.now().isoformat()
            proposal["rejection_reason"] = reason
            rejected = proposal
            break

    if rejected:
        # Save updated pending file
        with open(pending_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Append to history
        history = []
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
        history.append(rejected)
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    return rejected
```

**Step 4: Run test to verify it passes**

Run: `cd default/lib/compound-learnings && python3 -m pytest test_rule_generator.py -v 2>&1 || python3 -m unittest test_rule_generator -v`

**Expected output:**
```
test_create_rule_file ... ok
test_create_skill_file ... ok
test_generate_proposal ... ok
test_generate_rule_content ... ok
test_generate_skill_content ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.XXXs

OK
```

**Step 5: Commit**

```bash
git add default/lib/compound-learnings/rule_generator.py default/lib/compound-learnings/test_rule_generator.py
git commit -m "feat(compound-learnings): add rule/skill generator from patterns"
```

**If Task Fails:**

1. **Permission errors creating files:**
   - Check: `ls -la` on test directory
   - Fix: Ensure write permissions
   - Rollback: `git checkout -- .`

2. **JSON serialization errors:**
   - Check: All data types are JSON-serializable
   - Fix: Convert datetime objects to strings before saving
   - Rollback: `git checkout -- .`

---

## Task 5: Create __init__.py for Library Package

**Files:**
- Create: `default/lib/compound-learnings/__init__.py`

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: All three library modules
- Environment: None

**Step 1: Create package init file**

```python
# default/lib/compound-learnings/__init__.py
"""Compound Learnings Library - Transform session learnings into permanent capabilities.

This package provides:
- Learning file parsing (learning_parser)
- Pattern detection across sessions (pattern_detector)
- Rule/skill generation from patterns (rule_generator)
"""

from .learning_parser import (
    parse_learning_file,
    extract_patterns,
    extract_what_worked,
    extract_what_failed,
    extract_key_decisions,
    load_all_learnings,
)

from .pattern_detector import (
    normalize_pattern,
    find_similar_patterns,
    aggregate_patterns,
    detect_recurring_patterns,
    categorize_pattern,
    generate_pattern_summary,
)

from .rule_generator import (
    generate_rule_content,
    generate_skill_content,
    create_rule_file,
    create_skill_file,
    generate_proposal,
    save_proposal,
    approve_proposal,
    reject_proposal,
)

__all__ = [
    # learning_parser
    "parse_learning_file",
    "extract_patterns",
    "extract_what_worked",
    "extract_what_failed",
    "extract_key_decisions",
    "load_all_learnings",
    # pattern_detector
    "normalize_pattern",
    "find_similar_patterns",
    "aggregate_patterns",
    "detect_recurring_patterns",
    "categorize_pattern",
    "generate_pattern_summary",
    # rule_generator
    "generate_rule_content",
    "generate_skill_content",
    "create_rule_file",
    "create_skill_file",
    "generate_proposal",
    "save_proposal",
    "approve_proposal",
    "reject_proposal",
]
```

**Step 2: Verify package imports**

Run: `cd default/lib && python3 -c "from compound_learnings import detect_recurring_patterns, generate_proposal; print('OK')"`

**Expected output:**
```
OK
```

**Step 3: Commit**

```bash
git add default/lib/compound-learnings/__init__.py
git commit -m "feat(compound-learnings): add library package init"
```

**If Task Fails:**

1. **Import errors:**
   - Check: Each module imports correctly in isolation
   - Fix: Check for circular imports
   - Rollback: `git checkout -- .`

---

## Task 6: Create Learning Extraction Hook (Python)

**Files:**
- Create: `default/hooks/learning-extract.py`

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `default/lib/compound-learnings/`
- Environment: None

**Step 1: Write the hook Python script**

```python
#!/usr/bin/env python3
"""Learning extraction hook for SessionEnd.

This hook runs on SessionEnd (Stop event) to extract learnings from
the current session and save them to .ring/cache/learnings/.

Input (stdin JSON):
{
    "type": "stop",
    "session_id": "optional session identifier",
    "reason": "user_stop|error|complete"
}

Output (stdout JSON):
{
    "result": "continue",
    "message": "Optional system reminder about learnings"
}
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime


def read_stdin() -> dict:
    """Read JSON input from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return {}


def get_project_root() -> Path:
    """Get the project root directory."""
    # Try CLAUDE_PROJECT_DIR first
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(os.environ["CLAUDE_PROJECT_DIR"])
    # Fall back to current directory
    return Path.cwd()


def get_session_id(input_data: dict) -> str:
    """Get session identifier from input or generate one."""
    if input_data.get("session_id"):
        return input_data["session_id"]
    # Generate based on timestamp
    return datetime.now().strftime("%H%M%S")


def extract_learnings_from_handoffs(project_root: Path, session_id: str) -> dict:
    """Extract learnings from recent handoffs in the artifact index.

    This queries the artifact index for handoffs from this session
    and extracts their what_worked, what_failed, and key_decisions.
    """
    learnings = {
        "what_worked": [],
        "what_failed": [],
        "key_decisions": [],
        "patterns": [],
    }

    # Try to query artifact index if available
    artifact_query_path = project_root / "default" / "lib" / "artifact-index" / "artifact_query.py"
    if not artifact_query_path.exists():
        # Artifact index not available yet, return empty
        return learnings

    # Import and query (would be implemented when artifact index exists)
    # For now, return empty learnings
    return learnings


def extract_learnings_from_outcomes(project_root: Path, session_id: str) -> dict:
    """Extract learnings from session outcomes.

    This looks at the outcome (SUCCEEDED/FAILED) and extracts
    relevant context for learning.
    """
    learnings = {
        "what_worked": [],
        "what_failed": [],
        "key_decisions": [],
        "patterns": [],
    }

    # Check for outcome file
    state_dir = project_root / ".ring" / "state"
    outcome_file = state_dir / "session-outcome.json"

    if outcome_file.exists():
        try:
            with open(outcome_file) as f:
                outcome = json.load(f)

            status = outcome.get("status", "unknown")
            if status in ["SUCCEEDED", "PARTIAL_PLUS"]:
                if outcome.get("summary"):
                    learnings["what_worked"].append(outcome["summary"])
            elif status in ["FAILED", "PARTIAL_MINUS"]:
                if outcome.get("summary"):
                    learnings["what_failed"].append(outcome["summary"])

            if outcome.get("key_decisions"):
                learnings["key_decisions"].extend(outcome["key_decisions"])

        except (json.JSONDecodeError, KeyError):
            pass

    return learnings


def save_learnings(project_root: Path, session_id: str, learnings: dict) -> Path:
    """Save learnings to cache file.

    Args:
        project_root: Project root directory
        session_id: Session identifier
        learnings: Extracted learnings dictionary

    Returns:
        Path to saved learnings file
    """
    # Create learnings directory
    learnings_dir = project_root / ".ring" / "cache" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{session_id}.md"
    file_path = learnings_dir / filename

    # Generate content
    content = f"""# Learnings from Session {session_id}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## What Worked

"""
    for item in learnings.get("what_worked", []):
        content += f"- {item}\n"
    if not learnings.get("what_worked"):
        content += "- (No successful patterns recorded)\n"

    content += """
## What Failed

"""
    for item in learnings.get("what_failed", []):
        content += f"- {item}\n"
    if not learnings.get("what_failed"):
        content += "- (No failures recorded)\n"

    content += """
## Key Decisions

"""
    for item in learnings.get("key_decisions", []):
        content += f"- {item}\n"
    if not learnings.get("key_decisions"):
        content += "- (No key decisions recorded)\n"

    content += """
## Patterns

"""
    for item in learnings.get("patterns", []):
        content += f"- {item}\n"
    if not learnings.get("patterns"):
        content += "- (No patterns identified)\n"

    # Write file
    file_path.write_text(content)
    return file_path


def main():
    """Main hook entry point."""
    input_data = read_stdin()

    # Only process on actual session end (not errors)
    if input_data.get("type") != "stop":
        print(json.dumps({"result": "continue"}))
        return

    project_root = get_project_root()
    session_id = get_session_id(input_data)

    # Combine learnings from different sources
    learnings = {
        "what_worked": [],
        "what_failed": [],
        "key_decisions": [],
        "patterns": [],
    }

    # Extract from handoffs (if artifact index available)
    handoff_learnings = extract_learnings_from_handoffs(project_root, session_id)
    for key in learnings:
        learnings[key].extend(handoff_learnings.get(key, []))

    # Extract from outcomes (if outcome tracking available)
    outcome_learnings = extract_learnings_from_outcomes(project_root, session_id)
    for key in learnings:
        learnings[key].extend(outcome_learnings.get(key, []))

    # Check if we have any learnings to save
    has_learnings = any(learnings.get(key) for key in learnings)

    if has_learnings:
        file_path = save_learnings(project_root, session_id, learnings)
        message = f"Session learnings saved to {file_path.relative_to(project_root)}"
    else:
        message = "No learnings extracted from this session (no handoffs or outcomes recorded)"

    # Output hook response
    output = {
        "result": "continue",
        "message": message,
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x default/hooks/learning-extract.py`

**Step 3: Test the hook manually**

Run: `echo '{"type": "stop", "session_id": "test123"}' | python3 default/hooks/learning-extract.py`

**Expected output:**
```json
{"result": "continue", "message": "No learnings extracted from this session (no handoffs or outcomes recorded)"}
```

**Step 4: Commit**

```bash
git add default/hooks/learning-extract.py
git commit -m "feat(compound-learnings): add learning extraction hook script"
```

**If Task Fails:**

1. **JSON parse error:**
   - Check: Input format matches expected schema
   - Fix: Validate JSON before parsing
   - Rollback: `git checkout -- .`

2. **Permission denied:**
   - Check: `chmod +x` was applied
   - Fix: Re-run chmod command
   - Rollback: `git checkout -- .`

---

## Task 7: Create Learning Extraction Shell Wrapper

**Files:**
- Create: `default/hooks/learning-extract.sh`

**Prerequisites:**
- Tools: bash
- Files must exist: `default/hooks/learning-extract.py`
- Environment: None

**Step 1: Create shell wrapper**

```bash
#!/usr/bin/env bash
# Learning extraction hook wrapper
# Calls Python script for SessionEnd learning extraction

set -euo pipefail

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find Python interpreter
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    # Python not available - output minimal JSON response
    echo '{"result": "continue", "error": "Python not available for learning extraction"}'
    exit 0
fi

# Pass stdin to Python script
cat | "$PYTHON_CMD" "${SCRIPT_DIR}/learning-extract.py"
```

**Step 2: Make script executable**

Run: `chmod +x default/hooks/learning-extract.sh`

**Step 3: Test the wrapper**

Run: `echo '{"type": "stop", "session_id": "test456"}' | bash default/hooks/learning-extract.sh`

**Expected output:**
```json
{"result": "continue", "message": "No learnings extracted from this session (no handoffs or outcomes recorded)"}
```

**Step 4: Commit**

```bash
git add default/hooks/learning-extract.sh
git commit -m "feat(compound-learnings): add learning extraction shell wrapper"
```

**If Task Fails:**

1. **Script not found:**
   - Check: `ls -la default/hooks/learning-extract.*`
   - Fix: Ensure both .py and .sh exist
   - Rollback: `git checkout -- .`

---

## Task 8: Register Learning Extraction Hook

**Files:**
- Modify: `default/hooks/hooks.json`

**Prerequisites:**
- Tools: None
- Files must exist: `default/hooks/hooks.json`, `default/hooks/learning-extract.sh`
- Environment: None

**Step 1: Read current hooks.json**

Run: `cat default/hooks/hooks.json`

**Step 2: Update hooks.json to add Stop hook**

The updated hooks.json should include a Stop event handler:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      },
      {
        "matcher": "clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-reminder.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/learning-extract.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 3: Verify JSON is valid**

Run: `python3 -c "import json; json.load(open('default/hooks/hooks.json'))"; echo "JSON valid"`

**Expected output:**
```
JSON valid
```

**Step 4: Commit**

```bash
git add default/hooks/hooks.json
git commit -m "feat(compound-learnings): register learning extraction in Stop hook"
```

**If Task Fails:**

1. **Invalid JSON:**
   - Check: Use `python3 -m json.tool default/hooks/hooks.json`
   - Fix: Correct JSON syntax errors
   - Rollback: `git checkout default/hooks/hooks.json`

---

## Task 9: Create Compound Learnings Skill

**Files:**
- Create: `default/skills/compound-learnings/SKILL.md`

**Prerequisites:**
- Tools: None
- Files must exist: `default/lib/compound-learnings/`
- Environment: None

**Step 1: Create skill directory**

Run: `mkdir -p default/skills/compound-learnings`

**Step 2: Create SKILL.md**

```markdown
---
name: compound-learnings
description: |
  Use when asked to "analyze learnings", "find patterns", "what should become rules",
  "compound my learnings", or after accumulating 5+ session learnings. Analyzes
  session learnings to detect recurring patterns (3+ occurrences), categorizes them
  as rule/skill/hook candidates, and generates proposals for user approval.

trigger: |
  - "What patterns should become permanent?"
  - "Analyze my learnings"
  - "Compound learnings"
  - "Turn learnings into rules"
  - After completing a feature with multiple sessions

skip_when: |
  - Fewer than 3 learning files exist
  - Just completed first session (no patterns to detect yet)
  - Looking for specific past learning (use artifact search instead)

related:
  complementary: [handoff-tracking, artifact-query]
---

# Compound Learnings

Transform ephemeral session learnings into permanent, compounding capabilities.

## Overview

This skill analyzes accumulated learnings from past sessions, detects recurring patterns (appearing in 3+ sessions), and generates proposals for new rules, skills, or hooks. User approval is REQUIRED before creating any permanent artifacts.

**Core Principle:** The system improves itself over time by learning from successes and failures.

## When to Use

- "What should I learn from recent sessions?"
- "Improve my setup based on recent work"
- "Turn learnings into skills/rules"
- "What patterns should become permanent?"
- "Compound my learnings"
- After completing a multi-session feature

## When NOT to Use

- Fewer than 3 learning files exist (insufficient data)
- Looking for a specific past learning (use artifact search)
- First session on a new project (no history yet)

## Process

### Step 1: Gather Learnings

```bash
# List learnings (most recent first)
ls -t $PROJECT_ROOT/.ring/cache/learnings/*.md 2>/dev/null | head -20

# Count total learnings
ls $PROJECT_ROOT/.ring/cache/learnings/*.md 2>/dev/null | wc -l
```

**If fewer than 3 files:** STOP. Insufficient data for pattern detection.

Read the most recent 5-10 files for analysis.

### Step 2: Extract and Consolidate Patterns

For each learnings file, extract entries from:

| Section Header | What to Extract |
|----------------|-----------------|
| `## What Worked` | Success patterns |
| `## What Failed` | Anti-patterns (invert to rules) |
| `## Key Decisions` | Design principles |
| `## Patterns` | Direct pattern candidates |

**Consolidate similar patterns before counting:**

| Raw Patterns | Consolidated To |
|--------------|-----------------|
| "Check artifacts before editing", "Verify outputs first", "Look before editing" | "Observe outputs before editing code" |
| "TDD approach", "Test-driven development", "Write tests first" | "Use TDD workflow" |

Use the most general formulation.

### Step 3: Detect Recurring Patterns

**Signal thresholds:**

| Occurrences | Action |
|-------------|--------|
| 1 | Skip (insufficient signal) |
| 2 | Consider - present to user for information only |
| 3+ | Strong signal - recommend creating permanent artifact |
| 4+ | Definitely create |

**Only patterns appearing in 3+ DIFFERENT sessions qualify for proposals.**

### Step 4: Categorize Patterns

For each qualifying pattern, determine artifact type:

```
Is it a sequence of commands/steps?
  → YES → SKILL (executable process)
  → NO ↓

Should it run automatically on an event?
  → YES → HOOK (SessionEnd, PostToolUse, etc.)
  → NO ↓

Is it "when X, do Y" or "never do X"?
  → YES → RULE (behavioral heuristic)
  → NO → Skip (not worth capturing)
```

**Examples:**

| Pattern | Type | Why |
|---------|------|-----|
| "Run tests before committing" | Hook (PreCommit) | Automatic gate |
| "Step-by-step debugging process" | Skill | Manual sequence |
| "Always use explicit file paths" | Rule | Behavioral heuristic |

### Step 5: Generate Proposals

Present each proposal in this format:

```markdown
---
## Pattern: [Generalized Name]

**Signal:** [N] sessions ([list session IDs])

**Category:** [rule / skill / hook]

**Rationale:** [Why this artifact type, why worth creating]

**Draft Content:**
[Preview of what would be created]

**Target Location:** `default/rules/[name].md` or `default/skills/[name]/SKILL.md`

**Your Action:** [APPROVE] / [REJECT] / [MODIFY]

---
```

### Step 6: WAIT FOR USER APPROVAL

**CRITICAL: DO NOT create any files without explicit user approval.**

User must explicitly say:
- "Approve" or "Create it" → Proceed to create
- "Reject" or "Skip" → Mark as rejected, do not create
- "Modify" → User provides changes, then re-propose

**NEVER assume approval. NEVER create without explicit consent.**

### Step 7: Create Approved Artifacts

#### For Rules:

```bash
# Create rule file
cat > default/rules/<slug>.md << 'EOF'
# [Rule Name]

**Context:** This rule emerged from [N] sessions where this pattern appeared.

## Pattern
[The reusable principle]

## DO
- [Concrete action]

## DON'T
- [Anti-pattern]

## Source Sessions
- [session-1]: [what happened]
- [session-2]: [what happened]
EOF
```

#### For Skills:

Create `default/skills/<slug>/SKILL.md` with:
- YAML frontmatter (name, description)
- Overview (what it does)
- When to Use (triggers)
- When NOT to Use
- Step-by-step process
- Source sessions

#### For Hooks:

Create shell wrapper + Python handler following Ring's hook patterns.
Register in `default/hooks/hooks.json`.

### Step 8: Archive Processed Learnings

After creating artifacts, move processed learnings:

```bash
# Create archive directory
mkdir -p $PROJECT_ROOT/.ring/cache/learnings/archived

# Move processed files (preserving them for reference)
mv $PROJECT_ROOT/.ring/cache/learnings/2025-*.md $PROJECT_ROOT/.ring/cache/learnings/archived/
```

### Step 9: Summary Report

```markdown
## Compounding Complete

**Learnings Analyzed:** [N] sessions
**Patterns Found:** [M]
**Artifacts Created:** [K]

### Created:
- Rule: `explicit-paths.md` - Always use explicit file paths
- Skill: `systematic-debugging` - Step-by-step debugging workflow

### Skipped (insufficient signal):
- "Pattern X" (2 occurrences - below threshold)

### Rejected by User:
- "Pattern Y" - User chose not to create

**Your setup is now permanently improved.**
```

## Quality Checks

Before creating any artifact:

1. **Is it general enough?** Would it apply in other projects?
2. **Is it specific enough?** Does it give concrete guidance?
3. **Does it already exist?** Check `default/rules/` and `default/skills/` first
4. **Is it the right type?** Sequences → skills, heuristics → rules

## Common Mistakes

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Creating without approval | Violates user consent | ALWAYS wait for explicit approval |
| Low-signal patterns | 1-2 occurrences is noise | Require 3+ session occurrences |
| Too specific | Won't apply elsewhere | Generalize to broader principle |
| Too vague | No actionable guidance | Include concrete DO/DON'T |
| Duplicate artifacts | Wastes space, confuses | Check existing rules/skills first |

## Files Reference

- Learnings input: `.ring/cache/learnings/*.md`
- Proposals: `.ring/cache/proposals/pending.json`
- History: `.ring/cache/proposals/history.json`
- Rules output: `default/rules/<name>.md`
- Skills output: `default/skills/<name>/SKILL.md`
- Hooks output: `default/hooks/<name>.sh`
```

**Step 3: Commit**

```bash
git add default/skills/compound-learnings/SKILL.md
git commit -m "feat(compound-learnings): add analysis and proposal skill"
```

**If Task Fails:**

1. **Directory already exists:**
   - Check: `ls default/skills/compound-learnings/`
   - Fix: Proceed with file creation
   - Rollback: `rm -rf default/skills/compound-learnings`

---

## Task 10: Create Compound Learnings Command

**Files:**
- Create: `default/commands/compound-learnings.md`

**Prerequisites:**
- Tools: None
- Files must exist: `default/skills/compound-learnings/SKILL.md`
- Environment: None

**Step 1: Create command file**

```markdown
---
name: compound-learnings
description: Analyze session learnings and propose new rules/skills
argument-hint: "[--approve <id>] [--reject <id>] [--list]"
---

Analyze accumulated session learnings to detect recurring patterns and propose new rules, skills, or hooks. Requires user approval before creating any permanent artifacts.

## Usage

```
/compound-learnings [options]
```

## Options

| Option | Description |
|--------|-------------|
| (none) | Analyze learnings and generate new proposals |
| `--list` | List pending proposals without analyzing |
| `--approve <id>` | Approve a specific proposal (e.g., `--approve proposal-1`) |
| `--reject <id>` | Reject a specific proposal with optional reason |
| `--history` | Show history of approved/rejected proposals |

## Examples

### Analyze Learnings (Default)
```
/compound-learnings
```
Analyzes all session learnings, detects patterns appearing 3+ times, and presents proposals.

### List Pending Proposals
```
/compound-learnings --list
```
Shows proposals waiting for approval without re-analyzing.

### Approve a Proposal
```
/compound-learnings --approve proposal-1
```
Creates the rule/skill from the approved proposal.

### Reject a Proposal
```
/compound-learnings --reject proposal-2 "Too project-specific"
```
Marks proposal as rejected with reason.

### View History
```
/compound-learnings --history
```
Shows all past approvals and rejections.

## Process

The command follows this workflow:

### 1. Gather (Automatic)
- Reads `.ring/cache/learnings/*.md` files
- Counts total sessions available

### 2. Analyze (Automatic)
- Extracts patterns from What Worked, What Failed, Key Decisions
- Consolidates similar patterns
- Detects patterns appearing in 3+ sessions

### 3. Categorize (Automatic)
- Classifies patterns as rule, skill, or hook candidates
- Generates preview content for each

### 4. Propose (Interactive)
- Presents each qualifying pattern
- Shows draft content
- Waits for your decision

### 5. Create (On Approval)
- Creates rule/skill/hook in appropriate location
- Updates proposal history
- Archives processed learnings

## Output Example

```markdown
## Compound Learnings Analysis

**Sessions Analyzed:** 12
**Patterns Detected:** 8
**Qualifying (3+ sessions):** 3

---

### Proposal 1: Always use explicit file paths

**Signal:** 5 sessions (abc, def, ghi, jkl, mno)
**Category:** Rule
**Sources:** patterns, what_worked

**Preview:**
```
# Always use explicit file paths
## Pattern
Never use relative paths like "./file" - always use absolute paths.
...
```

**Action Required:** Type `approve`, `reject`, or `modify`

---
```

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `compound-learnings` skill | Underlying skill with full process details |
| `handoff-tracking` | Provides source data (what_worked, what_failed) |
| `artifact-query` | Search past handoffs for context |

## Troubleshooting

### "No learnings found"
No `.ring/cache/learnings/*.md` files exist. Complete some sessions with outcome tracking enabled.

### "Insufficient data for patterns"
Fewer than 3 learning files. Continue working - patterns emerge after multiple sessions.

### "Pattern already exists"
Check `default/rules/` and `default/skills/` - a similar rule or skill may already exist.

### "Proposal not found"
The proposal ID doesn't exist in pending.json. Run `/compound-learnings --list` to see current proposals.
```

**Step 2: Commit**

```bash
git add default/commands/compound-learnings.md
git commit -m "feat(compound-learnings): add /compound-learnings command"
```

**If Task Fails:**

1. **File already exists:**
   - Check: `ls default/commands/compound-learnings.md`
   - Fix: Update existing file
   - Rollback: `git checkout default/commands/compound-learnings.md`

---

## Task 11: Run Code Review

**REQUIRED SUB-SKILL:** Use requesting-code-review

1. **Dispatch all 3 reviewers in parallel:**
   - code-reviewer
   - business-logic-reviewer
   - security-reviewer

2. **Handle findings by severity:**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments)
- Re-run all 3 reviewers after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code
- Format: `TODO(review): [Issue description] (reported by [reviewer], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer], severity: Cosmetic)`

3. **Proceed only when:**
   - Zero Critical/High/Medium issues
   - All Low issues have TODO comments
   - All Cosmetic issues have FIXME comments

---

## Task 12: Integration Testing

**Files:**
- Test: All files created in previous tasks

**Prerequisites:**
- All previous tasks completed
- Clean git state

**Step 1: Test learning extraction hook end-to-end**

```bash
# Create test learning file manually
mkdir -p .ring/cache/learnings
cat > .ring/cache/learnings/2025-12-27-test001.md << 'EOF'
# Learnings from Session test001

**Date:** 2025-12-27 10:00:00

## What Worked
- Using TDD approach
- Breaking tasks into small commits

## What Failed
- Trying to implement everything at once

## Key Decisions
- Chose SQLite for simplicity

## Patterns
- Always run tests before committing
EOF

# Create second test learning
cat > .ring/cache/learnings/2025-12-27-test002.md << 'EOF'
# Learnings from Session test002

**Date:** 2025-12-27 11:00:00

## What Worked
- TDD workflow
- Incremental commits

## What Failed
- Skipping planning phase

## Key Decisions
- Used Python for portability

## Patterns
- Run tests before commit
EOF

# Create third test learning (meets 3+ threshold)
cat > .ring/cache/learnings/2025-12-27-test003.md << 'EOF'
# Learnings from Session test003

**Date:** 2025-12-27 12:00:00

## What Worked
- Test-driven development
- Small atomic commits

## What Failed
- No planning upfront

## Key Decisions
- SQLite over PostgreSQL

## Patterns
- Test before committing changes
EOF
```

**Step 2: Test pattern detection**

```bash
cd default/lib/compound-learnings
python3 << 'EOF'
from learning_parser import load_all_learnings
from pattern_detector import detect_recurring_patterns, generate_pattern_summary
from pathlib import Path
import os

# Find project root
project_root = Path(os.getcwd()).parent.parent.parent
learnings_dir = project_root / ".ring" / "cache" / "learnings"

print(f"Loading learnings from: {learnings_dir}")
learnings = load_all_learnings(learnings_dir)
print(f"Loaded {len(learnings)} learnings")

recurring = detect_recurring_patterns(learnings, min_occurrences=3)
print(f"Found {len(recurring)} recurring patterns")

summary = generate_pattern_summary(recurring)
print(summary)
EOF
```

**Expected output:**
```
Loading learnings from: /path/to/.ring/cache/learnings
Loaded 3 learnings
Found 1 recurring patterns
# Recurring Patterns Analysis

## Rule Candidates (1)

### Run tests before commit...
- **Occurrences:** 3 sessions
...
```

**Step 3: Test proposal generation**

```bash
cd default/lib/compound-learnings
python3 << 'EOF'
from learning_parser import load_all_learnings
from pattern_detector import detect_recurring_patterns
from rule_generator import generate_proposal, save_proposal
from pathlib import Path
import os
import json

project_root = Path(os.getcwd()).parent.parent.parent
learnings_dir = project_root / ".ring" / "cache" / "learnings"
proposals_dir = project_root / ".ring" / "cache" / "proposals"

learnings = load_all_learnings(learnings_dir)
recurring = detect_recurring_patterns(learnings, min_occurrences=3)
proposal = generate_proposal(recurring)

print(f"Generated proposal with {len(proposal['proposals'])} items")
saved_path = save_proposal(proposal, proposals_dir)
print(f"Saved to: {saved_path}")

# Verify
with open(saved_path) as f:
    loaded = json.load(f)
print(f"Verification: {loaded['total_proposals']} proposals in file")
EOF
```

**Expected output:**
```
Generated proposal with 1 items
Saved to: /path/to/.ring/cache/proposals/pending.json
Verification: 1 proposals in file
```

**Step 4: Clean up test files**

```bash
rm -rf .ring/cache/learnings/2025-12-27-test*.md
rm -rf .ring/cache/proposals/
```

**Step 5: Commit integration test verification**

```bash
git add -A
git commit -m "test(compound-learnings): verify integration works end-to-end"
```

**If Task Fails:**

1. **Import errors:**
   - Check: PYTHONPATH includes lib directory
   - Fix: Add `sys.path.insert(0, ...)` if needed
   - Rollback: Clean up test files manually

2. **File not found:**
   - Check: All paths are correct
   - Fix: Verify directory structure exists
   - Rollback: `rm -rf .ring/cache/learnings .ring/cache/proposals`

---

## Task 13: Final Documentation Update

**Files:**
- Modify: `default/skills/using-ring/SKILL.md` (add compound-learnings reference)

**Prerequisites:**
- All previous tasks completed and tested

**Step 1: Update using-ring skill**

Add compound-learnings to the skills overview in `default/skills/using-ring/SKILL.md`:

Under the appropriate section (likely "Available Skills" or similar), add:

```markdown
### Context & Self-Improvement

| Skill | Use When |
|-------|----------|
| `compound-learnings` | Analyze learnings from multiple sessions, detect patterns, propose new rules/skills |
```

**Step 2: Commit documentation update**

```bash
git add default/skills/using-ring/SKILL.md
git commit -m "docs: add compound-learnings to using-ring skill reference"
```

**If Task Fails:**

1. **using-ring structure differs:**
   - Check: Read the file to understand current structure
   - Fix: Adapt the addition to match existing format
   - Rollback: `git checkout default/skills/using-ring/SKILL.md`

---

## Summary

This plan creates the Compound Learnings feature (Phase 4 of Context Management System):

| Component | Files Created | Purpose |
|-----------|---------------|---------|
| **Library** | `default/lib/compound-learnings/*.py` | Pattern detection, rule generation |
| **Hook** | `default/hooks/learning-extract.{sh,py}` | Automatic learning extraction on SessionEnd |
| **Skill** | `default/skills/compound-learnings/SKILL.md` | Interactive analysis and proposal workflow |
| **Command** | `default/commands/compound-learnings.md` | `/compound-learnings` slash command |
| **Rules Dir** | `default/rules/` | Storage for generated rules |

**Key Requirements Met:**
- Learnings extracted automatically at session end
- Pattern detection requires 3+ occurrences
- User MUST approve before creating rules
- Generated rules follow Ring's rule format
- System improves itself over time (the compounding loop)

**Verification Command:**
```bash
# After all tasks complete, verify:
ls -la default/lib/compound-learnings/
ls -la default/hooks/learning-extract.*
ls -la default/skills/compound-learnings/
ls -la default/commands/compound-learnings.md
ls -la default/rules/
cat default/hooks/hooks.json | grep -A5 "Stop"
```

---

## Failure Recovery

**If any task fails and cannot be recovered:**

1. Document: What failed and the error message
2. Rollback: `git reset --hard HEAD~N` where N is commits to undo
3. Stop: Return to orchestrator with detailed failure report
4. Don't: Try to fix without understanding root cause

**Global Rollback (start over):**
```bash
git reset --hard origin/main
rm -rf .ring/cache/learnings .ring/cache/proposals
rm -rf default/lib/compound-learnings default/rules
git checkout default/hooks/hooks.json
```
