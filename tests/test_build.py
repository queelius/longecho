"""Tests for the ECHO site builder."""

from pathlib import Path

import pytest
import yaml

from longecho.build import (
    BuildResult,
    build_site,
    discover_sub_sources,
    markdown_to_html,
)
from longecho.manifest import Manifest, SourceConfig


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
        assert sources[0].name == "Source 1"

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

    def test_rejects_non_echo_root(self, nested_echo_sources):
        # nested_echo_sources has no README at root, so build should fail
        result = build_site(nested_echo_sources)
        assert result.success is False


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


@pytest.fixture
def echo_compliant_with_sources(temp_dir):
    """Create an ECHO archive with sub-sources."""
    (temp_dir / "README.md").write_text("# Test Archive\n\nA test archive with multiple sources.")
    (temp_dir / "index.json").write_text("[]")  # durable file to make root compliant
    (temp_dir / "manifest.yaml").write_text(yaml.dump({
        "name": "Test Archive",
        "description": "A test archive",
        "sources": [
            {"path": "conversations/", "order": 1},
            {"path": "bookmarks/", "order": 2},
        ],
    }, default_flow_style=False))

    conv_dir = temp_dir / "conversations"
    conv_dir.mkdir()
    (conv_dir / "README.md").write_text("# Conversations\n\nChat history.")
    (conv_dir / "conversations.db").touch()
    (conv_dir / "manifest.yaml").write_text(yaml.dump({
        "name": "Conversations",
        "description": "AI conversation history",
        "icon": "\U0001F4AC",
    }, default_flow_style=False))

    btk_dir = temp_dir / "bookmarks"
    btk_dir.mkdir()
    (btk_dir / "README.md").write_text("# Bookmarks\n\nSaved links.")
    (btk_dir / "bookmarks.jsonl").write_text("")
    (btk_dir / "manifest.yaml").write_text(yaml.dump({
        "name": "Bookmarks",
        "description": "Personal bookmarks",
        "icon": "\U0001F516",
    }, default_flow_style=False))

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
