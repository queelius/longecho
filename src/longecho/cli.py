"""longecho CLI -- compliance validator, query tool, and site builder."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .build import build_site
from .checker import check_compliance
from .discovery import discover_sources, search_sources

app = typer.Typer(
    name="longecho",
    help="Compliance validator and site builder for durable personal archives.",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool):
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
        ...,
        help="Directory to check for compliance.",
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
        console.print(f"[green]\u2713[/green] longecho-compliant: {path}")

        if verbose and result.source:
            s = result.source
            console.print()
            console.print(f"  [dim]README:[/dim] {s.readme_path.name}")
            if s.description:
                desc = s.description
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                console.print(f"  [dim]Description:[/dim] {desc}")
            console.print(f"  [dim]Durable formats:[/dim] {', '.join(s.durable_formats)}")
            other = [f for f in s.formats if f not in s.durable_formats]
            if other:
                console.print(f"  [dim]Other formats:[/dim] {', '.join(other)}")
            if s.frontmatter:
                for key, val in s.frontmatter.items():
                    if key not in ("name", "description", "contents"):
                        console.print(f"  [dim]{key}:[/dim] {val}")
    else:
        console.print(f"[red]\u2717[/red] Not longecho-compliant: {path}")
        console.print(f"  [dim]Reason:[/dim] {result.reason}")
        raise typer.Exit(code=1)


@app.command()
def query(
    path: Path = typer.Argument(
        ...,
        help="Root directory to search.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="Search README text (case-insensitive).",
    ),
    depth: Optional[int] = typer.Option(
        None,
        "--depth",
        "-d",
        help="Maximum directory depth to scan.",
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
            entry: dict = {
                "path": str(s.path),
                "name": s.name,
                "description": s.description,
                "durable_formats": s.durable_formats,
            }
            if s.frontmatter:
                entry["frontmatter"] = s.frontmatter
            output.append(entry)
        console.print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    if not sources:
        label = f"matching '{search}'" if search else f"under {path}"
        console.print(f"[yellow]No longecho sources found {label}[/yellow]")
        return

    if table_format:
        table = Table(title=f"longecho sources under {path}")
        table.add_column("Name", style="cyan")
        table.add_column("Path")
        table.add_column("Formats", style="green")
        table.add_column("Description")

        for s in sources:
            desc = s.description or ""
            if len(desc) > 50:
                desc = desc[:47] + "..."
            table.add_row(
                s.name,
                str(s.path),
                ", ".join(s.durable_formats[:3]),
                desc,
            )

        console.print(table)
    else:
        console.print(f"[bold]Found {len(sources)} source(s):[/bold]")
        console.print()

        for s in sources:
            console.print(f"  [cyan]{s.name}[/cyan]  {s.path}")
            if s.description:
                desc = s.description
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                console.print(f"    [dim]{desc}[/dim]")
            console.print()


@app.command()
def build(
    path: Path = typer.Argument(
        ...,
        help="Archive directory to build site for.",
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
    open_browser: bool = typer.Option(
        False,
        "--open",
        help="Open in browser after build.",
    ),
):
    """Build a single-file static site from a longecho archive."""
    console.print(f"[bold]Building site for:[/bold] {path}")

    result = build_site(path=path, output=output)

    if result.success:
        console.print(f"[green]\u2713[/green] Built site with {result.sources_count} source(s)")
        console.print(f"  [dim]Output:[/dim] {result.output_path}")

        if open_browser and result.output_path:
            import webbrowser
            index = result.output_path / "index.html"
            webbrowser.open(index.as_uri())
    else:
        console.print(f"[red]\u2717[/red] Build failed: {result.error}")
        raise typer.Exit(code=1)


@app.command()
def formats():
    """List recognized durable formats by category."""
    console.print("[bold]longecho Durable Formats[/bold]")
    console.print()

    categories = {
        "Structured data": [".db", ".sqlite", ".sqlite3", ".json", ".jsonl"],
        "Documents": [".md", ".markdown", ".txt", ".text", ".rst"],
        "Archives": [".zip"],
        "Images": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
        "Tabular / data": [".csv", ".tsv", ".xml", ".yaml", ".yml"],
    }

    for category, extensions in categories.items():
        console.print(f"[cyan]{category}:[/cyan]")
        console.print(f"  {', '.join(extensions)}")
        console.print()


if __name__ == "__main__":
    app()
