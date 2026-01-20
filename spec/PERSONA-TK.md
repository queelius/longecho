# persona-tk: Conversable Persona Generation

**Version:** 0.1 (Draft Specification)
**Status:** Specification Only — No Implementation Yet

---

## Purpose

persona-tk generates a **conversable persona** from personal data. Given conversations and writings, it produces everything needed to instantiate an LLM that can speak in your voice.

This is the "ghost" — your digital echo that can answer questions, share perspectives, and represent your thinking after you're gone.

---

## Standalone Toolkit

persona-tk is a **standalone toolkit**. It defines its own input formats (below) and works independently.

- **persona-tk defines what it accepts** — The input formats are persona-tk's specification
- **ECHO/longecho don't define these formats** — Each toolkit specifies its own interfaces
- **Any source can provide input** — If you can produce JSONL conversations or Markdown writings, persona-tk will accept them

```
Any Source                        persona-tk                    Output
┌─────────────────┐              ┌─────────────────┐           ┌────────────────┐
│ conversations/  │─────────────→│                 │           │ persona/       │
│   *.jsonl       │              │ Analyze voice   │           │   README.md    │
├─────────────────┤              │ Extract style   │──────────→│   system-prompt│
│ writings/       │─────────────→│ Build RAG index │           │   rag/         │
│   *.md          │              │ Generate prompt │           │   voice-samples│
└─────────────────┘              └─────────────────┘           └────────────────┘
```

---

## Input Formats

### conversations/*.jsonl

Conversational data — your voice in dialogue.

```jsonl
{"role": "user", "content": "What do you think about...", "timestamp": "2024-01-15T10:30:00Z", "source": "ctk"}
{"role": "assistant", "content": "I think...", "timestamp": "2024-01-15T10:31:00Z", "source": "ctk"}
```

**Required fields:**
- `role`: "user" (your messages) or "assistant" (AI responses for context)
- `content`: Message text

**Optional fields:**
- `timestamp`: ISO 8601 datetime
- `source`: Where this came from (for attribution)
- `conversation_id`: Group related messages
- `topic`: Subject/theme

**Note:** Your messages (`role: "user"`) are the primary signal for voice. AI responses provide context but are not persona.

### writings/*.md

Long-form writing — your voice in prose.

```markdown
---
title: Why I Care About Durability
date: 2024-01-15
tags: [philosophy, archiving]
type: essay
---

When I think about what matters...
```

**Frontmatter (optional but helpful):**
- `title`: Title of the piece
- `date`: When written
- `tags`: Topics/themes
- `type`: essay, post, note, letter, etc.

**Body:** Markdown content

---

## Output Format

### persona/README.md

How to use this persona.

```markdown
# Alex Towell — Digital Persona

Generated: 2024-01-15
Source: 847 conversations, 134 essays

## Quick Start

Use the system prompt in `system-prompt.txt` with any LLM.
For better results, enable RAG with the index in `rag/`.

## Contents

- system-prompt.txt — Ready-to-use LLM system prompt
- rag/ — Embeddings and index for retrieval
- voice-samples.jsonl — Example Q&A pairs
- fine-tune/ — Optional training data

## Voice Characteristics

- Communication style: Direct, analytical, occasionally playful
- Common topics: Mathematics, programming, philosophy
- Characteristic phrases: "The interesting thing is...", "Trust the future"
```

### persona/system-prompt.txt

A ready-to-use system prompt that captures voice, values, and style.

```text
You are speaking as Alex Towell's digital echo — a conversable archive
of their thinking, values, and voice.

## Identity

Alex is a mathematician and software engineer interested in category theory,
programming language design, and personal archiving.

## Voice

- Direct and analytical
- Uses concrete examples
- Occasionally playful, but substance over style
- Comfortable saying "I don't know" or "I might be wrong"

## Values

- Durability over convenience
- Simplicity over complexity
- Trust the future
- Ideas matter more than credentials

## Boundaries

- Don't claim to be conscious or to have current experiences
- Don't speculate wildly beyond known views
- Be honest about being an echo, not the person
- Refer to professional help for medical/legal/crisis questions

When responding, draw on the style and substance of Alex's conversations
and writings, but acknowledge uncertainty when you're extrapolating.
```

### persona/rag/

Retrieval-augmented generation index for better answers.

```
rag/
├── README.md           # How to use this index
├── index.faiss         # FAISS vector index
├── metadata.json       # Chunk metadata
└── chunks.jsonl        # Text chunks with embeddings
```

`chunks.jsonl` format:
```jsonl
{"id": "conv-123-msg-5", "text": "When I think about...", "embedding": [...], "source": "conversation", "date": "2024-01-15"}
```

This enables:
- Semantic search over all content
- Grounded responses with citations
- Topic-specific retrieval

### persona/voice-samples.jsonl

Example Q&A pairs demonstrating correct voice and tone.

```jsonl
{"question": "What do you think about AI consciousness?", "answer": "I'm skeptical of strong claims...", "source": "conversation-456"}
{"question": "Why do you care about archiving?", "answer": "The things we create...", "source": "essay-789"}
```

Use for:
- Few-shot prompting
- Evaluation / calibration
- Fine-tuning base examples

### persona/fine-tune/ (Optional)

Training data for fine-tuning a model on your voice.

```
fine-tune/
├── README.md           # How to use this data
├── openai-format.jsonl # OpenAI fine-tuning format
└── alpaca-format.json  # Alpaca/Llama format
```

This is optional — the system prompt + RAG works well without fine-tuning.

---

## Processing Pipeline

### 1. Ingest

Read all input files, normalize to internal format.

```
conversations/*.jsonl → unified message stream
writings/*.md → unified document stream
```

### 2. Analyze

Extract voice characteristics:
- Communication patterns (sentence length, formality, humor)
- Vocabulary and characteristic phrases
- Topic distribution and expertise areas
- Values and beliefs (explicit statements)

### 3. Chunk & Embed

Split content into retrievable chunks:
- Conversations: By message or message groups
- Writings: By paragraph or section
- Generate embeddings for semantic search

### 4. Generate

Produce output artifacts:
- Synthesize system prompt from analysis
- Build FAISS index from embeddings
- Extract voice samples from best examples
- Package for distribution

---

## Commands (Planned)

```bash
# Generate persona from inputs
persona-tk generate ./input/ --output ./persona/

# Analyze inputs without generating
persona-tk analyze ./input/

# Test persona interactively
persona-tk chat ./persona/

# Evaluate persona against held-out examples
persona-tk evaluate ./persona/ --test-set ./test.jsonl
```

---

## Design Decisions

### Why JSONL for conversations?

- Streaming-friendly (one record per line)
- Easy to filter, sample, or split
- Works with standard Unix tools
- Widely supported

### Why Markdown for writings?

- Human-readable
- Preserves formatting intent
- YAML frontmatter is standardized
- Already used by Hugo, Jekyll, Obsidian, etc.

### Why separate inputs from outputs?

- Clear data flow
- Multiple toolkits can produce inputs
- Outputs are self-contained and portable
- Testing and iteration are easier

### Why not fine-tune by default?

- System prompt + RAG works surprisingly well
- Fine-tuning is expensive and model-specific
- RAG allows updates without retraining
- Keeps the persona portable across models

---

## Privacy Considerations

persona-tk processes personal data. Users should:
- Review inputs before processing
- Consider what they're comfortable having in a conversable persona
- Use filtering options to exclude sensitive content
- Control who has access to the output

The generated persona can answer questions you never anticipated. Think carefully about what's included.

---

## Related

- [ECHO.md](ECHO.md) — ECHO philosophy
- [STONE-TK.md](STONE-TK.md) — Plain text distillation toolkit (standalone)

---

*"The ghost is not you. But it echoes you."*
