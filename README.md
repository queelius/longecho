# longecho

A philosophy and a tool for durable personal archives.

## Status

**Alpha.** Spec v2 written. Implementation being updated to match.

## The Philosophy

Personal data is fragile. Companies shut down. Formats become obsolete. Hard drives fail.

longecho is a bet that with enough self-description and simple formats, your data can outlive the tools that created it. The name evokes what we're after: your voice, echoing forward through time.

A directory is **longecho-compliant** if it has:

1. A `README.md` or `README.txt` explaining what the data is
2. Data in durable formats (SQLite, JSON, Markdown, plain text, etc.)

That's it. No special files, no schema. The README is the interface. Optional YAML frontmatter adds structured metadata that the tool can parse, but freeform prose works just as well for humans and LLMs.

## Installation

```bash
pip install longecho
```

## Commands

```bash
longecho check ~/my-data/              # Is this compliant?
longecho query ~/                      # Find sources across the tree
longecho query ~/ --author "Alex"      # Filter by any frontmatter field
longecho query ~/ --search "bookmarks" # Search README text
longecho build ~/my-archive/           # Generate single-file static site
longecho formats                       # List recognized durable formats
```

## How It Works

Every longecho archive is a tree of self-describing directories. Each directory has a README, optionally with YAML frontmatter:

```markdown
---
name: Conversation Archive
description: AI conversation history
author: Alex Towell
contents:
  - path: chatgpt/
  - path: claude/
---

# Conversation Archive

Six years of AI conversations.
```

The structure is recursive — each sub-directory is the same kind of object. If the archive gets fragmented, each piece still explains itself.

`longecho build` walks the tree bottom-up and generates a single self-contained HTML file. README content and metadata are inlined; data files are linked via relative paths. Open it directly in a browser — no server needed.

## Design Decisions

**README is the only metadata source.** No manifest files. Frontmatter in the README is the single source of truth for structured metadata.

**No parent overrides.** A source's name and description always come from its own README, ensuring consistency regardless of context.

**Single-file application.** Build output is one HTML file with all content inlined and data files linked via relative paths. More durable than a directory of cross-linked files.

**Trust the future.** Don't over-engineer. Future humans and LLMs will be smarter. Focus on preserving content and context, not building complex infrastructure.

## Documentation

| Document | Description |
|----------|-------------|
| [spec/LONGECHO.md](spec/LONGECHO.md) | Full specification (philosophy + tool) |
| [spec/TOOLKIT-ECOSYSTEM.md](spec/TOOLKIT-ECOSYSTEM.md) | Standalone toolkits that produce longecho-compliant data |

## Development

```bash
pip install -e ".[dev,full]"
pytest tests/ -v
pytest tests/ --cov=src/longecho --cov-report=term-missing
mypy src/longecho/
ruff check src/longecho/
```
