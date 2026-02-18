"""Tests for the longecho compliance checker."""

from pathlib import Path

from longecho.checker import (
    ComplianceResult,
    EchoSource,
    check_compliance,
    detect_formats,
    find_readme,
    is_durable_format,
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
        assert ".md" not in formats  # README.md is excluded

    def test_respects_max_depth(self, temp_dir):
        (temp_dir / "level1" / "level2" / "level3").mkdir(parents=True)
        (temp_dir / "level1" / "level2" / "level3" / "deep.json").write_text("{}")
        (temp_dir / "shallow.txt").write_text("shallow")

        formats = detect_formats(temp_dir, max_depth=1)
        assert ".txt" in formats


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
        assert result.source is not None
        assert result.source.readme_path.name == "README.md"
        assert len(result.source.durable_formats) > 0
        assert ".db" in result.source.durable_formats or ".json" in result.source.durable_formats

    def test_non_compliant_no_readme(self, non_compliant_dir_no_readme):
        result = check_compliance(non_compliant_dir_no_readme)

        assert result.compliant is False
        assert result.source is None
        assert "README" in result.reason

    def test_non_compliant_no_durable_formats(self, non_compliant_dir_no_durable):
        result = check_compliance(non_compliant_dir_no_durable)

        assert result.compliant is False
        assert result.source is None
        assert "durable" in result.reason.lower()

    def test_nonexistent_path(self):
        result = check_compliance(Path("/nonexistent/path"))

        assert result.compliant is False
        assert result.source is None
        assert "not exist" in result.reason.lower()

    def test_file_path(self, temp_dir):
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        result = check_compliance(test_file)

        assert result.compliant is False
        assert result.source is None
        assert "not a directory" in result.reason.lower()


class TestComplianceResult:
    """Tests for ComplianceResult dataclass."""

    def test_str_compliant(self, temp_dir):
        result = ComplianceResult(
            compliant=True,
            path=temp_dir,
            source=EchoSource(
                path=temp_dir,
                readme_path=temp_dir / "README.md",
                name="test",
                description="test desc",
                durable_formats=[".db", ".json"],
            ),
        )

        assert "longecho-compliant" in str(result)

    def test_str_non_compliant(self, temp_dir):
        result = ComplianceResult(
            compliant=False,
            path=temp_dir,
            reason="No README found",
        )

        assert "Not longecho-compliant" in str(result)
        assert "No README" in str(result)


class TestEchoSource:
    """Tests for EchoSource dataclass."""

    def test_str_short_description(self, temp_dir):
        source = EchoSource(
            path=temp_dir,
            readme_path=temp_dir / "README.md",
            name="test",
            description="A short description",
        )
        s = str(source)
        assert str(temp_dir) in s
        assert "A short description" in s

    def test_str_long_description_truncated(self, temp_dir):
        long_desc = "A" * 80
        source = EchoSource(
            path=temp_dir,
            readme_path=temp_dir / "README.md",
            name="test",
            description=long_desc,
        )
        s = str(source)
        assert "..." in s
        assert len(s.split(": ", 1)[1]) <= 60

    def test_str_empty_description(self, temp_dir):
        source = EchoSource(
            path=temp_dir,
            readme_path=temp_dir / "README.md",
            name="test",
            description="",
        )
        assert "No description" in str(source)

    def test_defaults(self, temp_dir):
        source = EchoSource(
            path=temp_dir,
            readme_path=temp_dir / "README.md",
            name="test",
            description="desc",
        )
        assert source.formats == []
        assert source.durable_formats == []
        assert source.has_site is False
        assert source.site_path is None
        assert source.frontmatter is None
        assert source.contents is None


class TestCheckComplianceEchoSource:
    """Tests for EchoSource population in check_compliance."""

    def test_name_from_readme_title(self, echo_compliant_dir):
        result = check_compliance(echo_compliant_dir)
        assert result.source is not None
        assert result.source.name == "Test Data Archive"

    def test_description_from_readme(self, echo_compliant_dir):
        result = check_compliance(echo_compliant_dir)
        assert result.source is not None
        assert "test archive" in result.source.description.lower()

    def test_frontmatter_name_overrides_heading(self, temp_dir):
        """Frontmatter 'name' field takes priority over # Heading."""
        readme = temp_dir / "README.md"
        readme.write_text(
            "---\nname: Frontmatter Name\ndescription: Frontmatter desc\n---\n"
            "# Heading Title\n\nSome paragraph text.\n"
        )
        (temp_dir / "data.json").write_text("{}")

        result = check_compliance(temp_dir)
        assert result.source is not None
        assert result.source.name == "Frontmatter Name"
        assert result.source.description == "Frontmatter desc"

    def test_frontmatter_preserved(self, temp_dir):
        """All frontmatter is stored on the source."""
        readme = temp_dir / "README.md"
        readme.write_text(
            "---\nname: Test\nauthor: Alex\ndatetime: 2026-02-18\n---\n"
            "# Test\n\nA test source.\n"
        )
        (temp_dir / "data.json").write_text("{}")

        result = check_compliance(temp_dir)
        assert result.source is not None
        assert result.source.frontmatter is not None
        assert result.source.frontmatter["author"] == "Alex"

    def test_contents_field_parsed(self, temp_dir):
        """Contents field is parsed from frontmatter."""
        readme = temp_dir / "README.md"
        readme.write_text(
            "---\ncontents:\n  - path: data/\n  - path: index.json\n    description: An index\n---\n"
            "# Test\n\nA test source.\n"
        )
        (temp_dir / "data.json").write_text("{}")

        result = check_compliance(temp_dir)
        assert result.source is not None
        assert result.source.contents is not None
        assert len(result.source.contents) == 2
        assert result.source.contents[0]["path"] == "data/"

    def test_site_detection(self, temp_dir):
        (temp_dir / "README.md").write_text("# Test\n\nA test source.")
        (temp_dir / "data.db").touch()
        site_dir = temp_dir / "site"
        site_dir.mkdir()
        (site_dir / "index.html").write_text("<html></html>")

        result = check_compliance(temp_dir)
        assert result.source is not None
        assert result.source.has_site is True
        assert result.source.site_path == site_dir

    def test_no_site_without_index(self, temp_dir):
        (temp_dir / "README.md").write_text("# Test\n\nA test source.")
        (temp_dir / "data.db").touch()
        site_dir = temp_dir / "site"
        site_dir.mkdir()

        result = check_compliance(temp_dir)
        assert result.source is not None
        assert result.source.has_site is False

    def test_name_falls_back_to_dirname(self, temp_dir):
        (temp_dir / "README.md").write_text("Just some text without a heading.\n")
        (temp_dir / "data.csv").write_text("a,b\n1,2\n")

        result = check_compliance(temp_dir)
        assert result.source is not None
        assert result.source.name == temp_dir.name
