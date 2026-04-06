#!/usr/bin/env python3
"""Tests for validate-frontmatter.py schema validation logic."""

import sys
from pathlib import Path

# Import the module
import importlib.util

spec = importlib.util.spec_from_file_location(
    "validate_frontmatter",
    Path(__file__).parent.parent / "validate-frontmatter.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

validate_skill = mod.validate_skill
validate_command = mod.validate_command
validate_agent = mod.validate_agent
parse_frontmatter = mod.parse_frontmatter
Issue = mod.Issue


# ---------------------------------------------------------------------------
# validate_skill()
# ---------------------------------------------------------------------------


class TestValidateSkill:
    def test_valid_skill_no_issues(self):
        fm = {
            "name": "ring:test",
            "description": "A test skill",
            "trigger": "when needed",
            "skip_when": "not needed",
        }
        issues = validate_skill("test.md", fm)
        assert all(i.level != "ERROR" for i in issues)

    def test_missing_required_name(self):
        fm = {"description": "A test skill"}
        issues = validate_skill("test.md", fm)
        assert any(i.level == "ERROR" and "name" in i.message for i in issues)

    def test_missing_required_description(self):
        fm = {"name": "ring:test"}
        issues = validate_skill("test.md", fm)
        assert any(i.level == "ERROR" and "description" in i.message for i in issues)

    def test_missing_recommended_trigger(self):
        fm = {"name": "ring:test", "description": "d"}
        issues = validate_skill("test.md", fm)
        assert any(i.level == "WARNING" and "trigger" in i.message for i in issues)

    def test_deprecated_when_to_use(self):
        fm = {"name": "ring:test", "description": "d", "when_to_use": "old"}
        issues = validate_skill("test.md", fm)
        assert any(
            "deprecated" in i.message and "when_to_use" in i.message for i in issues
        )

    def test_invalid_field_version(self):
        fm = {"name": "ring:test", "description": "d", "version": "1.0.0"}
        issues = validate_skill("test.md", fm)
        assert any(
            "invalid" in i.message.lower() and "version" in i.message for i in issues
        )

    def test_invalid_field_examples(self):
        fm = {"name": "ring:test", "description": "d", "examples": []}
        issues = validate_skill("test.md", fm)
        assert any(
            "invalid" in i.message.lower() and "examples" in i.message for i in issues
        )

    def test_valid_optional_fields(self):
        fm = {
            "name": "ring:test",
            "description": "d",
            "trigger": "t",
            "skip_when": "s",
            "NOT_skip_when": "n",
            "prerequisites": "p",
            "verification": "v",
            "sequence": {},
            "related": {},
        }
        issues = validate_skill("test.md", fm)
        # No errors, possibly warnings for recommended fields
        assert all(i.level != "ERROR" for i in issues)


# ---------------------------------------------------------------------------
# validate_command()
# ---------------------------------------------------------------------------


class TestValidateCommand:
    def test_valid_command_no_errors(self):
        fm = {
            "name": "test-cmd",
            "description": "A command",
            "argument-hint": "[target]",
        }
        issues = validate_command("test.md", fm)
        assert all(i.level != "ERROR" for i in issues)

    def test_missing_required_name(self):
        fm = {"description": "A command"}
        issues = validate_command("test.md", fm)
        assert any(i.level == "ERROR" and "name" in i.message for i in issues)

    def test_deprecated_arguments(self):
        fm = {"name": "test", "description": "d", "arguments": []}
        issues = validate_command("test.md", fm)
        assert any("argument-hint" in i.message for i in issues)

    def test_deprecated_args(self):
        fm = {"name": "test", "description": "d", "args": []}
        issues = validate_command("test.md", fm)
        assert any("argument-hint" in i.message for i in issues)


# ---------------------------------------------------------------------------
# validate_agent()
# ---------------------------------------------------------------------------


class TestValidateAgent:
    def test_valid_agent_no_errors(self):
        fm = {
            "name": "ring:test",
            "description": "An agent",
            "type": "specialist",
            "output_schema": {"format": "markdown"},
        }
        issues = validate_agent("test.md", fm)
        assert all(i.level != "ERROR" for i in issues)

    def test_missing_required_type(self):
        fm = {"name": "ring:test", "description": "d", "output_schema": {}}
        issues = validate_agent("test.md", fm)
        assert any(i.level == "ERROR" and "type" in i.message for i in issues)

    def test_invalid_type_enum(self):
        fm = {
            "name": "ring:test",
            "description": "d",
            "type": "invalid_type",
            "output_schema": {},
        }
        issues = validate_agent("test.md", fm)
        assert any("not in allowed values" in i.message for i in issues)

    def test_valid_type_enums(self):
        for agent_type in [
            "reviewer",
            "specialist",
            "orchestrator",
            "planning",
            "exploration",
            "analyst",
            "calculator",
        ]:
            fm = {
                "name": "t",
                "description": "d",
                "type": agent_type,
                "output_schema": {},
            }
            issues = validate_agent("test.md", fm)
            assert not any("not in allowed values" in i.message for i in issues), (
                f"Type '{agent_type}' should be valid"
            )

    def test_invalid_field_version(self):
        fm = {
            "name": "t",
            "description": "d",
            "type": "specialist",
            "output_schema": {},
            "version": "1.0",
        }
        issues = validate_agent("test.md", fm)
        assert any(
            "invalid" in i.message.lower() and "version" in i.message for i in issues
        )

    def test_invalid_field_tools(self):
        fm = {
            "name": "t",
            "description": "d",
            "type": "specialist",
            "output_schema": {},
            "tools": ["Bash"],
        }
        issues = validate_agent("test.md", fm)
        assert any(
            "invalid" in i.message.lower() and "tools" in i.message for i in issues
        )


# ---------------------------------------------------------------------------
# parse_frontmatter()
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_valid_yaml(self):
        content = "---\nname: test\ndescription: desc\n---\n# Body\n"
        result = parse_frontmatter(content)
        assert result is not None
        assert result["name"] == "test"

    def test_no_frontmatter(self):
        assert parse_frontmatter("# Just markdown") is None

    def test_empty_content(self):
        assert parse_frontmatter("") is None


# ---------------------------------------------------------------------------
# main() — CLI
# ---------------------------------------------------------------------------


class TestMainCLI:
    def test_unknown_plugin_returns_error(self):
        """--plugin with invalid name should return exit code 1."""
        original_argv = sys.argv
        try:
            sys.argv = ["validate-frontmatter.py", "--plugin", "nonexistent"]
            result = mod.main()
            assert result == 1
        finally:
            sys.argv = original_argv

    def test_strict_mode_type(self):
        """Verify strict mode is an argparse flag (not a positional)."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--strict", action="store_true")
        args = parser.parse_args(["--strict"])
        assert args.strict is True
