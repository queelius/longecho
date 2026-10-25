"""longecho site builder -- generates a single-file application from a longecho archive."""

import json
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
# Elements whose content goes with them. Void elements (like ``embed``) have
# no content and no end tag, so they belong only off the allowlist, not here.
_DROP_WITH_CONTENT = frozenset({
    "script", "style", "iframe", "object", "template", "noscript",
    "svg", "math", "textarea", "select", "head", "title",
})
_URL_ATTRS = frozenset({"href", "src"})
_SAFE_SCHEMES = frozenset({"", "http", "https", "mailto", "file"})


def _safe_url(value: str) -> bool:
    """Relative links and a few plain schemes only. Browsers ignore control
    characters and whitespace inside a scheme, so those are removed first."""
    cleaned = "".join(ch for ch in value if ch > " " and ch != "\x7f")
    try:
        scheme = urlsplit(cleaned).scheme
    except ValueError:  # e.g. "http://[", an unterminated IPv6 host
        return False
    return scheme.lower() in _SAFE_SCHEMES


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
    readme = parse_readme(readme_path) if _is_file(readme_path) else None
    generator = (readme.frontmatter or {}).get("generator") if readme else None
    return str(generator) if generator else None


def _is_longecho_site(path: Path) -> bool:
    """A directory longecho build wrote: a view of the archive, not part of it."""
    generator = _site_generator(path)
    return generator is not None and generator.startswith(LONGECHO_GENERATOR)


def _is_dir(path: Path) -> bool:
    """``Path.is_dir`` that answers False for targets it may not inspect."""
    try:
        return path.is_dir()
    except OSError:
        return False


def _is_file(path: Path) -> bool:
    """``Path.is_file`` that answers False for targets it may not inspect."""
    try:
        return path.is_file()
    except OSError:
        return False


def _named_directories(source: EchoSource) -> list[Path]:
    """Every directory that ``contents`` names, resolved, in the order listed.

    File entries (informational) and paths that do not resolve, such as a
    symlink loop, are left out. Directories outside the source are kept here
    so that naming one still makes the list curated; the caller skips them.
    """
    named = []
    for entry in source.contents or []:
        entry_path = entry.get("path")
        if not isinstance(entry_path, str):
            continue
        try:
            sub_path = (source.path / entry_path).resolve()
        except (OSError, RuntimeError):  # RuntimeError: symlink loop before 3.13
            continue
        if _is_dir(sub_path):
            named.append(sub_path)
    return named


def _discovered_directories(source: EchoSource) -> list[Path]:
    """Every subdirectory that may hold a sub-source, alphabetically."""
    try:
        items = sorted(source.path.iterdir())
    except OSError:
        return []
    return [
        item for item in items
        if item.name != "site"
        and not should_skip_directory(item.name)
        and _is_dir(item)
        and not _is_longecho_site(item)  # an earlier build --output
    ]


def discover_sub_sources(source: EchoSource) -> list[EchoSource]:
    """The compliant sub-sources of ``source``, in display order.

    Directory entries in ``contents`` curate and order them; entries outside
    the source are skipped (no path traversal). File entries are
    informational, so a ``contents`` that names no directory leaves discovery
    automatic: every subdirectory, alphabetically. A source is never its own
    sub-source, whether through ``path: .`` or a symlink to itself.
    """
    named = _named_directories(source)
    if named:
        candidates = [p for p in named if p.is_relative_to(source.path)]
    else:
        candidates = _discovered_directories(source)
    sources: list[EchoSource] = []
    for candidate in candidates:
        result = check_compliance(candidate)
        if result.compliant and result.source and result.source.path != source.path:
            sources.append(result.source)
    return sources


_JSON_SCALARS = (str, int, float, bool, type(None))


def make_json_safe(obj: object) -> object:
    """Recursively convert YAML values that JSON cannot hold.

    ``yaml.safe_load`` can produce dates (as values or as keys), sets, and
    bytes (``!!binary``). Dates become ISO strings, sets become sorted lists,
    keys JSON cannot hold become strings, and any other value becomes its
    ``str``, so one unusual README never stops a build or a query.
    """
    if isinstance(obj, dict):
        return {_json_key(k): make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted((make_json_safe(v) for v in obj), key=str)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, _JSON_SCALARS):
        return obj
    return str(obj)


def _json_key(key: object) -> str:
    """The string JSON would use for this key. Keys must all be strings
    because the site's ``tojson`` sorts them, and ``3 < "b"`` is an error."""
    if isinstance(key, str):
        return key
    safe = make_json_safe(key)
    return safe if isinstance(safe, str) else json.dumps(safe)


def _source_to_json(
    source: EchoSource,
    output_path: Path,
    root: Optional[Path] = None,
    ancestors: frozenset[Path] = frozenset(),
) -> dict:
    """Convert an EchoSource to a JSON-serializable dict for the SFA, recursively.

    A child that is one of its own ancestors (a symlink pointing back up the
    tree) is left out, so every path through the tree ends.
    """
    readme_html = ""
    try:
        content = source.readme_path.read_text(encoding="utf-8")
        readme_html = markdown_to_html(content)
    except (OSError, UnicodeDecodeError):
        pass

    frontmatter: dict = make_json_safe(source.frontmatter or {})  # type: ignore[assignment]

    # Recursively discover and convert children
    lineage = ancestors | {source.path}
    child_sources = [c for c in discover_sub_sources(source) if c.path not in lineage]
    root = root or source.path
    children = [_source_to_json(c, output_path, root, lineage) for c in child_sources]

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
    # Resolved, so a site/ symlinked back to the archive counts too.
    if path.is_relative_to(output_path.resolve()):
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
