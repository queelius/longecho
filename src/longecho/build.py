"""longecho site builder -- generates a single-file application from a longecho archive."""

import os
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlsplit

from jinja2 import Environment, PackageLoader, select_autoescape

from . import __version__
from .checker import (
    EchoSource,
    check_compliance,
    parse_readme,
    should_skip_directory,
)
from .formats import format_for, is_unrecognized, preview_kind, sidecar_base

# The prefix of the generator stamp longecho writes into each site README.
LONGECHO_GENERATOR = "longecho build"

# Reported in place of a generator name when a site/ carries no stamp.
UNKNOWN_GENERATOR = "an unknown tool (no longecho generator stamp)"


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


# Tags Python-Markdown emits, and the attributes each may keep. Anything else
# is dropped (its text kept), and _DROP_WITH_CONTENT loses its text too.
_ALLOWED_TAGS: dict[str, frozenset[str]] = {
    **{tag: frozenset() for tag in (
        "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr", "em", "strong",
        "b", "i", "code", "pre", "blockquote", "ul", "ol", "li", "table",
        "thead", "tbody", "tr", "del", "sup", "sub", "dl", "dt", "dd", "span",
        "div", "abbr", "kbd", "details", "summary",
    )},
    "a": frozenset({"href", "title"}),
    "img": frozenset({"src", "alt", "title"}),
    "th": frozenset({"align"}),
    "td": frozenset({"align"}),
}
_VOID_TAGS = frozenset({"br", "hr", "img"})
_DROP_WITH_CONTENT = frozenset({
    "script", "style", "iframe", "object", "embed", "template", "noscript",
    "svg", "math", "textarea", "select", "head", "title",
})
_URL_ATTRS = frozenset({"href", "src"})
_SAFE_SCHEMES = frozenset({"", "http", "https", "mailto", "file"})


def _safe_url(value: str) -> bool:
    """Relative links and a few plain schemes only. Browsers ignore control
    characters and whitespace inside a scheme, so those are removed first."""
    cleaned = "".join(ch for ch in value if ch > " " and ch != "\x7f")
    return urlsplit(cleaned).scheme.lower() in _SAFE_SCHEMES


class _Sanitizer(HTMLParser):
    """Re-serialize HTML keeping only allowlisted tags, attributes, and URLs.

    The parser has already decoded entities in attribute values, so a URL
    like ``jav&#97;script:`` is checked as the ``javascript:`` it really is.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._dropping = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in _DROP_WITH_CONTENT:
            self._dropping += 1
            return
        if self._dropping or tag not in _ALLOWED_TAGS:
            return
        kept = []
        for name, value in attrs:
            if name not in _ALLOWED_TAGS[tag] or value is None:
                continue
            if name in _URL_ATTRS and not _safe_url(value):
                continue
            kept.append(f' {name}="{escape(value, quote=True)}"')
        self.out.append(f"<{tag}{''.join(kept)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag in _DROP_WITH_CONTENT:
            self._dropping -= 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _DROP_WITH_CONTENT:
            self._dropping = max(0, self._dropping - 1)
            return
        if not self._dropping and tag in _ALLOWED_TAGS and tag not in _VOID_TAGS:
            self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self._dropping:
            self.out.append(escape(data, quote=False))


def _sanitize_html(html: str) -> str:
    """Keep the formatting of rendered Markdown, drop anything that can run."""
    sanitizer = _Sanitizer()
    sanitizer.feed(html)
    sanitizer.close()
    return "".join(sanitizer.out)


def markdown_to_html(content: str) -> str:
    """Convert markdown to sanitized HTML."""
    import markdown

    html: str = markdown.markdown(content, extensions=["fenced_code", "tables"])
    return _sanitize_html(html)


def _link(target: Path, output_path: Path, root: Path) -> str:
    """The href that reaches ``target`` from the page at ``output_path/index.html``.

    When both the site and the target live inside the archive, links are
    relative and percent-encoded (``../photos/a%20b.png``), so the archive can
    move as a whole and no filename can turn into a URL scheme, query, or
    fragment. Otherwise (a site written outside the archive, or a symlinked
    source that lives elsewhere) the link is an absolute ``file://`` URI,
    since no relative path survives moving either one.
    """
    root = root.resolve()
    if output_path.resolve().is_relative_to(root) and target.resolve().is_relative_to(root):
        try:
            return quote(Path(os.path.relpath(target, output_path)).as_posix())
        except ValueError:  # different drives on Windows
            pass
    return target.resolve().as_uri()


def _get_data_files(
    source: EchoSource, output_path: Path, root: Optional[Path] = None
) -> list[dict]:
    """List every file this source owns, for the SFA's "Data Files" section.

    Ownership (see ``EchoSource.files``) already stops at nested sources,
    ``site/``, and the scan depth. Files outside the format list are listed
    too; ``warns`` marks the ones that ``check`` warns about (neither in a
    durable format nor UTF-8 text), so the page applies no rule of its own.
    SQLite sidecars are left out: they belong to their database. ``preview``
    names the inline element a browser can show the file with, if any.
    """
    files: list[dict] = []
    root = root or source.path

    for item in source.files:
        if sidecar_base(item) is not None:
            continue
        files.append({
            "name": item.relative_to(source.path).as_posix(),
            "path": _link(item, output_path, root),
            "durable": format_for(item) is not None,
            "warns": is_unrecognized(item),
            "preview": preview_kind(item),
        })

    return sorted(files, key=lambda x: x["name"])


def _is_foreign_site(output_path: Path) -> tuple[bool, str]:
    """Check if output_path contains a site that longecho did not generate.

    Only an empty directory, or one whose README.md frontmatter carries a
    ``generator`` starting with "longecho build", may be overwritten without
    an explicit force. Anything else (another tool's stamp, or a viewer with
    no stamp at all) belongs to someone else.

    Returns (is_foreign, generator_identifier).
    """
    if output_path.is_dir() and not any(output_path.iterdir()):
        return False, ""
    generator = _site_generator(output_path)
    if not generator:
        return True, UNKNOWN_GENERATOR
    return not generator.startswith(LONGECHO_GENERATOR), generator


def _site_generator(path: Path) -> Optional[str]:
    """The ``generator`` stamp in ``path/README.md`` frontmatter, if any."""
    readme_path = path / "README.md"
    readme = parse_readme(readme_path) if readme_path.is_file() else None
    generator = (readme.frontmatter or {}).get("generator") if readme else None
    return str(generator) if generator else None


def _is_longecho_site(path: Path) -> bool:
    """A directory longecho build wrote: a view of the archive, not part of it."""
    generator = _site_generator(path)
    return generator is not None and generator.startswith(LONGECHO_GENERATOR)


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
            if _is_longecho_site(item):  # an earlier build --output
                continue

            result = check_compliance(item)
            if result.compliant and result.source:
                sources.append(result.source)

    return sources


def make_json_safe(obj: object) -> object:
    """Recursively convert non-JSON-serializable types (e.g. datetime.date) to strings."""
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _source_to_json(
    source: EchoSource, output_path: Path, root: Optional[Path] = None
) -> dict:
    """Convert an EchoSource to a JSON-serializable dict for the SFA, recursively."""
    readme_html = ""
    try:
        content = source.readme_path.read_text(encoding="utf-8")
        readme_html = markdown_to_html(content)
    except (OSError, UnicodeDecodeError):
        pass

    frontmatter: dict = make_json_safe(source.frontmatter or {})  # type: ignore[assignment]

    # Recursively discover and convert children
    child_sources = discover_sub_sources(source)
    root = root or source.path
    children = [_source_to_json(c, output_path, root) for c in child_sources]

    # Compute relative path to source's site/index.html if it exists.
    # Skip self-references: the root source's site IS the output we're
    # generating right now, so linking to it would point at the current page.
    site_url = None
    if source.has_site and source.site_path:
        try:
            is_self_ref = source.site_path.resolve() == output_path.resolve()
        except OSError:
            is_self_ref = False
        if not is_self_ref:
            site_url = _link(source.site_path / "index.html", output_path, root)

    return {
        "name": source.name,
        "description": source.description,
        "durable_formats": source.durable_formats,
        "frontmatter": frontmatter,
        "readme_html": readme_html,
        "data_files": _get_data_files(source, output_path, root),
        "site_url": site_url,
        "children": children,
    }


def _generate_site_readme(
    name: str,
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
        "generator": f"{LONGECHO_GENERATOR} v{__version__}",
        "datetime": now,
        "contents": [
            {"path": "index.html", "description": "Single-file browsable archive"},
        ],
    }
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    content = f"---\n{fm_yaml}---\n\nGenerated by longecho from {len(sources)} source(s): {source_names}.\nOpen index.html in any browser to explore.\n"
    readme_path = output_path / "README.md"
    readme_path.write_text(content, encoding="utf-8")


def _count_sources(data: list[dict]) -> int:
    """Count all sources including nested children."""
    total = len(data)
    for s in data:
        total += _count_sources(s.get("children", []))
    return total


def build_site(
    path: Path,
    output: Optional[Path] = None,
    force: bool = False,
) -> BuildResult:
    """Build a single-file application for a longecho archive.

    If ``output`` already contains a site generated by another tool
    (detected via its README frontmatter ``generator`` field), the build
    fails unless ``force=True``. This protects tool-generated viewers
    (e.g. ctk, chartfold) from being silently clobbered.
    """
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
    # Pre-compute top-level children for the site README (cheap, sourced
    # from check_compliance cache; _source_to_json will walk again).
    top_level_children = discover_sub_sources(root_source)

    output_path = Path(output).resolve() if output else path / "site"

    # Writing index.html and README.md into the archive itself, or into a
    # directory that contains it, would replace a README someone wrote.
    if path.is_relative_to(output_path):
        return BuildResult(
            success=False,
            error=(
                f"Refusing to write the site into {output_path}: it is the archive "
                f"or contains it, and its README.md would be overwritten. "
                f"Choose an --output inside the archive (the default is site/) or elsewhere."
            ),
        )

    # Protect foreign-generated sites from accidental overwrite
    if output_path.exists() and not force:
        is_foreign, gen = _is_foreign_site(output_path)
        if is_foreign:
            return BuildResult(
                success=False,
                error=(
                    f"Output directory already contains a site generated by "
                    f"{gen if gen == UNKNOWN_GENERATOR else repr(gen)}. "
                    f"Use --force to overwrite, or choose a different --output path."
                ),
            )

    output_path.mkdir(parents=True, exist_ok=True)

    # Render the root source itself as a full JSON object (README, data
    # files, metadata, and recursively nested children). This unifies the
    # home view with the detail view: every view in the SFA is the detail
    # view of some source, and the home view is the root's detail view.
    root_data = _source_to_json(root_source, output_path)

    env = get_jinja_env()
    template = env.get_template("sfa.html")
    html = template.render(
        name=root_source.name,
        description=root_source.description,
        root_data=root_data,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    index_path = output_path / "index.html"
    index_path.write_text(html, encoding="utf-8")

    _generate_site_readme(root_source.name, top_level_children, output_path)

    return BuildResult(
        success=True,
        output_path=output_path,
        sources_count=_count_sources(root_data.get("children", [])),
    )
