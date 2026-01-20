# longecho

ECHO philosophy documentation and compliance validator.

## Status

**Incubating.** Specifications are being developed. No implementation yet.

## What This Is

longecho provides:

1. **Documentation** — Explains and motivates the ECHO philosophy
2. **Validator** — Checks if a directory is ECHO-compliant

## The ECHO Philosophy

ECHO is a philosophy for durable personal data:

- **Self-describing** — A `README.md` at the root explains what the data is
- **Durable formats** — SQLite, JSON, Markdown, plain text

A directory is ECHO-compliant if it has a README and uses durable formats. That's it.

See [spec/ECHO.md](spec/ECHO.md) for the full philosophy.

## Commands (Planned)

```bash
# Check if a directory is ECHO-compliant
longecho check ~/my-data/

# Find ECHO-compliant directories (optional)
longecho discover ~/

# Search README descriptions (optional)
longecho search ~/ "conversations"
```

## What longecho Is NOT

- **Not an orchestrator** — Toolkits invoke themselves
- **Not a format mediator** — Each toolkit defines its own interfaces
- **Not a registry** — Toolkits document their own compliance

## Documentation

| Document | What it covers |
|----------|----------------|
| [spec/ECHO.md](spec/ECHO.md) | ECHO philosophy |
| [spec/LONGECHO.md](spec/LONGECHO.md) | Validator specification |
| [spec/PERSONA-TK.md](spec/PERSONA-TK.md) | Persona toolkit spec (standalone) |
| [spec/STONE-TK.md](spec/STONE-TK.md) | Stone toolkit spec (standalone) |
| [spec/TOOLKIT-ECOSYSTEM.md](spec/TOOLKIT-ECOSYSTEM.md) | List of existing toolkits |
