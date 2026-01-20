---
title: Getting Started
---

# Getting Started with longecho

This guide helps you get started with longecho, the ECHO compliance validator.

## Installation

Install longecho using pip:

```bash
pip install longecho
```

Or install from source:

```bash
git clone https://github.com/alextowell/longecho.git
cd longecho
pip install -e .
```

## Quick Start

### Check a Directory

The most common operation is checking if a directory is ECHO-compliant:

```bash
longecho check ~/my-data/
```

If compliant, you'll see:
```
✓ ECHO-compliant: /home/user/my-data
```

If not compliant:
```
✗ Not ECHO-compliant: /home/user/my-data
  Reason: No README.md or README.txt found
```

Use `-v` for verbose output:

```bash
longecho check ~/my-data/ -v
```

### Discover ECHO Sources

Find all ECHO-compliant directories under a path:

```bash
longecho discover ~/
```

Output:
```
Found 3 ECHO source(s):

~/.local/share/ctk/
  AI conversation history
  Formats: .db, .json

~/blog/content/
  Personal blog
  Formats: .md

~/bookmarks/
  Bookmark collection
  Formats: .db, .jsonl
```

Use `--table` for a tabular view:

```bash
longecho discover ~/ --table
```

### Search Sources

Search README descriptions across all ECHO sources:

```bash
longecho search ~/ "conversations"
```

This finds any ECHO-compliant directory whose README contains "conversations".

## Making Your Data ECHO-Compliant

To make a directory ECHO-compliant, you need:

1. **A README file** — `README.md` or `README.txt` at the root
2. **Durable data formats** — SQLite, JSON, Markdown, etc.

### Example: Creating an ECHO-Compliant Export

Say you have some data you want to archive. Here's how to make it ECHO-compliant:

```bash
mkdir my-archive
cd my-archive

# Create your data file
echo '{"items": [1, 2, 3]}' > data.json

# Create a README explaining the data
cat > README.md << 'EOF'
# My Archive

Personal data archive.
Created: 2024-01-15

## Format

JSON file: data.json

Contains a list of items.

## Exploring

Open data.json in any text editor or JSON viewer.
EOF

# Verify compliance
longecho check .
```

### README Best Practices

Your README should answer:

1. **What is this?** — Brief description of the data
2. **Who created it?** — Attribution
3. **When?** — Creation/update dates
4. **Format** — What files exist and their structure
5. **How to explore** — Commands or tools to read the data

Example:

```markdown
# Conversation Archive

Alex Towell's AI conversation history.
Created: 2023-2024

## Format

- conversations.db — SQLite database
- index.json — List of all conversations

### Database Schema

Tables:
- conversations: id, title, created, source
- messages: id, conversation_id, role, content

## Exploring

sqlite3 conversations.db "SELECT title FROM conversations LIMIT 10"
```

## Durable Formats

longecho recognizes these as durable formats:

| Category | Extensions |
|----------|------------|
| Structured data | .db, .sqlite, .sqlite3, .json, .jsonl |
| Documents | .md, .markdown, .txt, .text, .rst |
| Archives | .zip |
| Images | .jpg, .jpeg, .png, .webp, .gif |
| Data | .csv, .tsv, .xml, .yaml, .yml |

List all recognized formats:

```bash
longecho formats
```

## Command Reference

| Command | Description |
|---------|-------------|
| `longecho check <path>` | Check if directory is ECHO-compliant |
| `longecho discover <path>` | Find all ECHO sources under path |
| `longecho search <path> <query>` | Search README descriptions |
| `longecho info <path>` | Show detailed info about a source |
| `longecho formats` | List recognized durable formats |
| `longecho --version` | Show version |

## Next Steps

- Read the [ECHO Philosophy](echo-philosophy.md) for the full philosophy
- See [Validator](validator.md) for detailed command reference
- Check out toolkits that export ECHO-compliant data:
  - **ctk** — Conversation toolkit
  - **btk** — Bookmark toolkit
  - **ebk** — E-book library manager
