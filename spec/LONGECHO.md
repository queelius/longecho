# longecho: ECHO Documentation and Validator

**Version:** 0.3 (Draft Specification)
**Status:** Incubating

---

## What longecho Is

longecho provides two things:

1. **Documentation** — Explains and motivates the ECHO philosophy
2. **Validator** — Checks if a directory is ECHO-compliant

That's it. longecho is not an orchestrator, not a format mediator, not a registry.

---

## The ECHO Philosophy

ECHO is a philosophy for durable personal data:

1. **Self-describing** — A `README.md` at the root explains what the data is
2. **Durable formats** — SQLite, JSON, Markdown, plain text

See [ECHO.md](ECHO.md) for the full philosophy.

A directory is **ECHO-compliant** if it has:
- A `README.md` or `README.txt` at the root
- Data in durable formats

---

## Commands

### Check Compliance

```bash
# Is this directory ECHO-compliant?
longecho check ~/my-data/

# Output:
#   ✓ README.md exists
#   ✓ Durable formats: SQLite (data.db), Markdown (*.md)
#   → ECHO-compliant
```

```bash
# Non-compliant directory
longecho check ~/random-folder/

# Output:
#   ✗ No README.md or README.txt found
#   → Not ECHO-compliant
```

### Discover Sources (Optional)

```bash
# Find ECHO-compliant directories under a path
longecho discover ~/

# Output:
#   ~/.local/share/ctk/
#     README says: AI conversation history
#     Format: SQLite
#
#   ~/blog/content/
#     README says: Personal blog
#     Format: Markdown
```

### Search Across Sources (Optional)

```bash
# Search README descriptions
longecho search ~/ "conversations"

# Output:
#   ~/.local/share/ctk/ — "AI conversation history"
```

---

## What longecho Is NOT

**Not an orchestrator.** Toolkits invoke themselves. `ctk export` runs ctk, not longecho.

**Not a format mediator.** There is no central interchange format. If persona-tk needs JSONL, persona-tk defines that in its own spec.

**Not a registry.** ECHO.md doesn't list which toolkits are compliant. If a toolkit is ECHO-compliant, its own README says so.

**Not a synthesis wrapper.** To run stone-tk, run stone-tk. longecho doesn't wrap it.

---

## Design Principles

### 1. Each Source Manages Itself

ctk has its own README explaining its format. btk has its own README. longecho doesn't need to know about them — it just checks if READMEs exist.

### 2. Toolkits Define Their Own Interfaces

persona-tk defines what input it accepts. stone-tk discovers sources by reading READMEs. There's no central specification that bridges them.

### 3. Minimal Scope

longecho is documentation + a validator. Nothing more. This keeps it from becoming a single point of failure or a bottleneck for evolution.

### 4. READMEs Are the Interface

A human or LLM can understand an ECHO source by reading its README. No schemas, no manifests, no special protocols.

---

## Optional Convenience Commands

longecho may provide hardcoded convenience operations for common tasks:

```bash
# Show what ECHO sources you have
longecho status ~/

# Quick overview of an ECHO source
longecho info ~/.local/share/ctk/
```

These are conveniences, not orchestration. They just read READMEs and report.

---

## Related

- [ECHO.md](ECHO.md) — The ECHO philosophy
- [PERSONA-TK.md](PERSONA-TK.md) — Persona toolkit (standalone)
- [STONE-TK.md](STONE-TK.md) — Plain text distillation toolkit (standalone)
- [TOOLKIT-ECOSYSTEM.md](TOOLKIT-ECOSYSTEM.md) — List of existing toolkits

---

*"The archive is not a monument. It is a conversation that outlasts its participants."*
