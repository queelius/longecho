"""longecho compliance checker."""

import os
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

import yaml

from .formats import (
    DURABLE_EXTENSIONS,
    DURABLE_FORMAT_CATEGORIES,
    is_unrecognized,
    sidecar_base,
)

__all__ = [
    "DURABLE_EXTENSIONS",
    "DURABLE_FORMAT_CATEGORIES",
    "ComplianceResult",
    "ComplianceWarning",
    "EchoSource",
    "Readme",
    "WarningKind",
    "check_compliance",
    "detect_durable_formats",
    "find_readme",
    "find_warnings",
    "is_durable_format",
    "parse_readme",
    "should_skip_directory",
]

# In lookup order: the first one present is the source's README.
README_NAMES: tuple[str, ...] = ("README.md", "README.txt", "readme.md", "readme.txt")

# Files that describe a directory or a code project rather than hold its
# data. They never count toward compliance and are not listed as data.
EXCLUDE_PATTERNS: set[str] = {
    *README_NAMES,
    "CLAUDE.md", "CHANGELOG.md",
    ".gitignore", ".gitattributes",
    "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt",
}

# Directories that never hold a source's own data (dot-prefixed dirs are
# always skipped via the startswith(".") check in should_skip_directory, so
# only non-dot names need to be listed here).
SKIP_DIRECTORIES: set[str] = {
    "node_modules", "__pycache__",
    "venv", "env",
    "dist", "build",
    "site-packages",
}


def should_skip_directory(name: str) -> bool:
    """Check if a directory should be skipped during discovery."""
    return name.startswith(".") or name in SKIP_DIRECTORIES or name.endswith(".egg-info")


DEFAULT_FORMAT_SCAN_DEPTH: int = 2
MAX_README_SUMMARY_LENGTH: int = 500


@dataclass
class Readme:
    """A README parsed into its structured parts."""

    frontmatter: Optional[dict]
    title: Optional[str]
    summary: Optional[str]


def _split_frontmatter(content: str) -> tuple[Optional[dict], str]:
    """Split YAML frontmatter from markdown content.

    Returns (frontmatter dict or None, remaining body).
    """
    if not content.startswith("---"):
        return None, content

    lines = content.split("\n")
    # Find closing ---
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            yaml_content = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            try:
                parsed = yaml.safe_load(yaml_content)
                if isinstance(parsed, dict):
                    return parsed, body
                return None, body
            except yaml.YAMLError:
                return None, body

    # No closing delimiter found
    return None, content


def parse_readme(readme_path: Path) -> Optional[Readme]:
    """Parse a README into frontmatter, title, and summary. Returns None if unreadable."""
    try:
        content = readme_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    import markdown

    frontmatter, body = _split_frontmatter(content)
    outline = _ReadmeOutline()
    outline.feed(markdown.markdown(body, extensions=["fenced_code", "tables"]))
    outline.close()

    summary = outline.summary[:MAX_README_SUMMARY_LENGTH] if outline.summary else None
    return Readme(frontmatter=frontmatter, title=outline.title, summary=summary)


class _ReadmeOutline(HTMLParser):
    """Collect the text of the first h1 and of the first paragraph that has text.

    Working from rendered Markdown means comments, raw HTML blocks, badge-only
    paragraphs, setext headings, and inline markup are all handled by the
    parser rather than by line-by-line guesses.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: Optional[str] = None
        self.summary: Optional[str] = None
        self._open: Optional[str] = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in ("h1", "p") and self._open is None:
            self._open = tag
            self._text = []

    def handle_endtag(self, tag: str) -> None:
        if tag != self._open:
            return
        text = " ".join("".join(self._text).split())
        if text and tag == "h1" and self.title is None:
            self.title = text
        elif text and tag == "p" and self.summary is None:
            self.summary = text
        self._open = None

    def handle_data(self, data: str) -> None:
        if self._open:
            self._text.append(data)


@dataclass
class EchoSource:
    """A longecho-compliant data source."""

    path: Path
    readme_path: Path
    name: str
    description: str
    durable_formats: list[str] = field(default_factory=list)
    has_site: bool = False
    site_path: Optional[Path] = None
    frontmatter: Optional[dict] = None
    contents: Optional[list[dict]] = None
    # Every file this source owns, durable or not, sorted. Files inside nested
    # sources, site/, and skipped directories belong elsewhere.
    files: list[Path] = field(default_factory=list, repr=False)
    # Owned directories below the scan depth, which nothing looked inside.
    unscanned: list[Path] = field(default_factory=list, repr=False)

    @cached_property
    def warnings(self) -> list["ComplianceWarning"]:
        """Computed on first access, so a tree walk that never shows warnings
        never reads file contents."""
        return find_warnings(self.path, self.files, self.unscanned)

    def __str__(self) -> str:
        desc = self.description or "No description"
        if len(desc) > 60:
            desc = desc[:57] + "..."
        return f"{self.path}: {desc}"


class WarningKind(Enum):
    """Why a warning was raised. Warnings never change the compliance verdict."""

    UNRECOGNIZED_FORMAT = "unrecognized-format"
    SIDECAR_AT_RISK = "sidecar-at-risk"
    NOT_INSPECTED = "not-inspected"


@dataclass
class ComplianceWarning:
    """Something a future reader may lose, found while checking a source."""

    kind: WarningKind
    message: str
    paths: list[Path]


@dataclass
class ComplianceResult:
    """Result of a longecho compliance check."""

    compliant: bool
    path: Path
    reason: Optional[str] = None
    source: Optional[EchoSource] = None  # populated when compliant
    # What the walk found, kept so warnings can be computed on a failing result.
    files: list[Path] = field(default_factory=list, repr=False)
    unscanned: list[Path] = field(default_factory=list, repr=False)

    @cached_property
    def warnings(self) -> list[ComplianceWarning]:
        """Warnings for this directory, computed on first access."""
        if self.source is not None:
            return self.source.warnings
        return find_warnings(self.path, self.files, self.unscanned)

    def __str__(self) -> str:
        if self.compliant:
            return f"longecho-compliant: {self.path}"
        return f"Not longecho-compliant: {self.path} ({self.reason})"


def find_readme(path: Path) -> Optional[Path]:
    """Find README file at the root of a directory."""
    for name in README_NAMES:
        readme = path / name
        try:
            if readme.is_file():
                return readme
        except OSError:  # a link into a directory we may not search
            continue
    return None


@dataclass
class _Inventory:
    """What one walk of a directory found."""

    durable: set[str]  # durable suffixes, from this source and nested ones
    owned: list[Path]  # files the source itself owns (see EchoSource.files)
    unscanned: list[Path]  # owned directories below max_depth, not looked into


def _entry_kind(entry: os.DirEntry) -> Optional[str]:
    """'file', 'dir', or None for anything unreadable (broken or looping links)."""
    try:
        if entry.is_file():
            return "file"
        if entry.is_dir():
            return "dir"
    except OSError:
        pass
    return None


def _has_readme(entries: list[os.DirEntry]) -> bool:
    return any(e.name in README_NAMES and _entry_kind(e) == "file" for e in entries)


def _list_dir(path: Path) -> Optional[list[os.DirEntry]]:
    try:
        with os.scandir(path) as it:
            return sorted(it, key=lambda e: e.name)
    except OSError:
        return None


def _worth_reporting(path: Path) -> bool:
    """Whether an unscanned directory may hide data this source owns."""
    entries = _list_dir(path)
    if entries is None:
        return True  # unreadable, so certainly not inspected
    visible = [e for e in entries if not e.name.startswith(".")]
    return bool(visible) and not _has_readme(visible)


def _take_inventory(path: Path, max_depth: int = DEFAULT_FORMAT_SCAN_DEPTH) -> _Inventory:
    """Walk ``path`` once, collecting durable suffixes and the source's own files.

    Durable suffixes count from nested sources too, so an archive whose data
    lives entirely in sub-sources is compliant. ``site/`` and tool directories
    (``SKIP_DIRECTORIES``) are not entered at all: a viewer or a dependency
    folder is not the data. Ownership stops at nested sources. ``os.scandir``
    supplies each entry's type without a separate stat, which keeps
    ``query ~`` fast, and entries whose type cannot be read are skipped.
    """
    inventory = _Inventory(durable=set(), owned=[], unscanned=[])

    def scan(dir_path: Path, depth: int, owned: bool) -> None:
        entries = _list_dir(dir_path)
        if entries is None:
            return
        if depth > 0 and _has_readme(entries):
            owned = False  # a nested source owns what is under it
        for entry in entries:
            if entry.name.startswith("."):
                continue
            kind = _entry_kind(entry)
            if kind == "file":
                if entry.name in EXCLUDE_PATTERNS:
                    continue
                suffix = os.path.splitext(entry.name)[1].lower()
                if suffix in DURABLE_EXTENSIONS:
                    inventory.durable.add(suffix)
                if owned:
                    inventory.owned.append(dir_path / entry.name)
            elif kind == "dir":
                if entry.name == "site" or should_skip_directory(entry.name):
                    continue
                child = dir_path / entry.name
                if depth + 1 <= max_depth:
                    scan(child, depth + 1, owned)
                elif owned and _worth_reporting(child):
                    inventory.unscanned.append(child)

    scan(path, 0, owned=True)
    return inventory


def detect_durable_formats(path: Path, max_depth: int = DEFAULT_FORMAT_SCAN_DEPTH) -> list[str]:
    """Detect durable file formats in a directory up to max_depth."""
    return sorted(_take_inventory(path, max_depth).durable)


def _nonempty(path: Path) -> bool:
    try:
        return path.stat().st_size > 0
    except OSError:  # a live database can remove its sidecar mid-walk
        return False


def find_warnings(
    root: Path, files: list[Path], unscanned: Sequence[Path] = ()
) -> list[ComplianceWarning]:
    """Warn about owned files a future reader may be unable to open or may lose.

    A file outside the format list is only a problem when it is not UTF-8
    text either: a text editor opens a .py or a LICENSE as well as a .txt.
    """
    warnings: list[ComplianceWarning] = []
    unrecognized: dict[str, list[Path]] = defaultdict(list)

    for f in files:
        paired = sidecar_base(f)
        if paired is not None:
            base, sidecar = paired
            risk = sidecar.describe_risk(base.relative_to(root).as_posix())
            if risk and _nonempty(f):
                warnings.append(ComplianceWarning(
                    kind=WarningKind.SIDECAR_AT_RISK,
                    message=f"{f.relative_to(root).as_posix()} {risk}",
                    paths=[f],
                ))
        elif is_unrecognized(f):
            unrecognized[f.suffix.lower()].append(f)

    for suffix in sorted(unrecognized):
        paths = unrecognized[suffix]
        where = f"in {suffix}" if suffix else "with no extension"
        warnings.append(ComplianceWarning(
            kind=WarningKind.UNRECOGNIZED_FORMAT,
            message=f"{_count(len(paths), 'file')} {where}: "
                    "not in a durable format, and not UTF-8 text",
            paths=paths,
        ))

    if unscanned:
        warnings.append(ComplianceWarning(
            kind=WarningKind.NOT_INSPECTED,
            message=f"{_count(len(unscanned), 'directory', 'directories')} more than "
                    f"{DEFAULT_FORMAT_SCAN_DEPTH} levels down not inspected: their files "
                    "are not checked or listed (give them a README to make them sources)",
            paths=list(unscanned),
        ))
    return warnings


def _count(n: int, singular: str, plural: Optional[str] = None) -> str:
    return f"{n} {singular if n == 1 else (plural or singular + 's')}"


def is_durable_format(extension: str) -> bool:
    """Check if a file extension is a durable format (with or without leading dot)."""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = "." + ext
    return ext in DURABLE_EXTENSIONS


def _parse_contents(frontmatter: dict) -> Optional[list[dict]]:
    """Parse the contents field from frontmatter into normalized dicts."""
    raw = frontmatter.get("contents")
    if not isinstance(raw, list):
        return None

    entries = []
    for item in raw:
        if isinstance(item, dict) and "path" in item:
            entries.append(item)
    return entries if entries else None


def check_compliance(path: Path) -> ComplianceResult:
    """Check if a directory is longecho-compliant (has README + durable formats)."""
    path = Path(path).resolve()

    if not path.exists():
        return ComplianceResult(compliant=False, path=path, reason="Path does not exist")
    if not path.is_dir():
        return ComplianceResult(compliant=False, path=path, reason="Path is not a directory")

    readme_file = find_readme(path)
    if not readme_file:
        return ComplianceResult(
            compliant=False, path=path, reason="No README.md or README.txt found"
        )

    inventory = _take_inventory(path)
    durable = sorted(inventory.durable)

    if not durable:
        return ComplianceResult(
            compliant=False,
            path=path,
            reason="No durable data formats found",
            files=inventory.owned,
            unscanned=inventory.unscanned,
        )

    readme = parse_readme(readme_file)

    # Name cascade: frontmatter name > # Heading > dirname
    name = (readme.title if readme else None) or path.name
    description = (readme.summary if readme else None) or ""
    frontmatter = readme.frontmatter if readme else None
    contents = None

    if frontmatter:
        name = frontmatter.get("name", name)
        description = frontmatter.get("description", description)
        contents = _parse_contents(frontmatter)

    site_dir = path / "site"
    has_site = site_dir.exists() and (site_dir / "index.html").exists()
    site_path = site_dir if has_site else None

    source = EchoSource(
        path=path,
        readme_path=readme_file,
        name=name,
        description=description,
        durable_formats=durable,
        has_site=has_site,
        site_path=site_path,
        frontmatter=frontmatter,
        contents=contents,
        files=inventory.owned,
        unscanned=inventory.unscanned,
    )

    return ComplianceResult(
        compliant=True,
        path=path,
        source=source,
        files=inventory.owned,
        unscanned=inventory.unscanned,
    )
