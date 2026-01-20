# longecho — Interview Insights

This document captures key design decisions from an in-depth interview (2026-01).

---

## Core Philosophy Confirmed

### Trust the Future

A consistent theme: don't over-engineer for future scenarios. The archive's job is to preserve content; future systems (LLMs, tools, humans) will figure out how to use it.

Implications:
- Skip complex verification infrastructure
- Don't pre-annotate for semantic decay — future LLMs can explain context
- Don't build elaborate persona extraction — raw conversations ARE the persona
- Don't worry about LLM prompt format changes — future models will be smarter

### Single Unified Archive

No audience tiers. One archive for everyone (family, researchers, public). Simplicity over audience-tailoring.

### Your Archive, Your Call

No consent model for photos/content featuring others. This is a personal archive, not a collaborative one.

---

## The True MVP

**Get conversations exported in durable format.** That's it.

Specifically:
- JSON primary (full tree structure)
- Markdown secondary (human-readable, latest path)
- Maybe include SQLite if not too large
- Raw conversations ARE the persona — skip explicit persona extraction for MVP

This is dramatically simpler than the full spec suggests. Everything else is enhancement.

---

## Key Design Decisions

### Temporal Identity

**Latest version wins.** When the ghost answers "what do you think about X", it represents current (most recent) views. Earlier views are context, not authoritative.

The ghost should have meta-awareness of intellectual history, but speak as current-you.

### Imperfection Handling

**Include everything, let the ghost handle it gracefully.** Don't curate out mistakes or embarrassing moments. Trust the ghost to acknowledge past errors naturally: "I used to think X, but later realized..."

### AI Dialogue Representation

Keep full conversations including AI responses. But:
- The persona is YOUR messages only
- AI responses provide necessary context for understanding your responses
- AI contributions are not part of "your voice"

### Source Authority for Persona

**Conversations AND writings dominate.** Both are "your direct voice." Other sources (bookmarks, repos, photos) support but don't define persona.

Quote: "These are actually my writings."

### Cross-Reference Detection

**Frequency-weighted.** Casual mentions fade; obsessions surface. A book mentioned once is noise; a topic discussed 50 times is signal.

### Synthesis vs. Source Data

**Strict separation.** Raw sources in one place, all synthesis/derived data clearly separated with provenance. Never mix interpretation with evidence.

---

## Priority Adjustments

### Promoted

- **ctk export** — THE critical path. MVP is conversations exported.
- **Writings (blogs, notes)** — Direct voice, high authority for persona.

### Demoted

- **ptk (photos)** — Lower priority than spec suggests. Conversations/writings more urgent for persona.
- **mtk (email)** — Demoted significantly. Maybe not important at all.
- **Verification/signing** — Skip entirely. Over-engineering.

### Unchanged

- **btk (bookmarks)** — MEDIUM
- **ebk (ebooks)** — MEDIUM
- **repoindex** — MEDIUM (use existing star/annotation features for curation)

---

## ECHO vs. longecho

**ECHO is the spec. longecho is one implementation.**

This decoupling matters:
- ECHO describes format and philosophy
- longecho is Python/SQLite implementation
- Others could build different implementations
- Don't couple ECHO spec too tightly to Python specifics

---

## Technical Ideas to Document

### Infinigram Mixture

An idea for biasing LLM output toward authentic voice:

> Use a mixture distribution: small weight on an infinigram model (n-gram trained on user's text) combined with a large LLM. The infinigram biases generation toward characteristic phrases/patterns without dominating.

Already implemented by the user. Worth documenting as an option for SOUL layer implementation.

### Update Cadence

**Provide tools, let user decide.** longecho doesn't dictate when to update. User might:
- Run manually when they feel like it
- Set up a cronjob
- Use a dead man's switch
- Update on life milestones

---

## Living Use vs. Legacy

**Legacy-focused.** Primary purpose is for after death. Living use is incidental/bonus.

This affects design:
- Don't optimize for daily querying/interaction
- Optimize for durability and completeness
- Focus on making it understandable to strangers

---

## Recipient Model

**Public release.** Intended to be publicly accessible after death.

Implications:
- No need for access control infrastructure
- No private/public tiers
- Anyone can have the archive

---

## What Must Happen Now

Things the future CAN'T recover:

1. **Content capture** — Export data from platforms before they die
2. **Context only you know** — "This conversation was about X", "I was wrong here", "John is my brother"

But even these aren't "lost forever" — future systems can work with raw data. The context annotations are nice-to-have, not critical.

---

## Core Tensions

Two things that keep the author up at night:

1. **Time pressure** — Will there be enough time to build this?
2. **Over-engineering fear** — Am I making this too complex despite trying not to?

These tensions are the heart of the project. Every decision should be evaluated against them.

---

## Summary: The Minimal Path

1. Export ctk conversations to JSON + markdown
2. Include SQLite database if reasonable
3. Skip persona extraction — raw conversations suffice
4. Skip verification infrastructure
5. Trust future LLMs to handle context, extrapolation, persona
6. Public release, single archive, no tiers
7. Other tools (btk, ebk, repoindex) can export when ready, but aren't blocking

Everything else is optional enhancement.
