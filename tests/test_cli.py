"""Tests for the longecho CLI."""

from typer.testing import CliRunner

from longecho.cli import app

runner = CliRunner()


class TestCheckCommand:
    """Tests for the check command."""

    def test_check_compliant_directory(self, echo_compliant_dir):
        result = runner.invoke(app, ["check", str(echo_compliant_dir)])

        assert result.exit_code == 0
        assert "longecho-compliant" in result.stdout

    def test_check_non_compliant_no_readme(self, non_compliant_dir_no_readme):
        result = runner.invoke(app, ["check", str(non_compliant_dir_no_readme)])

        assert result.exit_code == 1
        assert "Not longecho-compliant" in result.stdout
        assert "README" in result.stdout

    def test_check_verbose(self, echo_compliant_dir):
        result = runner.invoke(app, ["check", str(echo_compliant_dir), "-V"])

        assert result.exit_code == 0
        assert "README" in result.stdout
        assert "formats" in result.stdout.lower()

    def test_check_verbose_shows_frontmatter(self, temp_dir):
        """Verbose check shows custom frontmatter fields."""
        (temp_dir / "README.md").write_text(
            "---\nname: Test\nauthor: Alex\n---\n# Test\n\nA test."
        )
        (temp_dir / "data.json").write_text("{}")

        result = runner.invoke(app, ["check", str(temp_dir), "-V"])
        assert result.exit_code == 0
        assert "author" in result.stdout


class TestQueryCommand:
    """Tests for the query command."""

    def test_query_finds_sources(self, nested_echo_sources):
        result = runner.invoke(app, ["query", str(nested_echo_sources)])

        assert result.exit_code == 0
        assert "source" in result.stdout.lower()

    def test_query_search(self, nested_echo_sources):
        result = runner.invoke(app, [
            "query", str(nested_echo_sources),
            "--search", "conversation",
        ])

        assert result.exit_code == 0

    def test_query_search_no_matches(self, nested_echo_sources):
        result = runner.invoke(app, [
            "query", str(nested_echo_sources),
            "--search", "xyznonexistent",
        ])

        assert result.exit_code == 0
        assert "No longecho sources" in result.stdout

    def test_query_table_format(self, nested_echo_sources):
        result = runner.invoke(app, [
            "query", str(nested_echo_sources), "--table",
        ])

        assert result.exit_code == 0

    def test_query_json_format(self, nested_echo_sources):
        result = runner.invoke(app, [
            "query", str(nested_echo_sources), "--json",
        ])

        assert result.exit_code == 0

    def test_query_depth(self, nested_echo_sources):
        result = runner.invoke(app, [
            "query", str(nested_echo_sources),
            "--depth", "1",
        ])

        assert result.exit_code == 0


    def test_query_shows_relative_paths(self, nested_echo_sources):
        result = runner.invoke(app, ["query", str(nested_echo_sources)])

        assert result.exit_code == 0
        assert "./" in result.stdout

    def test_query_shows_tree_indentation(self, nested_echo_sources):
        """Deeper sources are indented more than shallow ones."""
        result = runner.invoke(app, ["query", str(nested_echo_sources)])
        assert result.exit_code == 0
        # The root should be at the leftmost position (no leading spaces before name)
        # Children should be indented
        lines = result.stdout.split("\n")
        # Find lines with source names (cyan-colored in rich output)
        name_lines = [l for l in lines if "./" in l or l.strip().startswith(".")]
        # At least one line should start with more spaces than another
        indents = [len(l) - len(l.lstrip()) for l in name_lines if l.strip()]
        if len(indents) > 1:
            assert max(indents) > min(indents), "Expected varying indentation for tree display"


class TestSpecCommand:
    """Tests for the spec command."""

    def test_spec_prints_summary(self):
        result = runner.invoke(app, ["spec"])

        assert result.exit_code == 0
        assert "longecho" in result.stdout
        assert "durable" in result.stdout.lower()
        assert "README" in result.stdout

    def test_spec_includes_formats(self):
        result = runner.invoke(app, ["spec"])

        assert ".db" in result.stdout
        assert ".json" in result.stdout
        assert ".html" in result.stdout

    def test_spec_includes_principles(self):
        result = runner.invoke(app, ["spec"])

        assert "Self-Describing" in result.stdout
        assert "Local-First" in result.stdout


class TestBuildCommand:
    """Tests for the build command."""

    def test_build_compliant(self, echo_compliant_dir):
        result = runner.invoke(app, ["build", str(echo_compliant_dir)])

        assert result.exit_code == 0
        assert "Built site" in result.stdout

    def test_build_non_compliant(self, non_compliant_dir_no_readme):
        result = runner.invoke(app, ["build", str(non_compliant_dir_no_readme)])

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()


class TestFormatsCommand:
    """Tests for the formats command."""

    def test_formats_lists_categories(self):
        result = runner.invoke(app, ["formats"])

        assert result.exit_code == 0
        assert "Structured data" in result.stdout
        assert "Documents" in result.stdout
        assert ".db" in result.stdout
        assert ".json" in result.stdout


class TestVersionFlag:
    """Tests for the version flag."""

    def test_version(self):
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "longecho version" in result.stdout
