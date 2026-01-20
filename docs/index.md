---
title: longecho - ECHO Documentation and Validator
---

# longecho

**ECHO philosophy documentation and compliance validator.**

longecho provides two things:

1. **Documentation** — Explains and motivates the ECHO philosophy for durable personal archives
2. **Validator** — Checks if a directory is ECHO-compliant

## What is ECHO?

ECHO is a philosophy for creating durable personal data archives. It's not software, not a format, not a protocol — it's a set of principles that guide how to structure personal data so it survives time.

A directory is **ECHO-compliant** if it has:

1. A `README.md` or `README.txt` explaining what the data is
2. Data stored in durable formats (SQLite, JSON, Markdown, etc.)

That's it. No manifest files, no schema specifications, no version numbers.

## Quick Start

```bash
# Install longecho
pip install longecho

# Check if a directory is ECHO-compliant
longecho check ~/my-data/

# Find all ECHO sources under a path
longecho discover ~/

# Search README descriptions
longecho search ~/ "conversations"
```

## Why ECHO?

Personal data is fragile. Companies shut down. Formats become obsolete. Passwords are forgotten. Hard drives fail.

ECHO is a bet that with enough self-description and simple formats, your data can outlive the tools that created it.

Your photos, your conversations, your writings, your bookmarks — these are the traces of a life. They deserve to last.

## Documentation

- [ECHO Philosophy](echo-philosophy.md) — The full ECHO philosophy
- [Getting Started](getting-started.md) — Quick start guide
- [Validator](validator.md) — Using the compliance validator

## Principles

### Self-Describing

Every data collection explains itself. A human or LLM finding your data in 50 years should be able to understand what they're looking at.

### Durable Formats

Data is stored in formats that can be read without proprietary software: SQLite, JSON, Markdown, plain text.

### Graceful Degradation

An archive remains useful as technology disappears. Design for the worst case, then add convenience layers.

### Local-First

The archive works entirely offline. No cloud dependencies, no API calls required to access your own data.

### Trust the Future

Future humans will be smarter. Future LLMs will be more capable. Focus on preserving content and context, not building complex infrastructure.

---

*"The archive is not a monument. It is a conversation that outlasts its participants."*
