"""Tests for the longecho compliance checker."""

from pathlib import Path

import pytest

from longecho.checker import (
    DURABLE_EXTENSIONS,
    DURABLE_FORMAT_CATEGORIES,
    ComplianceResult,
    EchoSource,
    WarningKind,
    check_compliance,
    detect_durable_formats,
    find_readme,
    is_durable_format,
)


class TestDurableFormatCategories:
    """Tests for the format category structure."""

    def test_extensions_derived_from_categories(self):
        """DURABLE_EXTENSIONS should contain every extension from every category."""
        for exts in DURABLE_FORMAT_CATEGORIES.values():
            for ext in exts:
                assert ext in DURABLE_EXTENSIONS

    def test_no_extra_extensions(self):
        """DURABLE_EXTENSIONS should contain only extensions from categories."""
        all_from_categories = {
            ext for exts in DURABLE_FORMAT_CATEGORIES.values() for ext in exts
        }
        assert DURABLE_EXTENSIONS == all_from_categories


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


class TestDetectDurableFormats:
    """Tests for detect_durable_formats function."""

    def test_detects_common_formats(self, temp_dir):
        (temp_dir / "data.db").touch()
        (temp_dir / "config.json").write_text("{}")
        (temp_dir / "notes.md").write_text("# Notes")

        formats = detect_durable_formats(temp_dir)
        assert ".db" in formats
        assert ".json" in formats
        assert ".md" in formats

    def test_excludes_readme(self, temp_dir):
        (temp_dir / "README.md").write_text("# Test")
        (temp_dir / "data.json").write_text("{}")

        formats = detect_durable_formats(temp_dir)
        assert ".json" in formats
        assert ".md" not in formats  # README.md is excluded

    def test_excludes_non_durable(self, temp_dir):
        (temp_dir / "data.json").write_text("{}")
        (temp_dir / "config.ini").write_text("[section]")
        (temp_dir / "script.sh").write_text("#!/bin/bash")

        formats = detect_durable_formats(temp_dir)
        assert ".json" in formats
        assert ".ini" not in formats
        assert ".sh" not in formats

    def test_respects_max_depth(self, temp_dir):
        (temp_dir / "level1" / "level2" / "level3").mkdir(parents=True)
        (temp_dir / "level1" / "level2" / "level3" / "deep.json").write_text("{}")
        (temp_dir / "shallow.txt").write_text("shallow")

        formats = detect_durable_formats(temp_dir, max_depth=1)
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

    def test_html_is_durable(self):
        assert is_durable_format(".html")
        assert is_durable_format(".htm")

    def test_archives_are_durable(self):
        """zip, gz (covers .tar.gz), and tgz all clear the durability bar.

        These compression formats have been part of every mainstream OS
        since the 1990s and decode without special tooling in 2026.
        """
        assert is_durable_format(".zip")
        assert is_durable_format(".gz")
        assert is_durable_format(".tgz")

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

    def test_compliance_passes_on_gzipped_structured_data(self, temp_dir):
        """A directory containing .jsonl.gz passes compliance via .gz suffix.

        Pins the pragmatic behavior: gzipped JSONL (a common export format
        from conversation tools, log pipelines, etc.) is recognized as
        durable. Path.suffix returns only the outer '.gz', so the jsonl
        part is not itself registered, but .gz is durable so the directory
        qualifies.
        """
        import gzip

        (temp_dir / "README.md").write_text("# Archive\n\nGzipped exports.")
        payload = gzip.compress(b'{"id": 1}\n{"id": 2}\n')
        (temp_dir / "conversations.jsonl.gz").write_bytes(payload)

        result = check_compliance(temp_dir)
        assert result.compliant is True
        assert result.source is not None
        assert ".gz" in result.source.durable_formats

    def test_compliance_passes_on_tar_gz(self, temp_dir):
        """.tar.gz is detected via the terminal .gz suffix.

        Documents the contract: there is no separate .tar.gz entry in
        DURABLE_EXTENSIONS. The .gz suffix is what earns durability,
        which matches how Path.suffix parses the filename.
        """
        import gzip

        (temp_dir / "README.md").write_text("# Archive\n\nA tarball.")
        (temp_dir / "backup.tar.gz").write_bytes(gzip.compress(b"fake tar"))

        result = check_compliance(temp_dir)
        assert result.compliant is True
        assert ".gz" in result.source.durable_formats

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


# Bytes no text editor would show as text: a NUL, then non-UTF-8.
BINARY = b"\x00\x01\xffheic"


class TestOwnedFiles:
    """EchoSource.files lists every file the source owns, durable or not."""

    def test_lists_durable_and_unrecognized(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / "b.heic").write_bytes(b"x")
        source = check_compliance(temp_dir).source
        assert source is not None
        assert [p.name for p in source.files] == ["a.json", "b.heic"]

    def test_excludes_readme_nested_sources_site_and_skipped_dirs(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        for name in ("sub", "site", "node_modules"):
            d = temp_dir / name
            d.mkdir()
            (d / "x.json").write_text("{}")
        (temp_dir / "sub" / "README.md").write_text("# Sub\n\nSub.")
        source = check_compliance(temp_dir).source
        assert source is not None
        assert [p.name for p in source.files] == ["a.json"]

    def test_dotfiles_are_not_owned(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / ".DS_Store").write_bytes(BINARY)
        result = check_compliance(temp_dir)
        assert result.source is not None
        assert [p.name for p in result.source.files] == ["a.json"]
        assert result.warnings == []

    def test_files_in_plain_subdirectories_are_owned(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "data").mkdir()
        (temp_dir / "data" / "r.jsonl").write_text("")
        source = check_compliance(temp_dir).source
        assert source is not None
        assert [p.relative_to(temp_dir).as_posix() for p in source.files] == ["data/r.jsonl"]


class TestComplianceWarnings:
    """Warnings flag risks without changing the compliance verdict."""

    def _archive(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        return temp_dir

    def test_clean_archive_has_no_warnings(self, temp_dir):
        result = check_compliance(self._archive(temp_dir))
        assert result.compliant and result.warnings == []

    def test_unrecognized_formats_grouped_by_extension(self, temp_dir):
        self._archive(temp_dir)
        (temp_dir / "one.heic").write_bytes(BINARY)
        (temp_dir / "two.HEIC").write_bytes(BINARY)
        (temp_dir / "memo.docx").write_bytes(BINARY)
        result = check_compliance(temp_dir)
        assert result.compliant
        unrecognized = [w for w in result.warnings if w.kind is WarningKind.UNRECOGNIZED_FORMAT]
        assert [len(w.paths) for w in unrecognized] == [1, 2]  # .docx, then .heic
        assert ".heic" in unrecognized[1].message

    def test_binary_files_without_extension(self, temp_dir):
        self._archive(temp_dir)
        (temp_dir / "blob").write_bytes(BINARY)
        result = check_compliance(temp_dir)
        assert len(result.warnings) == 1
        assert "no extension" in result.warnings[0].message

    def test_plain_text_in_any_extension_is_quiet(self, temp_dir):
        """A text editor opens these, so a future reader can too."""
        self._archive(temp_dir)
        (temp_dir / "LICENSE").write_text("MIT License\n")
        (temp_dir / "analysis.py").write_text("print('caf\u00e9')\n", encoding="utf-8")
        (temp_dir / "paper.tex").write_text("\\documentclass{article}\n")
        (temp_dir / "empty.cfg").write_bytes(b"")
        assert check_compliance(temp_dir).warnings == []

    def test_non_utf8_text_still_warns(self, temp_dir):
        self._archive(temp_dir)
        (temp_dir / "old.nfo").write_bytes(b"caf\xe9 au lait\n")  # Latin-1
        assert len(check_compliance(temp_dir).warnings) == 1

    def test_nonempty_wal_is_a_risk(self, temp_dir):
        self._archive(temp_dir)
        (temp_dir / "mail.db").write_bytes(BINARY)
        (temp_dir / "mail.db-wal").write_bytes(b"frames")
        (temp_dir / "mail.db-shm").write_bytes(b"index")
        result = check_compliance(temp_dir)
        assert [w.kind for w in result.warnings] == [WarningKind.SIDECAR_AT_RISK]
        warning = result.warnings[0]
        assert warning.paths == [temp_dir.resolve() / "mail.db-wal"]
        assert "<db>" not in warning.message
        assert "sqlite3 mail.db " in warning.message

    def test_sidecar_remedy_uses_the_path_from_the_source_root(self, temp_dir):
        self._archive(temp_dir)
        (temp_dir / "notes").mkdir()
        (temp_dir / "notes" / "j.db").write_bytes(BINARY)
        (temp_dir / "notes" / "j.db-wal").write_bytes(b"frames")
        message = check_compliance(temp_dir).warnings[0].message
        assert message.startswith("notes/j.db-wal ")
        assert "sqlite3 notes/j.db " in message

    def test_empty_wal_and_shm_are_quiet(self, temp_dir):
        """A checkpointed database leaves an empty -wal; -shm is always transient."""
        self._archive(temp_dir)
        (temp_dir / "mail.db").write_bytes(BINARY)
        (temp_dir / "mail.db-wal").write_bytes(b"")
        (temp_dir / "mail.db-shm").write_bytes(b"index")
        assert check_compliance(temp_dir).warnings == []

    def test_warnings_reported_even_when_not_compliant(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nOnly HEIC here.")
        (temp_dir / "photo.heic").write_bytes(BINARY)
        result = check_compliance(temp_dir)
        assert not result.compliant
        assert [w.kind for w in result.warnings] == [WarningKind.UNRECOGNIZED_FORMAT]

    def test_nested_source_warnings_stay_with_the_nested_source(self, temp_dir):
        self._archive(temp_dir)
        sub = temp_dir / "sub"
        sub.mkdir()
        (sub / "README.md").write_text("# Sub\n\nSub.")
        (sub / "x.json").write_text("{}")
        (sub / "y.heic").write_bytes(BINARY)
        assert check_compliance(temp_dir).warnings == []
        assert len(check_compliance(sub).warnings) == 1


class TestNewlyDurableFormats:
    """Formats added in 0.6.0 make a directory compliant on their own."""

    def test_pdf_alone_is_compliant(self, temp_dir):
        (temp_dir / "README.md").write_text("# Scans\n\nScanned letters.")
        (temp_dir / "letter.pdf").write_bytes(b"%PDF-1.7")
        result = check_compliance(temp_dir)
        assert result.compliant
        assert result.source is not None and result.source.durable_formats == [".pdf"]


class TestWalkRobustness:
    """Odd filesystem entries never crash a check (review findings, 0.6.0)."""

    def _archive(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        return temp_dir

    def test_symlink_loop(self, temp_dir):
        import os

        self._archive(temp_dir)
        os.symlink("loop", temp_dir / "loop")
        result = check_compliance(temp_dir)
        assert result.compliant
        assert result.warnings == []

    def test_symlink_into_unreadable_directory(self, temp_dir):
        import os

        if os.geteuid() == 0:
            pytest.skip("root can read everything")
        self._archive(temp_dir)
        locked = temp_dir / "locked"
        locked.mkdir()
        (locked / "f").write_text("x")
        os.symlink(locked / "f", temp_dir / "link")
        locked.chmod(0)
        try:
            result = check_compliance(temp_dir)
            assert result.compliant
        finally:
            locked.chmod(0o755)

    def test_broken_symlink_is_ignored(self, temp_dir):
        import os

        self._archive(temp_dir)
        os.symlink(temp_dir / "missing", temp_dir / "dangling")
        result = check_compliance(temp_dir)
        assert result.source is not None
        assert [p.name for p in result.source.files] == ["a.json"]

    def test_readme_symlink_into_unreadable_directory(self, temp_dir):
        import os

        if os.geteuid() == 0:
            pytest.skip("root can read everything")
        (temp_dir / "a.json").write_text("{}")
        locked = temp_dir / "locked"
        locked.mkdir()
        (locked / "README.md").write_text("# T\n")
        os.symlink(locked / "README.md", temp_dir / "README.md")
        locked.chmod(0)
        try:
            result = check_compliance(temp_dir)
            assert not result.compliant
        finally:
            locked.chmod(0o755)


class TestWhatCountsAsData:
    def test_lowercase_readme_is_not_its_own_data(self, temp_dir):
        (temp_dir / "readme.md").write_text("# T\n\nOnly a readme.")
        result = check_compliance(temp_dir)
        assert not result.compliant
        assert result.reason == "No durable data formats found"

    def test_durable_files_only_in_site_do_not_count(self, temp_dir):
        """A viewer is not the data: raw data must exist alongside site/."""
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "site").mkdir()
        (temp_dir / "site" / "index.html").write_text("<html></html>")
        assert not check_compliance(temp_dir).compliant

    def test_durable_files_only_in_tool_directories_do_not_count(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "node_modules").mkdir()
        (temp_dir / "node_modules" / "package.json").write_text("{}")
        assert not check_compliance(temp_dir).compliant

    def test_data_in_nested_sources_still_counts(self, temp_dir):
        (temp_dir / "README.md").write_text("# Root\n\nRoot.")
        sub = temp_dir / "sub"
        sub.mkdir()
        (sub / "README.md").write_text("# Sub\n\nSub.")
        (sub / "x.json").write_text("{}")
        assert check_compliance(temp_dir).compliant


class TestNotInspectedWarning:
    """Directories beyond the scan depth are named, not silently skipped."""

    def test_deep_directories_are_reported(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "notes.txt").write_text("hi")
        deep = temp_dir / "photos" / "2020" / "01"
        deep.mkdir(parents=True)
        (deep / "a.jpg").write_bytes(BINARY)
        result = check_compliance(temp_dir)
        kinds = [w.kind for w in result.warnings]
        assert kinds == [WarningKind.NOT_INSPECTED]
        assert result.warnings[0].paths == [deep]

    def test_empty_or_nested_source_dirs_at_the_boundary_are_quiet(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "notes.txt").write_text("hi")
        (temp_dir / "a" / "b" / "empty").mkdir(parents=True)
        nested = temp_dir / "a" / "b" / "src"
        nested.mkdir()
        (nested / "README.md").write_text("# S\n\nS.")
        (nested / "x.json").write_text("{}")
        assert check_compliance(temp_dir).warnings == []


class TestWarningMessages:
    def test_message_says_utf8(self, temp_dir):
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / "b.heic").write_bytes(BINARY)
        message = check_compliance(temp_dir).warnings[0].message
        assert message == "1 file in .heic: not in a durable format, and not UTF-8 text"


class TestWarningsAreLazy:
    """Walking a tree must not read file contents nobody will look at."""

    def test_discovery_reads_no_file_contents(self, temp_dir, monkeypatch):
        import longecho.formats as formats
        from longecho.discovery import discover_sources

        calls = []
        monkeypatch.setattr(formats, "reads_as_text", lambda p: calls.append(p) or False)
        (temp_dir / "README.md").write_text("# T\n\nT.")
        (temp_dir / "a.json").write_text("{}")
        (temp_dir / "b.heic").write_bytes(BINARY)
        sources = list(discover_sources(temp_dir))
        assert len(sources) == 1 and calls == []
        assert len(sources[0].warnings) == 1  # computed on first access
        assert len(calls) == 1
