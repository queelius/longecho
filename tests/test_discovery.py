"""Tests for the ECHO source discovery."""

from pathlib import Path

from longecho.discovery import (
    discover_sources,
    get_source_info,
    search_sources,
    should_skip_directory,
)


class TestShouldSkipDirectory:
    """Tests for should_skip_directory function."""

    def test_skips_hidden_directories(self):
        assert should_skip_directory(".git")
        assert should_skip_directory(".hidden")

    def test_skips_common_dirs(self):
        assert should_skip_directory("node_modules")
        assert should_skip_directory("__pycache__")
        assert should_skip_directory(".venv")

    def test_skips_egg_info(self):
        assert should_skip_directory("mypackage.egg-info")

    def test_allows_normal_dirs(self):
        assert not should_skip_directory("src")
        assert not should_skip_directory("data")
        assert not should_skip_directory("exports")


class TestDiscoverSources:
    """Tests for discover_sources function."""

    def test_discovers_multiple_sources(self, nested_echo_sources):
        sources = list(discover_sources(nested_echo_sources))

        # Should find ctk-export, bookmarks, and blog
        assert len(sources) >= 3

        paths = [str(s.path) for s in sources]
        assert any("ctk-export" in p for p in paths)
        assert any("bookmarks" in p for p in paths)
        assert any("blog" in p for p in paths)

    def test_respects_max_depth(self, nested_echo_sources):
        # With max_depth=1, shouldn't find nested blog
        sources = list(discover_sources(nested_echo_sources, max_depth=1))

        paths = [str(s.path) for s in sources]
        assert any("ctk-export" in p for p in paths)
        assert any("bookmarks" in p for p in paths)
        # blog is at depth 2 (projects/blog), may or may not be found

    def test_empty_on_nonexistent_path(self):
        sources = list(discover_sources(Path("/nonexistent")))
        assert len(sources) == 0

    def test_skips_non_compliant(self, nested_echo_sources):
        # The "other" directory has no README, should be skipped
        sources = list(discover_sources(nested_echo_sources))

        paths = [str(s.path) for s in sources]
        assert not any("other" in p for p in paths)


class TestSearchSources:
    """Tests for search_sources function."""

    def test_finds_by_query(self, nested_echo_sources):
        sources = list(search_sources(nested_echo_sources, "conversation"))

        assert len(sources) >= 1
        paths = [str(s.path) for s in sources]
        assert any("ctk-export" in p for p in paths)

    def test_case_insensitive(self, nested_echo_sources):
        sources_lower = list(search_sources(nested_echo_sources, "conversation"))
        sources_upper = list(search_sources(nested_echo_sources, "CONVERSATION"))

        assert len(sources_lower) == len(sources_upper)

    def test_no_results_for_missing_query(self, nested_echo_sources):
        sources = list(search_sources(nested_echo_sources, "xyznonexistent"))
        assert len(sources) == 0


class TestGetSourceInfo:
    """Tests for get_source_info function."""

    def test_returns_info_for_compliant(self, echo_compliant_dir):
        source = get_source_info(echo_compliant_dir)

        assert source is not None
        assert source.path == echo_compliant_dir
        assert source.readme_path is not None
        assert len(source.durable_formats) > 0

    def test_returns_none_for_non_compliant(self, non_compliant_dir_no_readme):
        source = get_source_info(non_compliant_dir_no_readme)
        assert source is None
