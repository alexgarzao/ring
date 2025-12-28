"""Tests for pattern_detector.py"""
import unittest

from pattern_detector import (
    normalize_pattern,
    find_similar_patterns,
    aggregate_patterns,
    detect_recurring_patterns,
    categorize_pattern,
    similarity_score,
    generate_pattern_summary,
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
                "what_failed": [],
            },
            {
                "session_id": "def",
                "patterns": ["always run tests before committing"],
                "what_worked": ["TDD workflow"],
                "what_failed": [],
            },
            {
                "session_id": "ghi",
                "patterns": ["test before committing changes"],
                "what_worked": ["test-driven development"],
                "what_failed": [],
            },
        ]
        recurring = detect_recurring_patterns(learnings, min_occurrences=3)
        # Should detect "run tests before commit" pattern (appears in 3 sessions)
        self.assertGreaterEqual(len(recurring), 1)

    def test_categorize_pattern_rule(self):
        """Test categorizing patterns as rules (heuristics)"""
        self.assertEqual(
            categorize_pattern("always run tests before committing"),
            "rule"
        )
        self.assertEqual(
            categorize_pattern("use explicit file paths"),
            "rule"
        )

    def test_categorize_pattern_skill(self):
        """Test categorizing patterns as skills (sequences/processes)"""
        self.assertEqual(
            categorize_pattern("step by step debugging process"),
            "skill"
        )
        self.assertEqual(
            categorize_pattern("follow these steps to deploy"),
            "skill"
        )

    def test_categorize_pattern_hook(self):
        """Test categorizing patterns as hooks (event triggers)"""
        self.assertEqual(
            categorize_pattern("on session end, save the state"),
            "hook"
        )
        self.assertEqual(
            categorize_pattern("automatically run lint after save"),
            "hook"
        )
        self.assertEqual(
            categorize_pattern("trigger validation on commit"),
            "hook"
        )

    def test_no_recurring_with_insufficient_data(self):
        """Test that insufficient data returns no patterns"""
        learnings = [
            {"session_id": "abc", "patterns": ["unique pattern"], "what_worked": [], "what_failed": []},
            {"session_id": "def", "patterns": ["another unique"], "what_worked": [], "what_failed": []},
        ]
        recurring = detect_recurring_patterns(learnings, min_occurrences=3)
        self.assertEqual(len(recurring), 0)

    def test_similarity_score_identical(self):
        """Test similarity score for identical strings"""
        self.assertEqual(similarity_score("test", "test"), 1.0)

    def test_similarity_score_similar(self):
        """Test similarity score for similar strings"""
        score = similarity_score("run tests before commit", "run tests before committing")
        self.assertGreater(score, 0.8)

    def test_similarity_score_different(self):
        """Test similarity score for different strings"""
        score = similarity_score("completely different", "no match at all")
        self.assertLess(score, 0.5)

    def test_generate_pattern_summary_empty(self):
        """Test summary generation with no patterns"""
        summary = generate_pattern_summary([])
        self.assertIn("No recurring patterns", summary)

    def test_generate_pattern_summary_with_patterns(self):
        """Test summary generation with patterns"""
        patterns = [
            {
                "canonical": "Test pattern for rules",
                "occurrences": 3,
                "sessions": ["a", "b", "c"],
                "category": "rule",
                "sources": ["patterns"]
            }
        ]
        summary = generate_pattern_summary(patterns)
        self.assertIn("# Recurring Patterns Analysis", summary)
        self.assertIn("Rule Candidates", summary)
        self.assertIn("Test pattern", summary)


if __name__ == "__main__":
    unittest.main()
