"""The durable format registry.

Which formats count as durable is a judgment, not a capability: longecho never
reads file contents, so there is nothing per format to plug in. The registry
records that judgment as data. Each entry says why the format qualifies,
measured against the Library of Congress sustainability factors below, and
which readers can open it, which is what ties a format to a rung of the
graceful-degradation ladder.

Everything else (the flat extension set, the category view, inline previews in
the generated site, the ``formats`` and ``spec`` output) is derived from
``FORMATS``. Adding a format means adding one entry with its reasons.
"""

import codecs
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

# The Library of Congress "Sustainability of Digital Formats" factors.
# A format is judged on balance against all of them.
DURABILITY_CRITERIA: tuple[tuple[str, str], ...] = (
    ("Disclosure", "The specification is published and open to anyone."),
    ("Adoption", "It is widely used, so new readers keep being written."),
    ("Transparency", "Simple tools can inspect it, ideally as plain text."),
    ("Self-documentation", "A file can carry its own descriptive metadata."),
    ("External dependencies", "It needs no particular program, platform, or service."),
    ("Impact of patents", "Patents do not limit who may write a reader."),
    ("Technical protection", "No DRM or mandatory encryption guards the content."),
)


class Reader(Enum):
    """The kinds of reader that can open a format, from the degradation ladder.

    Modern LLMs are left out on purpose: they read every text format here,
    and the ladder only matters for the readers that remain once they are gone.
    """

    STANDARD_TOOL = "standard tool"
    BROWSER = "web browser"
    TEXT_EDITOR = "text editor"

    @property
    def description(self) -> str:
        return _READER_DESCRIPTIONS[self]


_READER_DESCRIPTIONS: dict[Reader, str] = {
    Reader.STANDARD_TOOL: (
        "a free program that ships with or is packaged for every mainstream OS "
        "(sqlite3, unzip, an image viewer, a PDF or ebook reader)"
    ),
    Reader.BROWSER: "any web browser, opening the file directly",
    Reader.TEXT_EDITOR: "any text editor, reading the file as plain text",
}


@dataclass(frozen=True)
class Sidecar:
    """A companion file a format's own software writes next to it.

    ``risk`` explains what is lost when the main file is copied without this
    one; ``None`` means the sidecar is transient and safe to leave behind.
    """

    suffix: str
    risk: Optional[str] = None


@dataclass(frozen=True)
class Format:
    """One durable format and the reasons it qualifies."""

    extensions: tuple[str, ...]
    mimetype: str
    category: str
    readers: frozenset[Reader]
    rationale: str
    sidecars: tuple[Sidecar, ...] = ()


_TEXT = frozenset({Reader.TEXT_EDITOR})
_TEXT_AND_BROWSER = frozenset({Reader.TEXT_EDITOR, Reader.BROWSER})
_BROWSER_AND_TOOL = frozenset({Reader.BROWSER, Reader.STANDARD_TOOL})
_TOOL = frozenset({Reader.STANDARD_TOOL})

_SQLITE_SIDECARS = (
    Sidecar(
        "-wal",
        "may hold committed changes that are not yet in the database file; copy "
        "both together, or checkpoint first with "
        "sqlite3 <db> 'PRAGMA wal_checkpoint(TRUNCATE)'",
    ),
    Sidecar(
        "-journal",
        "is the rollback journal of an interrupted write; open the database "
        "once with sqlite3 so it can recover before you copy it",
    ),
    Sidecar("-shm"),
)

# Entries are grouped by category; the order here is the display order.
FORMATS: tuple[Format, ...] = (
    Format(
        (".db", ".sqlite", ".sqlite3"), "application/vnd.sqlite3",
        "Structured data", _TOOL,
        "SQLite: public-domain code, a documented and stable file format, a "
        "Library of Congress recommended format for datasets.",
        sidecars=_SQLITE_SIDECARS,
    ),
    Format(
        (".json",), "application/json", "Structured data", _TEXT_AND_BROWSER,
        "JSON: RFC 8259 and ECMA-404, plain text, a parser in every language.",
    ),
    Format(
        (".jsonl",), "application/jsonl", "Structured data", _TEXT,
        "JSON Lines: one JSON value per line, so it survives truncation and "
        "streams through grep and line tools.",
    ),
    Format(
        (".md", ".markdown"), "text/markdown", "Documents", _TEXT,
        "Markdown: RFC 7763, plain text that reads well even unrendered.",
    ),
    Format(
        (".txt", ".text"), "text/plain", "Documents", _TEXT_AND_BROWSER,
        "Plain text: the floor of the ladder, readable by anything.",
    ),
    Format(
        (".rst",), "text/x-rst", "Documents", _TEXT,
        "reStructuredText: a published plain-text markup, readable unrendered.",
    ),
    Format(
        (".html", ".htm"), "text/html", "Documents", _TEXT_AND_BROWSER,
        "HTML: an open standard, and the one format every browser renders.",
    ),
    Format(
        (".pdf",), "application/pdf", "Documents", _BROWSER_AND_TOOL,
        "PDF: ISO 32000, with PDF/A (ISO 19005) as its archival profile; "
        "browsers and OS viewers open it without extra software.",
    ),
    Format(
        (".epub",), "application/epub+zip", "Documents", _TOOL,
        "EPUB: a W3C standard, zipped XHTML underneath, so unzip and a "
        "browser still work when no ebook reader does.",
    ),
    Format(
        (".eml",), "message/rfc822", "Mail", _TEXT,
        "Email message: RFC 5322 plain text, headers and body readable as is.",
    ),
    Format(
        (".mbox",), "application/mbox", "Mail", _TEXT,
        "mbox: RFC 4155, RFC 5322 messages concatenated in one text file.",
    ),
    Format(
        (".csv",), "text/csv", "Tabular / data", _TEXT,
        "CSV: RFC 4180, plain text, opened by every spreadsheet.",
    ),
    Format(
        (".tsv",), "text/tab-separated-values", "Tabular / data", _TEXT,
        "TSV: an IANA-registered plain-text table, simpler to parse than CSV.",
    ),
    Format(
        (".xml",), "application/xml", "Tabular / data", _TEXT_AND_BROWSER,
        "XML: a W3C standard, plain text, with parsers everywhere.",
    ),
    Format(
        (".yaml", ".yml"), "application/yaml", "Tabular / data", _TEXT,
        "YAML: a published spec (RFC 9512 media type), plain text.",
    ),
    Format(
        (".jpg", ".jpeg"), "image/jpeg", "Images", _BROWSER_AND_TOOL,
        "JPEG: ISO/IEC 10918, decoded by every device made in 30 years.",
    ),
    Format(
        (".png",), "image/png", "Images", _BROWSER_AND_TOOL,
        "PNG: ISO/IEC 15948, lossless, patent-free by design.",
    ),
    Format(
        (".gif",), "image/gif", "Images", _BROWSER_AND_TOOL,
        "GIF: a published 1989 spec whose patents expired in 2004.",
    ),
    Format(
        (".webp",), "image/webp", "Images", _BROWSER_AND_TOOL,
        "WebP: RFC 9649, royalty-free, supported by every current browser.",
    ),
    Format(
        (".svg",), "image/svg+xml", "Images",
        frozenset({Reader.BROWSER, Reader.TEXT_EDITOR}),
        "SVG: a W3C standard, vector images stored as readable XML text.",
    ),
    Format(
        (".tif", ".tiff"), "image/tiff", "Images", _TOOL,
        "TIFF: a published spec (TIFF 6.0) and the archival standard for "
        "scans; OS image viewers open it, though most browsers do not.",
    ),
    Format(
        (".wav",), "audio/wav", "Audio", _BROWSER_AND_TOOL,
        "WAV: uncompressed PCM in a documented RIFF container, the simplest "
        "audio there is.",
    ),
    Format(
        (".flac",), "audio/flac", "Audio", _BROWSER_AND_TOOL,
        "FLAC: RFC 9639, lossless and royalty-free.",
    ),
    Format(
        (".mp3",), "audio/mpeg", "Audio", _BROWSER_AND_TOOL,
        "MP3: ISO/IEC 11172-3, the most widely decoded audio format; its "
        "patents expired in 2017.",
    ),
    Format(
        (".ogg",), "audio/ogg", "Audio", _BROWSER_AND_TOOL,
        "Ogg: RFC 3533 container, usually Vorbis audio, royalty-free.",
    ),
    Format(
        (".opus",), "audio/opus", "Audio", _BROWSER_AND_TOOL,
        "Opus: RFC 6716, royalty-free, the IETF's audio codec.",
    ),
    Format(
        (".mp4",), "video/mp4", "Video", _BROWSER_AND_TOOL,
        "MP4: ISO/IEC 14496-14. Its usual codecs carry patents, but every "
        "browser and OS decodes it, so on balance it is the safest video.",
    ),
    Format(
        (".webm",), "video/webm", "Video", _BROWSER_AND_TOOL,
        "WebM: a Matroska (RFC 9559) profile with royalty-free codecs.",
    ),
    Format(
        (".zip",), "application/zip", "Archives", _TOOL,
        "ZIP: a public spec since 1989 (ISO/IEC 21320-1 for its document "
        "subset); every OS unpacks it.",
    ),
    Format(
        (".gz",), "application/gzip", "Archives", _TOOL,
        "gzip: RFC 1952, decoded by every OS since the 1990s. Compounds such "
        "as .jsonl.gz and .tar.gz qualify through this suffix.",
    ),
    Format(
        (".tgz",), "application/gzip", "Archives", _TOOL,
        "The compact spelling of .tar.gz: a POSIX tar archive, gzipped.",
    ),
)

# Derived views. Never edit these directly; edit FORMATS.
FORMAT_BY_EXTENSION: dict[str, Format] = {
    ext: fmt for fmt in FORMATS for ext in fmt.extensions
}

DURABLE_EXTENSIONS: set[str] = set(FORMAT_BY_EXTENSION)

DURABLE_FORMAT_CATEGORIES: dict[str, list[str]] = {}
for _fmt in FORMATS:
    DURABLE_FORMAT_CATEGORIES.setdefault(_fmt.category, []).extend(_fmt.extensions)
del _fmt

PreviewKind = Literal["image", "audio", "video"]
_PREVIEWABLE: tuple[PreviewKind, ...] = ("image", "audio", "video")


def format_for(path: Path) -> Optional[Format]:
    """The registry entry for a file, by its terminal suffix, or None."""
    return FORMAT_BY_EXTENSION.get(path.suffix.lower())


def preview_kind(path: Path) -> Optional[PreviewKind]:
    """How a browser can show this file inline, if it can.

    Derived from the registry: a format previews when browsers open it and its
    media type is an image, audio, or video type.
    """
    fmt = format_for(path)
    if fmt is None or Reader.BROWSER not in fmt.readers:
        return None
    major = fmt.mimetype.split("/", 1)[0]
    for kind in _PREVIEWABLE:
        if major == kind:
            return kind
    return None


# How much of an unrecognized file reads_as_text looks at.
TEXT_SAMPLE_BYTES: int = 4096


def reads_as_text(path: Path, sample: int = TEXT_SAMPLE_BYTES) -> bool:
    """Whether a text editor would show this file as text: UTF-8 with no NUL.

    This is the text-editor rung of the ladder applied to files whose extension
    the registry does not know (source code, LICENSE, .tex). It reads only the
    first ``sample`` bytes, is used for warnings and site flags, and never
    affects compliance, which stays a matter of presence.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(sample)
    except OSError:
        return False
    if b"\x00" in head:
        return False
    # final=False tolerates a multibyte character cut off at the sample edge.
    try:
        codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
    except UnicodeDecodeError:
        return False
    return True


def sidecar_base(path: Path) -> Optional[tuple[Path, Sidecar]]:
    """If ``path`` is a sidecar of a durable file, return that file and the sidecar."""
    for fmt in FORMATS:
        for sidecar in fmt.sidecars:
            if not path.name.endswith(sidecar.suffix):
                continue
            base = path.with_name(path.name[: -len(sidecar.suffix)])
            if base.suffix.lower() in fmt.extensions:
                return base, sidecar
    return None
