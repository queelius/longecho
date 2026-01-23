# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Status

**Alpha.** Core functionality implemented and tested (78% coverage, 114 tests).

## What longecho Is

longecho provides:

1. **Documentation** — Explains and motivates the ECHO philosophy (`spec/`)
2. **Validator** — Checks ECHO compliance (`longecho check`)
3. **Discovery** — Finds ECHO sources (`longecho discover`, `longecho search`)
4. **Site Builder** — Generates unified static sites (`longecho build`)
5. **Dev Server** — Previews archives locally (`longecho serve`)

## Commands

```bash
longecho check ~/path       # Is this directory ECHO-compliant?
longecho discover ~/        # Find ECHO-compliant directories
longecho search ~/ "query"  # Search README descriptions
longecho info ~/path        # Show detailed source info
longecho formats            # List recognized durable formats
longecho build ~/archive    # Generate static site
longecho serve ~/archive    # Preview via HTTP
```

## Architecture

```
src/longecho/
├── __init__.py      # Public API exports
├── checker.py       # ECHO compliance checking
├── discovery.py     # Source discovery and search
├── manifest.py      # Manifest loading/validation
├── build.py         # Static site generation
├── serve.py         # HTTP server for preview
├── cli.py           # Typer CLI interface
└── templates/       # Jinja2 HTML templates
```

## Key Principles

1. **ECHO philosophy** — Self-describing data with README.md + durable formats
2. **Graceful degradation** — Archives work without longecho; longecho adds convenience
3. **Standalone toolkits** — ctk, btk, etc. work independently; longecho unifies their outputs

## Documentation Structure

```
spec/
├── ECHO.md              # ECHO philosophy (standalone)
├── LONGECHO.md          # Tool specification
├── MANIFEST-SCHEMA.md   # Manifest format spec
├── PERSONA-TK.md        # Persona toolkit spec
├── STONE-TK.md          # Stone toolkit spec
├── TOOLKIT-ECOSYSTEM.md # List of toolkits
└── INTERVIEW-INSIGHTS.md # Design decisions
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
- pytest for testing
- mypy for type checking
- ruff for linting
