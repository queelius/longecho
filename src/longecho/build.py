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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from .checker import ComplianceResult, check_compliance, find_readme
from .manifest import Manifest, load_manifest

# Icon mapping from identifiers to emoji
ICON_EMOJI_MAP = {
    "chat": "\U0001F4AC",      # speech balloon
    "bookmark": "\U0001F516",  # bookmark
    "document": "\U0001F4C4",  # page facing up
    "database": "\U0001F5C3",  # card file box
    "image": "\U0001F5BC",     # framed picture
    "music": "\U0001F3B5",     # musical note
    "video": "\U0001F3AC",     # clapper board
    "code": "\U0001F4BB",      # laptop
    "archive": "\U0001F4E6",   # package
    "default": "\U0001F4C1",   # folder
}


@dataclass
class SourceInfo:
    """Information about a source for template rendering."""

    name: str
    description: str
    path: Path
    url: str
    icon: Optional[str] = None
    icon_emoji: str = ICON_EMOJI_MAP["default"]
    type: Optional[str] = None
    formats: list[str] = field(default_factory=list)
    order: int = 0
    has_site: bool = False
    site_path: Optional[Path] = None


@dataclass
class BuildResult:
    """Result of a site build operation."""

    success: bool
    output_path: Optional[Path] = None
    sources_count: int = 0
    error: Optional[str] = None


def get_icon_emoji(icon: Optional[str]) -> str:
    """Get emoji for an icon identifier."""
    if icon and icon in ICON_EMOJI_MAP:
        return ICON_EMOJI_MAP[icon]
    return ICON_EMOJI_MAP["default"]


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


def _get_site_info(source_path: Path) -> tuple[bool, Optional[Path]]:
    """Check for existing site and return (has_site, site_path)."""
    site_dir = source_path / "site"
    if site_dir.exists() and (site_dir / "index.html").exists():
        return True, site_dir
    return False, None


def _build_source_info(
    source_path: Path,
    compliance_result: "ComplianceResult",
    sub_manifest: Optional[Manifest],
    name: str,
    order: int,
) -> SourceInfo:
    """
    Build SourceInfo from a path and its compliance result.

    Args:
        source_path: Path to the source directory
        compliance_result: Result from check_compliance()
        sub_manifest: Optional manifest loaded from the source
        name: Display name for the source
        order: Sort order for the source

    Returns:
        SourceInfo ready for template rendering
    """
    # Determine description from manifest or README
    description = ""
    if sub_manifest:
        description = sub_manifest.description
    elif compliance_result.readme_summary:
        description = compliance_result.readme_summary

    # Extract icon and type from manifest
    icon = sub_manifest.icon if sub_manifest else None
    source_type = sub_manifest.type if sub_manifest else None

    # Check for existing site
    has_site, site_path = _get_site_info(source_path)

    return SourceInfo(
        name=name,
        description=description,
        path=source_path,
        url=f"{source_path.name}/index.html",
        icon=icon,
        icon_emoji=get_icon_emoji(icon),
        type=source_type,
        formats=compliance_result.durable_formats,
        order=order,
        has_site=has_site,
        site_path=site_path,
    )


def discover_sub_sources(
    path: Path,
    manifest: Optional[Manifest] = None,
    deep: bool = False,
) -> list[SourceInfo]:
    """
    Discover sub-sources in an archive directory.

    Args:
        path: Archive root path
        manifest: Optional manifest with source configuration
        deep: Enable aggressive discovery

    Returns:
        List of source information
    """
    sources: list[SourceInfo] = []
    seen_paths: set = set()

    # If manifest specifies sources, use those first
    if manifest and manifest.sources:
        for source_config in manifest.sources:
            source_path = path / source_config.path
            if not source_path.exists() or not source_path.is_dir():
                continue

            # Check if this is an ECHO source
            result = check_compliance(source_path)
            if not result.compliant:
                continue

            sub_manifest = _load_sub_manifest(source_path)

            # Resolve name: config > manifest > directory name
            name = source_config.name
            if not name and sub_manifest:
                name = sub_manifest.name
            if not name:
                name = source_path.name

            sources.append(_build_source_info(
                source_path, result, sub_manifest, name, source_config.order or 0
            ))
            seen_paths.add(source_path)

    # Auto-discover additional sources
    for item in sorted(path.iterdir()):
        if not item.is_dir():
            continue
        if item.name.startswith("."):
            continue
        if item.name == "site":
            continue
        if item in seen_paths:
            continue

        # Check if this is an ECHO source
        result = check_compliance(item)
        if not result.compliant:
            continue

        sub_manifest = _load_sub_manifest(item)

        # Skip if not browsable
        if sub_manifest and not sub_manifest.browsable:
            continue

        # Resolve name and order from manifest or use defaults
        name = sub_manifest.name if sub_manifest else item.name
        order = sub_manifest.order if sub_manifest and sub_manifest.order is not None else 100

        sources.append(_build_source_info(item, result, sub_manifest, name, order))

    # Sort by order (None values sort last)
    sources.sort(key=lambda s: (s.order is None, s.order or 0))

    return sources


def build_source_page(
    env: Environment,
    source: SourceInfo,
    parent_name: str,
    output_dir: Path,
    bundle: bool = False,
) -> None:
    """
    Build a page for a single source.

    Args:
        env: Jinja2 environment
        source: Source information
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
            # Convert markdown to HTML (basic conversion)
            content = readme_path.read_text(encoding="utf-8")
            readme_html = markdown_to_html(content)
        except (OSError, UnicodeDecodeError):
            # OSError: file system errors (e.g., file disappeared)
            # UnicodeDecodeError: invalid UTF-8 encoding
            pass

    # Determine site URL
    site_url = None
    if source.has_site:
        if bundle and source.site_path:
            # Copy site contents
            dest_site = output_dir / "site"
            if source.site_path.exists():
                shutil.copytree(source.site_path, dest_site, dirs_exist_ok=True)
            site_url = "site/index.html"
        elif source.site_path:
            # Link to existing site
            site_url = str(source.site_path / "index.html")

    # Render source page
    template = env.get_template("source.html")
    html = template.render(
        name=source.name,
        description=source.description,
        parent_name=parent_name,
        icon_emoji=source.icon_emoji,
        type=source.type,
        formats=source.formats,
        path=str(source.path),
        readme_html=readme_html,
        has_site=source.has_site,
        site_url=site_url,
        files=[],  # Could list data files here
    )

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")


def build_site(
    path: Path,
    output: Optional[Path] = None,
    bundle: bool = False,
    deep: bool = False,
    offline: bool = True,
) -> BuildResult:
    """
    Build a static site for an ECHO archive.

    Args:
        path: Path to the archive
        output: Output directory (default: path/site/)
        bundle: Copy all sub-sites into unified site
        deep: Aggressive discovery mode
        offline: Bundle all CSS/JS/fonts (default: true)

    Returns:
        BuildResult with success status and details
    """
    path = Path(path).resolve()

    if not path.exists():
        return BuildResult(success=False, error=f"Path does not exist: {path}")

    if not path.is_dir():
        return BuildResult(success=False, error=f"Path is not a directory: {path}")

    # Check basic compliance
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
    if manifest:
        name = manifest.name
        description = manifest.description
    else:
        name = path.name
        description = result.readme_summary or ""

    # Discover sub-sources
    sources = discover_sub_sources(path, manifest, deep)

    # Set output directory
    output_path = Path(output).resolve() if output else path / "site"

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Get Jinja environment
    env = get_jinja_env()

    # Build source pages
    for source in sources:
        source_output = output_path / source.path.name
        build_source_page(env, source, name, source_output, bundle)

    # Build index page
    template = env.get_template("index.html")
    html = template.render(
        name=name,
        description=description,
        sources=[{
            "name": s.name,
            "description": s.description,
            "url": s.url,
            "icon_emoji": s.icon_emoji,
            "type": s.type,
            "formats": s.formats,
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
