# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Status

**Alpha.** Spec v2 implemented. 97 tests, 94% coverage.

## What longecho Is

longecho is both a philosophy and a tool for durable personal archives. One name, one concept.

- **Philosophy** — Self-describing data (README.md) in durable formats
- **Tool** — CLI that validates compliance, queries archives, and builds browsable sites

## Commands

```bash
longecho check ~/path              # Is this directory longecho-compliant?
longecho query ~/                  # Find/search/filter sources across the tree
longecho query ~/ --search "term"  # Search README text
longecho query ~/ --json           # Output as JSON
longecho build ~/archive           # Generate single-file static site
longecho formats                   # List recognized durable formats
```

## Architecture

```
src/longecho/
├── __init__.py      # Public API exports
├── checker.py       # Compliance checking + README parsing
├── discovery.py     # Source discovery (tree walk)
├── build.py         # Single-file application (SFA) generation
├── cli.py           # Typer CLI interface
└── templates/
    └── sfa.html     # Single-file application template
```

## Data Model

- **Readme** — Parsed README: frontmatter (dict), body, title, summary
- **EchoSource** — Compliant source: path, readme_path, name, description, formats, durable_formats, has_site, site_path, frontmatter, contents
- **ComplianceResult** — Check result: compliant, path, reason, source (Optional[EchoSource])
- **BuildResult** — Build result: success, output_path, sources_count, error
- **Name cascade:** frontmatter `name` > `# Heading` > dirname
- **Description cascade:** frontmatter `description` > first paragraph after heading
- **`contents` field** — lists directory entries (curation + ordering for build)

## Key Principles

1. **Self-describing** — README is the interface; frontmatter adds optional structured metadata
2. **Recursive/fractal** — Every directory is the same kind of object; nesting is unlimited
3. **Graceful degradation** — Archives work without longecho; longecho adds convenience
4. **No parent overrides** — A source's name/description always comes from its own README
5. **Single-file site** — Build output is a self-contained HTML file (SFA), works from `file://`

## Documentation

Everything is in `README.md` — philosophy, spec, CLI reference, ecosystem. No separate spec directory.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/ --cov=src/longecho --cov-report=term-missing
mypy src/longecho/
ruff check src/longecho/
```

## Tech Stack

- Python 3.9+
- Typer for CLI
- Rich for terminal output
- Jinja2 for templates
- PyYAML for frontmatter parsing
- Markdown for HTML conversion
- pytest for testing
- mypy for type checking
- ruff for linting
