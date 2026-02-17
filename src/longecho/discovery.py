"""
ECHO source discovery.

This module provides functionality to discover and search ECHO-compliant
directories under a root path. It recursively scans directories looking
for README files and checks each for ECHO compliance.

Key functions:
- `discover_sources()`: Find all ECHO sources under a path
- `search_sources()`: Find sources matching a search query
- `get_source_info()`: Get detailed info about a specific source

Example:
    >>> from longecho.discovery import discover_sources
    >>> for source in discover_sources("~/"):
    ...     print(f"{source.path}: {source.description}")
"""

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
    """
    Check if a directory should be skipped during discovery.

    Args:
        name: Directory name

    Returns:
        True if directory should be skipped
    """
    if name.startswith("."):
        return True
    if name in SKIP_DIRECTORIES:
        return True
    return bool(name.endswith(".egg-info"))


def discover_sources(
    root: Path,
    max_depth: Optional[int] = None,
    follow_symlinks: bool = False
) -> Iterator[EchoSource]:
    """
    Find all ECHO-compliant directories under a root path.

    Scans for README.md files and checks each containing directory
    for ECHO compliance.

    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth (None for unlimited)
        follow_symlinks: Whether to follow symbolic links

    Yields:
        EchoSource for each compliant directory found
    """
    root = Path(root).resolve()

    if not root.exists() or not root.is_dir():
        return

    def scan_directory(path: Path, depth: int):
        if max_depth is not None and depth > max_depth:
            return

        try:
            # Check if this directory has a README
            readme = find_readme(path)
            if readme:
                result = check_compliance(path)
                if result.compliant and result.source:
                    yield result.source

            # Recurse into subdirectories
            for item in sorted(path.iterdir()):
                # Check if item is a directory
                # For Python 3.8 compatibility, we handle symlinks separately
                is_directory = item.is_dir()
                if is_directory and not follow_symlinks and item.is_symlink():
                    continue
                if is_directory:
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
    """
    Search ECHO sources by README content.

    Finds ECHO-compliant directories whose README contains
    the query string (case-insensitive).

    Args:
        root: Root directory to scan
        query: Search string
        max_depth: Maximum directory depth

    Yields:
        EchoSource for each matching directory
    """
    query_lower = query.lower()

    for source in discover_sources(root, max_depth):
        # Check description
        if source.description and query_lower in source.description.lower():
            yield source
            continue

        # Check full README content
        try:
            content = source.readme_path.read_text(encoding="utf-8")
            if query_lower in content.lower():
                yield source
        except (OSError, UnicodeDecodeError):
            # OSError: file system errors (e.g., file disappeared)
            # UnicodeDecodeError: invalid UTF-8 encoding
            pass


def get_source_info(path: Path) -> Optional[EchoSource]:
    """
    Get detailed information about an ECHO source.

    Args:
        path: Path to check

    Returns:
        EchoSource if compliant, None otherwise
    """
    result = check_compliance(path)
    if not result.compliant:
        return None
    return result.source
