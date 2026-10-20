# longecho Revival Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn longecho from a stalled convention into the tool that verifies and binds the author's real archives: fix the bugs that contradict its ethos, write down its boundary with arkiv, then add the missing durability features and dogfood them on real data.

**Architecture:** longecho stays a small, read-only tool over directories. arkiv (and the memex tools, through arkiv) writes compliant directories; longecho checks, queries, fingerprints, and builds a site over them. Dependencies run one way: producers never require longecho at runtime, and longecho never imports arkiv or reads JSONL/SQLite records.

**Tech Stack:** Python 3.9+, Typer, Jinja2, python-markdown, PyYAML, pytest. Docs: Material for MkDocs (`mkdocs build --strict` in CI).

**Spec:** The 2026-10-19 review in this session (summarized in each phase below) and the shared contract at `docs/ideas/arkiv-boundary.md` (written in Task B1).

## Global Constraints

- No new runtime dependencies. Anything new uses the standard library or the five existing deps (typer, rich, jinja2, markdown, pyyaml).
- longecho never imports arkiv, never parses JSONL records or SQLite contents.
- Compliance stays "README + at least one durable file". No new required files or fields.
- Every artifact longecho writes must be verifiable or readable without longecho (plain text, standard tools).
- Authored prose (docs, README, CHANGELOG, commit messages) contains no em-dashes. The soul hook checks the whole file on every write, so editing README.md requires removing its existing em-dashes in the same change.
- Docs must pass `mkdocs build --strict`. When a rule, format, or flag changes, update README.md, `docs/spec.md`, `docs/cli.md`, CHANGELOG.md, and CLAUDE.md together.
- Commits go to `main` and are pushed (the author's chosen landing path for this repo). Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

- An existing `site/` that is empty must still build (not refused as foreign).
- A `site/` written by longecho before the generator stamp existed is refused; the error must name `--force` as the way through.
- A README whose first paragraph is only badges, images, or an HTML comment must not produce markup as its description; it should fall through to the next real paragraph, or to empty.
- Setext headings (`Title` underlined with `===`) must count as the title.
- Inline markup in the first paragraph (`**bold**`, links, code) must appear as plain text in the description, not as Markdown syntax.

---

## Phase A: Fix what contradicts the ethos, release 0.5.0 (do now)

### Task A1: Protect any non-longecho `site/` from overwrite

Today `_is_foreign_site` returns "not foreign" when the output has no README or no `generator`, so `longecho build` overwrites viewers (for example the memex HTML exports, which write no README). Flip the default: only a site stamped by longecho, or an empty directory, may be overwritten without `--force`.

**Files:**
- Modify: `src/longecho/build.py` (`_is_foreign_site`, and the error message in `build_site`)
- Test: `tests/test_build.py` (`TestIsForeignSite`, `TestForeignSiteProtection`)

**Interfaces:**
- Produces: `_is_foreign_site(output_path: Path) -> tuple[bool, str]`. Same signature. Second element is the generator string, or `"an unknown tool (no longecho generator stamp)"` when the directory has content but no stamp.

- [ ] **Step 1: Update and add tests in `TestIsForeignSite`.** Replace `test_nonexistent_readme`, `test_readme_without_frontmatter`, `test_readme_without_generator` with:
  - `test_empty_dir_is_not_foreign`: empty `temp_dir` gives `(False, "")`.
  - `test_index_without_readme_is_foreign`: write `index.html` only, expect `is_foreign is True` and `"unknown" in gen`.
  - `test_readme_without_frontmatter_is_foreign`: README with no frontmatter, expect `True`.
  - `test_readme_without_generator_is_foreign`: frontmatter without `generator`, expect `True`.
  - Keep `test_longecho_generator` (False) and `test_foreign_generator` (True, `gen == "ctk v2.1"`).
- [ ] **Step 2: Add to `TestForeignSiteProtection`:** `test_build_refuses_unstamped_viewer` (source with `site/index.html` and no README: `build_site` returns `success=False`, error contains `--force`, and `site/index.html` content is unchanged) and `test_build_force_overwrites_unstamped_viewer`.
- [ ] **Step 3: Run** `pytest tests/test_build.py -k "Foreign" -v`. Expected: the new tests FAIL.
- [ ] **Step 4: Implement.** In `_is_foreign_site`: if the directory has no entries, return `(False, "")`; if README frontmatter `generator` starts with `"longecho build"`, return `(False, gen)`; if a generator is present, return `(True, gen)`; otherwise return `(True, "an unknown tool (no longecho generator stamp)")`. Keep the `build_site` message naming `--force` and `--output`.
- [ ] **Step 5: Run** `pytest tests/ -q`. Expected: all pass.
- [ ] **Step 6: Commit** `fix(build): never overwrite a site/ that longecho did not stamp`.

### Task A2: Derive the README title and description from parsed Markdown

`parse_readme` scans lines, so real READMEs produce descriptions like `<!-- Licensed to ...`, `<a href=...`, and badge markup. Use the Markdown parser that is already a dependency.

**Files:**
- Modify: `src/longecho/checker.py` (`parse_readme`)
- Test: `tests/test_readme.py` (`TestParseReadme`)

**Interfaces:**
- Produces: unchanged `parse_readme(readme_path: Path) -> Optional[Readme]`; `Readme.title` is the text of the first `h1`; `Readme.summary` is the whitespace-normalized text of the first `p` whose text is non-empty, truncated to `MAX_README_SUMMARY_LENGTH` (500).

- [ ] **Step 1: Write failing tests** in `TestParseReadme`:
  - `test_skips_html_comment`: body `"<!-- license header -->\n\n# T\n\nReal description."` gives `summary == "Real description."`.
  - `test_skips_badge_only_paragraph`: `"# T\n\n[![DOI](https://x/badge.svg)](https://x)\n\nReal description."` gives `"Real description."`.
  - `test_skips_raw_html_block`: `"# T\n\n<p align=\"center\"><img src=\"logo.png\"></p>\n\nReal description."` gives `"Real description."`.
  - `test_setext_heading_is_title`: `"My Title\n========\n\nBody."` gives `title == "My Title"`.
  - `test_inline_markup_is_plain_text`: `"# T\n\nA **bold** [link](http://x) and `code`."` gives `"A bold link and code."`.
  - `test_badges_only_readme_has_no_summary`: `"# T\n\n[![b](u)](v)"` gives `summary is None`.
- [ ] **Step 2: Run** `pytest tests/test_readme.py -v`. Expected: the new tests FAIL; existing tests pass.
- [ ] **Step 3: Implement.** Render the body with `markdown.markdown(body, extensions=["fenced_code", "tables"])`, walk the HTML with a small `html.parser.HTMLParser` subclass that records the text of the first `h1` and the first `p` with non-empty text (comments and tags outside `h1`/`p` contribute nothing; raw HTML blocks are not `p` from Markdown, so they are skipped only if the parser does not wrap them; verify with the test). Collapse whitespace with `" ".join(text.split())`. Import `markdown` locally inside the function, matching `build.markdown_to_html`.
- [ ] **Step 4: Run** `pytest tests/ -q`. Expected: all pass (including `test_multiline_paragraph`, `test_skips_subheadings_before_paragraph`).
- [ ] **Step 5: Check on real data.** `longecho query ~/github --depth 1` shows no `<!--`, `<a `, or `[![` at the start of any description.
- [ ] **Step 6: Commit** `fix(checker): read README title and description from parsed Markdown`.

### Task A3: Make the docs agree with the tool and with each other

**Files:**
- Modify: `docs/ecosystem.md` (line 5: "an orchestration layer rather than a framework")
- Modify: `docs/spec.md:71`, `docs/cli.md:37` (overwrite rule now covers unstamped sites)
- Modify: `README.md` (line 192 "no relative links to break" contradicts relative data links; overwrite rule; remove all em-dashes in the same edit)
- Modify: `CLAUDE.md` (Site overwrite protection decision)

- [ ] **Step 1:** Rewrite `docs/ecosystem.md:5` to match the README's "Not an orchestrator": longecho reads what tools produced and builds over it; it never invokes or manages them.
- [ ] **Step 2:** State the new overwrite rule in `docs/spec.md`, `docs/cli.md`, README, CLAUDE.md: a non-empty `site/` is overwritten only if its README carries a `generator` starting with `longecho build`; otherwise `--force` is required.
- [ ] **Step 3:** README line 192: say content is inlined and data files are linked by relative path, so the site works from `file://` while the archive stays together.
- [ ] **Step 4: Verify.** `mkdocs build --strict` exits 0; `grep -cP '\x{2014}' README.md docs/*.md` prints 0 for every file; `grep -rn "orchestration layer" docs/` prints nothing.
- [ ] **Step 5: Commit** `docs: align overwrite rule and orchestration wording with the tool`.

### Task A4: Release 0.5.0

- [ ] **Step 1:** Bump `version` in `pyproject.toml` and `__version__` in `src/longecho/__init__.py` to `0.5.0`; update the CLAUDE.md status line.
- [ ] **Step 2:** CHANGELOG: rename `[Unreleased]` to `[0.5.0] - <date>`, add the A1 fix (under Changed, flagged as a behavior change), the A2 fix, the docs site, and the `Documentation` project URL.
- [ ] **Step 3: Verify.** `pytest tests/ -q` passes; `ruff check src/longecho/`; `mypy src/longecho/`; `python -m build` produces wheel and sdist; `twine check dist/*` passes; `longecho build` on a scratch copy of `dev/my-archive` stamps `generator: longecho build v0.5.0`.
- [ ] **Step 4:** Commit, tag `v0.5.0`, push with tags, `twine upload dist/longecho-0.5.0*`, create the GitHub release from the CHANGELOG section. Confirm `pip index versions longecho` (or the PyPI JSON API) shows 0.5.0.

---

## Phase B: Write down the boundary (do now)

### Task B1: Shared contract and arkiv handoff

**Files:**
- Create: `docs/ideas/arkiv-boundary.md` (the contract both projects hold to; excluded from the published site by `exclude_docs`)
- Create: `../arkiv/docs/handoffs/2026-10-19-from-longecho.md` (task list for a Claude Code session in arkiv; uncommitted until the author asks)

- [ ] **Step 1:** Write the contract: who owns what, the shared README frontmatter keys, `contents` semantics in each tool, the `site/` generator convention, the `schema.yaml` situation, dependency direction.
- [ ] **Step 2:** Write the handoff: context, verified evidence with paths, ordered tasks for arkiv, what arkiv should not do, open questions.
- [ ] **Step 3: Verify.** `mkdocs build --strict` still passes (ideas/ excluded); no em-dashes in either file.
- [ ] **Step 4: Commit** the longecho file only: `docs(ideas): record the arkiv/longecho boundary`.

---

## Phase C: Durability features (after arkiv settles the schema.yaml shape)

### Task C1: Show `schema.yaml` when present (revives `docs/ideas/schema-yaml-awareness.md`)

**Blocked on:** arkiv publishing the normative `schema.yaml` shape (handoff task 2).

**Files:** `src/longecho/checker.py` (`EchoSource.schema: Optional[dict]`), `src/longecho/build.py` (`_source_to_json` adds `schema`), `src/longecho/templates/sfa.html` (collapsed "Data dictionary" block), `src/longecho/cli.py` (`check --verbose`, `query --json`), tests in `test_checker.py`, `test_build.py`, `test_cli.py`.

- [ ] Tests: a source with a canonical `schema.yaml` exposes collections, record counts, and field descriptions in `query --json` and the SFA JSON; a malformed or differently shaped `schema.yaml` never fails `check` and never raises; a source without one is unchanged.
- [ ] Implement with a loose reader: accept a mapping, show what is recognizable, ignore the rest. No arkiv imports, no validation, no type checks.
- [ ] Docs: spec.md section "The data dictionary (optional)"; move the idea doc status to "implemented".

### Task C2: Durable media formats

**Decision needed from the author:** the exact list. Proposed, by longecho's own test (readable without proprietary software, multiple implementations, proven longevity): Documents add `.pdf`; Images add `.svg`, `.tif`, `.tiff`; new Audio category `.wav`, `.flac`; new Video category `.mp4`. DICOM stays out (open, but niche readers).

**Files:** `src/longecho/checker.py` (`DURABLE_FORMAT_CATEGORIES` only; everything else derives from it), `tests/test_checker.py`, README/spec format tables.

- [ ] Tests: one compliance test per new category; the existing invariant tests (flat set equals union of categories) keep passing unchanged.
- [ ] Implement by adding entries to `DURABLE_FORMAT_CATEGORIES`.
- [ ] Verify `longecho formats` and `longecho spec` show the new rows with no other code change.

### Task C3: Warn about live SQLite sidecars

**Files:** `src/longecho/checker.py` (`ComplianceResult.warnings: list[str]`), `src/longecho/cli.py` (`check` prints warnings, `query --json` includes them), tests.

- [ ] Tests: a source containing `x.db` and `x.db-wal` (or `x.db-journal`) passes compliance with one warning naming the file and suggesting a snapshot (`sqlite3 x.db ".backup snapshot.db"` or `VACUUM INTO`); a source without sidecars has no warnings; warnings never change pass/fail or the exit code.
- [ ] Implement by deriving sidecar names from the durable database extensions in `DURABLE_FORMAT_CATEGORIES` (no separate list).

### Task C4: Fixity

Detects bit rot over time. Separate from compliance: `check` does not change.

**Files:** Create `src/longecho/fixity.py`; modify `src/longecho/cli.py` (a `fixity` Typer sub-app with `init` and `check`); tests in `tests/test_fixity.py`; docs `cli.md`, `spec.md` ("Fixity" section), README.

**Interfaces:**
- `write_manifest(root: Path) -> Path` writes `root/FIXITY.sha256` in `sha256sum` format (`<hex>  <posix relpath>`, sorted by path), covering every regular file under `root` except `FIXITY.sha256` itself and any `site/` directory. Symlinks are listed as skipped, never followed.
- `verify_manifest(root: Path) -> FixityReport` with `changed`, `missing`, `added: list[str]`, and `ok: bool` (true when `changed` and `missing` are empty; `added` is reported but does not fail).

- [ ] Tests: init then check on an untouched tree is ok; editing a byte reports `changed`; deleting reports `missing`; a new file reports `added` and stays ok; `sha256sum -c FIXITY.sha256` run in `root` succeeds on the generated file (proves tool independence); `site/` changes never appear.
- [ ] CLI: `longecho fixity init PATH`, `longecho fixity check PATH [--json]`; check exits 1 when not ok.
- [ ] Declined from the same review item: `longecho mirror`. Document a plain `rsync -a` / `rclone copy` recipe in the docs instead of wrapping them.

---

## Phase D: Dogfood on real data

### Task D1: A real archive tree

Depends on handoff task 1 (every memex exporter writes compliant output) and on Phase C4.

- [ ] Create `~/archive/` with a hand-written root README (what this is, how to open it, in what order) and one subdirectory per memex tool, each filled by that tool's arkiv export as a directory (not a bare `.zip`).
- [ ] Each memex HTML viewer goes in the matching `site/` with a README carrying `generator: <tool> <version>` (memex-side change, listed in the handoff).
- [ ] A refresh script that lives in the archive itself (`~/archive/refresh.sh`, described in the root README): export each tool, then `longecho check`, `longecho fixity check` (then `init` after an intended refresh), `longecho build`. Schedule it with a systemd user timer or cron.
- [ ] Success: `longecho check ~/archive` passes, `longecho query ~/archive` lists every tool, the built site opens from `file://` and links to each tool's viewer.

---

## Phase E: Public writing and stray references (memex and metafunctor repos)

- [ ] book-memex: fix `github.com/alextowell/longecho` (`book_memex/cli.py:4032`, `book_memex/exports/echo_export.py:274`); add frontmatter to the ECHO export README or retire that export in favor of arkiv.
- [ ] metafunctor update notes pointing to https://queelius.github.io/longecho/ as canonical: `post/2026-01-longecho-orchestration` (add a note), `post/2025-01-long-echo` (fix the note, which points at the stale post), `post/2026-02-07-ecosystem-overview` (remove "redundant storage, format migration, integrity verification", or say fixity is planned), `series/the-long-echo/_index.md` ("ECHO"), `post/2026-01-20-long-echo-ghost-speaks` and `post/2026-01-19-long-echo-photos-mail` ("ECHO-compliant", `--format longecho`).
- [ ] `metafunctor-series/the-long-echo/README.md`: drop "Archive orchestration".
- [ ] **Decision needed from the author:** the two degradation ladders. The blog's ladder is about formats (app, SQLite, grep JSONL, Markdown/HTML, plain text); the docs' ladder is about the reader's capabilities (LLM, browser, file browser, text editor, fragments). Proposal: keep the reader ladder as the headline in the docs and add the format ladder beside it as "what each layer reads", one short table.

## Phase F: Deliberately not doing

- `longecho mirror` (see C4). Universal viewer (arkiv owns it). Persona synthesis (out of scope by the docs' own "speaks for no one"). Requiring a frontmatter opt-in to cut `query ~` noise (would break "no special files"). Dropping `rich` is optional and low priority; revisit only if dependency weight becomes a real problem.
