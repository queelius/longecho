# ECHO Manifest Schema

**Version:** 1.0
**Status:** Specification

---

## Overview

The ECHO manifest provides machine-readable metadata for archives. It enables tools to:

- Generate unified browsable sites
- Discover and configure data sources
- Present archives intelligently in user interfaces

The manifest follows ECHO philosophy: simple, self-describing, durable (JSON/YAML).

---

## Schema

The canonical JSON Schema is at: `schemas/manifest.schema.json`

---

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version (currently "1.0") |
| `name` | string | Human-readable name |
| `description` | string | Brief description of contents |

---

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | One of: `database`, `documents`, `site`, `mixed` |
| `browsable` | boolean | Whether to include in generated sites (default: `true`) |
| `site` | string | Path to pre-built site directory |
| `docs` | string | Path to markdown documentation |
| `icon` | string | Icon identifier for UI presentation |
| `sources` | array | For hierarchical archives: list of sub-archive configs |
| `order` | number | Display order in unified site |

---

## Examples

### Minimal Manifest

```json
{
  "version": "1.0",
  "name": "My Archive",
  "description": "Personal data archive"
}
```

### Data Source Manifest

```json
{
  "version": "1.0",
  "name": "Conversations",
  "description": "AI conversation history from ChatGPT and Claude",
  "type": "database",
  "browsable": true,
  "site": "site/"
}
```

### Top-Level Archive Manifest

For archives that contain other ECHO archives as subdirectories:

```json
{
  "version": "1.0",
  "name": "Alex's Data Archive",
  "description": "Personal data archive",
  "sources": [
    {"path": "conversations/", "order": 1},
    {"path": "bookmarks/", "order": 2},
    {"path": "blog/", "order": 3, "browsable": false}
  ]
}
```

### Complete Example

```json
{
  "version": "1.0",
  "name": "Conversation History",
  "description": "AI conversations exported from ChatGPT, Claude, and Gemini",
  "type": "database",
  "browsable": true,
  "site": "site/",
  "docs": "docs/",
  "icon": "chat",
  "order": 1
}
```

---

## Source Configuration

When a manifest includes `sources`, each source object can have:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Relative path to sub-archive directory |
| `order` | number | No | Display order (lower = first) |
| `browsable` | boolean | No | Override sub-archive's browsable setting |
| `name` | string | No | Override sub-archive's name |

Example:

```json
{
  "sources": [
    {"path": "conversations/", "order": 1},
    {"path": "bookmarks/", "order": 2, "name": "My Bookmarks"},
    {"path": "drafts/", "browsable": false}
  ]
}
```

---

## Icon Identifiers

Common icon identifiers (tools may support more):

| Icon | Suggested Use |
|------|---------------|
| `chat` | Conversations, messages |
| `bookmark` | Bookmarks, links |
| `document` | Documents, notes |
| `database` | Databases, structured data |
| `image` | Photos, images |
| `music` | Music, audio |
| `video` | Videos |
| `code` | Code, projects |
| `archive` | Generic archive |

---

## YAML Support

Manifests may also be written in YAML as `manifest.yaml`:

```yaml
version: "1.0"
name: "My Archive"
description: "Personal data archive"
type: database
browsable: true
site: site/
```

Tools should check for `manifest.json` first, then `manifest.yaml`.

---

## Related

- [ECHO.md](ECHO.md) — The ECHO philosophy
- [LONGECHO.md](LONGECHO.md) — Validator and site generator
