"""ECHO site builder -- generates static HTML sites from ECHO archives."""

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
        return None


def discover_sub_sources(
    path: Path,
    manifest: Optional[Manifest] = None,
) -> list[EchoSource]:
    """Discover sub-sources in an archive directory, sorted by order."""
    sources: list[EchoSource] = []
    seen_paths: set = set()

    if manifest and manifest.sources:
        for source_config in manifest.sources:
            source_path = (path / source_config.path).resolve()
            # Prevent path traversal (absolute or ../ paths escaping archive root)
            if not source_path.is_relative_to(path):
                continue
            if not source_path.exists() or not source_path.is_dir():
                continue

            result = check_compliance(source_path)
            if not result.compliant or not result.source:
                continue

            source = result.source
            if source_config.name:
                source.name = source_config.name
            if source_config.icon:
                source.icon = source_config.icon
            if source_config.order is not None:
                source.order = source_config.order

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
    """Build an HTML page for a single source."""
    output_dir.mkdir(parents=True, exist_ok=True)

    readme_html = ""
    readme_path = find_readme(source.path)
    if readme_path:
        try:
            content = readme_path.read_text(encoding="utf-8")
            readme_html = markdown_to_html(content)
        except (OSError, UnicodeDecodeError):
            pass

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
) -> BuildResult:
    """Build a static site for an ECHO archive."""
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

    manifest = None
    try:
        manifest = load_manifest(path)
    except ValueError as e:
        return BuildResult(success=False, error=str(e))

    assert result.source is not None
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


def _sanitize_html(html: str) -> str:
    """Strip dangerous HTML elements from rendered markdown."""
    import re

    # Remove script, style, iframe, object tags and their contents
    html = re.sub(r"<(script|style|iframe|object)\b[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove self-closing variants
    html = re.sub(r"<(script|style|iframe|object)\b[^>]*/?>", "", html, flags=re.IGNORECASE)
    # Remove on* event handlers from remaining tags
    html = re.sub(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+on\w+\s*=\s*\S+", "", html, flags=re.IGNORECASE)
    return html


def markdown_to_html(content: str) -> str:
    """Convert markdown to sanitized HTML."""
    import markdown

    html = markdown.markdown(content, extensions=["fenced_code", "tables"])
    return _sanitize_html(html)
