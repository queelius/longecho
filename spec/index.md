# longecho

**ECHO philosophy documentation, compliance validator, and static site builder.**

---

## What Is This?

longecho is both a philosophy and a tool:

- **ECHO** is a philosophy for creating durable personal data archives that survive time
- **longecho** is a CLI tool that validates ECHO compliance and builds browsable sites

## Quick Start

```bash
# Check if a directory is ECHO-compliant
longecho check ~/my-data/

# Find ECHO sources under a path
longecho discover ~/

# Build a static site from an archive
longecho build ~/my-archive/

# Preview locally
longecho serve ~/my-archive/
```

## Documentation

| Document | Description |
|----------|-------------|
| [ECHO Philosophy](ECHO.md) | Core principles for durable archives |
| [longecho Tool](LONGECHO.md) | CLI commands and usage |
| [Manifest Schema](MANIFEST-SCHEMA.md) | Machine-readable metadata format |

## Toolkits

ECHO-compliant toolkits that work with longecho:

| Toolkit | Purpose |
|---------|---------|
| [Persona Toolkit](PERSONA-TK.md) | Persona synthesis from archives |
| [Stone Toolkit](STONE-TK.md) | Plain text distillation |
| [Ecosystem](TOOLKIT-ECOSYSTEM.md) | Full list of toolkits |

## Design Notes

See [Interview Insights](INTERVIEW-INSIGHTS.md) for design decisions and rationale.

---

*"The archive is not a monument. It is a conversation that outlasts its participants."*
