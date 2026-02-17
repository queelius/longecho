"""
ECHO site builder.

This module generates static HTML sites from ECHO-compliant archives.
It discovers sub-sources (via manifest or auto-discovery), generates
navigation pages, and creates a unified browsable interface.

The primary function is `build_site()` which returns a `BuildResult`
with the output path and statistics.

Example:
    >>> from longecho.build import build_site
    >>> result = build_site("/path/to/archive")
    >>> if result.success:
    ...     print(f"Built site at {result.output_path}")
    ...     print(f"Found {result.sources_count} sources")
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from .checker import EchoSource, check_compliance, find_readme
from .manifest import Manifest, load_manifest


@dataclass
class BuildResult:
    """Result of a site build operation."""

    success: bool
    output_path: Optional[Path] = None
    sources_count: int = 0
    error: Optional[str] = None


def get_jinja_env() -> Environment:
    """Create Jinja2 environment with templates."""
    return Environment(
        loader=PackageLoader("longecho", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _load_sub_manifest(source_path: Path) -> Optional[Manifest]:
    """Load manifest from a source path, returning None on error."""
    try:
        return load_manifest(source_path)
    except (ValueError, OSError, UnicodeDecodeError):
        # ValueError: invalid manifest format/content
        # OSError: file system errors
        # UnicodeDecodeError: invalid UTF-8
        return None


def discover_sub_sources(
    path: Path,
    manifest: Optional[Manifest] = None,
) -> list[EchoSource]:
    """
    Discover sub-sources in an archive directory.

    Args:
        path: Archive root path
        manifest: Optional manifest with source configuration

    Returns:
        List of EchoSource objects sorted by order
    """
    sources: list[EchoSource] = []
    seen_paths: set = set()

    # If manifest specifies sources, use those first
    if manifest and manifest.sources:
        for source_config in manifest.sources:
            source_path = path / source_config.path
            if not source_path.exists() or not source_path.is_dir():
                continue

            result = check_compliance(source_path)
            if not result.compliant or not result.source:
                continue

            source = result.source
            # Apply manifest overrides
            if source_config.name:
                source.name = source_config.name
            if source_config.icon:
                source.icon = source_config.icon
            if source_config.order is not None:
                source.order = source_config.order

            # Also check sub-manifest for overrides
            sub_manifest = _load_sub_manifest(source_path)
            if sub_manifest:
                if not source_config.name and sub_manifest.name:
                    source.name = sub_manifest.name
                if not source_config.icon and sub_manifest.icon:
                    source.icon = sub_manifest.icon
                if sub_manifest.description:
                    source.description = sub_manifest.description

            sources.append(source)
            seen_paths.add(source_path)

    # Auto-discover additional sources
    for item in sorted(path.iterdir()):
        if not item.is_dir() or item.name.startswith(".") or item.name == "site" or item in seen_paths:
            continue

        result = check_compliance(item)
        if not result.compliant or not result.source:
            continue

        source = result.source
        sub_manifest = _load_sub_manifest(item)
        if sub_manifest:
            if sub_manifest.name:
                source.name = sub_manifest.name
            if sub_manifest.description:
                source.description = sub_manifest.description
            if sub_manifest.icon:
                source.icon = sub_manifest.icon
        source.order = 100  # default for auto-discovered

        sources.append(source)

    sources.sort(key=lambda s: s.order)
    return sources


def build_source_page(
    env: Environment,
    source: EchoSource,
    parent_name: str,
    output_dir: Path,
    bundle: bool = False,
) -> None:
    """
    Build a page for a single source.

    Args:
        env: Jinja2 environment
        source: EchoSource object
        parent_name: Parent archive name
        output_dir: Output directory for this source
        bundle: Whether to copy site contents
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read README content
    readme_html = ""
    readme_path = find_readme(source.path)
    if readme_path:
        try:
            content = readme_path.read_text(encoding="utf-8")
            readme_html = markdown_to_html(content)
        except (OSError, UnicodeDecodeError):
            pass

    # Determine site URL
    site_url = None
    if source.has_site:
        if bundle and source.site_path:
            dest_site = output_dir / "site"
            if source.site_path.exists():
                shutil.copytree(source.site_path, dest_site, dirs_exist_ok=True)
            site_url = "site/index.html"
        elif source.site_path:
            site_url = str(source.site_path / "index.html")

    template = env.get_template("source.html")
    html = template.render(
        name=source.name,
        description=source.description,
        parent_name=parent_name,
        icon=source.icon,
        durable_formats=source.durable_formats,
        path=str(source.path),
        readme_html=readme_html,
        has_site=source.has_site,
        site_url=site_url,
        files=[],
    )

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")


def build_site(
    path: Path,
    output: Optional[Path] = None,
    bundle: bool = False,
    offline: bool = True,
) -> BuildResult:
    """
    Build a static site for an ECHO archive.

    Args:
        path: Path to the archive
        output: Output directory (default: path/site/)
        bundle: Copy all sub-sites into unified site
        offline: Bundle all CSS/JS/fonts (default: true)

    Returns:
        BuildResult with success status and details
    """
    path = Path(path).resolve()

    if not path.exists():
        return BuildResult(success=False, error=f"Path does not exist: {path}")

    if not path.is_dir():
        return BuildResult(success=False, error=f"Path is not a directory: {path}")

    result = check_compliance(path)
    if not result.compliant:
        return BuildResult(
            success=False,
            error=f"Not an ECHO archive: {result.reason}"
        )

    # Load manifest if present
    manifest = None
    try:
        manifest = load_manifest(path)
    except ValueError as e:
        return BuildResult(success=False, error=str(e))

    # Determine archive name and description
    # Cascade: manifest > EchoSource (which already has frontmatter > heading > dirname)
    assert result.source is not None  # guaranteed by compliant check above
    name = (manifest.name if manifest else None) or result.source.name
    description = (manifest.description if manifest else None) or result.source.description

    sources = discover_sub_sources(path, manifest)

    output_path = Path(output).resolve() if output else path / "site"
    output_path.mkdir(parents=True, exist_ok=True)

    env = get_jinja_env()

    for source in sources:
        source_output = output_path / source.path.name
        build_source_page(env, source, name, source_output, bundle)

    template = env.get_template("index.html")
    html = template.render(
        name=name,
        description=description,
        sources=[{
            "name": s.name,
            "description": s.description,
            "url": f"{s.path.name}/index.html",
            "icon": s.icon,
            "durable_formats": s.durable_formats,
        } for s in sources],
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    index_path = output_path / "index.html"
    index_path.write_text(html, encoding="utf-8")

    return BuildResult(
        success=True,
        output_path=output_path,
        sources_count=len(sources),
    )


def markdown_to_html(content: str) -> str:
    """
    Convert markdown to HTML using the markdown library.

    Args:
        content: Markdown content

    Returns:
        HTML content with fenced code blocks and tables supported
    """
    import markdown

    result: str = markdown.markdown(content, extensions=["fenced_code", "tables"])
    return result
