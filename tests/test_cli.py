"""Tests for the longecho CLI."""

from typer.testing import CliRunner

from longecho.cli import app

runner = CliRunner()


class TestCheckCommand:
    """Tests for the check command."""

    def test_check_compliant_directory(self, echo_compliant_dir):
        result = runner.invoke(app, ["check", str(echo_compliant_dir)])

        assert result.exit_code == 0
        assert "ECHO-compliant" in result.stdout

    def test_check_non_compliant_no_readme(self, non_compliant_dir_no_readme):
        result = runner.invoke(app, ["check", str(non_compliant_dir_no_readme)])

        assert result.exit_code == 1
        assert "Not ECHO-compliant" in result.stdout
        assert "README" in result.stdout

    def test_check_verbose(self, echo_compliant_dir):
        result = runner.invoke(app, ["check", str(echo_compliant_dir), "-v"])

        assert result.exit_code == 0
        assert "README" in result.stdout
        assert "formats" in result.stdout.lower()


class TestDiscoverCommand:
    """Tests for the discover command."""

    def test_discover_finds_sources(self, nested_echo_sources):
        result = runner.invoke(app, ["discover", str(nested_echo_sources)])

        assert result.exit_code == 0
        assert "echo source" in result.stdout.lower()

    def test_discover_table_format(self, nested_echo_sources):
        result = runner.invoke(app, ["discover", str(nested_echo_sources), "--table"])

        assert result.exit_code == 0
        # Table format should have path column

    def test_discover_max_depth(self, nested_echo_sources):
        result = runner.invoke(app, [
            "discover",
            str(nested_echo_sources),
            "--max-depth", "1"
        ])

        assert result.exit_code == 0


class TestSearchCommand:
    """Tests for the search command."""

    def test_search_finds_matches(self, nested_echo_sources):
        result = runner.invoke(app, [
            "search",
            str(nested_echo_sources),
            "conversation"
        ])

        assert result.exit_code == 0
        assert "matching" in result.stdout.lower() or "ctk" in result.stdout.lower()

    def test_search_no_matches(self, nested_echo_sources):
        result = runner.invoke(app, [
            "search",
            str(nested_echo_sources),
            "xyznonexistent"
        ])

        assert result.exit_code == 0
        assert "No ECHO sources matching" in result.stdout


class TestInfoCommand:
    """Tests for the info command."""

    def test_info_compliant_directory(self, echo_compliant_dir):
        result = runner.invoke(app, ["info", str(echo_compliant_dir)])

        assert result.exit_code == 0
        assert "ECHO Source" in result.stdout

    def test_info_non_compliant_directory(self, non_compliant_dir_no_readme):
        result = runner.invoke(app, ["info", str(non_compliant_dir_no_readme)])

        assert result.exit_code == 1
        assert "Not an ECHO source" in result.stdout


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
