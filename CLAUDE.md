# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Status

**Alpha.** Spec v2 written. Implementation needs updating to match new spec.

## What longecho Is

longecho is both a philosophy and a tool for durable personal archives. One name, one concept.

- **Philosophy** — Self-describing data (README.md) in durable formats
- **Tool** — CLI that validates compliance, queries archives, and builds browsable sites

## Commands (target spec)

```bash
longecho check ~/path              # Is this directory longecho-compliant?
longecho query ~/                  # Find/search/filter sources across the tree
longecho query ~/ --author "Alex"  # Filter by any frontmatter field
longecho build ~/archive           # Generate single-file static site
longecho formats                   # List recognized durable formats
```

## Architecture

```
src/longecho/
├── __init__.py      # Public API exports
├── checker.py       # Compliance checking + README parsing
├── discovery.py     # Source discovery (tree walk)
├── build.py         # Single-file site generation
├── cli.py           # Typer CLI interface
└── templates/       # Jinja2 HTML template (single SFA template)
```

Note: `manifest.py` and `serve.py` are being removed per spec v2.

## Data Model

- **Readme** — Parsed README: frontmatter (dict), body, title, summary
- **EchoSource** — Compliant source: path, readme_path, name, description, formats, durable_formats, has_site, site_path
- **ComplianceResult** — Check result: compliant, path, reason, source (Optional[EchoSource])
- **Name cascade:** frontmatter `name` > `# Heading` > dirname
- **Description cascade:** frontmatter `description` > first paragraph after heading
- **`contents` field** — lists directory entries (curation + ordering for build)

## Key Principles

1. **Self-describing** — README is the interface; frontmatter adds optional structured metadata
2. **Recursive/fractal** — Every directory is the same kind of object; nesting is unlimited
3. **Graceful degradation** — Archives work without longecho; longecho adds convenience
4. **No parent overrides** — A source's name/description always comes from its own README
5. **Single-file site** — Build output is a self-contained HTML file (SFA), works from `file://`

## Documentation Structure

```
spec/
├── index.md             # Documentation index
├── LONGECHO.md          # Unified spec (philosophy + tool)
└── TOOLKIT-ECOSYSTEM.md # List of toolkits
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/longecho --cov-report=term-missing

# Type checking
mypy src/longecho/

# Linting
ruff check src/longecho/
```

## Tech Stack

- Python 3.9+
- Typer for CLI
- Rich for terminal output
- Jinja2 for templates
- PyYAML for frontmatter parsing
- pytest for testing
- mypy for type checking
- ruff for linting
