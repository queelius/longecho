# longecho: ECHO Documentation, Validator, and Site Builder

**Version:** 0.2.0
**Status:** Alpha

---

## What longecho Is

longecho provides:

1. **Documentation** — Explains and motivates the ECHO philosophy
2. **Validator** — Checks if a directory is ECHO-compliant
3. **Discovery** — Finds and searches ECHO sources
4. **Site Builder** — Generates unified static sites from archives
5. **Dev Server** — Previews archives via HTTP

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
#   ✓ ECHO-compliant: /home/user/my-data
```

```bash
# Non-compliant directory
longecho check ~/random-folder/

# Output:
#   ✗ Not ECHO-compliant: /home/user/random-folder
#     Reason: No README.md or README.txt found
```

Use `--verbose` for detailed output showing README location and detected formats.

### Discover Sources

```bash
# Find ECHO-compliant directories under a path
longecho discover ~/

# Output:
#   Found 3 ECHO source(s):
#
#   ~/.local/share/ctk/
#     AI conversation history
#     Formats: .db, .json
#
#   ~/blog/content/
#     Personal blog
#     Formats: .md
```

Use `--table` for tabular output, `--max-depth` to limit recursion.

### Search Sources

```bash
# Search README descriptions
longecho search ~/ "conversations"

# Output:
#   Found 1 matching source(s):
#
#   ~/.local/share/ctk/
#     AI conversation history
```

### Source Info

```bash
# Detailed information about a source
longecho info ~/.local/share/ctk/

# Output shows README, formats, and summary
```

### List Formats

```bash
# Show recognized durable formats
longecho formats

# Lists: Structured data, Documents, Archives, Images, Data
```

### Build Static Site

```bash
# Generate unified static site from archive(s)
longecho build ~/my-archive/

# Output:
#   Building site for: /home/user/my-archive
#   ✓ Built site with 3 source(s)
#     Output: /home/user/my-archive/site
```

The build command:

- Reads `manifest.json` or `manifest.yaml` if present
- Auto-discovers sub-archives (manifest overrides auto-discovery)
- For sources with `site/`: links by default, copies with `--bundle`
- Generates index pages with navigation between sources
- Output: `site/` directory with `index.html`

**Flags:**

| Flag | Description |
|------|-------------|
| `--bundle` | Copy all sub-sites into unified site (portable) |
| `--deep` | Aggressive discovery mode |
| `--output` | Custom output directory (default: `site/`) |

### Serve Archive

```bash
# Serve archive via HTTP for local preview
longecho serve ~/my-archive/ --port 8000

# Output:
#   Building site for: /home/user/my-archive
#   Built site with 3 source(s)
#   Serving at http://localhost:8000
#   Press Ctrl+C to stop
```

The serve command:

- Runs `longecho build` if `site/` doesn't exist
- Serves the `site/` directory via HTTP
- Use `--no-build` to skip automatic building
- Use `--open` to open browser automatically

---

## Boundaries

**longecho unifies, but doesn't orchestrate toolkits.** Each toolkit (ctk, btk, etc.) exports its own ECHO-compliant archive. longecho's `build` command combines these into a unified browsable site, but doesn't invoke or manage the toolkits themselves.

**longecho doesn't mediate formats.** There is no central interchange format. Each toolkit defines its own input/output formats.

**longecho doesn't maintain a registry.** If a toolkit is ECHO-compliant, its own README documents that fact.

---

## Design Principles

### 1. Each Source Manages Itself

ctk has its own README explaining its format. btk has its own README. longecho checks for READMEs but doesn't need to understand the underlying data.

### 2. Toolkits Define Their Own Interfaces

persona-tk defines what input it accepts. stone-tk discovers sources by reading READMEs. There's no central specification that bridges them.

### 3. READMEs Are the Interface

A human or LLM can understand an ECHO source by reading its README. Manifests are optional machine-readable metadata, not required.

### 4. Graceful Degradation

An ECHO archive works without longecho. longecho adds convenience (site generation, discovery) but the archive is self-contained.

---

## Related

- [ECHO.md](ECHO.md) — The ECHO philosophy
- [MANIFEST-SCHEMA.md](MANIFEST-SCHEMA.md) — Manifest format specification
- [PERSONA-TK.md](PERSONA-TK.md) — Persona toolkit (standalone)
- [STONE-TK.md](STONE-TK.md) — Plain text distillation toolkit (standalone)
- [TOOLKIT-ECOSYSTEM.md](TOOLKIT-ECOSYSTEM.md) — List of existing toolkits

---

*"The archive is not a monument. It is a conversation that outlasts its participants."*
