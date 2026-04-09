# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
