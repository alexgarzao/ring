"""Tests for learning_parser.py"""
import unittest
from pathlib import Path
import tempfile
import shutil

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

    def test_parse_missing_sections(self):
        """Test parsing file with missing sections"""
        sparse_content = """# Learnings from Session sparse

**Date:** 2025-12-27 12:00:00

## What Worked

- One thing worked
"""
        sparse_path = Path(self.test_dir) / "2025-12-27-sparse.md"
        sparse_path.write_text(sparse_content)

        result = parse_learning_file(sparse_path)
        self.assertEqual(result["session_id"], "sparse")
        self.assertEqual(len(result["what_worked"]), 1)
        self.assertEqual(len(result["what_failed"]), 0)
        self.assertEqual(len(result["patterns"]), 0)


    def test_extract_session_id_with_date_prefix(self):
        """Test session ID extraction from filename with date"""
        from learning_parser import _extract_session_id
        self.assertEqual(_extract_session_id("2025-12-27-abc123"), "abc123")
        self.assertEqual(_extract_session_id("2025-12-27-multi-part-id"), "multi-part-id")

    def test_extract_session_id_date_only(self):
        """Test session ID extraction from date-only filename"""
        from learning_parser import _extract_session_id
        # Date-only filenames should return empty string
        self.assertEqual(_extract_session_id("2025-12-27"), "")

    def test_extract_session_id_no_hyphens(self):
        """Test session ID extraction from filename without hyphens"""
        from learning_parser import _extract_session_id
        self.assertEqual(_extract_session_id("session"), "session")

    def test_load_all_learnings(self):
        """Test loading all learning files from directory"""
        # Create second learning file with earlier date
        second_learning = Path(self.test_dir) / "2025-12-26-def456.md"
        second_learning.write_text("""# Learnings from Session def456

**Date:** 2025-12-26 08:00:00

## What Worked

- Something else worked
""")
        from learning_parser import load_all_learnings
        learnings = load_all_learnings(Path(self.test_dir))

        self.assertEqual(len(learnings), 2)
        # Should be sorted newest first (by date string)
        self.assertEqual(learnings[0]["session_id"], "abc123")

    def test_load_all_learnings_empty_dir(self):
        """Test loading from empty directory"""
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir()

        from learning_parser import load_all_learnings
        learnings = load_all_learnings(empty_dir)

        self.assertEqual(learnings, [])

    def test_load_all_learnings_nonexistent_dir(self):
        """Test loading from non-existent directory"""
        from learning_parser import load_all_learnings
        learnings = load_all_learnings(Path("/nonexistent/path"))

        self.assertEqual(learnings, [])


if __name__ == "__main__":
    unittest.main()
