"""longecho source discovery -- find and search longecho-compliant directories."""

from collections.abc import Iterator
from pathlib import Path
from typing import Optional

from .checker import EchoSource, check_compliance

# Directories to skip during discovery (dot-prefixed dirs are always skipped
# via the startswith(".") check in should_skip_directory, so only non-dot
# names need to be listed here).
SKIP_DIRECTORIES: set[str] = {
    "node_modules", "__pycache__",
    "venv", "env",
    "dist", "build",
    "site-packages",
}


def should_skip_directory(name: str) -> bool:
    """Check if a directory should be skipped during discovery."""
    return name.startswith(".") or name in SKIP_DIRECTORIES or name.endswith(".egg-info")


def discover_sources(
    root: Path,
    max_depth: Optional[int] = None,
    follow_symlinks: bool = False
) -> Iterator[EchoSource]:
    """Find all longecho-compliant directories under a root path."""
    root = Path(root).resolve()

    if not root.exists() or not root.is_dir():
        return

    def scan_directory(path: Path, depth: int):
        if max_depth is not None and depth > max_depth:
            return

        try:
            result = check_compliance(path)
            if result.compliant and result.source:
                yield result.source

            for item in sorted(path.iterdir()):
                if not item.is_dir():
                    continue
                if not follow_symlinks and item.is_symlink():
                    continue
                if not should_skip_directory(item.name):
                    yield from scan_directory(item, depth + 1)
        except PermissionError:
            pass

    yield from scan_directory(root, 0)


def _build_search_text(source: EchoSource) -> str:
    """Build a searchable text blob from a source (name, description, README, frontmatter)."""
    parts = [source.name, source.description]
    try:
        content = source.readme_path.read_text(encoding="utf-8")
        parts.append(content)
    except (OSError, UnicodeDecodeError):
        pass
    if source.frontmatter:
        for v in source.frontmatter.values():
            parts.append(str(v))
    return " ".join(parts).lower()


def matches_query(source: EchoSource, query: str) -> bool:
    """Check if a source matches a text query. Case-insensitive substring match."""
    if not query.strip():
        return True
    search_text = _build_search_text(source)
    return query.strip().lower() in search_text


def search_sources(
    root: Path,
    query: str,
    max_depth: Optional[int] = None
) -> Iterator[EchoSource]:
    """Search sources by text. Case-insensitive match against name, description, README, frontmatter."""
    for source in discover_sources(root, max_depth):
        if matches_query(source, query):
            yield source


def get_source_info(path: Path) -> Optional[EchoSource]:
    """Get detailed information about a longecho source, or None if not compliant."""
    result = check_compliance(path)
    return result.source if result.compliant else None
