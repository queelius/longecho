---
title: ECHO Philosophy
---

# ECHO: Philosophy for Durable Personal Archives

**Version:** 1.0

ECHO is a philosophy for creating durable personal data archives. The name evokes what we're after: your voice, echoing forward through time.

## Core Principles

### 1. Self-Describing

Every data collection must explain itself. A human or LLM finding your data in 50 years, with no context, should be able to understand what they're looking at.

**The rule:** Include a `README.md` (or `README.txt`) at the root of every data collection.

The README should answer:

- What is this data?
- Who created it?
- When was it created/last updated?
- What format is the data in?
- How can someone explore it without special tools?

### 2. Durable Formats

Data must be stored in formats that:

- Can be read without proprietary software
- Have multiple implementations
- Are documented (formally or informally)
- Have proven longevity

**Preferred formats:**

| Category | Formats |
|----------|---------|
| Structured data | SQLite, JSON, JSONL |
| Documents | Markdown, plain text |
| Archives | ZIP (uncompressed or deflate) |
| Images | JPEG, PNG, WebP |
| Last resort | Plain ASCII text |

**Avoid:**

- Proprietary formats requiring specific software
- Binary formats without documentation
- Formats with single implementations
- Anything that requires a network to decode

### 3. Graceful Degradation

An archive should remain useful as technology disappears. Design for the worst case, then add convenience layers.

| If you have... | You can still... |
|----------------|------------------|
| Modern LLMs | Have conversations with the archive |
| Search/databases | Query and analyze structured data |
| A web browser | Navigate a beautiful website |
| A file browser | Explore organized directories |
| A text editor | Read plain text files |
| Paper and printer | Print and read physical copies |
| Only fragments | Understand each piece independently |

### 4. Local-First

The archive must work entirely offline. No cloud dependencies, no API calls required to access your own data.

Cloud services can sync, backup, or enhance — but the archive is complete without them.

### 5. Trust the Future

Don't over-engineer. Future humans will be smarter. Future LLMs will be more capable. Focus on preserving **content** and **context**, not building complex infrastructure.

If you have to choose between:

- A simple format that future tools can interpret
- A complex format that's "more correct"

Choose simple.

## ECHO Compliance

A data source is **ECHO-compliant** if it has:

1. A `README.md` or `README.txt` at the root explaining what the data is
2. Data stored in durable formats

That's it. No manifest files, no schema specifications, no version numbers, no special conventions.

## Examples

### ECHO-Compliant Conversation Archive

```
conversations/
├── README.md                 # What this is, how to explore it
├── conversations.db          # SQLite database
└── exports/
    ├── by-date/
    │   └── 2024-01/
    │       └── conversation-abc123.md
    └── all.jsonl
```

`README.md` contents:
```markdown
# Conversation Archive

Alex Towell's AI conversation history (ChatGPT, Claude, etc.)
Created: 2023-2024

## Format

SQLite database: conversations.db

Key tables:
- conversations: id, title, created, source
- messages: id, conversation_id, role, content, timestamp

## Exploring

Open with any SQLite browser, or:
  sqlite3 conversations.db "SELECT title FROM conversations LIMIT 10"

Human-readable exports in exports/
```

### ECHO-Compliant Blog

```
blog/
├── README.md
├── content/
│   ├── posts/
│   │   ├── 2024-01-15-hello-world.md
│   │   └── 2024-02-20-second-post.md
│   └── pages/
│       └── about.md
└── static/
    └── images/
```

### ECHO-Compliant Photo Archive

```
photos/
├── README.md
├── photos.db                 # SQLite with metadata
├── originals/               # Full-resolution photos
│   └── 2024/
│       └── 01/
│           └── IMG_1234.jpg
└── thumbnails/              # Quick preview
    └── 2024/
        └── 01/
            └── IMG_1234.jpg
```

## What ECHO Is Not

**ECHO is not software.** There's no `echo` command (well, except for longecho). It's a philosophy that any software can follow.

**ECHO is not a schema.** There's no required JSON structure, no mandatory fields. The README is the interface.

**ECHO is not a sync protocol.** It doesn't specify how to merge, replicate, or version data.

**ECHO is not a standard body.** There's no compliance certification, no governance, no committee.

## Why This Matters

Personal data is fragile. Companies shut down. Formats become obsolete. Passwords are forgotten. Hard drives fail.

ECHO is a bet that with enough self-description and simple formats, your data can outlive the tools that created it.

Your photos, your conversations, your writings, your bookmarks — these are the traces of a life. They deserve to last.

---

*"Trust the future."*
