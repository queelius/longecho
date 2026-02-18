"""longecho site builder -- generates a single-file application from a longecho archive."""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from . import __version__
from .checker import EchoSource, check_compliance, find_readme
from .discovery import should_skip_directory


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


def _sanitize_html(html: str) -> str:
    """Strip dangerous HTML elements from rendered markdown."""
    # Remove dangerous tags with content
    html = re.sub(
        r"<(script|style|iframe|object|embed)\b[^>]*>.*?</\1>",
        "", html, flags=re.DOTALL | re.IGNORECASE,
    )
    # Remove self-closing dangerous tags
    html = re.sub(
        r"<(script|style|iframe|object|embed|base|meta|link)\b[^>]*/?>",
        "", html, flags=re.IGNORECASE,
    )
    # Remove opening-only dangerous tags (base, meta, link are void elements)
    html = re.sub(
        r"<(base|meta|link)\b[^>]*>",
        "", html, flags=re.IGNORECASE,
    )
    # Remove form tags
    html = re.sub(r"</?form\b[^>]*>", "", html, flags=re.IGNORECASE)
    # Remove on* event handlers (quoted)
    html = re.sub(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
    # Remove on* event handlers (unquoted, stop at > or whitespace)
    html = re.sub(r"\s+on\w+\s*=\s*[^\s>]+", "", html, flags=re.IGNORECASE)
    # Remove javascript: URIs in href/src/action attributes
    html = re.sub(
        r'(href|src|action)\s*=\s*["\']?\s*javascript:[^"\'>\s]*["\']?',
        "", html, flags=re.IGNORECASE,
    )
    return html


def markdown_to_html(content: str) -> str:
    """Convert markdown to sanitized HTML."""
    import markdown

    html: str = markdown.markdown(content, extensions=["fenced_code", "tables"])
    return _sanitize_html(html)


def _get_data_files(source: EchoSource, output_path: Path) -> list[dict]:
    """Get data files in a source directory, with relative paths from output_path."""
    files = []
    for fmt in source.durable_formats:
        for f in source.path.glob(f"*{fmt}"):
            if f.is_file():
                try:
                    rel = Path(f.relative_to(output_path.parent))
                except ValueError:
                    # output_path is outside the archive — use absolute file:// URI
                    rel = Path(f.as_uri()) if hasattr(f, "as_uri") else f
                files.append({"name": f.name, "path": str(rel)})
    return sorted(files, key=lambda x: x["name"])


def discover_sub_sources(source: EchoSource) -> list[EchoSource]:
    """Discover sub-sources using contents field or auto-discovery."""
    path = source.path
    sources: list[EchoSource] = []

    if source.contents:
        # Curated: only listed paths, in order
        for entry in source.contents:
            entry_path = entry.get("path", "")
            sub_path = (path / entry_path).resolve()
            # Prevent path traversal
            if not sub_path.is_relative_to(path):
                continue
            if not sub_path.is_dir():
                continue

            result = check_compliance(sub_path)
            if result.compliant and result.source:
                sources.append(result.source)
    else:
        # Auto-discover: all compliant subdirectories, alphabetical
        for item in sorted(path.iterdir()):
            if not item.is_dir():
                continue
            if item.name == "site" or should_skip_directory(item.name):
                continue

            result = check_compliance(item)
            if result.compliant and result.source:
                sources.append(result.source)

    return sources


def _source_to_json(source: EchoSource, output_path: Path) -> dict:
    """Convert an EchoSource to a JSON-serializable dict for the SFA."""
    readme_html = ""
    readme_path = find_readme(source.path)
    if readme_path:
        try:
            content = readme_path.read_text(encoding="utf-8")
            readme_html = markdown_to_html(content)
        except (OSError, UnicodeDecodeError):
            pass

    return {
        "name": source.name,
        "description": source.description,
        "formats": source.durable_formats,
        "frontmatter": source.frontmatter or {},
        "readme_html": readme_html,
        "data_files": _get_data_files(source, output_path),
    }


def _generate_site_readme(
    name: str,
    description: str,
    sources: list[EchoSource],
    output_path: Path,
) -> None:
    """Generate a longecho-compliant README.md for the site/ directory."""
    import yaml

    source_names = ", ".join(s.name for s in sources)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    frontmatter = {
        "name": f"{name} Site",
        "description": "Static site generated from longecho archive",
        "generator": f"longecho build v{__version__}",
        "datetime": now,
        "contents": [
            {"path": "index.html", "description": "Single-file browsable archive"},
        ],
    }
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    content = f"---\n{fm_yaml}---\n\nGenerated by longecho from {len(sources)} source(s): {source_names}.\nOpen index.html in any browser to explore.\n"
    readme_path = output_path / "README.md"
    readme_path.write_text(content, encoding="utf-8")


def build_site(
    path: Path,
    output: Optional[Path] = None,
) -> BuildResult:
    """Build a single-file application for a longecho archive."""
    path = Path(path).resolve()

    if not path.exists():
        return BuildResult(success=False, error=f"Path does not exist: {path}")

    if not path.is_dir():
        return BuildResult(success=False, error=f"Path is not a directory: {path}")

    result = check_compliance(path)
    if not result.compliant or not result.source:
        return BuildResult(
            success=False,
            error=f"Not a longecho archive: {result.reason}"
        )

    root_source = result.source
    name = root_source.name
    description = root_source.description

    sources = discover_sub_sources(root_source)

    output_path = Path(output).resolve() if output else path / "site"
    output_path.mkdir(parents=True, exist_ok=True)

    # Build JSON data for each source
    sources_data = [_source_to_json(s, output_path) for s in sources]

    env = get_jinja_env()
    template = env.get_template("sfa.html")
    html = template.render(
        name=name,
        description=description,
        sources_data=sources_data,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    index_path = output_path / "index.html"
    index_path.write_text(html, encoding="utf-8")

    _generate_site_readme(name, description, sources, output_path)

    return BuildResult(
        success=True,
        output_path=output_path,
        sources_count=len(sources),
    )
