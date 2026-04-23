# longecho

**A philosophy and a tool for durable personal archives.**

---

## The Philosophy

Personal data is fragile. Companies shut down. Formats become obsolete. Passwords are forgotten. Hard drives fail.

longecho is a bet that with enough self-description and simple formats, your data can outlive the tools that created it. The name evokes what we're after: your voice, echoing forward through time.

### Core Principles

**1. Self-Describing.** Every data collection must explain itself. A human or LLM finding your data in 50 years, with no context, should be able to understand what they're looking at.

**2. Durable Formats.** Data must be stored in formats that can be read without proprietary software, have multiple implementations, and have proven longevity.

**3. Graceful Degradation.** An archive should remain useful as technology disappears:

| If you have... | You can still... |
|----------------|------------------|
| Modern LLMs | Have conversations with the archive |
| A web browser | Navigate a generated site |
| A file browser | Explore organized directories |
| A text editor | Read plain text files |
| Only fragments | Understand each piece independently |

**4. Local-First.** The archive must work entirely offline. Cloud services can sync or backup, but the archive is complete without them.

**5. Trust the Future.** Don't over-engineer. Future humans will be smarter. Future LLMs will be more capable. Focus on preserving content and context, not building complex infrastructure. If you have to choose between a simple format and a "more correct" one, choose simple.

---

## Compliance

A directory is **longecho-compliant** if it has:

1. A `README.md` or `README.txt` at the root explaining what the data is
2. Data stored in durable formats

That's it. No special files, no schema, no version numbers.

### Durable Formats

| Category | Formats |
|----------|---------|
| Structured data | `.db`, `.sqlite`, `.sqlite3`, `.json`, `.jsonl` |
| Documents | `.md`, `.markdown`, `.txt`, `.text`, `.rst`, `.html`, `.htm` |
| Archives | `.zip`, `.gz`, `.tgz` |
| Images | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` |
| Tabular / data | `.csv`, `.tsv`, `.xml`, `.yaml`, `.yml` |

Gzipped files are recognized by their terminal `.gz` suffix, so `.jsonl.gz`, `.csv.gz`, `.tar.gz`, and similar compounds all qualify. The `.tgz` form is the compact tar-gzip spelling.

The principle: formats that can be read without proprietary software, have multiple implementations, and are widely documented.

---

## The README

The README is the interface. A human or LLM can understand any longecho source by reading its README. Everything else is optional.

### Frontmatter

READMEs can include optional YAML frontmatter for structured metadata:

```markdown
---
name: Conversation Archive
description: AI conversation history from 2020-2026
author: Alex Towell
datetime: 2026-02-18
origin: Exported from ChatGPT and Claude
contents:
  - path: ctk.db
    description: SQLite database of all conversations
  - path: index.json
    description: Conversation index
---

# Conversation Archive

Six years of AI conversations, exported using ctk.
```

All frontmatter is optional. A README with no frontmatter is perfectly valid — the heading and first paragraph provide name and description, and the directory name is the fallback.

### Fields With Special Behavior

Three fields change how the longecho tool behaves:

| Field | Behavior |
|-------|----------|
| `name` | Used as the source name. Cascade: frontmatter `name` > `# Heading` > directory name |
| `description` | Used as the source description. Cascade: frontmatter `description` > first paragraph after heading |
| `contents` | Lists what's in this directory. The tool uses it for build curation and ordering (see below) |

### All Other Frontmatter

Any valid YAML can go in frontmatter. The tool preserves it, displays it in generated sites, and makes it queryable. Common fields worth including:

- `author` — who created this
- `datetime` — when
- `origin` — where the data came from
- `generator` — what tool produced this
- `tool` / `tool_url` — what program best understands this data

These aren't privileged — they're just commonly useful. Include whatever you think a future reader would find helpful. longecho parses what it recognizes; a human or LLM reads everything.

---

## Nesting

A longecho source can contain other longecho sources. The structure is recursive — each level is the same kind of object:

```
my-archive/
├── README.md
├── conversations/
│   ├── README.md
│   ├── chatgpt/
│   │   ├── README.md
│   │   └── data.db
│   └── claude/
│       ├── README.md
│       └── data.jsonl
└── bookmarks/
    ├── README.md
    └── bookmarks.jsonl
```

Every directory is self-describing. If the archive gets fragmented, each piece still explains itself.

### The `contents` Field

The `contents` field in frontmatter lists what's in a directory. It serves two purposes: it tells humans and LLMs what's here, and it controls how `longecho build` curates sub-sources.

```yaml
contents:
  - path: conversations/
  - path: bookmarks/
  - path: ctk.db
    description: Combined conversation database
```

Entries always use the explicit `path:` form. Additional fields like `description` are optional and informational.

When `contents` is present, `longecho build` uses it as follows:

- **Directory entries** (`conversations/`, `bookmarks/`) control **curation** and **ordering** of sub-sources. Only listed directories become navigable sub-sources in the build output, and they appear in the order listed.
- **File entries** (`ctk.db`) are **informational metadata**: they describe what's in the directory for humans and LLMs who read the README, but do not affect build structure. They are preserved in the frontmatter (where any reader can see them), but longecho does not surface them separately in the generated site.

When `contents` is absent, the tool auto-discovers all longecho-compliant subdirectories in alphabetical order, and all durable data files in the directory appear in the site's "Data Files" list.

Each sub-source is always self-describing. The parent's `contents` field controls which children appear and in what order, but never overrides a child's own name or description.

---

## The `site/` Convention

A `site/` directory provides a static, browsable representation of a source. This is a convenience layer — raw data must still exist alongside it.

Any tool MAY generate a `site/` for its data. `longecho build` generates one for the archive as a whole, but individual toolkits (ctk, btk, chartfold, etc.) can generate their own. The `site/` directory follows the same rules as any longecho source — self-describing via README.md.

```
my-archive/
├── README.md
├── conversations/
│   ├── README.md
│   ├── conversations.db
│   └── site/
│       ├── README.md      ← self-describing (generator: ctk)
│       └── index.html     ← ctk's conversation browser
├── bookmarks/
│   └── ...
└── site/
    ├── README.md          ← self-describing (generator: longecho)
    └── index.html         ← longecho's archive navigator
```

### Composition

The pattern is fractal: a parent SFA links to its children's sites. `longecho build` detects when a source has a `site/` and presents an "Open interactive viewer" link in the archive navigator. This means you can compose archives of archives — `longecho build` at any level produces a working SFA that connects to all the interfaces below it.

### Single-File Application

`longecho build` generates a self-contained `site/index.html` — a single-file application with all content, CSS, and JavaScript inlined. No external dependencies, no relative links to break. Single-file is recommended for all `site/` generators (maximum durability), but not required.

The SFA inlines all README content and metadata as JSON, with client-side JavaScript for navigation between views and search across sources. Actual data files (`.db`, `.json`, `.jsonl`, etc.) are linked via relative paths — the browser can open or download them directly. Because everything is self-contained or relative, the file works from `file://` — no server required.

### Self-Describing Output

The generated `site/` directory is itself longecho-compliant:

```markdown
---
name: My Archive Site
description: Static site generated from longecho archive
generator: longecho build v0.3.0
datetime: 2026-02-18T14:30:00
contents:
  - path: index.html
    description: Single-file browsable archive
---

Generated by longecho from 2 sources: conversations, bookmarks.
Open index.html in any browser to explore.
```

---

## What longecho Is Not

**Not a schema.** There's no required JSON structure, no mandatory fields beyond a README.

**Not a sync protocol.** It doesn't specify how to merge, replicate, or version data.

**Not a registry.** It doesn't maintain a central list of sources or toolkits.

**Not an orchestrator.** Each toolkit (ctk, btk, etc.) exports its own data. longecho unifies the outputs but doesn't invoke or manage the toolkits.

---

## Installation

```bash
pip install longecho
```

## Commands

Every command is a tree walk over the archive structure, with different filters and output modes.

```bash
longecho check ~/my-data/              # Is this compliant?
longecho check ~/my-data/ --verbose    # Show README, formats, frontmatter

longecho query ~/                      # Find sources across the tree
longecho query ~/ --search "bookmarks" # Search README text
longecho query ~/ --depth 1            # Control depth
longecho query ~/ --json               # Output as JSON

longecho build ~/my-archive/           # Generate single-file static site
longecho build ~/my-archive/ --open    # Open in browser after build

longecho spec                          # Print specification summary
longecho formats                       # List recognized durable formats
```

---

## Ecosystem

Tools that produce longecho-compliant data. Each is self-contained, works without longecho, and is documented in its own repo. Tagged members share the `longecho-ecosystem` GitHub topic.

| Tool | What it manages |
|------|-----------------|
| [memex](https://github.com/queelius/memex) | Conversation knowledge base |
| [chartfold](https://github.com/queelius/chartfold) | Personal health data |
| [repoindex](https://github.com/queelius/repoindex) | Git repo metadata |
| [jot](https://github.com/queelius/jot) | Plaintext journal/notes |
| [pagevault](https://github.com/queelius/pagevault) | Password-protected static content |
| arkiv | Universal personal data format (JSONL to SQL) |

Personal toolkits like `ctk` (conversations), `btk` (bookmarks), `ebk` (ebooks), and `mtk` (mail) also produce longecho-compliant data. They appear as illustrative examples throughout this README. The `site/` convention works with any tool that writes durable formats and a self-describing README.

Markdown-based sources (Hugo, Jekyll, Obsidian, etc.) are inherently longecho-compliant.

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/ --cov=src/longecho --cov-report=term-missing
mypy src/longecho/
ruff check src/longecho/
```

---

*"The archive is not a monument. It is a conversation that outlasts its participants."*
