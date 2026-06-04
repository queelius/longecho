# longecho Documentation Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a succinct, ethos-forward Material for MkDocs site for longecho that articulates and promotes the durable-archive philosophy, and that passes the already-wired `mkdocs build --strict` CI.

**Architecture:** Five-page site (Home/manifesto, Quickstart, Specification, CLI reference, Ecosystem). `mkdocs.yml` at repo root, content in `docs/`, internal planning files (`docs/ideas/`, `docs/superpowers/`) excluded from the build via `exclude_docs`. Pages are independent prose, drafted in parallel, each grounded in authoritative repo sources, then assembled and verified with one strict build.

**Tech Stack:** Material for MkDocs (already pinned by `.github/workflows/docs.yml`), Python, GitHub Pages.

**Verification model (replaces unit-test TDD):** there is no application code here. The acceptance gate for the whole site is `mkdocs build --strict` exiting 0 with zero warnings. Each content task additionally has a content-fidelity checklist: specific facts and verbatim quotes that must appear, plus the editorial rules from the spec. Drafting agents must read the cited repo source files directly. They must not invent capabilities.

**Editorial rules (apply to every page):**
1. Vocabulary anchors on the shipped CLI: *longecho-compliant*, `contents` frontmatter, commands `check`/`query`/`build`/`spec`/`formats`. Never use ECHO-compliant, `manifest.yaml`, `serve`, `discover`, `search`.
2. Tone: plain, declarative, anti-hype, technically precise, quietly emotional. Verbatim epigraphs as pull-quotes. Personal "why" is one honest line plus an outbound link, never a memoir.
3. Version-agnostic prose: never hardcode a version number. Say "the current release" and let `pip install longecho` be the source of truth.
4. Honesty: compliance checks presence, not validity. No claims of content validation, archive traversal, query DSL, autonomous behavior, or persona synthesis. **No mention of longshade anywhere.**
5. Internal links must resolve (strict mode fails otherwise). External links to metafunctor.com are fine (strict does not check them).
6. **Voice: no em-dashes.** Use commas, periods, colons, or parentheses. This is enforced by a soul voice hook on every write.

**Commit policy:** Per the user's global rule ("commit only when asked; branch first on the default branch"), this plan does not commit per-task. All file changes accumulate in the working tree. A single branch (`docs/mkdocs-site`) plus commit happens at the end only when the user approves (Task 8).

---

## File structure

| File | Responsibility |
|------|----------------|
| `mkdocs.yml` (create) | Site config: theme, nav, markdown extensions, `exclude_docs`. |
| `pyproject.toml` (modify) | Add `[project.optional-dependencies] docs`. |
| `docs/index.md` (create) | Home / manifesto, the promote surface. |
| `docs/quickstart.md` (create) | Install, then compliant in 5 min, then build a site. |
| `docs/spec.md` (create) | Canonical reference for compliance, formats, README contract, recursion, site/SFA. |
| `docs/cli.md` (create) | The five commands and their key flags. |
| `docs/ecosystem.md` (create) | Sibling-toolkit map plus outbound links. |

`docs/ideas/` and `docs/superpowers/` are untouched and excluded from the build.

---

## Task 1: Scaffold the build (config plus minimal home) and prove `--strict` passes

**Files:**
- Create: `mkdocs.yml`
- Modify: `pyproject.toml` (add docs extra)
- Create: `docs/index.md` (temporary minimal stub, replaced in Task 3)

- [ ] **Step 1: Write `mkdocs.yml`**

```yaml
site_name: longecho
site_description: A philosophy and a tool for durable personal archives.
site_url: https://queelius.github.io/longecho/
repo_url: https://github.com/queelius/longecho
repo_name: queelius/longecho
copyright: Copyright &copy; Alexander Towell

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle:
        icon: material/weather-night
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle:
        icon: material/weather-sunny
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.top
    - content.code.copy
    - search.suggest
    - toc.follow

nav:
  - Home: index.md
  - Quickstart: quickstart.md
  - Specification: spec.md
  - CLI reference: cli.md
  - Ecosystem: ecosystem.md

markdown_extensions:
  - admonition
  - attr_list
  - md_in_html
  - tables
  - toc:
      permalink: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true

exclude_docs: |
  ideas/
  superpowers/
```

- [ ] **Step 2: Add the docs extra to `pyproject.toml`**

In `[project.optional-dependencies]`, after the `dev = [...]` list, add:

```toml
docs = [
    "mkdocs-material>=9.0.0",
]
```

- [ ] **Step 3: Write a temporary `docs/index.md` stub** so the nav's first entry resolves

```markdown
# longecho

A philosophy and a tool for durable personal archives.
```

> Note: the four other nav targets (`quickstart.md`, `spec.md`, `cli.md`, `ecosystem.md`) do not exist yet, so a strict build at this step will fail on missing nav files. That is expected. The real strict gate is Task 7, once all pages exist. To prove the config itself is valid now, run a NON-strict build.

- [ ] **Step 4: Install docs deps and verify a non-strict build succeeds**

Run:
```bash
cd /home/spinoza/github/beta/longecho
pip install -e ".[docs]"
mkdocs build 2>&1 | tail -20
```
Expected: build completes and writes `site/`. Warnings about the four not-yet-created nav files are acceptable at this step. Confirm there is no error about `exclude_docs`, theme, or markdown extensions.

- [ ] **Step 5: Verify internal planning files are excluded**

Run:
```bash
test ! -e site/superpowers && test ! -e site/ideas && echo "EXCLUDED OK" || echo "LEAK"
```
Expected: `EXCLUDED OK`.

---

## Task 2 (parallel-eligible): Draft `docs/quickstart.md`

**Files:** Create `docs/quickstart.md`
**Read first (authoritative):** `README.md` (Compliance, The README, Building a Site sections), `src/longecho/cli.py` (command/flag surface).

**Content-fidelity checklist, the page MUST:**
- [ ] Open with the promise: in a few minutes, make a directory into a durable, self-describing archive.
- [ ] Show install: `pip install longecho`.
- [ ] Show `longecho check ~/some/dir` and explain the two requirements it verifies: a `README.md`/`README.txt` and at least one file in a durable format. Quote: *"That's it. No special files, no schema, no version numbers."*
- [ ] Show the "make it compliant" path: add a `README.md` that says what the data is, then keep data in durable formats (link to Specification for the full list).
- [ ] Show building the viewer: `longecho build ~/some/dir`, then open `site/index.html` directly. State it works from `file://` with no server.
- [ ] Show one query example: `longecho query ~/ --search "term"`, and mention `--json` for piping to `jq`.
- [ ] End with a CTA linking to `spec.md` (the full contract) and `index.md` (the why).
- [ ] Use Material admonitions/tabs sparingly for the copy-paste commands.

**Verification:** included in Task 7 strict build. Self-check: `grep -i "manifest\|serve\|discover\b\|ECHO-compliant" docs/quickstart.md` returns nothing.

---

## Task 3 (parallel-eligible): Draft `docs/index.md` (Home / manifesto), replaces the stub

**Files:** Create/overwrite `docs/index.md`
**Read first:** `README.md` (Philosophy plus Core Principles plus Compliance), and the survey's verbatim quotes below.

**Content-fidelity checklist, the page MUST:**
- [ ] Lead with the thesis, verbatim: *"longecho is a bet that with enough self-description and simple formats, your data can outlive the tools that created it. The name evokes what we're after: your voice, echoing forward through time."*
- [ ] Feature the epigraph as a pull-quote (blockquote): *"Not resurrection. Not immortality. Just love that still responds."* Immediately follow with ONE honest personal line (durability is urgent, these tools are built under that awareness) and an outbound link to the essays at `https://metafunctor.com/series/the-long-echo/`. No more personal detail than that.
- [ ] Distill the five principles (Self-Describing, Durable Formats, Graceful Degradation, Local-First, Trust the Future), one tight sentence each. Include the line: *"A human or LLM finding your data in 50 years, with no context, should be able to understand what they're looking at."* and *"If you have to choose between a simple format and a 'more correct' one, choose simple."*
- [ ] Present the graceful-degradation ladder as the centerpiece table (verbatim rows):

  | If you have... | You can still... |
  |----------------|------------------|
  | Modern LLMs | Have conversations with the archive |
  | A web browser | Navigate a generated site |
  | A file browser | Explore organized directories |
  | A text editor | Read plain text files |
  | Only fragments | Understand each piece independently |

- [ ] Include a **"What longecho is not"** section (a section here, not its own nav page): no autonomous daemon or "digital ghost", no fake presence; it does not validate file contents (presence, not validity); it does not traverse into archives (extract first); it has no query language (plain substring search, with `--json | jq` for structure). Frame these as deliberate, ethos-driven boundaries.
- [ ] Close with the epigraph: *"The archive is not a monument. It is a conversation that outlasts its participants."*
- [ ] End with a clear CTA to `quickstart.md`.

**Verification:** Task 7 strict build. Self-check: the home page must NOT mention longshade, manifest.yaml, or version numbers.

---

## Task 4 (parallel-eligible): Draft `docs/spec.md` (Specification)

**Files:** Create `docs/spec.md`
**Read first:** `README.md` (Compliance, Durable Formats, The README, Frontmatter, Nesting, The site/ convention), `CLAUDE.md` (Key Design Decisions), `src/longecho/checker.py` (DURABLE_FORMAT_CATEGORIES, name/description cascade), `src/longecho/build.py` (contents field, SFA).

**Content-fidelity checklist, the page MUST cover, with anchored `##` sections:**
- [ ] **Compliance:** a directory is longecho-compliant if and only if it has a root `README.md`/`README.txt` AND at least one file in a durable format. Quote *"That's it. No special files, no schema, no version numbers."* Note that compliance checks presence, not validity, and that a failed check returns a human-readable reason, not just a boolean.
- [ ] **Durable formats:** the full current table (Structured `.db .sqlite .sqlite3 .json .jsonl`; Documents `.md .markdown .txt .text .rst .html .htm`; Archives `.zip .gz .tgz`; Images `.jpg .jpeg .png .webp .gif`; Tabular/data `.csv .tsv .xml .yaml .yml`). State the principle: readable without proprietary software, multiple implementations, proven longevity. Explain the terminal-suffix rule (`.jsonl.gz`, `.csv.gz`, `.tar.gz` qualify via `.gz`). Explain archive opacity, quoting *"they are transport containers, not working formats."*
- [ ] **The README is the interface:** quote *"The README is the interface."* Document optional YAML frontmatter, the name cascade (frontmatter `name`, then first `# Heading`, then directory name) and description cascade (frontmatter `description`, then first paragraph). State: identity always comes from a source's own README, no parent overrides.
- [ ] **The `contents` field:** directory entries curate and order sub-sources for `build`; file entries are informational metadata only and do not affect build structure; absent `contents`, discovery is alphabetical.
- [ ] **Recursive structure:** every level is the same kind of self-describing source; archives nest arbitrarily; each source owns only the data files it directly contains (nested sources own theirs).
- [ ] **The `site/` convention plus SFA:** `longecho build` emits a single self-contained `site/index.html` (all content/CSS/JS inlined, data files linked relatively) that works from `file://`; the generated `site/` is itself longecho-compliant; foreign-site overwrite protection guards tool-generated viewers unless `--force` is passed.

**Verification:** Task 7 strict build. Self-check: every durable extension listed matches `DURABLE_FORMAT_CATEGORIES` in `src/longecho/checker.py` exactly.

---

## Task 5 (parallel-eligible): Draft `docs/cli.md` (CLI reference)

**Files:** Create `docs/cli.md`
**Read first:** `src/longecho/cli.py` (the five commands and their options), `README.md` (usage examples).

**Content-fidelity checklist, one concise `##` section per command:**
- [ ] `check [PATH]`: report whether a directory is compliant and why, a human-readable pass/fail with reasons. Default PATH is `.`.
- [ ] `query [PATH]`: discover/search/filter sources across a tree; `--search "term"` for case-insensitive text search across name, description, README, and frontmatter values; `--json` for machine output (pipe to `jq`); mention `--depth` for filesystem depth.
- [ ] `build [PATH]`: generate the single-file site (`site/index.html`); `--force`/`-f` to override foreign-site overwrite protection; note it works from `file://`.
- [ ] `spec`: print the specification summary (the five principles, derived from code).
- [ ] `formats`: list recognized durable formats (rendered from the single source of truth).
- [ ] State that all commands default PATH to the current directory, and that `--json` output is plain (jq-friendly).

**Verification:** Task 7 strict build. Self-check: only these five commands appear, no `serve`/`discover`/`search` subcommands.

---

## Task 6 (parallel-eligible): Draft `docs/ecosystem.md` (Ecosystem)

**Files:** Create `docs/ecosystem.md`
**Read first:** `README.md` (Ecosystem section, authoritative), `CLAUDE.md` (Ecosystem line: arkiv, memex, repoindex, chartfold, jot, pagevault). Ground the page in what the repo actually says. Do not import the blog's older framing.

**Content-fidelity checklist, the page MUST:**
- [ ] Frame longecho as an orchestration/convention layer: any tool that emits a `README.md` plus durable formats produces a longecho-compliant source; longecho checks, queries, and builds across them without modifying the data.
- [ ] Present the tagged `longecho-ecosystem` members from the repo (arkiv, memex, repoindex, chartfold, jot, pagevault, posthumous), one line each, each clearly labeled a separate repo.
- [ ] Present the personal toolkits (ctk, btk, ebk, mtk, ptk) as illustrative example producers of durable exports, distinct from the tagged ecosystem members (mirror the CHANGELOG's distinction). One line each.
- [ ] Note that the generated `site/` is fractal: a parent archive's site links to its children's sites.
- [ ] Link out to the blog series (`https://metafunctor.com/series/the-long-echo/`) and the longecho project page (`https://metafunctor.com/projects/longecho/`) for the broader narrative.
- [ ] **No persona-synthesis / longshade content. No "digital afterlife" endpoint.**

**Verification:** Task 7 strict build. Self-check: `grep -i "longshade\|persona synth\|digital afterlife" docs/ecosystem.md` returns nothing.

---

## Task 7: Assemble, reconcile cross-links, and pass the strict build (the real gate)

**Files:** all five `docs/*.md`, possibly `mkdocs.yml`

- [ ] **Step 1: Verify all five nav files exist**

```bash
cd /home/spinoza/github/beta/longecho
for f in index quickstart spec cli ecosystem; do test -f "docs/$f.md" && echo "ok $f" || echo "MISSING $f"; done
```
Expected: five `ok` lines.

- [ ] **Step 2: Reconcile internal cross-links** so every `[...](....md)` link and anchor between pages resolves (Home to Quickstart, Quickstart to Spec/Home, Spec anchors, and so on). Use relative `.md` links (Material resolves them).

- [ ] **Step 3: Run the strict build (THE acceptance gate)**

```bash
mkdocs build --strict 2>&1 | tail -30
```
Expected: exits 0, prints no `WARNING`/`ERROR` lines. Strict fails on broken internal links and orphaned pages. Fix any reported issue and re-run until clean.

- [ ] **Step 4: Re-verify planning files stayed excluded**

```bash
test ! -e site/superpowers && test ! -e site/ideas && echo "EXCLUDED OK" || echo "LEAK"
```
Expected: `EXCLUDED OK`.

- [ ] **Step 5: Editorial self-check across the source pages**

```bash
grep -rIi "manifest.yaml\|ECHO-compliant\|longshade\|\bserve\b\|\bdiscover\b" docs/*.md || echo "CLEAN VOCAB"
```
Expected: `CLEAN VOCAB` (no stale vocabulary or out-of-scope mentions).

---

## Task 8: Branch plus commit (only on user approval)

- [ ] **Step 1: Ask the user to confirm committing** (per global "commit only when asked" rule).
- [ ] **Step 2: Branch and commit** (we are on `main`, so branch first)

```bash
cd /home/spinoza/github/beta/longecho
git checkout -b docs/mkdocs-site
git add mkdocs.yml pyproject.toml docs/index.md docs/quickstart.md docs/spec.md docs/cli.md docs/ecosystem.md docs/superpowers/
git commit -m "docs: add Material for MkDocs site articulating the longecho ethos

Five-page ethos-forward site (Home/manifesto, Quickstart, Specification,
CLI reference, Ecosystem) that fills in the already-wired docs.yml CI.
Internal planning files excluded via exclude_docs.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 3:** Offer to push and open a PR, or to merge to `main`, per the user's preference.

---

## Self-Review (run against the spec)

**Spec coverage:** Home (ethos, principles, ladder, what-it-is-not, epigraphs) maps to Task 3. Quickstart maps to Task 2. Specification (compliance, formats, README contract, recursion, site/SFA) maps to Task 4. CLI (five commands) maps to Task 5. Ecosystem (toolkits, links, no longshade) maps to Task 6. `mkdocs.yml` plus `exclude_docs` plus docs extra map to Task 1. Strict-build gate plus exclusion plus vocab check map to Task 7. Commit policy maps to Task 8. All spec sections covered.

**Placeholder scan:** no TBD/TODO. Every config block and content checklist is concrete, and commands have expected output.

**Type/consistency:** the five filenames, nav titles, and `exclude_docs` patterns are identical across Tasks 1, 7, 8. The durable-formats list is identical between the spec and Task 4. The command set (check/query/build/spec/formats) is identical between the spec, Task 5, and Task 7's vocab check.
