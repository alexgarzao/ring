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
discover_files = mod.discover_files
Issue = mod.Issue


# ---------------------------------------------------------------------------
# validate_skill()
# ---------------------------------------------------------------------------


class TestValidateSkill:
    def test_valid_skill_no_issues(self):
        fm = {
            "name": "ring:test",
            "description": "A test skill",
        }
        issues = validate_skill("test.md", fm)
        assert issues == []

    def test_missing_required_name(self):
        fm = {"description": "A test skill"}
        issues = validate_skill("test.md", fm)
        assert any(i.level == "ERROR" and "name" in i.message for i in issues)

    def test_missing_required_description(self):
        fm = {"name": "ring:test"}
        issues = validate_skill("test.md", fm)
        assert any(i.level == "ERROR" and "description" in i.message for i in issues)

    def test_unknown_field_warns(self):
        fm = {"name": "ring:test", "description": "d", "trigger": "old field"}
        issues = validate_skill("test.md", fm)
        assert any(
            i.level == "WARNING" and "trigger" in i.message for i in issues
        )

    def test_optional_canonical_fields_accepted(self):
        fm = {
            "name": "ring:test",
            "description": "d",
            "argument-hint": "[target]",
            "allowed-tools": ["Bash"],
            "disable-model-invocation": False,
            "user-invocable": True,
            "paths": ["**/*.go"],
            "model": "sonnet",
        }
        issues = validate_skill("test.md", fm)
        assert issues == []

    def test_missing_ring_prefix_errors(self):
        fm = {"name": "test", "description": "d"}
        issues = validate_skill("test.md", fm)
        assert any(
            i.level == "ERROR" and "ring:" in i.message and "prefix" in i.message
            for i in issues
        )

    def test_ring_prefix_passes(self):
        fm = {"name": "ring:test", "description": "d"}
        issues = validate_skill("test.md", fm)
        assert issues == []


# ---------------------------------------------------------------------------
# validate_command()
# ---------------------------------------------------------------------------


class TestValidateCommand:
    def test_valid_command_no_issues(self):
        fm = {
            "name": "ring:test-cmd",
            "description": "A command",
            "argument-hint": "[target]",
        }
        issues = validate_command("test.md", fm)
        assert issues == []

    def test_missing_required_name(self):
        fm = {"description": "A command"}
        issues = validate_command("test.md", fm)
        assert any(i.level == "ERROR" and "name" in i.message for i in issues)

    def test_unknown_field_warns(self):
        fm = {"name": "ring:test", "description": "d", "arguments": []}
        issues = validate_command("test.md", fm)
        assert any(
            i.level == "WARNING" and "arguments" in i.message for i in issues
        )

    def test_optional_canonical_fields_accepted(self):
        fm = {
            "name": "ring:test",
            "description": "d",
            "argument-hint": "[t]",
            "allowed-tools": ["Bash"],
            "model": "sonnet",
        }
        issues = validate_command("test.md", fm)
        assert issues == []

    def test_missing_ring_prefix_errors(self):
        fm = {"name": "test-cmd", "description": "d"}
        issues = validate_command("test.md", fm)
        assert any(
            i.level == "ERROR" and "ring:" in i.message and "prefix" in i.message
            for i in issues
        )


# ---------------------------------------------------------------------------
# validate_agent()
# ---------------------------------------------------------------------------


class TestValidateAgent:
    def test_valid_agent_no_issues(self):
        fm = {
            "name": "ring:test",
            "description": "An agent",
        }
        issues = validate_agent("test.md", fm)
        assert issues == []

    def test_missing_required_name(self):
        fm = {"description": "d"}
        issues = validate_agent("test.md", fm)
        assert any(i.level == "ERROR" and "name" in i.message for i in issues)

    def test_missing_required_description(self):
        fm = {"name": "ring:t"}
        issues = validate_agent("test.md", fm)
        assert any(i.level == "ERROR" and "description" in i.message for i in issues)

    def test_optional_canonical_fields_accepted(self):
        fm = {
            "name": "ring:test",
            "description": "d",
            "model": "sonnet",
            "tools": ["Bash"],
            "color": "blue",
        }
        issues = validate_agent("test.md", fm)
        assert issues == []

    def test_unknown_field_warns(self):
        fm = {"name": "ring:t", "description": "d", "type": "specialist"}
        issues = validate_agent("test.md", fm)
        assert any(
            i.level == "WARNING" and "type" in i.message for i in issues
        )

    def test_missing_ring_prefix_errors(self):
        fm = {"name": "agent-name", "description": "d"}
        issues = validate_agent("test.md", fm)
        assert any(
            i.level == "ERROR" and "ring:" in i.message and "prefix" in i.message
            for i in issues
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

    def test_empty_frontmatter_returns_none(self):
        # Frontmatter delimiters with nothing between → None (both YAML
        # and fallback parsers reject empty bodies).
        assert parse_frontmatter("---\n---\n") is None

    def test_frontmatter_with_only_whitespace(self):
        # Whitespace-only body → None.
        assert parse_frontmatter("---\n  \n---\n") is None

    def test_frontmatter_with_only_name_lacks_description(self):
        # name present but description missing → validate_skill emits ERROR.
        fm = parse_frontmatter("---\nname: ring:t\n---\n")
        assert fm == {"name": "ring:t"}
        issues = validate_skill("x.md", fm)
        assert any(
            i.level == "ERROR" and "description" in i.message for i in issues
        )

    def test_utf8_description_preserved(self):
        content = '---\nname: ring:t\ndescription: "Olá, ção, 中文, 🌟"\n---\n'
        result = parse_frontmatter(content)
        assert result is not None
        assert result["description"] == "Olá, ção, 中文, 🌟"

    def test_malformed_yaml_falls_back(self):
        # Unclosed quoted scalar trips PyYAML → fallback regex parser kicks in.
        content = '---\nname: ring:t\ndescription: "[unclosed\n---\n'

        # Sanity-pin: the YAML parser MUST reject this input, otherwise we are
        # never exercising the fallback path. PyYAML behavior changes could
        # otherwise let this test pass without testing what it claims to test.
        assert mod.parse_frontmatter_yaml(content) is None

        result = parse_frontmatter(content)
        assert result is not None
        assert result["name"] == "ring:t"
        # Fallback strips matched outer quotes only; an unclosed leading quote
        # is preserved verbatim along with the rest of the value.
        assert result["description"] == '"[unclosed'


# ---------------------------------------------------------------------------
# discover_files()
# ---------------------------------------------------------------------------


class TestDiscoverFiles:
    def test_discover_files_skips_shared_patterns(self, tmp_path):
        # Build a fake plugin layout: one real skill + a shared-patterns dir
        # that must be skipped entirely.
        plugin_dir = tmp_path / "default"
        skills_dir = plugin_dir / "skills"
        (skills_dir / "real-skill").mkdir(parents=True)
        (skills_dir / "real-skill" / "SKILL.md").write_text(
            "---\nname: ring:real\ndescription: x\n---\n"
        )
        (skills_dir / "shared-patterns").mkdir()
        (skills_dir / "shared-patterns" / "some-pattern.md").write_text(
            "---\nname: ring:bad\ndescription: y\n---\n"
        )

        skill_files, _, _ = discover_files(tmp_path, ["default"])

        assert any(p.name == "SKILL.md" for p in skill_files)
        assert not any("shared-patterns" in str(p) for p in skill_files)

    def test_discover_files_picks_up_commands_and_agents(self, tmp_path):
        # Sanity-pin: commands/ and agents/ directories are picked up
        # alongside skills/ — keeps shared-patterns skip from over-skipping.
        plugin_dir = tmp_path / "default"
        (plugin_dir / "commands").mkdir(parents=True)
        (plugin_dir / "commands" / "foo.md").write_text(
            "---\nname: ring:foo\ndescription: x\n---\n"
        )
        (plugin_dir / "agents").mkdir(parents=True)
        (plugin_dir / "agents" / "bar.md").write_text(
            "---\nname: ring:bar\ndescription: y\n---\n"
        )

        skills, commands, agents = discover_files(tmp_path, ["default"])
        assert skills == []
        assert any(p.name == "foo.md" for p in commands)
        assert any(p.name == "bar.md" for p in agents)


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

    def _make_fake_repo(self, tmp_path, skill_body):
        """Build a fake repo layout with one default-plugin skill.

        validate-frontmatter.py resolves repo_root as
        Path(__file__).resolve().parent.parent.parent — i.e. assumes the
        script lives at <repo_root>/default/hooks/<file>. We mirror that.
        """
        fake_script = tmp_path / "default" / "hooks" / "validate-frontmatter.py"
        fake_script.parent.mkdir(parents=True)
        fake_script.write_text("# fake")
        skill_dir = tmp_path / "default" / "skills" / "demo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(skill_body)
        return fake_script

    def test_main_returns_zero_on_valid_skill(self, tmp_path, monkeypatch):
        """Happy path: a single valid SKILL.md → main() returns 0."""
        fake_script = self._make_fake_repo(
            tmp_path,
            "---\nname: ring:demo\ndescription: A demo skill\n---\n# Body\n",
        )
        monkeypatch.setattr(mod, "__file__", str(fake_script))
        monkeypatch.setattr(sys, "argv", ["validate-frontmatter.py"])

        assert mod.main() == 0

    def test_main_strict_returns_one_on_warning(self, tmp_path, monkeypatch):
        """--strict + a warning-only finding → exit code 1."""
        # An unknown field triggers a WARNING (not ERROR). Without --strict
        # this would still return 0; --strict promotes warnings to failure.
        fake_script = self._make_fake_repo(
            tmp_path,
            "---\nname: ring:demo\ndescription: A demo skill\n"
            "trigger: legacy-field\n---\n# Body\n",
        )
        monkeypatch.setattr(mod, "__file__", str(fake_script))
        monkeypatch.setattr(
            sys, "argv", ["validate-frontmatter.py", "--strict"]
        )

        assert mod.main() == 1
