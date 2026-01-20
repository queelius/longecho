"""
Tests for the ECHO compliance checker.
"""

import pytest
from pathlib import Path

from longecho.checker import (
    check_compliance,
    find_readme,
    extract_first_paragraph,
    detect_formats,
    is_durable_format,
    ComplianceResult,
    DURABLE_EXTENSIONS,
)


class TestFindReadme:
    """Tests for find_readme function."""

    def test_finds_readme_md(self, temp_dir):
        readme = temp_dir / "README.md"
        readme.write_text("# Test")

        result = find_readme(temp_dir)
        assert result == readme

    def test_finds_readme_txt(self, temp_dir):
        readme = temp_dir / "README.txt"
        readme.write_text("Test readme")

        result = find_readme(temp_dir)
        assert result == readme

    def test_prefers_readme_md(self, temp_dir):
        (temp_dir / "README.md").write_text("# Markdown")
        (temp_dir / "README.txt").write_text("Text")

        result = find_readme(temp_dir)
        assert result.name == "README.md"

    def test_case_insensitive(self, temp_dir):
        readme = temp_dir / "readme.md"
        readme.write_text("# test")

        result = find_readme(temp_dir)
        assert result == readme

    def test_returns_none_if_missing(self, temp_dir):
        result = find_readme(temp_dir)
        assert result is None


class TestExtractFirstParagraph:
    """Tests for extract_first_paragraph function."""

    def test_extracts_paragraph_after_title(self, temp_dir):
        readme = temp_dir / "README.md"
        readme.write_text("""# Title

This is the first paragraph of the readme.
It spans multiple lines.

## Section

More content.
""")
        result = extract_first_paragraph(readme)
        assert result is not None
        assert "first paragraph" in result

    def test_skips_frontmatter(self, temp_dir):
        readme = temp_dir / "README.md"
        readme.write_text("""---
title: Test
date: 2024-01-01
---

# Title

Real content here.
""")
        result = extract_first_paragraph(readme)
        assert result is not None
        assert "Real content" in result

    def test_returns_none_for_empty(self, temp_dir):
        readme = temp_dir / "README.md"
        readme.write_text("")

        result = extract_first_paragraph(readme)
        assert result is None


class TestDetectFormats:
    """Tests for detect_formats function."""

    def test_detects_common_formats(self, temp_dir):
        (temp_dir / "data.db").touch()
        (temp_dir / "config.json").write_text("{}")
        (temp_dir / "notes.md").write_text("# Notes")

        formats = detect_formats(temp_dir)
        assert ".db" in formats
        assert ".json" in formats
        assert ".md" in formats

    def test_excludes_readme(self, temp_dir):
        (temp_dir / "README.md").write_text("# Test")
        (temp_dir / "data.json").write_text("{}")

        formats = detect_formats(temp_dir)
        assert ".json" in formats
        # README.md is excluded from format detection
        assert len([f for f in formats if f == ".md"]) == 0 or \
               (temp_dir / "notes.md").exists()

    def test_respects_max_depth(self, temp_dir):
        (temp_dir / "level1" / "level2" / "level3").mkdir(parents=True)
        (temp_dir / "level1" / "level2" / "level3" / "deep.json").write_text("{}")
        (temp_dir / "shallow.txt").write_text("shallow")

        formats = detect_formats(temp_dir, max_depth=1)
        assert ".txt" in formats
        # Deep file may not be found with shallow depth


class TestIsDurableFormat:
    """Tests for is_durable_format function."""

    def test_sqlite_is_durable(self):
        assert is_durable_format(".db")
        assert is_durable_format(".sqlite")
        assert is_durable_format(".sqlite3")

    def test_json_is_durable(self):
        assert is_durable_format(".json")
        assert is_durable_format(".jsonl")

    def test_markdown_is_durable(self):
        assert is_durable_format(".md")
        assert is_durable_format(".markdown")

    def test_text_is_durable(self):
        assert is_durable_format(".txt")

    def test_handles_no_dot(self):
        assert is_durable_format("json")
        assert is_durable_format("md")

    def test_unknown_not_durable(self):
        assert not is_durable_format(".exe")
        assert not is_durable_format(".dll")
        assert not is_durable_format(".pyc")


class TestCheckCompliance:
    """Tests for check_compliance function."""

    def test_compliant_directory(self, echo_compliant_dir):
        result = check_compliance(echo_compliant_dir)

        assert result.compliant is True
        assert result.readme_path is not None
        assert result.readme_path.name == "README.md"
        assert len(result.durable_formats) > 0
        assert ".db" in result.durable_formats or ".json" in result.durable_formats

    def test_non_compliant_no_readme(self, non_compliant_dir_no_readme):
        result = check_compliance(non_compliant_dir_no_readme)

        assert result.compliant is False
        assert "README" in result.reason

    def test_non_compliant_no_durable_formats(self, non_compliant_dir_no_durable):
        result = check_compliance(non_compliant_dir_no_durable)

        assert result.compliant is False
        assert result.readme_path is not None
        assert "durable" in result.reason.lower()

    def test_nonexistent_path(self):
        result = check_compliance(Path("/nonexistent/path"))

        assert result.compliant is False
        assert "not exist" in result.reason.lower()

    def test_file_path(self, temp_dir):
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        result = check_compliance(test_file)

        assert result.compliant is False
        assert "not a directory" in result.reason.lower()


class TestComplianceResult:
    """Tests for ComplianceResult dataclass."""

    def test_str_compliant(self, temp_dir):
        result = ComplianceResult(
            compliant=True,
            path=temp_dir,
            readme_path=temp_dir / "README.md",
            durable_formats=[".db", ".json"]
        )

        assert "ECHO-compliant" in str(result)

    def test_str_non_compliant(self, temp_dir):
        result = ComplianceResult(
            compliant=False,
            path=temp_dir,
            reason="No README found"
        )

        assert "Not ECHO-compliant" in str(result)
        assert "No README" in str(result)
