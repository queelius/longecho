# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-10-19

### Changed
- **Behavior change:** `longecho build` now overwrites a non-empty `site/`
  only when its `README.md` carries a `generator` starting with
  "longecho build". A `site/` with another tool's stamp, a README without
  one, or no README at all (for example a memex HTML viewer) is left alone
  unless you pass `--force`. Previously only sites with a foreign stamp were
  protected, so unstamped viewers were silently overwritten.
- README titles and descriptions are read from the parsed Markdown instead
  of a line scan. Descriptions no longer start with HTML comments, raw HTML
  blocks, or badge markup; lists such as a table of contents no longer count
  as the first paragraph; setext headings count as titles; inline markup
  becomes plain text. This renders each README, so `query` over a large tree
  is slower (0.8s to 2.0s for 269 sources in testing).
- The version now lives only in `src/longecho/__init__.py`; `pyproject.toml`
  reads it through `[tool.hatch.version]`.

### Fixed
- `longecho build --output` pointing at an existing file is refused instead
  of crashing.

### Added
- Documentation site at https://queelius.github.io/longecho/ (Material for
  MkDocs, deployed from `main`), and a `Documentation` project URL.
- `.gz` and `.tgz` accepted as durable archive formats. Gzip has shipped with
  every mainstream OS since 1992 and decodes without special tooling.
  Compound extensions like `.jsonl.gz`, `.csv.gz`, and `.tar.gz` qualify via
  their terminal `.gz` suffix.
- Compliance smoke tests for `.jsonl.gz` and `.tar.gz` pin the behavior and
  document the contract (there is no separate `.tar.gz` entry; the `.gz`
  suffix is what earns durability).

### Changed
- README durable-formats section clarifies that gzipped files qualify via
  terminal `.gz`, covering `.jsonl.gz`, `.csv.gz`, `.tar.gz`, etc.

## [0.4.0] - 2026-04-09

### Added
- Foreign site overwrite protection: `longecho build` refuses to overwrite a
  `site/` whose `README.md` `generator` field is not longecho's own. New
  `--force` / `-f` flag to bypass the check. Protects tool-generated viewers
  (ctk, chartfold, etc.) from being silently clobbered.
- The archive root is now rendered as a full detail view on the home page
  of the generated SFA. Root-level README content, data files, and metadata
  are visible where they were previously hidden. Home view and detail view
  share a single rendering path.
- `TestSiteLink`, `TestRecursiveDataFiles`, `TestIsForeignSite`,
  `TestForeignSiteProtection`, `TestRootSourceRendering`,
  `TestModuleEntryPoint` test classes (22 new tests).
- `CHANGELOG.md` (this file).

### Changed
- `_get_data_files` walks the source tree recursively up to
  `DEFAULT_FORMAT_SCAN_DEPTH`, stopping at nested sub-sources and `site/`
  directories. Data files in subdirectories like `data/raw/*.jsonl` now
  appear in the SFA when they belong to the source being rendered.
- SFA JSON: the per-source `formats` key is renamed to `durable_formats`
  for consistency with the Python data model. **This is a breaking change
  for anyone reading the SFA JSON directly.** Internal consumers (the SFA
  JavaScript) have been updated.
- `Readme` dataclass no longer carries a `body` field. It was unused
  externally and only held a transient copy of the parsed body.
  **Breaking change for anyone importing `Readme` and accessing `.body`.**
- `--depth` help text clarified to specify filesystem depth.
- README `contents` field documentation clarified: directory entries control
  build curation and ordering; file entries are informational metadata and
  do not affect build structure.
- Ecosystem section mentions personal toolkits (ctk, btk, ebk, mtk) as
  illustrative examples distinct from the tagged `longecho-ecosystem`
  members.
- CLAUDE.md updated with new design decisions (site overwrite protection,
  data file scoping) and the `__main__.py` entry point.

### Fixed
- Root archive's own data files and README content were never displayed in
  the generated SFA (pre-existing gap, now fixed by rendering the root as
  a full source).
- `_get_data_files` previously only globbed the source's top-level
  directory, missing files detected by `detect_durable_formats` at deeper
  levels.

## [0.3.0] - 2026-02-18

### Added
- First publication to PyPI.
- `longecho spec` command prints the specification summary.
- `longecho build` generates a single-file application (SFA) with all
  content, CSS, and JavaScript inlined. Works from `file://` with no
  server or external dependencies.
- Recursive SFA navigation with breadcrumb for unlimited nesting depth.
- Source-level site linking: when a source has its own `site/index.html`,
  the archive SFA surfaces an "Open interactive viewer" link.
- `.html` and `.htm` added to the durable formats list.
- `python -m longecho` entry point via `__main__.py`.
- `LICENSE` (MIT).

### Changed
- `DURABLE_FORMAT_CATEGORIES` dict is the single source of truth for
  format categorization. `DURABLE_EXTENSIONS` and all display and spec
  commands derive from it.
- Text search is plain substring matching (no special query syntax).
  Structured queries go through `--json | jq`.
- `EchoSource` no longer carries a non-durable `formats` field. Only
  `durable_formats` remains.
- `detect_formats` renamed to `detect_durable_formats`. Filters during
  the walk rather than after.
- `split_frontmatter` made internal (`_split_frontmatter`).
- `longecho query --json` output uses relative paths instead of absolute.
- All CLI commands default their path argument to the current directory.
- The generated `site/` directory is longecho-compliant itself, with its
  own self-describing `README.md`.
