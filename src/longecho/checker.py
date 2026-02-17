"""
ECHO compliance checker.

This module provides functionality to check if a directory is ECHO-compliant.
A directory is ECHO-compliant if it meets two criteria:

1. Has a README.md or README.txt at the root explaining the data
2. Contains data in durable formats (SQLite, JSON, Markdown, etc.)

The primary function is `check_compliance()` which returns a `ComplianceResult`
with detailed information about the compliance status.

Example:
    >>> from longecho.checker import check_compliance
    >>> result = check_compliance("/path/to/archive")
    >>> if result.compliant:
    ...     print(f"Compliant! Formats: {result.source.durable_formats}")
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# Durable formats recognized by ECHO
DURABLE_EXTENSIONS: set[str] = {
    # Structured data
    ".db", ".sqlite", ".sqlite3",  # SQLite
    ".json", ".jsonl",              # JSON
    # Documents
    ".md", ".markdown",             # Markdown
    ".txt", ".text",                # Plain text
    ".rst",                         # reStructuredText
    # Archives
    ".zip",                         # ZIP
    # Images (for photos/media archives)
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    # Data
    ".csv", ".tsv",                 # Tabular data
    ".xml",                         # XML
    ".yaml", ".yml",                # YAML
}

# Patterns to exclude from format detection
EXCLUDE_PATTERNS: set[str] = {
    "README.md", "README.txt",      # Don't count README as "data"
    "CLAUDE.md", "CHANGELOG.md",    # Meta files
    ".gitignore", ".gitattributes",
    "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt",
}

# Configuration constants
DEFAULT_FORMAT_SCAN_DEPTH: int = 2  # Max depth for format detection
MAX_README_SUMMARY_LENGTH: int = 500  # Max characters for README summary


@dataclass
class Readme:
    """A README parsed into its constituent parts."""

    frontmatter: Optional[dict]
    body: str
    title: Optional[str]
    summary: Optional[str]


def split_frontmatter(content: str) -> tuple[Optional[dict], str]:
    """Split YAML frontmatter from markdown content.

    Frontmatter must start at the very beginning of the content,
    delimited by --- lines.

    Returns:
        (frontmatter dict or None, remaining content)
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
    """Parse a README into frontmatter, title, and summary.

    Returns None if the file can't be read.
    """
    try:
        content = readme_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    frontmatter, body = split_frontmatter(content)

    title = None
    summary_lines: list[str] = []
    in_paragraph = False

    for line in body.split("\n"):
        stripped = line.strip()

        # Extract first # heading as title
        if stripped.startswith("# ") and title is None:
            title = stripped[2:].strip()
            continue

        # Skip other headings
        if stripped.startswith("#"):
            if summary_lines:
                break  # hit next section, stop collecting
            continue

        # Empty line ends paragraph
        if not stripped:
            if in_paragraph:
                break
            continue

        in_paragraph = True
        summary_lines.append(stripped)

    summary = " ".join(summary_lines)[:MAX_README_SUMMARY_LENGTH] if summary_lines else None
    return Readme(frontmatter=frontmatter, body=body, title=title, summary=summary)


@dataclass
class EchoSource:
    """An ECHO-compliant data source."""

    path: Path
    readme_path: Path
    name: str
    description: str
    formats: list[str] = field(default_factory=list)
    durable_formats: list[str] = field(default_factory=list)
    icon: Optional[str] = None
    order: int = 0
    has_site: bool = False
    site_path: Optional[Path] = None

    def __str__(self) -> str:
        desc = self.description or "No description"
        if len(desc) > 60:
            desc = desc[:57] + "..."
        return f"{self.path}: {desc}"


@dataclass
class ComplianceResult:
    """Result of an ECHO compliance check."""

    compliant: bool
    path: Path
    reason: Optional[str] = None
    source: Optional[EchoSource] = None  # populated when compliant

    def __str__(self) -> str:
        if self.compliant:
            return f"ECHO-compliant: {self.path}"
        return f"Not ECHO-compliant: {self.path} ({self.reason})"


def find_readme(path: Path) -> Optional[Path]:
    """
    Find README file at the root of a directory.

    Args:
        path: Directory to check

    Returns:
        Path to README if found, None otherwise
    """
    for name in ["README.md", "README.txt", "readme.md", "readme.txt"]:
        readme = path / name
        if readme.is_file():
            return readme
    return None


def detect_formats(path: Path, max_depth: int = DEFAULT_FORMAT_SCAN_DEPTH) -> list[str]:
    """
    Detect file formats in a directory.

    Args:
        path: Directory to scan
        max_depth: Maximum directory depth to scan

    Returns:
        List of file extensions found
    """
    formats = set()

    def scan_directory(dir_path: Path, depth: int):
        if depth > max_depth:
            return

        try:
            for item in dir_path.iterdir():
                if item.name.startswith("."):
                    continue

                if item.is_file():
                    if item.name not in EXCLUDE_PATTERNS:
                        suffix = item.suffix.lower()
                        if suffix:
                            formats.add(suffix)
                elif item.is_dir():
                    scan_directory(item, depth + 1)
        except PermissionError:
            pass

    scan_directory(path, 0)
    return sorted(formats)


def is_durable_format(extension: str) -> bool:
    """
    Check if a file extension is a durable format.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        True if the format is durable
    """
    ext = extension.lower()
    if not ext.startswith("."):
        ext = "." + ext
    return ext in DURABLE_EXTENSIONS


def check_compliance(path: Path) -> ComplianceResult:
    """Check if a directory is ECHO-compliant.

    A directory is ECHO-compliant if it has:
    1. A README.md or README.txt at the root
    2. Data in durable formats

    Args:
        path: Directory to check

    Returns:
        ComplianceResult with compliance status and details
    """
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

    formats = detect_formats(path)
    durable = [f for f in formats if is_durable_format(f)]

    if not durable:
        return ComplianceResult(
            compliant=False, path=path, reason="No durable data formats found"
        )

    # Parse README for name/description
    readme = parse_readme(readme_file)
    name = (readme.title if readme else None) or path.name
    description = (readme.summary if readme else None) or ""

    # Check for frontmatter overrides
    if readme and readme.frontmatter:
        fm = readme.frontmatter
        name = fm.get("title", name)
        description = fm.get("description", description)

    # Check for site/
    has_site = False
    site_path = None
    site_dir = path / "site"
    if site_dir.exists() and (site_dir / "index.html").exists():
        has_site = True
        site_path = site_dir

    source = EchoSource(
        path=path,
        readme_path=readme_file,
        name=name,
        description=description,
        formats=formats,
        durable_formats=durable,
        icon=readme.frontmatter.get("icon") if readme and readme.frontmatter else None,
        has_site=has_site,
        site_path=site_path,
    )

    return ComplianceResult(compliant=True, path=path, source=source)
