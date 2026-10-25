"""longecho CLI -- compliance validator, query tool, and site builder."""

import json
import textwrap
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from . import __version__
from .build import build_site, make_json_safe
from .checker import ComplianceWarning, EchoSource, check_compliance
from .discovery import discover_sources, search_sources
from .formats import (
    DURABILITY_CRITERIA,
    DURABLE_FORMAT_CATEGORIES,
    FORMATS,
    Reader,
    format_for,
)

app = typer.Typer(
    name="longecho",
    help="Compliance validator and site builder for durable personal archives.",
    no_args_is_help=True,
)

console = Console()

# How many paths `check --verbose` lists under each warning.
MAX_WARNING_PATHS: int = 5


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _lit(value: object) -> str:
    """Untrusted text (paths, README fields, messages) for a markup string."""
    return escape(str(value))


def _print_warnings(
    warnings: list[ComplianceWarning], root: Path, verbose: bool
) -> None:
    """Print warnings under a check result; with verbose, name the files."""
    for w in warnings:
        console.print(f"  [yellow]![/yellow] {_lit(w.message)}", highlight=False)
        if not verbose:
            continue
        for p in w.paths[:MAX_WARNING_PATHS]:
            console.print(f"      [dim]{_lit(p.relative_to(root).as_posix())}[/dim]", highlight=False)
        if len(w.paths) > MAX_WARNING_PATHS:
            console.print(f"      [dim]and {len(w.paths) - MAX_WARNING_PATHS} more[/dim]")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"longecho version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    longecho - compliance validator for durable personal archives.

    A directory is longecho-compliant if it has:

    1. A README.md or README.txt explaining the data
    2. Data stored in durable formats (SQLite, JSON, Markdown, etc.)
    """
    pass


@app.command()
def check(
    path: Path = typer.Argument(
        ".",
        help="Directory to check for compliance (default: current directory).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Show detailed information.",
    ),
):
    """Check if a directory is longecho-compliant."""
    result = check_compliance(path)

    if result.compliant:
        console.print(f"[green]\u2713[/green] longecho-compliant: {_lit(path)}")

        if verbose and result.source:
            s = result.source
            console.print()
            console.print(f"  [dim]README:[/dim] {_lit(s.readme_path.name)}")
            if s.description:
                console.print(f"  [dim]Description:[/dim] {_lit(_truncate(s.description, 100))}")
            console.print(f"  [dim]Durable formats:[/dim] {', '.join(s.durable_formats)}")
            readers = _source_readers(s)
            if readers:
                console.print(f"  [dim]Readable with:[/dim] {readers}")
            if s.frontmatter:
                for key, val in s.frontmatter.items():
                    if key not in ("name", "description", "contents"):
                        console.print(f"  [dim]{_lit(key)}:[/dim] {_lit(val)}")
        _print_warnings(result.warnings, path, verbose)
    else:
        console.print(f"[red]\u2717[/red] Not longecho-compliant: {_lit(path)}")
        console.print(f"  [dim]Reason:[/dim] {_lit(result.reason)}")
        _print_warnings(result.warnings, path, verbose)
        raise typer.Exit(code=1)


@app.command()
def query(
    path: Path = typer.Argument(
        ".",
        help="Root directory to search (default: current directory).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="Text to search for in names, descriptions, and READMEs.",
    ),
    depth: Optional[int] = typer.Option(
        None,
        "--depth",
        "-d",
        help="Maximum filesystem depth to walk (0 = root only).",
    ),
    table_format: bool = typer.Option(
        False,
        "--table",
        "-t",
        help="Output as a table.",
    ),
    json_format: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON.",
    ),
):
    """Find, search, and filter sources across the archive tree."""
    if search:
        sources = list(search_sources(path, search, depth))
    else:
        sources = list(discover_sources(path, depth))

    if json_format:
        output: list[dict] = []
        for s in sources:
            try:
                rel = str(s.path.relative_to(path))
                display_path = f"./{rel}" if rel != "." else "."
            except ValueError:
                display_path = str(s.path)
            entry: dict = {
                "path": display_path,
                "name": s.name,
                "description": s.description,
                "durable_formats": s.durable_formats,
            }
            if s.frontmatter:
                entry["frontmatter"] = make_json_safe(s.frontmatter)
            warnings = s.warnings
            if warnings:
                entry["warnings"] = [
                    {
                        "kind": w.kind.value,
                        "message": w.message,
                        "paths": [p.relative_to(s.path).as_posix() for p in w.paths],
                    }
                    for w in warnings
                ]
            output.append(entry)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    if not sources:
        label = f"matching '{search}'" if search else f"under {path}"
        console.print(f"[yellow]No longecho sources found {_lit(label)}[/yellow]")
        return

    if table_format:
        table = Table(title=f"longecho sources under {_lit(path)}")
        table.add_column("Name", style="cyan")
        table.add_column("Path")
        table.add_column("Formats", style="green")
        table.add_column("Description")

        for s in sources:
            table.add_row(
                Text(str(s.name)),
                Text(str(s.path)),
                ", ".join(s.durable_formats[:3]),
                Text(_truncate(s.description or "", 50)),
            )

        console.print(table)
    else:
        console.print(f"[bold]Found {len(sources)} source(s):[/bold]")
        console.print()

        for s in sources:
            # Compute indentation and relative path from query root
            try:
                rel_path = s.path.relative_to(path)
                depth_level = len(rel_path.parts)
                display_path = f"./{rel_path}" if str(rel_path) != "." else "."
            except ValueError:
                depth_level = 1
                display_path = str(s.path)
            indent = "  " * depth_level

            console.print(f"{indent}[cyan]{_lit(s.name)}[/cyan]  [dim]{_lit(display_path)}[/dim]")
            if s.description:
                console.print(f"{indent}  [dim]{_lit(_truncate(s.description, 80))}[/dim]")
            console.print()


@app.command()
def build(
    path: Path = typer.Argument(
        ".",
        help="Archive directory to build site for (default: current directory).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory (default: path/site/).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing site even if generated by another tool.",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        help="Open in browser after build.",
    ),
):
    """Build a single-file static site from a longecho archive."""
    console.print(f"[bold]Building site for:[/bold] {_lit(path)}")

    result = build_site(path=path, output=output, force=force)

    if result.success:
        console.print(f"[green]\u2713[/green] Built site with {result.sources_count} source(s)")
        console.print(f"  [dim]Output:[/dim] {_lit(result.output_path)}")

        if open_browser and result.output_path:
            import webbrowser
            index = result.output_path / "index.html"
            webbrowser.open(index.as_uri())
    else:
        console.print(f"[red]\u2717[/red] Build failed: {_lit(result.error)}")
        raise typer.Exit(code=1)


def _format_spec() -> str:
    """Generate the spec summary from structured data."""
    lines = [
        "longecho: a philosophy and tool for durable personal archives.",
        "",
        "A directory is longecho-compliant if it has:",
        "  1. A README.md or README.txt explaining the data",
        "  2. At least one file in a durable format, within two levels of the README",
        "",
        "Core Principles:",
        "  Self-Describing       Every collection explains itself via README",
        "  Durable Formats       Formats readable without proprietary software",
        "  Graceful Degradation  Useful with LLMs, standard tools, browsers, editors",
        "  Local-First           Complete without cloud services",
        "  Trust the Future      Simple over \"correct\"; future humans are smart",
        "",
        "The README:",
        "  The README is the interface. Optional YAML frontmatter adds metadata.",
        "  Special fields: name, description, contents (build curation and order).",
        "  All other frontmatter is preserved, displayed, and queryable.",
        "  The top-level README is where a reader with no context starts: write it",
        "  for someone with none of your tools, and say how to open each file type.",
        "",
        "  Name cascade:        frontmatter name > first # heading > directory name",
        "  Description cascade: frontmatter description > first paragraph",
        "",
        "Nesting:",
        "  Sources can contain other sources. Structure is recursive: every level is",
        "  the same kind of object, self-describing even if fragmented.",
        "",
        "  The contents field lists what's in a directory. Its directory entries",
        "  control curation (only listed directories built) and ordering. File",
        "  entries are informational. When it names no directory, the tool",
        "  auto-discovers compliant subdirectories alphabetically.",
        "",
        "Durable Formats:",
        "  A format is durable when it does well, on balance, on the",
        "  Library of Congress sustainability factors:",
    ]
    width = max(len(name) for name, _ in DURABILITY_CRITERIA)
    lines += [f"    {name:<{width}s}  {question}" for name, question in DURABILITY_CRITERIA]
    lines.append("")
    # Derive format display from the single source of truth
    width = max(len(category) for category in DURABLE_FORMAT_CATEGORIES) + 1
    for category, extensions in DURABLE_FORMAT_CATEGORIES.items():
        lines.append(f"  {category + ':':<{width}s} {' '.join(extensions)}")
    lines += [
        "",
        "  `longecho formats` shows who can open each format, and why it qualifies.",
        "",
        "Warnings (never change the verdict):",
        "  Files neither in a durable format nor UTF-8 text; SQLite databases with",
        "  changes still in a -wal or -journal file; directories too deep to inspect.",
        "",
        "The site/ Convention:",
        "  longecho build generates a single-file application (site/index.html) with all",
        "  content inlined. Works from file:// with no server. The site/ directory is",
        "  itself longecho-compliant.",
        "",
        "Full spec: https://queelius.github.io/longecho/spec/",
    ]
    return "\n".join(lines)


@app.command()
def spec():
    """Print the longecho specification summary."""
    console.print(_format_spec(), highlight=False)


def _indented(text: str, indent: int) -> str:
    """Wrap text to the console width with a hanging indent."""
    pad = " " * indent
    return textwrap.fill(
        text, width=max(console.width, 40), initial_indent=pad, subsequent_indent=pad
    )


def _source_readers(source: EchoSource) -> str:
    """Which readers can open some of this source's own durable files."""
    readers: set[Reader] = set()
    for f in source.files:
        fmt = format_for(f)
        if fmt is not None:
            readers |= fmt.readers
    return _readers_label(frozenset(readers))


def _readers_label(readers: frozenset[Reader]) -> str:
    """Readers in ladder order (the enum's order), joined for display."""
    return ", ".join(r.value for r in Reader if r in readers)


@app.command()
def formats(
    json_format: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output the format registry as JSON.",
    ),
):
    """List recognized durable formats: who can open each, and why it qualifies."""
    if json_format:
        entries = [
            {
                "extensions": list(f.extensions),
                "mimetype": f.mimetype,
                "category": f.category,
                "mimetype_aliases": list(f.mimetype_aliases),
                "readers": [r.value for r in Reader if r in f.readers],
                "rationale": f.rationale,
            }
            for f in FORMATS
        ]
        print(json.dumps(entries, indent=2, ensure_ascii=False))
        return

    console.print("[bold]longecho Durable Formats[/bold]")
    console.print(Text(
        "Judged on the Library of Congress sustainability factors (`longecho spec`).",
        style="dim",
    ))

    category = None
    for f in FORMATS:
        if f.category != category:
            category = f.category
            console.print()
            console.print(f"[cyan]{category}:[/cyan]")
        console.print(
            f"  [bold]{' '.join(f.extensions)}[/bold]  "
            f"[green]{_readers_label(f.readers)}[/green]",
            highlight=False,
        )
        console.print(Text(_indented(f.rationale, 4), style="dim"))

    console.print()
    console.print("[cyan]Readers:[/cyan]")
    for reader in Reader:
        console.print(Text(_indented(f"{reader.value}: {reader.description}", 2)))


if __name__ == "__main__":
    app()
