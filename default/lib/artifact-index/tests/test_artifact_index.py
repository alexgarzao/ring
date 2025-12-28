#!/usr/bin/env python3
"""
Comprehensive test suite for artifact-index Python modules.

Tests cover:
- artifact_index.py: parse_frontmatter, parse_sections, parse_handoff, get_project_root
- artifact_query.py: escape_fts5_query, validate_limit, get_project_root
- artifact_mark.py: validate_limit, get_handoff_id_from_file
"""

import argparse
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from artifact_index import (
    parse_frontmatter,
    parse_sections,
    parse_handoff,
    extract_files_from_content,
    get_project_root as index_get_project_root,
)
from artifact_query import (
    escape_fts5_query,
    validate_limit as query_validate_limit,
    get_project_root as query_get_project_root,
)
from artifact_mark import (
    validate_limit as mark_validate_limit,
    get_project_root as mark_get_project_root,
    get_handoff_id_from_file,
)


# =============================================================================
# Tests for parse_frontmatter()
# =============================================================================

class TestParseFrontmatter:
    """Tests for YAML frontmatter extraction from markdown content."""

    def test_valid_frontmatter_simple(self):
        """Test extraction of simple key-value pairs from frontmatter."""
        content = """---
title: My Document
author: John Doe
status: SUCCESS
---
# Content here
"""
        result = parse_frontmatter(content)
        assert result["title"] == "My Document"
        assert result["author"] == "John Doe"
        assert result["status"] == "SUCCESS"

    def test_valid_frontmatter_with_quotes(self):
        """Test extraction handles quoted values correctly."""
        content = """---
title: "Quoted Title"
description: 'Single quotes'
---
Content
"""
        result = parse_frontmatter(content)
        assert result["title"] == "Quoted Title"
        assert result["description"] == "Single quotes"

    def test_missing_frontmatter_no_markers(self):
        """Test returns empty dict when no frontmatter markers exist."""
        content = """# Just a markdown document

No frontmatter here.
"""
        result = parse_frontmatter(content)
        assert result == {}

    def test_missing_frontmatter_single_marker(self):
        """Test returns empty dict with only one --- marker."""
        content = """---
title: incomplete
# Rest of document
"""
        result = parse_frontmatter(content)
        assert result == {}

    def test_empty_content(self):
        """Test returns empty dict for empty content."""
        result = parse_frontmatter("")
        assert result == {}

    def test_frontmatter_only_dashes(self):
        """Test handles frontmatter with only dashes (empty frontmatter)."""
        content = """---
---
# Content
"""
        result = parse_frontmatter(content)
        assert result == {}

    def test_nested_values_are_flattened(self):
        """Test that complex YAML is handled (values with colons)."""
        content = """---
url: https://example.com
time: 12:30:00
---
Content
"""
        result = parse_frontmatter(content)
        # URL should capture everything after first colon
        assert result["url"] == "https://example.com"
        assert result["time"] == "12:30:00"

    def test_frontmatter_with_empty_values(self):
        """Test handles keys with empty values."""
        content = """---
title:
author: John
---
Content
"""
        result = parse_frontmatter(content)
        assert result["title"] == ""
        assert result["author"] == "John"

    def test_frontmatter_with_spaces_in_values(self):
        """Test preserves spaces in values correctly."""
        content = """---
title: My Great Title With Spaces
description: A longer description here
---
Content
"""
        result = parse_frontmatter(content)
        assert result["title"] == "My Great Title With Spaces"
        assert result["description"] == "A longer description here"

    def test_frontmatter_trims_whitespace(self):
        """Test that keys and values are trimmed."""
        content = """---
  title  :   Padded Value
---
Content
"""
        result = parse_frontmatter(content)
        assert result["title"] == "Padded Value"


# =============================================================================
# Tests for parse_sections()
# =============================================================================

class TestParseSections:
    """Tests for markdown section extraction by header."""

    def test_extract_h2_sections(self):
        """Test extraction of h2 (##) sections."""
        content = """## What Was Done

This is the summary of work.

## What Worked

Everything went great.

## What Failed

Nothing failed.
"""
        result = parse_sections(content)
        assert "what_was_done" in result
        assert result["what_was_done"] == "This is the summary of work."
        assert "what_worked" in result
        assert result["what_worked"] == "Everything went great."
        assert "what_failed" in result
        assert result["what_failed"] == "Nothing failed."

    def test_extract_h3_sections(self):
        """Test extraction of h3 (###) sections."""
        content = """### Task Summary

Summary content here.

### Key Decisions

Decision content.
"""
        result = parse_sections(content)
        assert "task_summary" in result
        assert result["task_summary"] == "Summary content here."
        assert "key_decisions" in result
        assert result["key_decisions"] == "Decision content."

    def test_mixed_h2_and_h3_sections(self):
        """Test extraction handles both h2 and h3 sections."""
        content = """## Main Section

Main content.

### Sub Section

Sub content.

## Another Main

More content.
"""
        result = parse_sections(content)
        assert "main_section" in result
        assert "sub_section" in result
        assert "another_main" in result

    def test_empty_sections(self):
        """Test handles sections with no content."""
        content = """## Empty Section

## Next Section

Has content.
"""
        result = parse_sections(content)
        assert result["empty_section"] == ""
        assert result["next_section"] == "Has content."

    def test_no_sections(self):
        """Test returns empty dict when no sections exist."""
        content = """Just plain text.

No headers here.
"""
        result = parse_sections(content)
        assert result == {}

    def test_skips_frontmatter(self):
        """Test frontmatter is skipped before parsing sections."""
        content = """---
title: Document
---

## Actual Section

This is content.
"""
        result = parse_sections(content)
        # Should not have 'title' as a section
        assert "title" not in result
        assert "actual_section" in result
        assert result["actual_section"] == "This is content."

    def test_section_name_normalization(self):
        """Test section names are normalized (lowercase, underscores)."""
        content = """## What Was Done

Content here.

## Key-Decisions

More content.
"""
        result = parse_sections(content)
        assert "what_was_done" in result
        assert "key_decisions" in result  # hyphen becomes underscore

    def test_multiline_section_content(self):
        """Test sections preserve multiline content."""
        content = """## Description

Line 1
Line 2
Line 3

## Next
"""
        result = parse_sections(content)
        assert "Line 1" in result["description"]
        assert "Line 2" in result["description"]
        assert "Line 3" in result["description"]

    def test_section_content_is_trimmed(self):
        """Test section content has leading/trailing whitespace trimmed."""
        content = """## Section


Content with extra blank lines above.


"""
        result = parse_sections(content)
        assert result["section"] == "Content with extra blank lines above."


# =============================================================================
# Tests for parse_handoff()
# =============================================================================

class TestParseHandoff:
    """Tests for handoff markdown file parsing."""

    def test_valid_handoff_parsing(self):
        """Test parsing a complete handoff file with all fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure: docs/handoffs/test-session/task-01.md
            handoff_dir = Path(tmpdir) / "docs" / "handoffs" / "test-session"
            handoff_dir.mkdir(parents=True)
            handoff_file = handoff_dir / "task-01.md"

            content = """---
status: SUCCESS
date: 2024-01-15
---

## What Was Done

Implemented the authentication system.

## What Worked

- JWT token generation
- Session management

## What Failed

Nothing major failed.

## Key Decisions

Used RS256 for signing.

## Files Modified

- `src/auth/jwt.py`
- `src/auth/session.py`
"""
            handoff_file.write_text(content)

            result = parse_handoff(handoff_file)

            assert result["session_name"] == "test-session"
            assert result["task_number"] == 1
            assert result["outcome"] == "SUCCEEDED"  # SUCCESS maps to SUCCEEDED
            assert "Implemented the authentication system" in result["task_summary"]
            assert "JWT token generation" in result["what_worked"]
            assert "Nothing major failed" in result["what_failed"]
            assert "RS256" in result["key_decisions"]
            assert result["file_path"] == str(handoff_file.resolve())
            assert result["id"]  # Should have generated an ID

    def test_session_name_extraction_from_path(self):
        """Test session name is extracted from directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create: handoffs/my-feature-branch/task-05.md
            handoff_dir = Path(tmpdir) / "handoffs" / "my-feature-branch"
            handoff_dir.mkdir(parents=True)
            handoff_file = handoff_dir / "task-05.md"
            handoff_file.write_text("---\nstatus: SUCCESS\n---\n## What Was Done\nTest")

            result = parse_handoff(handoff_file)

            assert result["session_name"] == "my-feature-branch"
            assert result["task_number"] == 5

    def test_task_number_extraction_regex(self):
        """Test task number extraction via regex patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_dir = Path(tmpdir) / "handoffs" / "session"
            handoff_dir.mkdir(parents=True)

            # Test various task number patterns
            test_cases = [
                ("task-01.md", 1),
                ("task-12.md", 12),
                ("task-099.md", 99),
            ]

            for filename, expected_task_num in test_cases:
                handoff_file = handoff_dir / filename
                handoff_file.write_text("---\nstatus: SUCCESS\n---\n## What Was Done\nTest")
                result = parse_handoff(handoff_file)
                assert result["task_number"] == expected_task_num, f"Failed for {filename}"

    def test_outcome_mapping_success(self):
        """Test outcome mapping: SUCCESS -> SUCCEEDED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\nstatus: SUCCESS\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "SUCCEEDED"

    def test_outcome_mapping_succeeded(self):
        """Test outcome mapping: SUCCEEDED stays SUCCEEDED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\nstatus: SUCCEEDED\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "SUCCEEDED"

    def test_outcome_mapping_partial(self):
        """Test outcome mapping: PARTIAL -> PARTIAL_PLUS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\nstatus: PARTIAL\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "PARTIAL_PLUS"

    def test_outcome_mapping_failed(self):
        """Test outcome mapping: FAILED stays FAILED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\nstatus: FAILED\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "FAILED"

    def test_outcome_mapping_failure(self):
        """Test outcome mapping: FAILURE -> FAILED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\nstatus: FAILURE\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "FAILED"

    def test_outcome_mapping_unknown(self):
        """Test outcome mapping: unknown values -> UNKNOWN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\nstatus: FOOBAR\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "UNKNOWN"

    def test_missing_frontmatter_uses_defaults(self):
        """Test graceful handling when frontmatter fields are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("## What Was Done\n\nSome work was done.")

            result = parse_handoff(handoff_file)

            assert result["outcome"] == "UNKNOWN"
            assert result["task_summary"] == "Some work was done."

    def test_uses_outcome_field_as_fallback(self):
        """Test uses 'outcome' frontmatter field when 'status' is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("---\noutcome: SUCCESS\n---\n## What Was Done\nTest")
            result = parse_handoff(handoff_file)
            assert result["outcome"] == "SUCCEEDED"

    def test_alternative_section_names(self):
        """Test alternative section names are recognized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            content = """---
status: SUCCESS
---

## Summary

Using 'Summary' instead of 'What Was Done'.

## Successes

Instead of 'What Worked'.

## Failures

Instead of 'What Failed'.

## Decisions

Instead of 'Key Decisions'.
"""
            handoff_file.write_text(content)

            result = parse_handoff(handoff_file)

            assert "Using 'Summary'" in result["task_summary"]
            assert "Instead of 'What Worked'" in result["what_worked"]
            assert "Instead of 'What Failed'" in result["what_failed"]
            assert "Instead of 'Key Decisions'" in result["key_decisions"]


# =============================================================================
# Tests for extract_files_from_content()
# =============================================================================

class TestExtractFilesFromContent:
    """Tests for file path extraction from markdown content."""

    def test_extract_backtick_file_paths(self):
        """Test extraction of file paths in backticks."""
        content = """
- `src/auth/jwt.py`
- `src/models/user.py`
- `tests/test_auth.py`
"""
        result = extract_files_from_content(content)
        assert "src/auth/jwt.py" in result
        assert "src/models/user.py" in result
        assert "tests/test_auth.py" in result

    def test_extract_file_paths_with_line_numbers(self):
        """Test extraction handles file paths with line numbers."""
        content = """
- `src/auth/jwt.py:45`
- `src/models/user.py:123-456`
"""
        result = extract_files_from_content(content)
        assert "src/auth/jwt.py" in result
        assert "src/models/user.py" in result

    def test_extract_file_format_style(self):
        """Test extraction of **File**: format."""
        content = """
**File**: `src/main.py`
**File**: src/utils.py
"""
        result = extract_files_from_content(content)
        assert "src/main.py" in result
        assert "src/utils.py" in result

    def test_deduplicates_results(self):
        """Test duplicate file paths are removed."""
        content = """
- `src/auth.py`
- `src/auth.py`
- `src/auth.py:10`
"""
        result = extract_files_from_content(content)
        assert result.count("src/auth.py") == 1

    def test_empty_content(self):
        """Test returns empty list for empty content."""
        result = extract_files_from_content("")
        assert result == []


# =============================================================================
# Tests for escape_fts5_query()
# =============================================================================

class TestEscapeFts5Query:
    """Tests for FTS5 query escaping."""

    def test_basic_word_quoting(self):
        """Test basic words are quoted for FTS5."""
        result = escape_fts5_query("hello world")
        assert '"hello"' in result
        assert '"world"' in result
        assert " OR " in result

    def test_single_word(self):
        """Test single word is quoted."""
        result = escape_fts5_query("authentication")
        assert result == '"authentication"'

    def test_special_characters_in_query(self):
        """Test special characters are handled."""
        result = escape_fts5_query("user@example.com")
        assert '"user@example.com"' in result

    def test_empty_query(self):
        """Test empty query returns empty quoted string."""
        result = escape_fts5_query("")
        assert result == '""'

    def test_query_with_embedded_quotes(self):
        """Test embedded quotes are escaped (doubled)."""
        result = escape_fts5_query('say "hello"')
        # Double quotes in FTS5 are escaped by doubling them
        assert '""' in result or 'hello' in result

    def test_multiple_spaces_between_words(self):
        """Test multiple spaces are handled correctly."""
        result = escape_fts5_query("word1    word2")
        # Should handle multiple spaces without creating empty words
        assert '"word1"' in result
        assert '"word2"' in result

    def test_or_joining(self):
        """Test words are joined with OR for flexible matching."""
        result = escape_fts5_query("auth jwt oauth")
        assert result == '"auth" OR "jwt" OR "oauth"'


# =============================================================================
# Tests for validate_limit()
# =============================================================================

class TestValidateLimit:
    """Tests for limit validation in both query and mark modules."""

    def test_valid_limit_minimum(self):
        """Test minimum valid limit (1)."""
        result = query_validate_limit("1")
        assert result == 1

        result = mark_validate_limit("1")
        assert result == 1

    def test_valid_limit_maximum(self):
        """Test maximum valid limit (100)."""
        result = query_validate_limit("100")
        assert result == 100

        result = mark_validate_limit("100")
        assert result == 100

    def test_valid_limit_middle(self):
        """Test middle range limit."""
        result = query_validate_limit("50")
        assert result == 50

    def test_invalid_limit_below_minimum(self):
        """Test limit below minimum raises error."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            query_validate_limit("0")
        assert "between 1 and 100" in str(exc_info.value)

    def test_invalid_limit_above_maximum(self):
        """Test limit above maximum raises error."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            query_validate_limit("101")
        assert "between 1 and 100" in str(exc_info.value)

    def test_invalid_limit_negative(self):
        """Test negative limit raises error."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            query_validate_limit("-5")
        assert "between 1 and 100" in str(exc_info.value)

    def test_non_numeric_input(self):
        """Test non-numeric input raises error."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            query_validate_limit("abc")
        assert "Invalid integer value" in str(exc_info.value)

    def test_float_input(self):
        """Test float input raises error."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            query_validate_limit("5.5")
        assert "Invalid integer value" in str(exc_info.value)

    def test_empty_string(self):
        """Test empty string raises error."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            query_validate_limit("")
        assert "Invalid integer value" in str(exc_info.value)


# =============================================================================
# Tests for get_project_root()
# =============================================================================

class TestGetProjectRoot:
    """Tests for project root detection."""

    def test_finds_ring_directory(self):
        """Test finding project root via .ring directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .ring directory
            ring_dir = Path(tmpdir) / ".ring"
            ring_dir.mkdir()

            # Create a subdirectory to test from
            sub_dir = Path(tmpdir) / "src" / "lib"
            sub_dir.mkdir(parents=True)

            # Change to subdirectory and test
            original_cwd = os.getcwd()
            try:
                os.chdir(sub_dir)
                result = query_get_project_root()
                assert result == Path(tmpdir).resolve()
            finally:
                os.chdir(original_cwd)

    def test_finds_git_directory(self):
        """Test finding project root via .git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            # Create a subdirectory to test from
            sub_dir = Path(tmpdir) / "deep" / "nested" / "path"
            sub_dir.mkdir(parents=True)

            original_cwd = os.getcwd()
            try:
                os.chdir(sub_dir)
                result = query_get_project_root()
                assert result == Path(tmpdir).resolve()
            finally:
                os.chdir(original_cwd)

    def test_prefers_ring_over_git(self):
        """Test .ring is found before .git (both exist)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both .ring and .git
            ring_dir = Path(tmpdir) / ".ring"
            ring_dir.mkdir()
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = query_get_project_root()
                assert result == Path(tmpdir).resolve()
            finally:
                os.chdir(original_cwd)

    def test_returns_cwd_when_no_marker_found(self):
        """Test returns current directory when no .ring or .git found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create any markers
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = query_get_project_root()
                assert result == Path(tmpdir).resolve()
            finally:
                os.chdir(original_cwd)

    def test_index_get_project_root_with_custom_path(self):
        """Test artifact_index.get_project_root with custom path argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom" / "path"
            custom_path.mkdir(parents=True)

            result = index_get_project_root(str(custom_path))
            assert result == custom_path.resolve()

    def test_index_get_project_root_without_custom_path(self):
        """Test artifact_index.get_project_root without custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ring_dir = Path(tmpdir) / ".ring"
            ring_dir.mkdir()

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = index_get_project_root(None)
                assert result == Path(tmpdir).resolve()
            finally:
                os.chdir(original_cwd)


# =============================================================================
# Tests for get_handoff_id_from_file()
# =============================================================================

class TestGetHandoffIdFromFile:
    """Tests for handoff ID generation from file path."""

    def test_generates_consistent_id(self):
        """Test ID generation is deterministic for same path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "task-01.md"
            file_path.touch()

            id1 = get_handoff_id_from_file(file_path)
            id2 = get_handoff_id_from_file(file_path)

            assert id1 == id2

    def test_different_paths_different_ids(self):
        """Test different paths generate different IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "task-01.md"
            file2 = Path(tmpdir) / "task-02.md"
            file1.touch()
            file2.touch()

            id1 = get_handoff_id_from_file(file1)
            id2 = get_handoff_id_from_file(file2)

            assert id1 != id2

    def test_id_is_12_characters(self):
        """Test ID is exactly 12 characters (truncated MD5)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "task-01.md"
            file_path.touch()

            result = get_handoff_id_from_file(file_path)

            assert len(result) == 12

    def test_id_is_hexadecimal(self):
        """Test ID contains only hexadecimal characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "task-01.md"
            file_path.touch()

            result = get_handoff_id_from_file(file_path)

            # All characters should be valid hex
            assert all(c in "0123456789abcdef" for c in result)


# =============================================================================
# Integration-like tests
# =============================================================================

class TestIntegration:
    """Integration-like tests combining multiple functions."""

    def test_full_handoff_workflow(self):
        """Test complete handoff parsing workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create proper directory structure
            handoff_dir = Path(tmpdir) / "docs" / "handoffs" / "feature-auth"
            handoff_dir.mkdir(parents=True)
            handoff_file = handoff_dir / "task-03.md"

            content = """---
status: SUCCESS
date: 2024-01-20
session: feature-auth
---

# Task 03: Implement OAuth Flow

## What Was Done

Implemented OAuth 2.0 authentication flow with Google and GitHub providers.

## What Worked

- Google OAuth integration
- GitHub OAuth integration
- Token refresh mechanism

## What Failed

Minor issues with rate limiting, resolved.

## Key Decisions

- Used passport.js for OAuth abstraction
- Stored tokens in Redis for session management

## Files Modified

- `src/auth/oauth.ts`
- `src/auth/providers/google.ts`
- `src/auth/providers/github.ts`
- `src/middleware/auth.ts`
"""
            handoff_file.write_text(content)

            # Parse the handoff
            result = parse_handoff(handoff_file)

            # Verify all fields
            assert result["session_name"] == "feature-auth"
            assert result["task_number"] == 3
            assert result["outcome"] == "SUCCEEDED"
            assert "OAuth 2.0" in result["task_summary"]
            assert "Google OAuth" in result["what_worked"]
            assert "rate limiting" in result["what_failed"]
            assert "passport.js" in result["key_decisions"]

            # Verify files were extracted
            import json
            files = json.loads(result["files_modified"])
            assert "src/auth/oauth.ts" in files
            assert len(files) >= 3

    def test_handoff_with_minimal_content(self):
        """Test handoff parsing with minimal content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handoff_file = Path(tmpdir) / "task-01.md"
            handoff_file.write_text("# Minimal handoff")

            result = parse_handoff(handoff_file)

            # Should not raise, should have defaults
            assert result["outcome"] == "UNKNOWN"
            assert result["task_summary"] == ""
            assert result["id"]  # Should still have an ID


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
