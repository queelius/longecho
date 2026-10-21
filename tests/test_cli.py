"""Tests for the longecho CLI."""

import json

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


class TestCheckWarnings:
    """check reports warnings without changing the exit code."""

    def _archive(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / "photo.heic").write_bytes(b"\x00\xffheic")
        return temp_dir

    def test_compliant_with_warning_exits_zero(self, temp_dir):
        result = runner.invoke(app, ["check", str(self._archive(temp_dir))])
        assert result.exit_code == 0
        assert ".heic" in result.stdout

    def test_verbose_lists_the_files(self, temp_dir):
        result = runner.invoke(app, ["check", str(self._archive(temp_dir)), "-V"])
        assert "photo.heic" in result.stdout

    def test_verbose_caps_the_file_list(self, temp_dir):
        from longecho.cli import MAX_WARNING_PATHS

        self._archive(temp_dir)
        for i in range(MAX_WARNING_PATHS):
            (temp_dir / f"extra{i}.heic").write_bytes(b"\x00\xffheic")
        result = runner.invoke(app, ["check", str(temp_dir), "-V"])
        assert "and 1 more" in result.stdout

    def test_non_compliant_still_shows_warnings(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "photo.heic").write_bytes(b"\x00\xffheic")
        result = runner.invoke(app, ["check", str(temp_dir)])
        assert result.exit_code == 1
        assert ".heic" in result.stdout

    def test_query_json_includes_warnings_only_when_present(self, temp_dir):
        self._archive(temp_dir)
        clean = temp_dir / "clean"
        clean.mkdir()
        (clean / "README.md").write_text("# Clean\n\nClean.")
        (clean / "x.json").write_text("{}")
        result = runner.invoke(app, ["query", str(temp_dir), "--json"])
        by_path = {e["path"]: e for e in json.loads(result.stdout)}
        warning = by_path["."]["warnings"][0]
        assert warning["kind"] == "unrecognized-format"
        assert warning["paths"] == ["photo.heic"]
        assert "warnings" not in by_path["./clean"]


class TestUntrustedTextIsPrintedLiterally:
    """Filenames and README text are data, never Rich markup."""

    def test_markup_in_filenames(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / "[red]secret.bin").write_bytes(b"\x00\xff")
        result = runner.invoke(app, ["check", str(temp_dir), "-V"])
        assert result.exit_code == 0
        assert "[red]secret.bin" in result.stdout

    def test_unbalanced_markup_does_not_crash(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / "[").mkdir()
        (temp_dir / "[" / "b]").write_bytes(b"\x00\xff")
        result = runner.invoke(app, ["check", str(temp_dir), "-V"])
        assert result.exit_code == 0, result.output
        assert "[/b]" in result.stdout

    def test_markup_in_names_and_descriptions(self, temp_dir):
        (temp_dir / "README.md").write_text("# [bold]Loud[/bold]\n\nA [link] here.")
        (temp_dir / "a.json").write_text("{}")
        result = runner.invoke(app, ["query", str(temp_dir)])
        assert "[bold]Loud[/bold]" in result.stdout
        assert "A [link] here." in result.stdout


class TestVerboseReaders:
    def test_lists_the_readers_that_can_open_the_data(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.db").write_bytes(b"x")
        result = runner.invoke(app, ["check", str(temp_dir), "-V"])
        assert "Readable with: standard tool" in result.stdout

    def test_union_in_ladder_order(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.db").write_bytes(b"x")
        (temp_dir / "b.json").write_text("{}")
        result = runner.invoke(app, ["check", str(temp_dir), "-V"])
        assert "Readable with: standard tool, web browser, text editor" in result.stdout


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

    def test_spec_states_the_durability_criteria(self):
        result = runner.invoke(app, ["spec"])
        assert "Library of Congress" in result.stdout
        assert "Impact of patents" in result.stdout

    def test_spec_lists_every_category(self):
        from longecho.formats import DURABLE_FORMAT_CATEGORIES

        result = runner.invoke(app, ["spec"])
        for category in DURABLE_FORMAT_CATEGORIES:
            assert category in result.stdout

    def test_spec_fits_80_columns(self):
        from longecho.cli import _format_spec

        assert max(len(line) for line in _format_spec().splitlines()) <= 80

    def test_spec_mentions_warnings_and_description_cascade(self):
        from longecho.cli import _format_spec

        text = _format_spec()
        assert "Warnings" in text
        assert "Description cascade" in text

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

    def test_formats_shows_readers_and_reasons(self):
        result = runner.invoke(app, ["formats"])
        assert ".pdf" in result.stdout
        assert "web browser" in result.stdout
        assert "ISO 32000" in result.stdout

    def test_formats_json_is_the_registry(self):
        from longecho.formats import FORMATS

        result = runner.invoke(app, ["formats", "--json"])
        assert result.exit_code == 0
        entries = json.loads(result.stdout)
        assert len(entries) == len(FORMATS)
        pdf = next(e for e in entries if ".pdf" in e["extensions"])
        assert pdf["mimetype"] == "application/pdf"
        assert pdf["category"] == "Documents"
        assert sorted(pdf["readers"]) == ["standard tool", "web browser"]
        assert pdf["rationale"]
        wav = next(e for e in entries if ".wav" in e["extensions"])
        assert "audio/x-wav" in wav["mimetype_aliases"]


class TestVersionFlag:
    """Tests for the version flag."""

    def test_version(self):
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "longecho version" in result.stdout


class TestModuleEntryPoint:
    """Smoke test for `python -m longecho` (exercises __main__.py)."""

    def test_python_m_longecho(self):
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "longecho", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "longecho version" in result.stdout
