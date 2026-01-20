---
title: Validator Reference
---

# longecho Validator Reference

longecho is the ECHO compliance validator. It checks if directories follow the ECHO philosophy for durable personal archives.

## Compliance Rules

A directory is **ECHO-compliant** if:

1. It has a `README.md` or `README.txt` at the root
2. It contains data in durable formats

### Durable Formats

longecho recognizes these file extensions as durable:

**Structured data:**
- `.db`, `.sqlite`, `.sqlite3` — SQLite databases
- `.json`, `.jsonl` — JSON and JSON Lines

**Documents:**
- `.md`, `.markdown` — Markdown
- `.txt`, `.text` — Plain text
- `.rst` — reStructuredText

**Archives:**
- `.zip` — ZIP archives

**Images:**
- `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`

**Data:**
- `.csv`, `.tsv` — Tabular data
- `.xml` — XML
- `.yaml`, `.yml` — YAML

## Commands

### check

Check if a directory is ECHO-compliant.

```bash
longecho check <path> [--verbose/-v]
```

**Arguments:**
- `path` — Directory to check

**Options:**
- `--verbose, -v` — Show detailed information

**Exit codes:**
- `0` — Directory is ECHO-compliant
- `1` — Directory is not ECHO-compliant

**Examples:**

```bash
# Basic check
longecho check ~/my-archive/

# Verbose output
longecho check ~/my-archive/ -v
```

**Output (compliant):**
```
✓ ECHO-compliant: /home/user/my-archive
```

**Output (compliant, verbose):**
```
✓ ECHO-compliant: /home/user/my-archive

  README: README.md
  Summary: Personal data archive containing...
  Durable formats: .db, .json, .md
  Other formats: .ini
```

**Output (non-compliant):**
```
✗ Not ECHO-compliant: /home/user/my-archive
  Reason: No README.md or README.txt found
```

### discover

Find all ECHO-compliant directories under a root path.

```bash
longecho discover <path> [--max-depth/-d N] [--table/-t]
```

**Arguments:**
- `path` — Root directory to scan

**Options:**
- `--max-depth, -d` — Maximum directory depth to scan
- `--table, -t` — Output as a table

**Examples:**

```bash
# Find all ECHO sources
longecho discover ~/

# Limit depth
longecho discover ~/ --max-depth 3

# Table format
longecho discover ~/ --table
```

**Output:**
```
Found 3 ECHO source(s):

/home/user/.local/share/ctk/
  AI conversation history
  Formats: .db, .json

/home/user/blog/content/
  Personal blog
  Formats: .md

/home/user/bookmarks/
  Bookmark collection
  Formats: .db, .jsonl
```

### search

Search ECHO sources by README content.

```bash
longecho search <path> <query> [--max-depth/-d N]
```

**Arguments:**
- `path` — Root directory to search
- `query` — Search string (case-insensitive)

**Options:**
- `--max-depth, -d` — Maximum directory depth to scan

**Examples:**

```bash
# Search for sources mentioning "conversations"
longecho search ~/ "conversations"

# Search with depth limit
longecho search ~/ "photos" --max-depth 2
```

**Output:**
```
Found 1 matching source(s):

/home/user/.local/share/ctk/
  AI conversation history from ChatGPT and Claude
```

### info

Show detailed information about an ECHO source.

```bash
longecho info <path>
```

**Arguments:**
- `path` — ECHO source directory

**Examples:**

```bash
longecho info ~/.local/share/ctk/
```

**Output:**
```
╭─────────────────── ECHO Source ───────────────────╮
│ Path: /home/user/.local/share/ctk                 │
│ README: README.md                                 │
│ Summary: AI conversation history from ChatGPT... │
│ Durable formats: .db, .json, .md                  │
│ Other formats: .ini                               │
╰───────────────────────────────────────────────────╯
```

### formats

List recognized durable formats.

```bash
longecho formats
```

**Output:**
```
ECHO Durable Formats

Structured data:
  .db, .sqlite, .sqlite3, .json, .jsonl

Documents:
  .md, .markdown, .txt, .text, .rst

Archives:
  .zip

Images:
  .jpg, .jpeg, .png, .webp, .gif

Data:
  .csv, .tsv, .xml, .yaml, .yml
```

## Python API

longecho can also be used as a Python library.

### check_compliance

```python
from longecho import check_compliance
from pathlib import Path

result = check_compliance(Path("~/my-archive"))

if result.compliant:
    print(f"Compliant! Formats: {result.durable_formats}")
else:
    print(f"Not compliant: {result.reason}")
```

### discover_sources

```python
from longecho import discover_sources
from pathlib import Path

for source in discover_sources(Path("~/")):
    print(f"{source.path}: {source.readme_summary}")
    print(f"  Formats: {source.durable_formats}")
```

### Data Classes

**ComplianceResult:**
```python
@dataclass
class ComplianceResult:
    compliant: bool
    path: Path
    readme_path: Optional[Path]
    readme_summary: Optional[str]
    formats: List[str]
    durable_formats: List[str]
    reason: Optional[str]
```

**EchoSource:**
```python
@dataclass
class EchoSource:
    path: Path
    readme_path: Path
    readme_summary: Optional[str]
    formats: List[str]
    durable_formats: List[str]
```

## Integration with Toolkits

Several toolkits support ECHO export:

- **ctk** — `ctk export ~/export/ --format echo`
- **btk** — `btk export ~/export/ --format echo`
- **ebk** — `ebk export echo ~/library ~/export/`

After exporting, verify compliance:

```bash
longecho check ~/export/
```
