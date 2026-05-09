#!/usr/bin/env python3
"""Tests for generate-skills-ref.py frontmatter parsing and markdown generation."""

from pathlib import Path

import pytest

# We need to import the module by its filename (contains hyphens in concept but not in actual name)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "generate_skills_ref",
    Path(__file__).parent.parent / "generate-skills-ref.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

Skill = mod.Skill
condense_description = mod.condense_description
parse_frontmatter_yaml = mod.parse_frontmatter_yaml
parse_frontmatter_fallback = mod.parse_frontmatter_fallback
parse_skill_file = mod.parse_skill_file
scan_skills_directory = mod.scan_skills_directory
generate_markdown = mod.generate_markdown
scan_all_plugins = mod.scan_all_plugins


# ---------------------------------------------------------------------------
# condense_description()
# ---------------------------------------------------------------------------


class TestCondenseDescription:
    def test_empty_string(self):
        assert condense_description("") == ""

    def test_single_line_unchanged(self):
        assert condense_description("hello world") == "hello world"

    def test_multiline_collapsed(self):
        assert condense_description("hello\nworld") == "hello world"

    def test_collapses_runs_of_whitespace(self):
        assert condense_description("hello   \n   world") == "hello world"

    def test_strips_outer_whitespace(self):
        assert condense_description("  hello world  ") == "hello world"

    def test_none_input(self):
        # None must be treated as empty (`not text` falsy guard).
        assert condense_description(None) == ""


# ---------------------------------------------------------------------------
# parse_frontmatter_yaml()
# ---------------------------------------------------------------------------


class TestParseFrontmatterYaml:
    def test_valid_frontmatter(self):
        pytest.importorskip("yaml")
        content = "---\nname: test\ndescription: desc\n---\n# Body\n"
        result = parse_frontmatter_yaml(content)
        assert result["name"] == "test"

    def test_no_frontmatter(self):
        assert parse_frontmatter_yaml("# Just markdown") is None


# ---------------------------------------------------------------------------
# parse_frontmatter_fallback()
# ---------------------------------------------------------------------------


class TestParseFrontmatterFallback:
    def test_valid_frontmatter(self):
        content = "---\nname: test\ndescription: A skill\n---\n# Body\n"
        result = parse_frontmatter_fallback(content)
        assert result is not None
        assert result["name"] == "test"
        assert result["description"] == "A skill"

    def test_no_frontmatter(self):
        assert parse_frontmatter_fallback("# Just markdown") is None

    def test_block_scalar_description_joined(self):
        content = (
            "---\n"
            "name: test\n"
            "description: |\n"
            "  Line one of description.\n"
            "  Line two of description.\n"
            "---\n"
        )
        result = parse_frontmatter_fallback(content)
        assert result is not None
        assert "Line one" in result["description"]
        assert "Line two" in result["description"]

    def test_oversized_frontmatter_rejected(self):
        """Size guard: frontmatter > 10KB should return None."""
        huge = "---\nname: test\ndescription: " + "x" * 11000 + "\n---\n"
        result = parse_frontmatter_fallback(huge)
        assert result is None


# ---------------------------------------------------------------------------
# Skill constructor
# ---------------------------------------------------------------------------


class TestSkillConstructor:
    def test_basic_construction(self):
        s = Skill(name="ring:test", description="d", directory="test")
        assert s.name == "ring:test"
        assert s.description == "d"
        assert s.directory == "test"

    def test_categorize_pre_dev(self):
        s = Skill(name="x", description="d", directory="pre-dev-prd-creation")
        assert s.category == "Pre-Dev Workflow"

    def test_categorize_meta(self):
        s = Skill(name="x", description="d", directory="using-ring")
        assert s.category == "Meta Skills"

    def test_categorize_other(self):
        s = Skill(name="x", description="d", directory="random-thing")
        assert s.category == "Other"


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

    def test_multiline_description_condensed(self):
        s = Skill(
            name="ring:test",
            description="First line.\nSecond line.",
            directory="test",
        )
        result = generate_markdown([s])
        assert "First line. Second line." in result

    def test_skills_grouped_by_category(self):
        skills = [
            Skill(name="ring:a", description="d", directory="pre-dev-foo"),
            Skill(name="ring:b", description="d", directory="using-ring"),
        ]
        result = generate_markdown(skills)
        assert "Pre-Dev Workflow" in result
        assert "Meta Skills" in result

    def test_skill_count_in_category_heading(self):
        skills = [
            Skill(name="ring:a", description="d", directory="using-x"),
            Skill(name="ring:b", description="d", directory="using-y"),
        ]
        result = generate_markdown(skills)
        assert "Meta Skills (2 skills)" in result


# ---------------------------------------------------------------------------
# scan_all_plugins() — multi-plugin aggregation
# ---------------------------------------------------------------------------


class TestScanAllPlugins:
    def test_aggregates_across_plugins(self, tmp_path):
        """Skills from multiple plugin directories are aggregated."""
        # Plugin A
        skill_a = tmp_path / "default" / "skills" / "skill-a"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text(
            "---\nname: ring:skill-a\ndescription: First skill\n---\n# Body\n"
        )
        # Plugin B
        skill_b = tmp_path / "dev-team" / "skills" / "skill-b"
        skill_b.mkdir(parents=True)
        (skill_b / "SKILL.md").write_text(
            "---\nname: ring:skill-b\ndescription: Second skill\n---\n# Body\n"
        )
        # Missing plugin C is skipped silently
        result = scan_all_plugins(tmp_path, ["default", "dev-team", "pm-team"])
        names = sorted(s.name for s in result)
        assert names == ["ring:skill-a", "ring:skill-b"]


# ---------------------------------------------------------------------------
# scan_skills_directory() — filesystem scan
# ---------------------------------------------------------------------------


class TestScanSkillsDirectory:
    def test_skips_shared_patterns(self, tmp_path):
        # Real skill should be picked up; shared-patterns/ must be skipped
        # even when it contains a file named SKILL.md.
        real = tmp_path / "real-skill"
        real.mkdir()
        (real / "SKILL.md").write_text(
            "---\nname: ring:real\ndescription: real\n---\n"
        )
        shared = tmp_path / "shared-patterns"
        shared.mkdir()
        (shared / "SKILL.md").write_text(
            "---\nname: ring:should-not-appear\ndescription: nope\n---\n"
        )

        skills = scan_skills_directory(tmp_path)

        names = [s.name for s in skills]
        assert "ring:real" in names
        assert "ring:should-not-appear" not in names

    def test_skips_dirs_without_skill_md(self, tmp_path, capsys):
        # Subdirectories lacking SKILL.md are warned about and skipped.
        (tmp_path / "incomplete").mkdir()
        good = tmp_path / "good"
        good.mkdir()
        (good / "SKILL.md").write_text(
            "---\nname: ring:good\ndescription: ok\n---\n"
        )
        skills = scan_skills_directory(tmp_path)
        captured = capsys.readouterr()
        assert "Warning: No SKILL.md" in captured.err
        assert "incomplete" in captured.err
        assert [s.name for s in skills] == ["ring:good"]


# ---------------------------------------------------------------------------
# parse_skill_file() — edge cases
# ---------------------------------------------------------------------------


class TestParseSkillFileEdgeCases:
    def test_empty_frontmatter_returns_none(self, tmp_path):
        # Empty frontmatter (no name, no description) → None per contract.
        p = tmp_path / "SKILL.md"
        p.write_text("---\n---\n")
        assert parse_skill_file(p) is None

    def test_frontmatter_without_name_returns_none(self, tmp_path):
        # Missing required `name` → None.
        p = tmp_path / "SKILL.md"
        p.write_text("---\ndescription: only desc\n---\n")
        assert parse_skill_file(p) is None

    def test_frontmatter_without_description_defaults_empty(self, tmp_path):
        # Missing description is permitted at parse time; defaults to "".
        # (validate-frontmatter.py handles the schema-level error.)
        p = tmp_path / "SKILL.md"
        p.write_text("---\nname: ring:t\n---\n")
        s = parse_skill_file(p)
        assert s is not None
        assert s.name == "ring:t"
        assert s.description == ""

    def test_utf8_in_name_and_description_preserved(self, tmp_path):
        p = tmp_path / "SKILL.md"
        p.write_text(
            '---\nname: ring:t\ndescription: "Olá, ção, 中文, 🌟"\n---\n',
            encoding="utf-8",
        )
        s = parse_skill_file(p)
        assert s is not None
        assert s.name == "ring:t"
        assert s.description == "Olá, ção, 中文, 🌟"

    def test_returns_none_for_directory_passed_as_skill_md(self, tmp_path):
        # Passing a directory where SKILL.md is expected exercises the
        # broad except handler (open() on a directory raises IsADirectoryError).
        fake = tmp_path / "broken_skill"
        fake.mkdir()
        skill_md = fake / "SKILL.md"
        skill_md.mkdir()  # directory, not file
        result = parse_skill_file(skill_md)
        assert result is None
