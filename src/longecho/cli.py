"""
longecho CLI - ECHO compliance validator.

Commands:
    check    - Check if a directory is ECHO-compliant
    discover - Find ECHO-compliant directories
    search   - Search README descriptions
    info     - Show detailed info about an ECHO source
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .checker import check_compliance, DURABLE_EXTENSIONS
from .discovery import discover_sources, search_sources, get_source_info

app = typer.Typer(
    name="longecho",
    help="ECHO philosophy documentation and compliance validator.",
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
    longecho - ECHO compliance validator.

    ECHO is a philosophy for durable personal data archives.
    A directory is ECHO-compliant if it has:

    1. A README.md or README.txt explaining the data
    2. Data stored in durable formats (SQLite, JSON, Markdown, etc.)
    """
    pass


@app.command()
def check(
    path: Path = typer.Argument(
        ...,
        help="Directory to check for ECHO compliance.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information.",
    ),
):
    """
    Check if a directory is ECHO-compliant.

    A directory is ECHO-compliant if it has:
    - A README.md or README.txt at the root
    - Data in durable formats
    """
    result = check_compliance(path)

    if result.compliant:
        console.print(f"[green]✓[/green] ECHO-compliant: {path}")

        if verbose:
            console.print()
            console.print(f"  [dim]README:[/dim] {result.readme_path.name}")
            if result.readme_summary:
                console.print(f"  [dim]Summary:[/dim] {result.readme_summary[:100]}...")
            console.print(f"  [dim]Durable formats:[/dim] {', '.join(result.durable_formats)}")
            if result.formats:
                other = [f for f in result.formats if f not in result.durable_formats]
                if other:
                    console.print(f"  [dim]Other formats:[/dim] {', '.join(other)}")
    else:
        console.print(f"[red]✗[/red] Not ECHO-compliant: {path}")
        console.print(f"  [dim]Reason:[/dim] {result.reason}")

        if verbose and result.readme_path:
            console.print(f"  [dim]README found:[/dim] {result.readme_path.name}")

        raise typer.Exit(code=1)


@app.command()
def discover(
    path: Path = typer.Argument(
        ...,
        help="Root directory to scan for ECHO sources.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--max-depth",
        "-d",
        help="Maximum directory depth to scan.",
    ),
    table_format: bool = typer.Option(
        False,
        "--table",
        "-t",
        help="Output as a table.",
    ),
):
    """
    Find ECHO-compliant directories under a root path.

    Scans for directories containing README files and checks
    each for ECHO compliance.
    """
    sources = list(discover_sources(path, max_depth))

    if not sources:
        console.print(f"[yellow]No ECHO-compliant sources found under {path}[/yellow]")
        return

    if table_format:
        table = Table(title=f"ECHO Sources under {path}")
        table.add_column("Path", style="cyan")
        table.add_column("Formats", style="green")
        table.add_column("Description")

        for source in sources:
            desc = source.readme_summary or ""
            if len(desc) > 50:
                desc = desc[:47] + "..."
            table.add_row(
                str(source.path),
                ", ".join(source.durable_formats[:3]),
                desc
            )

        console.print(table)
    else:
        console.print(f"[bold]Found {len(sources)} ECHO source(s):[/bold]")
        console.print()

        for source in sources:
            console.print(f"[cyan]{source.path}[/cyan]")
            if source.readme_summary:
                desc = source.readme_summary
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                console.print(f"  [dim]{desc}[/dim]")
            console.print(f"  Formats: {', '.join(source.durable_formats)}")
            console.print()


@app.command()
def search(
    path: Path = typer.Argument(
        ...,
        help="Root directory to search.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    query: str = typer.Argument(
        ...,
        help="Search string to find in README files.",
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--max-depth",
        "-d",
        help="Maximum directory depth to scan.",
    ),
):
    """
    Search ECHO sources by README content.

    Finds ECHO-compliant directories whose README contains
    the query string (case-insensitive).
    """
    sources = list(search_sources(path, query, max_depth))

    if not sources:
        console.print(f"[yellow]No ECHO sources matching '{query}' found[/yellow]")
        return

    console.print(f"[bold]Found {len(sources)} matching source(s):[/bold]")
    console.print()

    for source in sources:
        console.print(f"[cyan]{source.path}[/cyan]")
        if source.readme_summary:
            desc = source.readme_summary
            if len(desc) > 80:
                desc = desc[:77] + "..."
            console.print(f"  [dim]{desc}[/dim]")
        console.print()


@app.command()
def info(
    path: Path = typer.Argument(
        ...,
        help="ECHO source directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
):
    """
    Show detailed information about an ECHO source.
    """
    source = get_source_info(path)

    if not source:
        result = check_compliance(path)
        console.print(f"[red]Not an ECHO source:[/red] {result.reason}")
        raise typer.Exit(code=1)

    # Build info panel
    info_lines = [
        f"[bold]Path:[/bold] {source.path}",
        f"[bold]README:[/bold] {source.readme_path.name}",
    ]

    if source.readme_summary:
        info_lines.append(f"[bold]Summary:[/bold] {source.readme_summary}")

    info_lines.append(f"[bold]Durable formats:[/bold] {', '.join(source.durable_formats)}")

    if source.formats:
        other = [f for f in source.formats if f not in source.durable_formats]
        if other:
            info_lines.append(f"[bold]Other formats:[/bold] {', '.join(other)}")

    panel = Panel(
        "\n".join(info_lines),
        title="ECHO Source",
        border_style="green",
    )
    console.print(panel)


@app.command()
def formats():
    """
    List recognized durable formats.
    """
    console.print("[bold]ECHO Durable Formats[/bold]")
    console.print()

    categories = {
        "Structured data": [".db", ".sqlite", ".sqlite3", ".json", ".jsonl"],
        "Documents": [".md", ".markdown", ".txt", ".text", ".rst"],
        "Archives": [".zip"],
        "Images": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
        "Data": [".csv", ".tsv", ".xml", ".yaml", ".yml"],
    }

    for category, extensions in categories.items():
        console.print(f"[cyan]{category}:[/cyan]")
        console.print(f"  {', '.join(extensions)}")
        console.print()


if __name__ == "__main__":
    app()
