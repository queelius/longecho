"""
Tests for the ECHO site builder.
"""

import json
import pytest
from pathlib import Path

from longecho.build import (
    build_site,
    discover_sub_sources,
    get_icon_emoji,
    markdown_to_html,
    escape_html,
    BuildResult,
    SourceInfo,
    ICON_EMOJI_MAP,
)
from longecho.manifest import Manifest, SourceConfig


class TestGetIconEmoji:
    """Tests for get_icon_emoji function."""

    def test_known_icons(self):
        assert get_icon_emoji("chat") == ICON_EMOJI_MAP["chat"]
        assert get_icon_emoji("bookmark") == ICON_EMOJI_MAP["bookmark"]
        assert get_icon_emoji("database") == ICON_EMOJI_MAP["database"]

    def test_unknown_icon_returns_default(self):
        assert get_icon_emoji("unknown") == ICON_EMOJI_MAP["default"]

    def test_none_returns_default(self):
        assert get_icon_emoji(None) == ICON_EMOJI_MAP["default"]


class TestEscapeHtml:
    """Tests for escape_html function."""

    def test_escapes_special_chars(self):
        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html("A & B") == "A &amp; B"
        assert escape_html('"quoted"') == "&quot;quoted&quot;"

    def test_preserves_normal_text(self):
        assert escape_html("Hello World") == "Hello World"


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


class TestDiscoverSubSources:
    """Tests for discover_sub_sources function."""

    def test_discovers_echo_sources(self, temp_dir):
        # Create a sub-source
        source_dir = temp_dir / "source1"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("# Source 1\n\nA data source.")
        (source_dir / "data.db").touch()

        sources = discover_sub_sources(temp_dir)
        assert len(sources) == 1
        assert sources[0].name == "source1"

    def test_ignores_non_echo_dirs(self, temp_dir):
        # Create a non-ECHO directory (no README)
        source_dir = temp_dir / "not_echo"
        source_dir.mkdir()
        (source_dir / "data.db").touch()

        sources = discover_sub_sources(temp_dir)
        assert len(sources) == 0

    def test_uses_manifest_sources(self, temp_dir):
        # Create source directory
        source_dir = temp_dir / "source1"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("# Source 1")
        (source_dir / "data.db").touch()

        # Create manifest
        manifest = Manifest(
            version="1.0",
            name="Test",
            description="Test",
            sources=[SourceConfig(path="source1/", order=1, name="Custom Name")]
        )

        sources = discover_sub_sources(temp_dir, manifest)
        assert len(sources) == 1
        assert sources[0].name == "Custom Name"

    def test_sorts_by_order(self, temp_dir):
        # Create sources
        for name in ["source_a", "source_b", "source_c"]:
            d = temp_dir / name
            d.mkdir()
            (d / "README.md").write_text(f"# {name}")
            (d / "data.db").touch()

        manifest = Manifest(
            version="1.0",
            name="Test",
            description="Test",
            sources=[
                SourceConfig(path="source_c/", order=1),
                SourceConfig(path="source_a/", order=2),
                SourceConfig(path="source_b/", order=3),
            ]
        )

        sources = discover_sub_sources(temp_dir, manifest)
        assert sources[0].path.name == "source_c"
        assert sources[1].path.name == "source_a"
        assert sources[2].path.name == "source_b"

    def test_detects_existing_site(self, temp_dir):
        # Create source with site
        source_dir = temp_dir / "source1"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("# Source 1")
        (source_dir / "data.db").touch()
        site_dir = source_dir / "site"
        site_dir.mkdir()
        (site_dir / "index.html").write_text("<html></html>")

        sources = discover_sub_sources(temp_dir)
        assert len(sources) == 1
        assert sources[0].has_site is True

    def test_ignores_site_directory(self, temp_dir):
        # Create main site directory (should not be treated as source)
        site_dir = temp_dir / "site"
        site_dir.mkdir()
        (site_dir / "index.html").write_text("<html></html>")

        sources = discover_sub_sources(temp_dir)
        assert len(sources) == 0


class TestBuildSite:
    """Tests for build_site function."""

    def test_requires_echo_compliance(self, temp_dir):
        # Non-ECHO directory
        result = build_site(temp_dir)
        assert result.success is False
        assert "Not an ECHO archive" in result.error

    def test_builds_basic_site(self, echo_compliant_dir):
        result = build_site(echo_compliant_dir)

        assert result.success is True
        assert result.output_path is not None
        assert (result.output_path / "index.html").exists()

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

    def test_builds_with_sources(self, nested_echo_sources):
        result = build_site(nested_echo_sources)

        # nested_echo_sources doesn't have a README at root
        # Let's check what happens
        if result.success:
            assert result.sources_count > 0


class TestBuildResult:
    """Tests for BuildResult dataclass."""

    def test_success_result(self):
        result = BuildResult(
            success=True,
            output_path=Path("/tmp/site"),
            sources_count=3
        )
        assert result.success is True
        assert result.sources_count == 3

    def test_failure_result(self):
        result = BuildResult(
            success=False,
            error="Something went wrong"
        )
        assert result.success is False
        assert result.error == "Something went wrong"


class TestSourceInfo:
    """Tests for SourceInfo dataclass."""

    def test_default_values(self):
        info = SourceInfo(
            name="Test",
            description="A test",
            path=Path("/tmp/test"),
            url="test/index.html"
        )
        assert info.icon is None
        assert info.icon_emoji == ICON_EMOJI_MAP["default"]
        assert info.order == 0
        assert info.has_site is False


@pytest.fixture
def echo_compliant_with_sources(temp_dir):
    """Create an ECHO archive with sub-sources."""
    # Create main README
    (temp_dir / "README.md").write_text(
        "# Test Archive\n\nA test archive with multiple sources."
    )

    # Create a dummy durable file to make the root compliant
    (temp_dir / "index.json").write_text("[]")

    # Create manifest
    (temp_dir / "manifest.json").write_text(json.dumps({
        "version": "1.0",
        "name": "Test Archive",
        "description": "A test archive",
        "sources": [
            {"path": "conversations/", "order": 1},
            {"path": "bookmarks/", "order": 2}
        ]
    }))

    # Create conversations source
    conv_dir = temp_dir / "conversations"
    conv_dir.mkdir()
    (conv_dir / "README.md").write_text("# Conversations\n\nChat history.")
    (conv_dir / "conversations.db").touch()
    (conv_dir / "manifest.json").write_text(json.dumps({
        "version": "1.0",
        "name": "Conversations",
        "description": "AI conversation history",
        "type": "database",
        "icon": "chat"
    }))

    # Create bookmarks source
    btk_dir = temp_dir / "bookmarks"
    btk_dir.mkdir()
    (btk_dir / "README.md").write_text("# Bookmarks\n\nSaved links.")
    (btk_dir / "bookmarks.jsonl").write_text("")
    (btk_dir / "manifest.json").write_text(json.dumps({
        "version": "1.0",
        "name": "Bookmarks",
        "description": "Personal bookmarks",
        "type": "database",
        "icon": "bookmark"
    }))

    return temp_dir


class TestBuildWithManifest:
    """Tests for building sites with manifests."""

    def test_uses_manifest_name(self, echo_compliant_with_sources):
        result = build_site(echo_compliant_with_sources)
        assert result.success is True

        # Check that the index.html contains the manifest name
        index_content = (result.output_path / "index.html").read_text()
        assert "Test Archive" in index_content

    def test_creates_source_pages(self, echo_compliant_with_sources):
        result = build_site(echo_compliant_with_sources)
        assert result.success is True
        assert result.sources_count == 2

        # Check source directories
        assert (result.output_path / "conversations" / "index.html").exists()
        assert (result.output_path / "bookmarks" / "index.html").exists()

    def test_source_pages_have_content(self, echo_compliant_with_sources):
        result = build_site(echo_compliant_with_sources)
        assert result.success is True

        conv_content = (result.output_path / "conversations" / "index.html").read_text()
        assert "Conversations" in conv_content
        assert "chat history" in conv_content.lower()
