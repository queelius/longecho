"""Tests for the longecho site builder."""

import json
from pathlib import Path

import pytest

from longecho.build import (
    BuildResult,
    build_site,
    discover_sub_sources,
    markdown_to_html,
)
from longecho.checker import check_compliance


class TestMarkdownToHtml:
    """Tests for markdown_to_html function."""

    def test_converts_headers(self):
        result = markdown_to_html("# Title")
        assert "<h1>" in result
        assert "Title" in result

    def test_converts_h2(self):
        result = markdown_to_html("## Section")
        assert "<h2>" in result
        assert "Section" in result

    def test_converts_paragraphs(self):
        result = markdown_to_html("This is a paragraph.\n\nAnother one.")
        assert "<p>" in result
        assert "paragraph" in result

    def test_handles_code_blocks(self):
        result = markdown_to_html("```\ncode here\n```")
        assert "<pre><code>" in result
        assert "code here" in result

    def test_sanitizes_script_tags(self):
        result = markdown_to_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert" not in result

    def test_sanitizes_event_handlers(self):
        result = markdown_to_html('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result


class TestDiscoverSubSources:
    """Tests for discover_sub_sources function."""

    def test_discovers_sources(self, temp_dir):
        # Create root
        (temp_dir / "README.md").write_text("# Root\n\nRoot archive.")
        (temp_dir / "index.json").write_text("[]")

        # Create a sub-source
        source_dir = temp_dir / "source1"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("# Source 1\n\nA data source.")
        (source_dir / "data.db").touch()

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 1
        assert sources[0].name == "Source 1"

    def test_ignores_non_compliant_dirs(self, temp_dir):
        (temp_dir / "README.md").write_text("# Root\n\nRoot archive.")
        (temp_dir / "index.json").write_text("[]")

        source_dir = temp_dir / "not_compliant"
        source_dir.mkdir()
        (source_dir / "data.db").touch()  # no README

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 0

    def test_uses_contents_field(self, temp_dir):
        """When contents is present, only listed paths are included."""
        (temp_dir / "README.md").write_text(
            "---\nname: Root\ncontents:\n  - path: source1/\n---\n# Root\n\nRoot archive."
        )
        (temp_dir / "index.json").write_text("[]")

        # Listed source
        s1 = temp_dir / "source1"
        s1.mkdir()
        (s1 / "README.md").write_text("# Source 1\n\nFirst.")
        (s1 / "data.db").touch()

        # Unlisted source (should be excluded)
        s2 = temp_dir / "source2"
        s2.mkdir()
        (s2 / "README.md").write_text("# Source 2\n\nSecond.")
        (s2 / "data.db").touch()

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 1
        assert sources[0].name == "Source 1"

    def test_contents_ordering(self, temp_dir):
        """Contents field controls ordering."""
        (temp_dir / "README.md").write_text(
            "---\ncontents:\n  - path: beta/\n  - path: alpha/\n---\n# Root\n\nRoot."
        )
        (temp_dir / "index.json").write_text("[]")

        for name in ["alpha", "beta"]:
            d = temp_dir / name
            d.mkdir()
            (d / "README.md").write_text(f"# {name}\n\nSource {name}.")
            (d / "data.db").touch()

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 2
        assert sources[0].name == "beta"
        assert sources[1].name == "alpha"

    def test_auto_discovery_alphabetical(self, temp_dir):
        """Without contents, sources are discovered alphabetically."""
        (temp_dir / "README.md").write_text("# Root\n\nRoot.")
        (temp_dir / "index.json").write_text("[]")

        for name in ["charlie", "alpha", "beta"]:
            d = temp_dir / name
            d.mkdir()
            (d / "README.md").write_text(f"# {name}\n\nSource.")
            (d / "data.db").touch()

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 3
        assert sources[0].name == "alpha"
        assert sources[1].name == "beta"
        assert sources[2].name == "charlie"

    def test_detects_existing_site(self, temp_dir):
        (temp_dir / "README.md").write_text("# Root\n\nRoot.")
        (temp_dir / "index.json").write_text("[]")

        source_dir = temp_dir / "source1"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("# Source 1\n\nA source.")
        (source_dir / "data.db").touch()
        site_dir = source_dir / "site"
        site_dir.mkdir()
        (site_dir / "index.html").write_text("<html></html>")

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 1
        assert sources[0].has_site is True

    def test_ignores_site_directory(self, temp_dir):
        (temp_dir / "README.md").write_text("# Root\n\nRoot.")
        (temp_dir / "index.json").write_text("[]")

        site_dir = temp_dir / "site"
        site_dir.mkdir()
        (site_dir / "index.html").write_text("<html></html>")

        result = check_compliance(temp_dir)
        assert result.source is not None
        sources = discover_sub_sources(result.source)
        assert len(sources) == 0


class TestBuildSite:
    """Tests for build_site function."""

    def test_requires_compliance(self, temp_dir):
        result = build_site(temp_dir)
        assert result.success is False
        assert "Not a longecho archive" in result.error

    def test_builds_basic_site(self, echo_compliant_dir):
        result = build_site(echo_compliant_dir)

        assert result.success is True
        assert result.output_path is not None
        assert (result.output_path / "index.html").exists()

    def test_generates_site_readme(self, echo_compliant_dir):
        result = build_site(echo_compliant_dir)

        assert result.success is True
        readme = result.output_path / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "longecho" in content.lower()

    def test_custom_output_path(self, echo_compliant_dir, temp_dir):
        output = temp_dir / "custom_output"
        result = build_site(echo_compliant_dir, output=output)

        assert result.success is True
        assert result.output_path == output
        assert (output / "index.html").exists()

    def test_nonexistent_path(self):
        result = build_site(Path("/nonexistent/path"))
        assert result.success is False
        assert "does not exist" in result.error

    def test_file_path(self, temp_dir):
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        result = build_site(test_file)
        assert result.success is False
        assert "not a directory" in result.error

    def test_sfa_output_is_single_file(self, echo_compliant_dir):
        """Build output should be a single index.html, not multi-file."""
        result = build_site(echo_compliant_dir)
        assert result.success is True

        # Should have index.html and README.md, no subdirectory pages
        html_files = list(result.output_path.glob("**/*.html"))
        assert len(html_files) == 1
        assert html_files[0].name == "index.html"


class TestBuildResult:
    """Tests for BuildResult."""

    def test_success_result(self):
        result = BuildResult(
            success=True,
            output_path=Path("/tmp/site"),
            sources_count=3,
        )
        assert result.success is True
        assert result.sources_count == 3

    def test_failure_result(self):
        result = BuildResult(
            success=False,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"


@pytest.fixture
def archive_with_sources(temp_dir):
    """Create a longecho archive with sub-sources using frontmatter contents."""
    (temp_dir / "README.md").write_text(
        "---\nname: Test Archive\ndescription: A test archive\n"
        "contents:\n  - path: conversations/\n  - path: bookmarks/\n---\n"
        "# Test Archive\n\nA test archive with multiple sources."
    )
    (temp_dir / "index.json").write_text("[]")

    conv_dir = temp_dir / "conversations"
    conv_dir.mkdir()
    (conv_dir / "README.md").write_text(
        "---\nname: Conversations\ndescription: AI conversation history\n---\n"
        "# Conversations\n\nChat history."
    )
    (conv_dir / "conversations.db").touch()

    btk_dir = temp_dir / "bookmarks"
    btk_dir.mkdir()
    (btk_dir / "README.md").write_text(
        "---\nname: Bookmarks\ndescription: Personal bookmarks\n---\n"
        "# Bookmarks\n\nSaved links."
    )
    (btk_dir / "bookmarks.jsonl").write_text("")

    return temp_dir


class TestBuildWithSources:
    """Tests for building sites with sub-sources."""

    def test_uses_archive_name(self, archive_with_sources):
        result = build_site(archive_with_sources)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        assert "Test Archive" in index_content

    def test_counts_sources(self, archive_with_sources):
        result = build_site(archive_with_sources)
        assert result.success is True
        assert result.sources_count == 2

    def test_inlines_source_data_as_json(self, archive_with_sources):
        result = build_site(archive_with_sources)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        assert "Conversations" in index_content
        assert "Bookmarks" in index_content
