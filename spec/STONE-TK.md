# stone-tk: Plain Text Distillation

**Version:** 0.1 (Draft Specification)
**Status:** Specification Only — No Implementation Yet

---

## Purpose

stone-tk generates the **most durable layer** of a personal archive: plain text files readable with nothing but eyes and basic literacy.

If every computer dies, if every format is forgotten, if only fragments survive — the STONE layer remains readable. This is your message in a bottle.

---

## Philosophy

STONE is the last line of defense. It assumes:
- No software exists to read special formats
- No context about the modern world
- A reader with basic literacy but nothing else

Given these constraints, STONE must be:
- **Pure text** — No markup, no formatting codes, no binary
- **Self-explaining** — Every file describes itself
- **Human-organized** — Logical structure a person can navigate
- **Essential** — Distilled to what matters most

---

## Standalone Toolkit

stone-tk is a **standalone toolkit**. It works independently and discovers sources by reading READMEs.

- **stone-tk defines its own discovery** — It finds sources by looking for READMEs
- **ECHO/longecho don't mediate** — stone-tk reads READMEs directly
- **Any ECHO-compliant source works** — If it has a README explaining the data, stone-tk can distill it

```
ECHO Sources                      stone-tk                      Output
┌─────────────────┐              ┌─────────────────┐           ┌────────────────┐
│ ctk/README.md   │─────────────→│                 │           │ stone/         │
│   (SQLite)      │              │ Read READMEs    │           │   README.txt   │
├─────────────────┤              │ Inspect data    │──────────→│   WHO-I-AM.txt │
│ blog/README.md  │─────────────→│ Distill essence │           │   MY-LIFE.txt  │
│   (Markdown)    │              │ Select essential│           │   essential/   │
├─────────────────┤              │ Generate text   │           │                │
│ photos/README.md│─────────────→│                 │           │                │
│   (SQLite+files)│              └─────────────────┘           └────────────────┘
└─────────────────┘
```

stone-tk doesn't have hardcoded handlers for ctk or Hugo. It:
1. Finds ECHO sources (by their READMEs)
2. Uses LLM assistance to understand each source
3. Extracts and distills the content
4. Generates pure text output

---

## Output Format

### stone/README.txt

What this archive is.

```text
================================================================
                    PERSONAL ARCHIVE
                     Alex Towell
                     1985 - 2024
================================================================

This is a plain text archive of one human life.

CONTENTS
--------
WHO-I-AM.txt         Identity and self-description
WHAT-I-BELIEVED.txt  Values, worldview, beliefs
MY-LIFE.txt          Timeline of major events
PEOPLE.txt           Important relationships
essential/           Selected writings and conversations

HOW TO READ THIS
----------------
These are plain text files. Open with any text editor, or
print them. Each file is self-contained and self-describing.
No special software is needed.

ABOUT THIS FORMAT
-----------------
This archive was created to survive format obsolescence,
software death, and civilizational discontinuity. If you
are reading this in the distant future with no context
about our time, everything you need is in these files.

Generated: January 2024
```

### stone/WHO-I-AM.txt

Identity in plain prose.

```text
================================================================
                      WHO I AM
================================================================

My name is Alex Towell.

I was born in 1985 in [place]. I am a mathematician and
software engineer. I care about ideas, about durability,
about the things that last.

WHAT I DO
---------
I write software. I write essays. I teach. I build tools
for thinking and remembering.

My work includes:
- Mathematical research in category theory
- Software tools for personal archiving
- Essays on technology and philosophy

WHAT MATTERS TO ME
------------------
Ideas. Craft. Honesty. The long view.

I believe that human knowledge has value beyond individual
lifetimes. I believe in building things that last. I believe
in trusting the future.

[...]
```

### stone/WHAT-I-BELIEVED.txt

Values and worldview.

```text
================================================================
                    WHAT I BELIEVED
================================================================

These are the ideas that shaped my thinking. They emerged
from conversations, writings, and the arc of my life.

CORE VALUES
-----------
Durability over convenience.
  The things we build should outlast us.

Simplicity over complexity.
  If you can say it simply, do.

Trust the future.
  Future people will be smart. Don't over-engineer.

[...]

ON [TOPIC]
----------
[Distilled views on major topics]

[...]
```

### stone/MY-LIFE.txt

Timeline of major events.

```text
================================================================
                      MY LIFE
================================================================

A timeline of the events that shaped me.

1985    Born in [place]
1990s   [Childhood events]
2003    Started university
2007    [Major event]
[...]
2024    Created this archive

ERAS
----
THE EARLY YEARS (1985-2003)
[Description]

THE LEARNING YEARS (2003-2010)
[Description]

[...]
```

### stone/PEOPLE.txt

Important relationships.

```text
================================================================
                       PEOPLE
================================================================

The people who mattered in my life.

FAMILY
------
[Name] - [Relationship]
  [Brief description of relationship]

[...]

FRIENDS
-------
[...]

COLLEAGUES
----------
[...]

MENTORS
-------
[...]
```

### stone/essential/

The most important content, selected and formatted for durability.

```
essential/
├── README.txt           # What's in this directory
├── writings/
│   ├── 01-[title].txt  # Key essays
│   ├── 02-[title].txt
│   └── ...
├── conversations/
│   ├── 01-[topic].txt  # Important conversations
│   └── ...
└── letters/
    ├── to-[person].txt # Significant correspondence
    └── ...
```

Each file in `essential/` is self-describing with a header explaining what it is and why it's included.

---

## Format Specification

### Text Encoding

- **Preferred:** ASCII (7-bit, universal)
- **Acceptable:** UTF-8 (for names, quotes in other languages)
- **Never:** UTF-16, other encodings

### Line Format

- Line width: 70 characters (readable on narrow screens, paper)
- Line endings: Unix (LF) preferred, Windows (CRLF) acceptable
- Paragraphs: Separated by blank line

### File Structure

```text
================================================================
                      TITLE IN CAPS
================================================================

Introduction paragraph.

SECTION HEADING
---------------
Section content.

ANOTHER SECTION
---------------
More content.

---

Footer or metadata.
```

### Conventions

- Headers: ALL CAPS, underlined with dashes or equals
- Emphasis: Use *asterisks* sparingly, or just clear prose
- Lists: Dash or asterisk prefix
- Dates: Written out (January 15, 2024) for clarity

---

## Selection Criteria

Not everything goes in STONE. This layer is distilled.

### Include

- Self-authored content (conversations, writings)
- Identity and values
- Major life events
- Important relationships
- Best/most representative work

### Exclude

- Raw data (leave that in DATA layer)
- Exhaustive lists (select highlights)
- Temporary or trivial content
- Others' words (except as context)
- Anything you wouldn't want surviving forever

### The Question

For each piece: *If only this survived, would it represent me well?*

---

## Commands (Planned)

```bash
# Discover ECHO sources and generate STONE layer
stone-tk generate ~/ --output ./stone/

# Discover sources, show what would be included
stone-tk discover ~/

# Generate from specific sources
stone-tk generate --sources ./ctk,./blog --output ./stone/

# Interactive selection of essential content
stone-tk select ./stone/essential/
```

---

## Processing Pipeline

### 1. Discover

Find ECHO-compliant sources by scanning for README.md files.

```bash
stone-tk discover ~/
# Found:
#   ~/github/ctk/       - AI conversations (SQLite)
#   ~/blog/content/     - Blog posts (Markdown)
#   ~/photos/           - Photo archive (SQLite + files)
```

### 2. Analyze

Read each README, inspect the data, build understanding.

For sources without explicit structure:
- Use LLM to read README and sample data
- Infer what content is available
- Map to STONE output categories

### 3. Distill

Extract essence from each source:
- Conversations → Key exchanges, characteristic voice
- Writings → Best essays, clearest statements
- Photos → Captions and descriptions (photos themselves go in PAPER layer)
- Timeline → Major events, eras

### 4. Generate

Produce plain text output:
- Synthesize identity files (WHO-I-AM, WHAT-I-BELIEVED, etc.)
- Select essential content
- Format for maximum durability
- Generate READMEs for each directory

---

## Why Plain Text?

| Format | Requires |
|--------|----------|
| Word docs | Proprietary software |
| PDF | PDF reader |
| HTML | Browser |
| Markdown | Markdown renderer (or accept raw) |
| JSON | Parser or technical knowledge |
| **Plain text** | **Eyes** |

Plain text is:
- The only format guaranteed readable by any future civilization
- Printable directly, no conversion
- Editable with anything
- Transmittable by any medium (even carved in stone)

---

## Relationship to Other Layers

STONE is one of several durability layers:

| Layer | Requires | Contains |
|-------|----------|----------|
| **STONE** | Eyes | Distilled essence in plain text |
| PAPER | Printer/eyes | Printable PDFs with photos |
| BROWSE | File browser | Organized directories, Markdown |
| WEB | Browser | Interactive website |
| DATA | Software | SQLite, embeddings, structured data |
| SOUL | LLM | Conversable persona |

STONE is the foundation. If everything else is lost, STONE remains.

---

## Related

- [ECHO.md](ECHO.md) — ECHO philosophy
- [PERSONA-TK.md](PERSONA-TK.md) — Persona toolkit (standalone)

---

*"Carve your message in stone."*
