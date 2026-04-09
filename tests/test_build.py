"""Tests for the longecho site builder."""

import json
from pathlib import Path

import pytest

from longecho.build import (
    BuildResult,
    _get_data_files,
    _is_foreign_site,
    build_site,
    discover_sub_sources,
    make_json_safe,
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

    def test_sfa_has_query_features(self, archive_with_sources):
        """SFA should include text search functionality."""
        result = build_site(archive_with_sources)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        assert "matchesQuery" in index_content
        assert "Search sources" in index_content

    def test_sfa_has_search_index(self, archive_with_sources):
        """SFA should build a search index from README content."""
        result = build_site(archive_with_sources)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        assert "_searchText" in index_content


class TestSiteLink:
    """Tests for linking to source-level interactive sites."""

    def test_source_with_site_has_site_url(self, temp_dir):
        """When a source has site/index.html, the SFA JSON should include site_url."""
        (temp_dir / "README.md").write_text(
            "---\nname: Root\ncontents:\n  - path: data-source/\n---\n# Root\n\nRoot."
        )
        (temp_dir / "data.json").write_text("{}")

        source_dir = temp_dir / "data-source"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("# Data Source\n\nHas its own viewer.")
        (source_dir / "data.db").touch()
        site_dir = source_dir / "site"
        site_dir.mkdir()
        (site_dir / "README.md").write_text("---\ngenerator: ctk\n---\nViewer.")
        (site_dir / "index.html").write_text("<html><body>Viewer</body></html>")

        result = build_site(temp_dir)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        assert "site_url" in index_content
        assert "Open interactive viewer" in index_content

    def test_source_without_site_has_null_site_url(self, temp_dir):
        """When a source has no site/, site_url should be null."""
        import re
        (temp_dir / "README.md").write_text(
            "---\nname: Root\ncontents:\n  - path: plain/\n---\n# Root\n\nRoot."
        )
        (temp_dir / "data.json").write_text("{}")

        plain_dir = temp_dir / "plain"
        plain_dir.mkdir()
        (plain_dir / "README.md").write_text("# Plain\n\nNo viewer.")
        (plain_dir / "data.db").touch()

        result = build_site(temp_dir)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        match = re.search(r'var ROOT = (.+?);\n', index_content)
        assert match is not None
        root_data = json.loads(match.group(1))
        # Root's child "plain" has no site
        assert root_data["children"][0]["site_url"] is None


@pytest.fixture
def nested_archive(temp_dir):
    """Create a 3-level nested archive: root > conversations > chatgpt."""
    (temp_dir / "README.md").write_text(
        "---\nname: Root\ndescription: Root archive\n"
        "contents:\n  - path: conversations/\n---\n"
        "# Root\n\nRoot archive."
    )
    (temp_dir / "data.json").write_text("{}")

    conv_dir = temp_dir / "conversations"
    conv_dir.mkdir()
    (conv_dir / "README.md").write_text(
        "---\nname: Conversations\ndescription: Chat history\n"
        "contents:\n  - path: chatgpt/\n---\n"
        "# Conversations\n\nAll chats."
    )
    (conv_dir / "conversations.db").touch()

    chatgpt_dir = conv_dir / "chatgpt"
    chatgpt_dir.mkdir()
    (chatgpt_dir / "README.md").write_text(
        "---\nname: ChatGPT\ndescription: ChatGPT exports\n---\n"
        "# ChatGPT\n\nExported from OpenAI."
    )
    (chatgpt_dir / "conversations.jsonl").write_text("")

    return temp_dir


class TestRecursiveBuild:
    """Tests for recursive nested source building."""

    def test_builds_nested_children(self, nested_archive):
        result = build_site(nested_archive)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        # All three levels should appear in the SFA
        assert "Conversations" in index_content
        assert "ChatGPT" in index_content

    def test_counts_all_nested_sources(self, nested_archive):
        result = build_site(nested_archive)
        assert result.success is True
        # 1 (conversations) + 1 (chatgpt) = 2 total
        assert result.sources_count == 2

    def test_children_in_json_structure(self, nested_archive):
        """Verify the JSON data has nested children arrays."""
        import re
        result = build_site(nested_archive)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        match = re.search(r'var ROOT = (.+?);\n', index_content)
        assert match is not None
        root_data = json.loads(match.group(1))

        # Root is a single source object with its own children
        assert root_data["name"] == "Root"
        assert len(root_data["children"]) == 1
        assert root_data["children"][0]["name"] == "Conversations"
        # Conversations has 1 child (chatgpt)
        assert len(root_data["children"][0]["children"]) == 1
        assert root_data["children"][0]["children"][0]["name"] == "ChatGPT"
        # ChatGPT has no children
        assert len(root_data["children"][0]["children"][0]["children"]) == 0


class TestMakeJsonSafe:
    """Tests for make_json_safe function."""

    def test_converts_date(self):
        from datetime import date
        result = make_json_safe({"date": date(2026, 2, 18)})
        assert result == {"date": "2026-02-18"}
        # Verify it's actually JSON-serializable
        json.dumps(result)

    def test_converts_datetime(self):
        from datetime import datetime
        dt = datetime(2026, 2, 18, 14, 30, 0)
        result = make_json_safe({"created": dt})
        assert result == {"created": "2026-02-18T14:30:00"}
        json.dumps(result)

    def test_handles_nested(self):
        from datetime import date
        data = {"meta": {"date": date(2026, 1, 1)}, "items": [date(2025, 6, 15)]}
        result = make_json_safe(data)
        assert result == {"meta": {"date": "2026-01-01"}, "items": ["2025-06-15"]}
        json.dumps(result)

    def test_passes_through_normal_types(self):
        data = {"name": "test", "count": 42, "flag": True, "items": [1, "two"]}
        assert make_json_safe(data) == data


class TestRecursiveDataFiles:
    """Tests for _get_data_files walking nested directories."""

    def _make_source(self, temp_dir):
        (temp_dir / "README.md").write_text("# Test\n\nTest source.")
        result = check_compliance(temp_dir)
        assert result.source is not None
        return result.source

    def test_finds_top_level_files(self, temp_dir):
        (temp_dir / "data.json").write_text("{}")
        source = self._make_source(temp_dir)

        files = _get_data_files(source, temp_dir / "site")
        names = [f["name"] for f in files]
        assert "data.json" in names

    def test_finds_nested_files(self, temp_dir):
        """Files in subdirectories should be found (within max scan depth)."""
        (temp_dir / "data.json").write_text("{}")
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        (data_dir / "records.jsonl").write_text("")
        source = self._make_source(temp_dir)

        files = _get_data_files(source, temp_dir / "site")
        names = [f["name"] for f in files]
        assert "data.json" in names
        # Nested file uses relative path as display name
        assert "data/records.jsonl" in names

    def test_stops_at_nested_sources(self, temp_dir):
        """Don't descend into directories that are themselves compliant sources."""
        (temp_dir / "top.json").write_text("{}")

        # A nested source — has its own README
        sub = temp_dir / "subsource"
        sub.mkdir()
        (sub / "README.md").write_text("# Sub\n\nA sub-source.")
        (sub / "sub.jsonl").write_text("")

        source = self._make_source(temp_dir)
        files = _get_data_files(source, temp_dir / "site")
        names = [f["name"] for f in files]
        assert "top.json" in names
        # sub.jsonl belongs to the sub-source, not the parent
        assert not any("sub.jsonl" in n for n in names)

    def test_skips_site_directory(self, temp_dir):
        """site/ subdirectory should never appear in data files (it's a viewer)."""
        (temp_dir / "data.json").write_text("{}")
        site_dir = temp_dir / "site"
        site_dir.mkdir()
        (site_dir / "README.md").write_text("---\ngenerator: ctk\n---\n")
        (site_dir / "index.html").write_text("<html>viewer</html>")

        source = self._make_source(temp_dir)
        files = _get_data_files(source, temp_dir / "site_output")
        names = [f["name"] for f in files]
        assert "data.json" in names
        assert not any("index.html" in n for n in names)

    def test_excludes_readme_and_excluded_files(self, temp_dir):
        """README.md, CLAUDE.md, etc. should not be listed as data files."""
        (temp_dir / "CLAUDE.md").write_text("# Claude notes")
        (temp_dir / "data.json").write_text("{}")
        source = self._make_source(temp_dir)

        files = _get_data_files(source, temp_dir / "site")
        names = [f["name"] for f in files]
        assert "data.json" in names
        assert "README.md" not in names
        assert "CLAUDE.md" not in names


class TestIsForeignSite:
    """Tests for _is_foreign_site detection."""

    def test_nonexistent_readme(self, temp_dir):
        is_foreign, gen = _is_foreign_site(temp_dir)
        assert is_foreign is False
        assert gen == ""

    def test_readme_without_frontmatter(self, temp_dir):
        (temp_dir / "README.md").write_text("# Some site\n\nNo frontmatter.")
        is_foreign, gen = _is_foreign_site(temp_dir)
        assert is_foreign is False

    def test_readme_without_generator(self, temp_dir):
        (temp_dir / "README.md").write_text(
            "---\nname: Some Site\n---\n# Some site\n\nNo generator field."
        )
        is_foreign, gen = _is_foreign_site(temp_dir)
        assert is_foreign is False

    def test_longecho_generator(self, temp_dir):
        (temp_dir / "README.md").write_text(
            "---\ngenerator: longecho build v0.3.0\n---\n# Our site"
        )
        is_foreign, gen = _is_foreign_site(temp_dir)
        assert is_foreign is False
        assert "longecho build" in gen

    def test_foreign_generator(self, temp_dir):
        (temp_dir / "README.md").write_text(
            "---\ngenerator: ctk v2.1\n---\n# CTK-generated site"
        )
        is_foreign, gen = _is_foreign_site(temp_dir)
        assert is_foreign is True
        assert gen == "ctk v2.1"


class TestRootSourceRendering:
    """Tests for the unified home/detail view (root as a full source)."""

    def test_root_readme_inlined(self, temp_dir):
        """Root source's README content should appear in the SFA."""
        (temp_dir / "README.md").write_text(
            "---\nname: Root Archive\n---\n"
            "# Root Archive\n\nThis description has a UNIQUE_ROOT_TOKEN."
        )
        (temp_dir / "data.json").write_text("{}")

        result = build_site(temp_dir)
        assert result.success is True
        index_content = (result.output_path / "index.html").read_text()
        assert "UNIQUE_ROOT_TOKEN" in index_content

    def test_root_data_files_rendered(self, temp_dir):
        """Root source's direct data files should appear in the SFA JSON."""
        import re
        (temp_dir / "README.md").write_text("# Root\n\nRoot archive.")
        (temp_dir / "root_data.jsonl").write_text("")
        (temp_dir / "root_config.json").write_text("{}")

        result = build_site(temp_dir)
        assert result.success is True

        index_content = (result.output_path / "index.html").read_text()
        match = re.search(r'var ROOT = (.+?);\n', index_content)
        assert match is not None
        root_data = json.loads(match.group(1))

        file_names = [f["name"] for f in root_data["data_files"]]
        assert "root_data.jsonl" in file_names
        assert "root_config.json" in file_names

    def test_root_site_url_is_self_skipped(self, temp_dir):
        """Root's site_url should be None (don't link to self)."""
        import re
        (temp_dir / "README.md").write_text("# Root\n\nRoot archive.")
        (temp_dir / "data.json").write_text("{}")

        # First build creates a site/
        result1 = build_site(temp_dir)
        assert result1.success is True

        # Second build should see the existing site but skip self-reference
        result2 = build_site(temp_dir)
        assert result2.success is True

        index_content = (result2.output_path / "index.html").read_text()
        match = re.search(r'var ROOT = (.+?);\n', index_content)
        assert match is not None
        root_data = json.loads(match.group(1))
        assert root_data["site_url"] is None

    def test_root_with_no_children_still_renders(self, temp_dir):
        """An archive with only direct files (no sub-sources) should render."""
        (temp_dir / "README.md").write_text(
            "# Single-Level Archive\n\nNo sub-sources, just data."
        )
        (temp_dir / "data.json").write_text('{"hello": "world"}')

        result = build_site(temp_dir)
        assert result.success is True
        assert result.sources_count == 0  # no children
        index_content = (result.output_path / "index.html").read_text()
        assert "Single-Level Archive" in index_content


class TestForeignSiteProtection:
    """Tests for build_site refusing to overwrite foreign-generated sites."""

    def test_refuses_to_overwrite_foreign_site(self, echo_compliant_dir):
        """Build should fail cleanly when output contains a foreign site."""
        site_dir = echo_compliant_dir / "site"
        site_dir.mkdir()
        (site_dir / "README.md").write_text(
            "---\nname: CTK Viewer\ngenerator: ctk v2.1\n---\n# CTK"
        )
        (site_dir / "index.html").write_text("<html>CTK VIEWER</html>")

        result = build_site(echo_compliant_dir)
        assert result.success is False
        assert "ctk" in result.error.lower()

        # Existing files must not be touched
        assert "CTK VIEWER" in (site_dir / "index.html").read_text()

    def test_force_overwrites_foreign_site(self, echo_compliant_dir):
        """--force bypasses the foreign-site check."""
        site_dir = echo_compliant_dir / "site"
        site_dir.mkdir()
        (site_dir / "README.md").write_text(
            "---\ngenerator: ctk v2.1\n---\n# CTK"
        )
        (site_dir / "index.html").write_text("<html>CTK VIEWER</html>")

        result = build_site(echo_compliant_dir, force=True)
        assert result.success is True
        # Original content overwritten
        assert "CTK VIEWER" not in (site_dir / "index.html").read_text()

    def test_overwrites_own_previous_site(self, echo_compliant_dir):
        """Sites generated by longecho build should be freely overwritable."""
        result1 = build_site(echo_compliant_dir)
        assert result1.success is True

        # Second build should succeed without --force
        result2 = build_site(echo_compliant_dir)
        assert result2.success is True

    def test_empty_output_directory_ok(self, echo_compliant_dir, temp_dir):
        """Building to an empty or non-existent directory should work."""
        empty_out = temp_dir / "fresh_output"
        result = build_site(echo_compliant_dir, output=empty_out)
        assert result.success is True
        assert (empty_out / "index.html").exists()
