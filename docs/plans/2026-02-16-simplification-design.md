# Design: longecho Simplification

**Date:** 2026-02-16
**Status:** Approved

## Summary

Simplify longecho's design by reducing the manifest to all-optional YAML-only fields, unifying three data representations into one, extracting README frontmatter as structured metadata, and focusing the spec directory. Net result: fewer concepts, less code, more capability.

## Spec Files

```
spec/
├── index.md              # Landing page
├── ECHO.md               # Pure philosophy (no tooling details)
├── LONGECHO.md           # Tool spec + manifest spec + site conventions
└── TOOLKIT-ECOSYSTEM.md  # Toolkit listing

DESIGN-NOTES.md           # Project root — moved from spec/INTERVIEW-INSIGHTS.md
```

**Deleted:** PERSONA-TK.md, STONE-TK.md, MANIFEST-SCHEMA.md, schemas/

**ECHO.md changes:** Remove "Optional: Web Presentation" section (move to LONGECHO.md). ECHO stays pure philosophy: README + durable formats + graceful degradation.

**LONGECHO.md changes:** Absorb manifest spec and site conventions from ECHO.md and MANIFEST-SCHEMA.md.

## Dependencies

```toml
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "jinja2>=3.0.0",
    "markdown>=3.0.0",
    "pyyaml>=6.0.0",         # promoted from [full] — needed for frontmatter + manifest
]

[project.optional-dependencies]
full = [
    "datasette>=0.64.0",     # jsonschema removed
]
```

## Data Model

### Readme (new)

```python
@dataclass
class Readme:
    frontmatter: Optional[dict]   # parsed YAML or None
    body: str                      # content after frontmatter
    title: Optional[str]           # first # heading
    summary: Optional[str]         # first paragraph
```

Produced by `parse_readme(path) -> Optional[Readme]`, which uses `split_frontmatter(content) -> (Optional[dict], str)` internally.

### ComplianceResult (simplified)

```python
@dataclass
class ComplianceResult:
    compliant: bool
    path: Path
    reason: Optional[str] = None
    source: Optional[EchoSource] = None  # populated when compliant
```

### EchoSource (unified — replaces EchoSource + SourceInfo)

```python
@dataclass
class EchoSource:
    path: Path
    readme_path: Path
    name: str                          # cascade: manifest > frontmatter > heading > dirname
    description: str                   # cascade: manifest > frontmatter > paragraph > ""
    formats: list[str]
    durable_formats: list[str]
    icon: Optional[str] = None         # raw emoji string
    order: int = 0
    has_site: bool = False
    site_path: Optional[Path] = None
```

### Manifest (simplified — all fields optional, YAML-only)

```python
@dataclass
class SourceConfig:
    path: str
    name: Optional[str] = None
    icon: Optional[str] = None
    order: Optional[int] = None

@dataclass
class Manifest:
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sources: list[SourceConfig] = field(default_factory=list)
    path: Optional[Path] = None  # where loaded from
```

### BuildResult (unchanged)

```python
@dataclass
class BuildResult:
    success: bool
    output_path: Optional[Path] = None
    sources_count: int = 0
    error: Optional[str] = None
```

## Manifest Format

YAML-only. All fields optional. Sources can be plain strings or objects.

```yaml
name: Alex's Archive
description: Personal data archive
icon: "\U0001F4E6"
sources:
  - conversations/
  - path: bookmarks/
    name: My Bookmarks
    icon: "\U0001F516"
```

## Name/Description/Icon Cascade

```
name:        manifest > frontmatter["title"] > readme heading > dirname
description: manifest > frontmatter["description"] > readme paragraph > ""
icon:        manifest > frontmatter["icon"] > None
```

## What Dies

- SourceInfo dataclass, ICON_EMOJI_MAP, get_icon_emoji()
- schemas/manifest.schema.json, _find_schema_path(), jsonschema validation
- version/type/browsable/site/docs manifest fields + validation
- JSON manifest parsing branch
- Duplicate EchoSource construction in 3 places
- extract_first_paragraph heuristics (replaced by parse_readme)
- PERSONA-TK.md, STONE-TK.md, MANIFEST-SCHEMA.md spec files

## What's New

- Readme dataclass + parse_readme() + split_frontmatter()
- Frontmatter cascade for name/description/icon resolution
- README frontmatter as zero-config alternative to manifest
