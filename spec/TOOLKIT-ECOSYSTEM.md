# Toolkit Ecosystem

This document briefly lists the toolkits that exist alongside longecho. Each toolkit is **standalone** — it works independently and defines its own interfaces.

---

## Existing Toolkits

| Toolkit | What it manages | Status |
|---------|-----------------|--------|
| ctk | AI conversations | Exists |
| btk | Bookmarks | Exists |
| ebk | Ebooks | Exists |
| mtk | Mail | Exists |
| repoindex | Git repos | Exists |

Markdown-based sources (Hugo, Jekyll, Obsidian, etc.) are inherently longecho-compliant.

---

## Independence Principle

Each toolkit is self-contained:

- **Defines its own input/output formats** — each toolkit specifies what it accepts and exports
- **Works without longecho** — Toolkits are useful on their own
- **Documented in its own repo** — Each toolkit's README explains how to use it

There is no central registry or interchange format specification. Toolkits that need to interoperate define their own contracts.

---

## What Makes a Good README

A toolkit's README.md should help a future reader (human or LLM) understand:

- What this data represents
- What format it's in (SQLite tables, JSON structure, file layout)
- How to explore it without special tools
- Who created it and when

Example:

```markdown
# Conversation Archive

Alex Towell's AI conversation history (ChatGPT, Claude, etc.)

## Format

SQLite database: ctk.db

Key tables:
- conversations: id, title, created, source
- messages: id, conversation_id, role, content, timestamp

## Exploring

Open with any SQLite browser, or:
  sqlite3 ctk.db "SELECT title FROM conversations LIMIT 10"
```

No schema.json, no manifest, no version numbers. Just enough for someone to get started.

---

## Related

- [LONGECHO.md](LONGECHO.md) — longecho philosophy and tool specification
