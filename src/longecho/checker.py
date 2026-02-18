"""longecho compliance checker."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

DURABLE_EXTENSIONS: set[str] = {
    # Structured data
    ".db", ".sqlite", ".sqlite3", ".json", ".jsonl",
    # Documents
    ".md", ".markdown", ".txt", ".text", ".rst",
    # Archives
    ".zip",
    # Images
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    # Tabular / data
    ".csv", ".tsv", ".xml", ".yaml", ".yml",
}

EXCLUDE_PATTERNS: set[str] = {
    "README.md", "README.txt",
    "CLAUDE.md", "CHANGELOG.md",
    ".gitignore", ".gitattributes",
    "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt",
}

DEFAULT_FORMAT_SCAN_DEPTH: int = 2
MAX_README_SUMMARY_LENGTH: int = 500


@dataclass
class Readme:
    """A README parsed into its constituent parts."""

    frontmatter: Optional[dict]
    body: str
    title: Optional[str]
    summary: Optional[str]


def split_frontmatter(content: str) -> tuple[Optional[dict], str]:
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

    frontmatter, body = split_frontmatter(content)

    title = None
    summary_lines: list[str] = []
    in_paragraph = False

    for line in body.split("\n"):
        stripped = line.strip()

        if stripped.startswith("# ") and title is None:
            title = stripped[2:].strip()
            continue

        if stripped.startswith("#"):
            if summary_lines:
                break
            continue

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
    """A longecho-compliant data source."""

    path: Path
    readme_path: Path
    name: str
    description: str
    formats: list[str] = field(default_factory=list)
    durable_formats: list[str] = field(default_factory=list)
    has_site: bool = False
    site_path: Optional[Path] = None
    frontmatter: Optional[dict] = None
    contents: Optional[list[dict]] = None

    def __str__(self) -> str:
        desc = self.description or "No description"
        if len(desc) > 60:
            desc = desc[:57] + "..."
        return f"{self.path}: {desc}"


@dataclass
class ComplianceResult:
    """Result of a longecho compliance check."""

    compliant: bool
    path: Path
    reason: Optional[str] = None
    source: Optional[EchoSource] = None  # populated when compliant

    def __str__(self) -> str:
        if self.compliant:
            return f"longecho-compliant: {self.path}"
        return f"Not longecho-compliant: {self.path} ({self.reason})"


def find_readme(path: Path) -> Optional[Path]:
    """Find README file at the root of a directory."""
    for name in ["README.md", "README.txt", "readme.md", "readme.txt"]:
        readme = path / name
        if readme.is_file():
            return readme
    return None


def detect_formats(path: Path, max_depth: int = DEFAULT_FORMAT_SCAN_DEPTH) -> list[str]:
    """Detect file formats in a directory up to max_depth."""
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

    formats = detect_formats(path)
    durable = [f for f in formats if is_durable_format(f)]

    if not durable:
        return ComplianceResult(
            compliant=False, path=path, reason="No durable data formats found"
        )

    readme = parse_readme(readme_file)

    # Name cascade: frontmatter name > # Heading > dirname
    name = (readme.title if readme else None) or path.name
    description = (readme.summary if readme else None) or ""
    frontmatter = None
    contents = None

    if readme and readme.frontmatter:
        fm = readme.frontmatter
        frontmatter = fm
        name = fm.get("name", name)
        description = fm.get("description", description)
        contents = _parse_contents(fm)

    site_dir = path / "site"
    has_site = site_dir.exists() and (site_dir / "index.html").exists()
    site_path = site_dir if has_site else None

    source = EchoSource(
        path=path,
        readme_path=readme_file,
        name=name,
        description=description,
        formats=formats,
        durable_formats=durable,
        has_site=has_site,
        site_path=site_path,
        frontmatter=frontmatter,
        contents=contents,
    )

    return ComplianceResult(compliant=True, path=path, source=source)
