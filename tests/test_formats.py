"""Tests for the durable format registry."""

from pathlib import Path

import pytest

from longecho.formats import (
    DURABLE_EXTENSIONS,
    DURABLE_FORMAT_CATEGORIES,
    FORMATS,
    Reader,
    format_for,
    preview_kind,
    reads_as_text,
    sidecar_base,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestRegistryShape:
    """Every entry carries what a reviewer needs to judge it."""

    def test_every_format_has_a_rationale(self):
        for fmt in FORMATS:
            assert fmt.rationale.strip(), fmt.extensions

    def test_every_format_names_at_least_one_reader(self):
        for fmt in FORMATS:
            assert fmt.readers, fmt.extensions

    def test_every_mimetype_is_type_slash_subtype(self):
        for fmt in FORMATS:
            major, _, minor = fmt.mimetype.partition("/")
            assert major and minor, fmt.mimetype

    def test_extensions_are_lowercase_and_dotted(self):
        for fmt in FORMATS:
            for ext in fmt.extensions:
                assert ext.startswith(".") and ext == ext.lower(), ext

    def test_no_extension_is_claimed_twice(self):
        seen: list[str] = []
        for fmt in FORMATS:
            seen.extend(fmt.extensions)
        assert len(seen) == len(set(seen))


class TestDerivedViews:
    """The flat set and the category dict are derived, never maintained."""

    def test_extensions_set_matches_registry(self):
        assert {e for f in FORMATS for e in f.extensions} == DURABLE_EXTENSIONS

    def test_categories_group_the_registry(self):
        for category, exts in DURABLE_FORMAT_CATEGORIES.items():
            expected = [e for f in FORMATS if f.category == category for e in f.extensions]
            assert exts == expected
        flattened = {e for exts in DURABLE_FORMAT_CATEGORIES.values() for e in exts}
        assert flattened == DURABLE_EXTENSIONS


class TestAdditions:
    """Formats added in 0.6.0, each with a reason in the registry."""

    @pytest.mark.parametrize(
        "ext",
        [".pdf", ".svg", ".tif", ".tiff", ".wav", ".flac", ".mp3", ".ogg",
         ".opus", ".mp4", ".webm", ".epub", ".eml", ".mbox"],
    )
    def test_added(self, ext):
        assert ext in DURABLE_EXTENSIONS

    @pytest.mark.parametrize("ext", [".heic", ".docx", ".doc", ".psd", ".mov"])
    def test_still_not_durable(self, ext):
        assert ext not in DURABLE_EXTENSIONS


class TestFormatFor:
    def test_case_insensitive(self):
        fmt = format_for(Path("PHOTO.JPG"))
        assert fmt is not None and fmt.mimetype == "image/jpeg"

    def test_terminal_suffix_only(self):
        fmt = format_for(Path("conversations.jsonl.gz"))
        assert fmt is not None and ".gz" in fmt.extensions

    def test_unknown_returns_none(self):
        assert format_for(Path("photo.heic")) is None
        assert format_for(Path("LICENSE")) is None


class TestPreviewKind:
    """Inline previews are derived from mimetype plus browser support."""

    def test_browser_images_preview_as_image(self):
        assert preview_kind(Path("a.png")) == "image"
        assert preview_kind(Path("a.svg")) == "image"

    def test_audio_and_video(self):
        assert preview_kind(Path("a.mp3")) == "audio"
        assert preview_kind(Path("a.webm")) == "video"

    def test_tiff_has_no_preview_because_browsers_do_not_render_it(self):
        fmt = format_for(Path("scan.tiff"))
        assert fmt is not None and Reader.BROWSER not in fmt.readers
        assert preview_kind(Path("scan.tiff")) is None

    def test_documents_and_unknown_have_no_preview(self):
        assert preview_kind(Path("a.pdf")) is None
        assert preview_kind(Path("a.heic")) is None


class TestReadsAsText:
    def test_utf8_and_empty(self, temp_dir):
        (temp_dir / "a").write_text("hello \u00e9\n", encoding="utf-8")
        (temp_dir / "b").write_bytes(b"")
        assert reads_as_text(temp_dir / "a") and reads_as_text(temp_dir / "b")

    def test_multibyte_character_split_at_the_sample_edge(self, temp_dir):
        # 4095 ASCII bytes, then a 2-byte character straddling byte 4096
        (temp_dir / "a").write_bytes(b"x" * 4095 + "\u00e9".encode())
        assert reads_as_text(temp_dir / "a")

    def test_nul_or_invalid_utf8_is_binary(self, temp_dir):
        (temp_dir / "a").write_bytes(b"abc\x00def")
        (temp_dir / "b").write_bytes(b"\xff\xfe")
        assert not reads_as_text(temp_dir / "a")
        assert not reads_as_text(temp_dir / "b")

    def test_unreadable_is_not_text(self, temp_dir):
        assert not reads_as_text(temp_dir / "missing")


class TestSidecars:
    def test_sqlite_wal_belongs_to_its_database(self):
        base, sidecar = sidecar_base(Path("x/mail.db-wal"))
        assert base == Path("x/mail.db")
        assert sidecar.suffix == "-wal" and sidecar.risk

    def test_journal_and_shm(self):
        base, journal = sidecar_base(Path("a.sqlite-journal"))
        assert base == Path("a.sqlite") and journal.risk
        base, shm = sidecar_base(Path("a.sqlite3-shm"))
        assert base == Path("a.sqlite3")
        assert shm.risk is None  # transient, safe to leave behind

    def test_not_a_sidecar(self):
        assert sidecar_base(Path("notes.txt")) is None
        # The suffix alone is not enough: the base must be a SQLite file.
        assert sidecar_base(Path("notes.txt-wal")) is None


@pytest.mark.parametrize("doc", ["README.md", "docs/spec.md"])
def test_docs_list_every_extension(doc):
    """The hand-written format tables must not drift from the registry."""
    path = REPO_ROOT / doc
    if not path.exists():
        pytest.skip(f"{doc} not shipped in this distribution")
    text = path.read_text(encoding="utf-8")
    missing = [ext for ext in sorted(DURABLE_EXTENSIONS) if f"`{ext}`" not in text]
    assert not missing, f"{doc} is missing {missing}"
