# The arkiv / longecho boundary

**Status:** agreed direction, 2026-10-19. This is the contract both projects hold to. When either side changes something listed here, update this file and arkiv's `SPEC.md` (section 4) together.

## Two axes

arkiv's SPEC (section 4.1) already states it: arkiv addresses complexity (many silos, one queryable format), longecho addresses time (still readable when every current tool is gone). They meet at one place: **a directory with a README.**

## Who owns what

| Concern | Owner | Notes |
|---|---|---|
| Producing a compliant archive directory (README frontmatter, `schema.yaml`, JSONL, `media/`) | arkiv | One producer function that every exporter calls, so compliance is guaranteed, not hand-assembled per tool. |
| The `schema.yaml` shape | arkiv | Normative in arkiv `SPEC.md` 1.4. |
| Packing bundles (`.zip`, `.tar.gz`) | arkiv | A bundle is transport, not a source (see below). |
| Universal fallback viewer | arkiv | Lives in arkiv; longecho's site links to viewers, never becomes one. |
| The definition of compliance and of durable formats | longecho | `DURABLE_FORMAT_CATEGORIES` in `src/longecho/checker.py`. |
| Discovery and search across a tree of archives | longecho | `longecho query`. |
| The archive-of-archives site | longecho | `longecho build`, fractal: links to each source's own `site/`. |
| Fixity (bit-rot detection) | longecho | `FIXITY.sha256`, verifiable with `sha256sum -c` alone (planned). |

## The shared contract

1. **The unit of work is a directory.** A `.zip` or `.tar.gz` bundle counts as a durable file, but longecho never reads inside it, so a bundle on its own is not a source. Exporters that want longecho to see an archive write the directory form, or put the bundle in a directory with a README.
2. **README frontmatter keys.** `name`, `description`, `datetime`, `generator`, `contents`. arkiv adds `arkiv_format`. All optional; unknown keys are preserved. Name cascade: frontmatter `name`, then the first level-one heading, then the directory name. Description cascade: frontmatter `description`, then the first paragraph. A source's identity always comes from its own README, never a parent's.
3. **`contents` means different things to each tool, by design.** Directory entries: longecho uses them to curate and order sub-sources in `build`. File entries: arkiv uses them as its import list and order; longecho treats them as information for readers only. Neither tool reinterprets the other's meaning.
4. **The `site/` generator convention.** Any tool that writes a viewer into `site/` also writes `site/README.md` with `generator: <tool> <version>`. From longecho 0.5.0, `longecho build` overwrites a non-empty `site/` only when that stamp starts with `longecho build`; any other `site/`, stamped or not, needs `--force`.
5. **`schema.yaml` is optional and read loosely by longecho.** longecho may display it (collections, counts, field descriptions). It is never required for compliance, never validated, and a shape longecho does not recognize is ignored, not an error.
6. **Durable formats.** longecho's list is the definition. arkiv's guidance for `media/` should prefer formats on it. longecho plans to add `.pdf`, `.svg`, `.tif`/`.tiff`, `.wav`, `.flac`, `.mp4` (pending the author's decision).
7. **Dependency direction.** Neither project requires the other at runtime. A test-only dependency is fine: arkiv's tests may assert that its output passes `longecho.checker.check_compliance(path).compliant`.
8. **Files longecho may add to an archive.** `FIXITY.sha256` at an archive root (planned) and `site/` (from `build`). arkiv should not treat these as collections and should not delete them when re-exporting into the same directory.

## Known divergence to resolve (arkiv's side)

As of 2026-10-19, six memex exporters write `schema.yaml` in two incompatible shapes:

- Collection-keyed, arkiv's documented shape (`<collection>: {record_count, metadata_keys}`): llm-memex, photo-memex, health-memex.
- Kind-keyed (`{scheme, counts, kinds: {<kind>: {description, uri, fields}}}`): mail-memex, book-memex, bookmark-memex.

arkiv decides the canonical shape; longecho's display waits for that decision (see `schema-yaml-awareness.md`).
