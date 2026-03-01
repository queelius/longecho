# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

longecho is both a philosophy and a tool for durable personal archives. A directory is longecho-compliant if it has a README.md/README.txt + data in durable formats. The CLI validates compliance, queries archives, and builds single-file browsable sites.

**Status:** Alpha. 119 tests, 94% coverage.

## Commands

```bash
longecho check ~/path              # Is this directory longecho-compliant?
longecho query ~/                  # Find/search/filter sources across the tree
longecho query ~/ --search "term"  # Text search across names, descriptions, READMEs
longecho query ~/ --json           # JSON output (pipe to jq for structured queries)
longecho build ~/archive           # Generate single-file static site
longecho spec                      # Print specification summary
longecho formats                   # List recognized durable formats
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v                                        # run all tests
pytest tests/test_discovery.py::TestMatchesQuery -v     # run single test class
pytest tests/ -k "test_builds_basic"                    # run by name pattern
pytest tests/ --cov=src/longecho --cov-report=term-missing  # coverage
mypy src/longecho/
ruff check src/longecho/
```

## Architecture

Five modules, each with a clear responsibility:

- **checker.py** — Core data model (`Readme`, `EchoSource`, `ComplianceResult`) and compliance logic. Parses READMEs (frontmatter + body), detects durable formats, checks compliance. The `DURABLE_EXTENSIONS` set is the single source of truth for format recognition.
- **discovery.py** — Tree-walking (`discover_sources`) and text search (`search_sources`, `matches_query`). Search builds a text blob from name + description + README body + frontmatter values, then does case-insensitive substring matching.
- **build.py** — SFA (Single-File Application) generation. `_source_to_json` recursively converts sources to JSON including `children`. `discover_sub_sources` uses the `contents` frontmatter field for curated ordering, or auto-discovers alphabetically. `make_json_safe` handles `datetime.date` objects from YAML parsing.
- **cli.py** — Typer CLI. All commands default path to `"."`. JSON output uses `print()` not `console.print()` (Rich wraps lines, breaking JSON).
- **templates/sfa.html** — Jinja2 template for the single-file site. Inlines all source data as JSON. JavaScript handles navigation (recursive via `navStack`), breadcrumbs, and text search. Works from `file://`.

## Data Flow

```
check_compliance(path)  →  ComplianceResult(source: EchoSource)
discover_sources(root)  →  Iterator[EchoSource]   (tree walk)
search_sources(root, q) →  Iterator[EchoSource]   (filtered)
build_site(path)        →  BuildResult             (generates site/index.html)
```

Build pipeline: `check_compliance` → `discover_sub_sources` (recursive) → `_source_to_json` (recursive, produces `children`) → Jinja2 render → `site/index.html`

## Key Design Decisions

- **Name cascade:** frontmatter `name` > `# Heading` > dirname. Description: frontmatter `description` > first paragraph.
- **`contents` field** in frontmatter controls build curation + ordering. Without it, auto-discovery is alphabetical.
- **No parent overrides** — a source's identity always comes from its own README.
- **`site/` is longecho-compliant** — the generated site directory has its own README + index.html. It appears in query results.
- **Search is plain text** — no special query syntax. Power users use `--json | jq` for structured queries.
- **YAML `datetime.date` pitfall** — `yaml.safe_load` parses bare dates into `datetime.date` objects. `make_json_safe()` in build.py converts these for JSON serialization. Both build and CLI JSON output paths need this.

## Ecosystem

Part of the `longecho-ecosystem` (GitHub topic). Related tools: arkiv, memex, repoindex, chartfold, jot, pagevault.
