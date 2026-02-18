"""longecho source discovery -- find and search longecho-compliant directories."""

from collections.abc import Iterator
from pathlib import Path
from typing import Optional

from .checker import EchoSource, check_compliance, find_readme

# Directories to skip during discovery
SKIP_DIRECTORIES = {
    ".git", ".hg", ".svn",
    "node_modules", "__pycache__", ".pytest_cache",
    ".venv", "venv", ".env", "env",
    ".tox", ".nox",
    "dist", "build", "*.egg-info",
    ".mypy_cache", ".ruff_cache",
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
            readme = find_readme(path)
            if readme:
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


def search_sources(
    root: Path,
    query: str,
    max_depth: Optional[int] = None
) -> Iterator[EchoSource]:
    """Search longecho sources by README content (case-insensitive)."""
    query_lower = query.lower()

    for source in discover_sources(root, max_depth):
        if source.description and query_lower in source.description.lower():
            yield source
            continue

        try:
            content = source.readme_path.read_text(encoding="utf-8")
            if query_lower in content.lower():
                yield source
        except (OSError, UnicodeDecodeError):
            pass


def get_source_info(path: Path) -> Optional[EchoSource]:
    """Get detailed information about an longecho source, or None if not compliant."""
    result = check_compliance(path)
    return result.source if result.compliant else None
