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
    slugify,
    save_proposal,
    load_pending_proposals,
    approve_proposal,
    reject_proposal,
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

    def test_slugify(self):
        """Test converting text to slug"""
        self.assertEqual(slugify("Always Run Tests"), "always-run-tests")
        self.assertEqual(slugify("Use TDD!!!"), "use-tdd")
        self.assertEqual(slugify("Step-by-step Process"), "step-by-step-process")

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

    def test_generate_rule_for_avoid_pattern(self):
        """Test generating rule for anti-patterns (Avoid: ...)"""
        pattern = {
            "canonical": "Avoid: implementing everything at once",
            "occurrences": 3,
            "sessions": ["abc", "def", "ghi"],
            "sources": ["what_failed"],
        }
        content = generate_rule_content(pattern)
        self.assertIn("## DON'T", content)
        # Should have inverted DO/DON'T for avoid patterns
        self.assertIn("implementing everything at once", content)

    def test_slugify_empty_input(self):
        """Test slugify with empty or special-only input"""
        self.assertEqual(slugify(""), "unnamed-pattern")
        self.assertEqual(slugify("!@#$%"), "unnamed-pattern")
        self.assertEqual(slugify("   "), "unnamed-pattern")

    def test_save_and_load_proposal(self):
        """Test saving and loading proposal"""
        proposals_dir = self.test_dir / "proposals"

        proposal = {
            "generated": "2025-12-27T10:00:00",
            "total_proposals": 1,
            "proposals": [{"id": "proposal-1", "canonical": "Test", "status": "pending"}]
        }
        path = save_proposal(proposal, proposals_dir)

        self.assertTrue(path.exists())
        loaded = load_pending_proposals(proposals_dir)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["total_proposals"], 1)

    def test_load_pending_proposals_nonexistent(self):
        """Test loading from nonexistent directory"""
        proposals_dir = self.test_dir / "nonexistent"
        loaded = load_pending_proposals(proposals_dir)
        self.assertIsNone(loaded)

    def test_approve_proposal(self):
        """Test approving a proposal"""
        proposals_dir = self.test_dir / "proposals"

        proposal = {
            "generated": "2025-12-27T10:00:00",
            "total_proposals": 1,
            "proposals": [{"id": "proposal-1", "canonical": "Test", "status": "pending"}]
        }
        save_proposal(proposal, proposals_dir)

        result = approve_proposal("proposal-1", proposals_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "approved")
        self.assertIn("approved_at", result)

    def test_reject_proposal(self):
        """Test rejecting a proposal with reason"""
        proposals_dir = self.test_dir / "proposals"

        proposal = {
            "generated": "2025-12-27T10:00:00",
            "total_proposals": 1,
            "proposals": [{"id": "proposal-1", "canonical": "Test", "status": "pending"}]
        }
        save_proposal(proposal, proposals_dir)

        result = reject_proposal("proposal-1", proposals_dir, "Not useful")

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["rejection_reason"], "Not useful")

    def test_approve_nonexistent_proposal(self):
        """Test approving a proposal that doesn't exist"""
        proposals_dir = self.test_dir / "proposals"

        proposal = {
            "generated": "2025-12-27T10:00:00",
            "total_proposals": 1,
            "proposals": [{"id": "proposal-1", "canonical": "Test", "status": "pending"}]
        }
        save_proposal(proposal, proposals_dir)

        result = approve_proposal("proposal-999", proposals_dir)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
