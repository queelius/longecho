# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

longecho is both a philosophy and a tool for durable personal archives. A directory is longecho-compliant if it has a README.md/README.txt + data in durable formats. The CLI validates compliance, queries archives, and builds single-file browsable sites.

**Status:** Alpha. v0.5.0 on PyPI (`pip install longecho`). The version lives only in `src/longecho/__init__.py`; pyproject reads it via `[tool.hatch.version]`.

## Commands

```bash
longecho check ~/path              # Is this directory longecho-compliant?
longecho query ~/                  # Find/search/filter sources across the tree
longecho query ~/ --search "term"  # Text search across names, descriptions, READMEs
longecho query ~/ --json           # JSON output (pipe to jq for structured queries)
longecho build ~/archive           # Generate single-file static site
longecho spec                      # Print specification summary
longecho formats                   # Durable formats with readers and reasons (--json for the registry)
```

Other flags: `check --verbose`, `query --depth N` (0 = root only) and `--table`, `build --output PATH`, `--force`/`-f`, `--open`.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v                                        # run all tests
pytest tests/test_discovery.py::TestMatchesQuery -v     # run single test class
pytest tests/ -k "test_builds_basic"                    # run by name pattern
pytest tests/ --cov=src/longecho --cov-report=term-missing  # coverage
mypy src/longecho/
ruff check src/longecho/

pip install -e ".[docs]"        # mkdocs-material
mkdocs serve                    # preview docs locally
mkdocs build --strict           # what CI runs; must pass with zero warnings
```

Tests are split by module (`test_formats.py`, `test_checker.py`, `test_discovery.py`, `test_build.py`, `test_cli.py`) plus `test_readme.py` for frontmatter/README parsing. `test_formats.py` also fails if README.md or docs/spec.md omits an extension the registry has. Fixtures in `conftest.py` create durable files with `.touch()`, which works because compliance checks presence, not content.

## Documentation Site

Material for MkDocs, published at https://queelius.github.io/longecho/. `.github/workflows/docs.yml` runs `mkdocs build --strict` and deploys to GitHub Pages on **every push to `main`**, so a broken internal link or a page missing from `nav` turns CI red and blocks the deploy.

- `mkdocs.yml` lists five pages explicitly in `nav`: `index.md` (the philosophy, ethos-forward), `quickstart.md`, `spec.md` (canonical reference), `cli.md`, `ecosystem.md`.
- `exclude_docs` keeps `docs/ideas/` (parked proposals, e.g. `schema-yaml-awareness.md`) and `docs/superpowers/` (design specs and plans) in the repo but out of the published site.
- Link between pages by bare filename (`[Specification](spec.md)`); cross-page `#anchor` links are fragile under `--strict`.
- The same rules are written in several places: `README.md`, `docs/spec.md`, `docs/cli.md`, the `longecho spec` output (generated from code), and `CHANGELOG.md`. When compliance rules, formats, or CLI flags change, update all of them.
- Docs vocabulary matches the shipped CLI: "longecho-compliant", the `contents` field, commands `check`/`query`/`build`/`spec`/`formats`. Older blog posts use "ECHO-compliant", `manifest.yaml`, and `discover`/`search`/`serve`; those are historical and should not appear in the docs.
- The ecosystem page lists tools by the live `longecho-ecosystem` GitHub topic (`gh api repos/queelius/<repo> --jq .topics`), not from memory.
- Prose avoids em-dashes (the author's voice rule; a hook rejects them).

## Architecture

Seven files in `src/longecho/`, each with a clear responsibility:

- **formats.py**: The durable format registry. `FORMATS` is the single source of truth: a tuple of `Format(extensions, mimetype, category, readers, rationale, sidecars)`, judged against `DURABILITY_CRITERIA` (the Library of Congress sustainability factors). `Reader` is the degradation-ladder rung that opens a format. `DURABLE_EXTENSIONS`, `DURABLE_FORMAT_CATEGORIES`, `DURABLE_MIMETYPES`/`is_durable_mimetype` (canonical type plus `mimetype_aliases`), `format_for`, `preview_kind` (site previews), `reads_as_text`, `is_unrecognized` (the single "warn about this file" rule, used by checker and build), and `sidecar_base` (SQLite `-wal`/`-journal`/`-shm`) are all derived. To add a format, add one entry with its reason, then add the extension to the README and spec tables (a test enforces this).
- **checker.py**: Core data model (`Readme`, `EchoSource`, `ComplianceResult`, `ComplianceWarning`, `WarningKind`) and compliance logic. Parses READMEs (frontmatter + body) and walks each source once (`_take_inventory`, `os.scandir`, two levels deep): `site/` and `SKIP_DIRECTORIES` are never entered; durable suffixes from the source and its nested sources decide compliance; `EchoSource.files` keeps only the files the source owns (ownership stops at nested sources); `unscanned` records owned directories below the depth limit. Entries whose type cannot be read (symlink loops, unreadable targets) are skipped, never raised. `warnings` on `EchoSource` and `ComplianceResult` is a `cached_property` over `find_warnings`, so tree walks that never show warnings never read file contents.
- **discovery.py**: Tree-walking (`discover_sources`) and text search (`search_sources`, `matches_query`). Search builds a text blob from name + description + README body + frontmatter values, then does case-insensitive substring matching.
- **build.py**: SFA (Single-File Application) generation. `_source_to_json` recursively converts sources to JSON including `children`. `discover_sub_sources` uses the `contents` frontmatter field for curated ordering, or auto-discovers alphabetically. `_get_data_files` lists `source.files` (owned files, scanned to `DEFAULT_FORMAT_SCAN_DEPTH`, currently 2) with `durable`, `warns`, and `preview` flags, dropping SQLite sidecars. `_link` makes every href: percent-encoded and relative to the page when page and target are both inside the archive root, else an absolute `file://` URI. `_is_foreign_site` reads the output's `README.md` to detect sites generated by other tools; `build_site(..., force=True)` overrides the check. `build_site` always refuses an output that is the archive or contains it. Auto-discovery skips directories stamped `generator: longecho build` (`_is_longecho_site`). README HTML goes through `_Sanitizer`, an `HTMLParser` allowlist of tags, attributes, and URL schemes (no regex).
- **cli.py**: Typer CLI. `check`/`query`/`build` default path to `"."`. JSON output uses `print()` not `console.print()` (Rich wraps lines, breaking JSON). Any untrusted text (paths, README fields, warning messages) goes through `_lit()` (`rich.markup.escape`) or `Text`, never raw into a markup string. The `build` command has a `--force` flag for the foreign-site override.
- **templates/sfa.html**: Jinja2 template for the single-file site. Inlines all source data as JSON. JavaScript handles navigation (recursive via `navStack`), breadcrumbs, and text search. Surfaces per-source interactive sites via `site_url`. `createFileEntry` renders each data file, with a "not in a durable format, and not UTF-8 text" flag when `warns` is set (the page applies no rule of its own) and an inline `<img>`/`<audio>`/`<video>` when `preview` is set. Works from `file://`.
- **__main__.py**: Tiny module entry point so `python -m longecho` works.

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
- **`contents` field in frontmatter:** *directory* entries control build curation and ordering. *File* entries are preserved as informational metadata (visible in frontmatter to humans and LLMs) but do not affect build structure. Without `contents`, auto-discovery is alphabetical and every file the source owns appears in "Data Files".
- **No parent overrides:** a source's identity always comes from its own README.
- **`site/` is longecho-compliant:** the generated site directory has its own README plus index.html. It appears in query results.
- **Site overwrite protection:** `longecho build` overwrites a non-empty `site/` only when its `README.md` `generator` starts with "longecho build". Another tool's stamp, a README without one, or no README at all (e.g. a memex HTML viewer) all count as foreign. This protects tool-generated viewers (ctk, chartfold, etc.) from being clobbered. Pass `--force` to override.
- **Data files are source-scoped:** ownership stops at nested sources, so each source's SFA detail view lists only the files it directly owns, not files belonging to sub-sources. Unrecognized files are listed and flagged, never hidden.
- **No format plugins:** durability is a judgment recorded as data with a reason, not a capability. Plugins would make compliance depend on what is installed. Viewing belongs to the browser (previews), each tool's own `site/`, and future LLMs.
- **Warnings never fail:** `ComplianceResult.warnings` (unrecognized formats, SQLite sidecars at risk) never change the verdict or exit code. The WAL check is a size test on the sidecar, so it says "may hold" changes. Files with unknown extensions warn only if `reads_as_text` (first 4 KB is UTF-8 without NUL) says they are binary; that peek is the only content read anywhere, and compliance never uses it.
- **No `START_HERE.txt`:** the top-level README is the start-here note. The early essays' format ladder and reader ladder are merged into one table (docs/index.md, README).
- **Search is plain text:** no special query syntax. Power users use `--json | jq` for structured queries.
- **YAML `datetime.date` pitfall:** `yaml.safe_load` parses bare dates into `datetime.date` objects. `make_json_safe()` in build.py converts these for JSON serialization. Both build and CLI JSON output paths need this.
- **`site/` asymmetry between build and query:** `discover_sub_sources` (build) skips `site/` directories because they're the viewer, not the content. `discover_sources` (query) does NOT skip them, because a tool-generated `site/` is still a legitimate longecho-compliant source that should be discoverable. This is intentional: build walks the archive content tree, query walks the whole filesystem.
- **Archives are opaque:** `.zip`, `.gz`, `.tgz` count as durable formats but longecho never reads inside them. A directory containing only an archive plus a README is compliant; the archive is treated as a transport container, not a working format. To work with archive contents, extract first.
- **Compound extensions via terminal suffix:** `Path.suffix` returns only the last extension, so `conversations.jsonl.gz` qualifies via `.gz` (not `.jsonl.gz`). This is intentional and tested. Consequence: a source's `durable_formats` list lumps all `*.gz` files under `.gz` regardless of their underlying type.

## Ecosystem

Part of the `longecho-ecosystem` (GitHub topic). Tagged (check live with `gh search repos --owner queelius --topic longecho-ecosystem`): arkiv, chartfold, jot, llm-memex, pagevault, repoindex. The other `*-memex` archives (book, bookmark, mail, photo) export arkiv directories but are not tagged. `posthumous` is adjacent (same local-first stack) but not tagged.

Unreleased work sits under `[Unreleased]` in CHANGELOG.md; on release, bump `__version__` in `src/longecho/__init__.py` and the status line above.
