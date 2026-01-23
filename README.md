# longecho

ECHO philosophy documentation, compliance validator, and static site builder.

## Status

**Alpha.** Core functionality implemented and tested.

## What This Is

longecho provides:

1. **Documentation** — Explains and motivates the ECHO philosophy
2. **Validator** — Checks if a directory is ECHO-compliant
3. **Discovery** — Finds and searches ECHO sources
4. **Site Builder** — Generates unified static sites from archives
5. **Dev Server** — Previews archives via HTTP

## The ECHO Philosophy

ECHO is a philosophy for durable personal data:

- **Self-describing** — A `README.md` at the root explains what the data is
- **Durable formats** — SQLite, JSON, Markdown, plain text

A directory is ECHO-compliant if it has a README and uses durable formats. That's it.

See [spec/ECHO.md](spec/ECHO.md) for the full philosophy.

## Installation

```bash
pip install longecho

# With optional dependencies for YAML manifests
pip install longecho[full]
```

## Commands

```bash
# Check if a directory is ECHO-compliant
longecho check ~/my-data/

# Find ECHO-compliant directories
longecho discover ~/

# Search README descriptions
longecho search ~/ "conversations"

# Show detailed info about a source
longecho info ~/my-data/

# List recognized durable formats
longecho formats

# Build a static site from an ECHO archive
longecho build ~/my-archive/

# Serve an archive via HTTP for preview
longecho serve ~/my-archive/ --port 8000
```

## Boundaries

**longecho unifies, but doesn't orchestrate toolkits.** Each toolkit (ctk, btk, etc.) exports its own ECHO-compliant archive independently. longecho's `build` command combines these into a unified browsable site, but doesn't invoke or manage the toolkits themselves.

**longecho doesn't mediate formats.** There is no central interchange format. Each toolkit defines its own input/output formats.

**longecho doesn't maintain a registry.** If a toolkit is ECHO-compliant, its own README documents that fact.

## Documentation

| Document | What it covers |
|----------|----------------|
| [spec/ECHO.md](spec/ECHO.md) | ECHO philosophy |
| [spec/LONGECHO.md](spec/LONGECHO.md) | Tool specification |
| [spec/MANIFEST-SCHEMA.md](spec/MANIFEST-SCHEMA.md) | Manifest format for archives |
| [spec/TOOLKIT-ECOSYSTEM.md](spec/TOOLKIT-ECOSYSTEM.md) | List of ECHO-compliant toolkits |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/longecho/

# Linting
ruff check src/longecho/
```
