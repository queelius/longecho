# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Status

**longecho is specification-only.** No implementation exists yet.

## What longecho Is

longecho provides:

1. **Documentation** — Explains and motivates the ECHO philosophy
2. **Validator** — Checks if a directory is ECHO-compliant (`longecho check`)

That's it. longecho is not an orchestrator, not a format mediator, not a registry.

## What longecho Is NOT

- **Not an orchestrator** — Toolkits (ctk, btk, persona-tk, stone-tk) invoke themselves
- **Not a format mediator** — Each toolkit defines its own input/output formats
- **Not a registry** — Each toolkit's own README documents its compliance

## Key Principles

1. **ECHO philosophy** — Self-describing data with README.md + durable formats
2. **Minimal scope** — longecho is docs + validator only
3. **Standalone toolkits** — persona-tk and stone-tk work independently

## Documentation Structure

```
spec/
├── ECHO.md              # ECHO philosophy (standalone)
├── LONGECHO.md          # Validator specification
├── PERSONA-TK.md        # Persona toolkit spec (standalone)
├── STONE-TK.md          # Stone toolkit spec (standalone)
├── TOOLKIT-ECOSYSTEM.md # List of existing toolkits
└── INTERVIEW-INSIGHTS.md # Design decisions
```

## Expected Commands (When Implemented)

```bash
longecho check ~/path    # Is this directory ECHO-compliant?
longecho discover ~/     # Find ECHO-compliant directories
longecho search ~/       # Search README descriptions
```

## Expected Tech Stack

- Python 3.8+
- pytest for testing
- black/flake8/mypy for code quality
- Typer for CLI
