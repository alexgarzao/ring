#!/usr/bin/env python3
"""Tests for generate-skills-ref.py frontmatter parsing and markdown generation."""

import sys
from pathlib import Path

# Add parent directory to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

# We need to import the module by its filename (contains hyphens in concept but not in actual name)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "generate_skills_ref",
    Path(__file__).parent.parent / "generate-skills-ref.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

Skill = mod.Skill
first_line = mod.first_line
parse_frontmatter_yaml = mod.parse_frontmatter_yaml
parse_frontmatter_fallback = mod.parse_frontmatter_fallback
parse_skill_file = mod.parse_skill_file
generate_markdown = mod.generate_markdown
_safe_display_text = mod._safe_display_text
_format_prerequisites = mod._format_prerequisites
_format_verification = mod._format_verification


# ---------------------------------------------------------------------------
# first_line()
# ---------------------------------------------------------------------------


class TestFirstLine:
    def test_empty_string(self):
        assert first_line("") == ""

    def test_none_input(self):
        assert first_line(None) == ""

    def test_single_line(self):
        assert first_line("hello world") == "hello world"

    def test_multiline_takes_first(self):
        assert first_line("first\nsecond\nthird") == "first"

    def test_list_item_strips_marker(self):
        assert first_line("- first item\n- second") == "first item"

    def test_whitespace_stripped(self):
        assert first_line("  spaced  \n  text  ") == "spaced"


# ---------------------------------------------------------------------------
# _safe_display_text()
# ---------------------------------------------------------------------------


class TestSafeDisplayText:
    def test_none_returns_empty(self):
        assert _safe_display_text(None) == ""

    def test_string_returns_first_line(self):
        assert _safe_display_text("hello\nworld") == "hello"

    def test_empty_string_returns_empty(self):
        assert _safe_display_text("") == ""

    def test_dict_returns_empty(self):
        """Dicts are not suitable for one-line display."""
        assert _safe_display_text({"key": "value"}) == ""

    def test_list_joins_names(self):
        assert _safe_display_text(["a", "b"]) == "a, b"

    def test_list_of_dicts_extracts_names(self):
        result = _safe_display_text([{"name": "pkg_a"}, {"name": "pkg_b"}])
        assert result == "pkg_a, pkg_b"

    def test_list_with_none_items_filtered(self):
        assert _safe_display_text(["a", None, "b"]) == "a, b"

    def test_empty_list_returns_empty(self):
        assert _safe_display_text([]) == ""


# ---------------------------------------------------------------------------
# _format_prerequisites()
# ---------------------------------------------------------------------------


class TestFormatPrerequisites:
    def test_none_returns_empty(self):
        assert _format_prerequisites(None) == ""

    def test_string(self):
        assert _format_prerequisites("framework installed") == "framework installed"

    def test_list_of_strings(self):
        assert _format_prerequisites(["a", "b"]) == "a, b"

    def test_list_of_dicts_with_name(self):
        result = _format_prerequisites([{"name": "pkg_a"}, {"name": "pkg_b"}])
        assert result == "pkg_a, pkg_b"

    def test_empty_list(self):
        assert _format_prerequisites([]) == ""

    def test_list_with_none_items(self):
        assert _format_prerequisites(["a", None, "b"]) == "a, b"

    def test_mixed_list(self):
        result = _format_prerequisites([{"name": "a"}, "b"])
        assert result == "a, b"

    def test_dict_without_name_falls_back_to_str(self):
        result = _format_prerequisites([{"other": "x"}])
        assert "other" in result  # str(dict) representation


# ---------------------------------------------------------------------------
# _format_verification()
# ---------------------------------------------------------------------------


class TestFormatVerification:
    def test_none_returns_empty(self):
        assert _format_verification(None) == ""

    def test_string(self):
        assert _format_verification("all tests pass") == "all tests pass"

    def test_empty_string(self):
        assert _format_verification("") == ""

    def test_nested_dict_with_automated(self):
        val = {
            "automated": [{"command": "go test ./...", "description": "Go tests pass"}],
            "manual": None,
        }
        result = _format_verification(val)
        assert result == "Go tests pass"

    def test_nested_dict_automated_without_description(self):
        val = {"automated": [{"command": "go test ./..."}]}
        result = _format_verification(val)
        assert result == "go test ./..."

    def test_nested_dict_manual_only(self):
        val = {"automated": [], "manual": ["Check logs"]}
        result = _format_verification(val)
        assert result == "Check logs"

    def test_empty_dict(self):
        assert _format_verification({}) == ""

    def test_dict_with_none_manual(self):
        val = {"automated": [], "manual": None}
        assert _format_verification(val) == ""

    def test_does_not_produce_raw_dict_string(self):
        """Critical: must never produce {'automated': ...} in output."""
        val = {"automated": [{"command": "test"}], "manual": None}
        result = _format_verification(val)
        assert "{'automated'" not in result
        assert "{'" not in result


# ---------------------------------------------------------------------------
# Skill constructor — None coalescing
# ---------------------------------------------------------------------------


class TestSkillConstructor:
    def test_none_skip_when_coalesced(self):
        s = Skill(name="test", description="d", directory="d", skip_when=None)
        assert s.skip_when == ""

    def test_none_not_skip_when_coalesced(self):
        s = Skill(name="test", description="d", directory="d", not_skip_when=None)
        assert s.not_skip_when == ""

    def test_none_prerequisites_coalesced(self):
        s = Skill(name="test", description="d", directory="d", prerequisites=None)
        assert s.prerequisites == ""

    def test_none_verification_coalesced(self):
        s = Skill(name="test", description="d", directory="d", verification=None)
        assert s.verification == ""

    def test_dict_prerequisites_preserved(self):
        """Dicts should be preserved (not coalesced to '') for _format_prerequisites."""
        val = [{"name": "a"}]
        s = Skill(name="test", description="d", directory="d", prerequisites=val)
        assert s.prerequisites == val

    def test_dict_verification_preserved(self):
        """Dicts should be preserved for _format_verification."""
        val = {"automated": [{"command": "test"}]}
        s = Skill(name="test", description="d", directory="d", verification=val)
        assert s.verification == val


# ---------------------------------------------------------------------------
# parse_frontmatter_yaml()
# ---------------------------------------------------------------------------


class TestParseFrontmatterYaml:
    def test_valid_frontmatter(self):
        content = "---\nname: test\ndescription: desc\n---\n# Body\n"
        result = parse_frontmatter_yaml(content)
        if result is not None:  # Only if pyyaml available
            assert result["name"] == "test"

    def test_no_frontmatter(self):
        assert parse_frontmatter_yaml("# Just markdown") is None

    def test_empty_yaml_value_returns_none_key(self):
        """YAML empty value produces None — verify we handle this."""
        content = "---\nname: test\nverification:\n---\n# Body\n"
        result = parse_frontmatter_yaml(content)
        if result is not None:
            assert "verification" in result
            assert result["verification"] is None  # This is the dict.get trap


# ---------------------------------------------------------------------------
# parse_frontmatter_fallback()
# ---------------------------------------------------------------------------


class TestParseFrontmatterFallback:
    def test_valid_frontmatter(self):
        content = "---\nname: test\ndescription: A skill\n---\n# Body\n"
        result = parse_frontmatter_fallback(content)
        assert result is not None
        assert result["name"] == "test"

    def test_no_frontmatter(self):
        assert parse_frontmatter_fallback("# Just markdown") is None

    def test_includes_new_fields(self):
        content = (
            "---\n"
            "name: test\n"
            "NOT_skip_when: override\n"
            "prerequisites: some prereq\n"
            "verification: all pass\n"
            "---\n"
        )
        result = parse_frontmatter_fallback(content)
        assert result is not None
        assert "NOT_skip_when" in result
        assert "prerequisites" in result
        assert "verification" in result

    def test_oversized_frontmatter_rejected(self):
        """Size guard: frontmatter > 10KB should return None."""
        huge = "---\nname: test\ndescription: " + "x" * 11000 + "\n---\n"
        result = parse_frontmatter_fallback(huge)
        assert result is None


# ---------------------------------------------------------------------------
# generate_markdown() — integration
# ---------------------------------------------------------------------------


class TestGenerateMarkdown:
    def test_empty_skills_list(self):
        result = generate_markdown([])
        assert "No skills found" in result

    def test_single_skill_basic(self):
        s = Skill(name="ring:test", description="Test skill", directory="test")
        result = generate_markdown([s])
        assert "ring:test" in result
        assert "Test skill" in result

    def test_skip_when_rendered(self):
        s = Skill(
            name="ring:test",
            description="d",
            directory="test",
            skip_when="No code changes",
        )
        result = generate_markdown([s])
        assert "Skip when: No code changes" in result

    def test_not_skip_when_rendered(self):
        s = Skill(
            name="ring:test",
            description="d",
            directory="test",
            not_skip_when="Code is simple still needs review",
        )
        result = generate_markdown([s])
        assert "NOT skip when:" in result

    def test_none_values_not_rendered(self):
        """None values should not appear as 'None' string in output."""
        s = Skill(
            name="ring:test",
            description="d",
            directory="test",
            skip_when=None,
            not_skip_when=None,
            prerequisites=None,
            verification=None,
        )
        result = generate_markdown([s])
        assert "None" not in result

    def test_dict_verification_not_raw(self):
        """Dict verification should not appear as raw Python repr."""
        s = Skill(
            name="ring:test",
            description="d",
            directory="test",
            verification={"automated": [{"command": "test"}]},
        )
        result = generate_markdown([s])
        assert "{'automated'" not in result

    def test_prerequisites_list_rendered(self):
        s = Skill(
            name="ring:test",
            description="d",
            directory="test",
            prerequisites=[{"name": "a"}, {"name": "b"}],
        )
        result = generate_markdown([s])
        assert "Prerequisites: a, b" in result
