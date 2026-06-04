# Design: longecho documentation site (mkdocs)

**Date:** 2026-06-04
**Status:** Approved (design), pending implementation
**Author:** Alexander Towell

## Goal

Create a small, ethos-forward documentation site for longecho using Material for
MkDocs. The site's job is to **articulate the longecho ethos and promote it**
(durable, self-describing personal archives), with the CLI as the proof. "Nice and
succinct" is an explicit constraint: a tight site, not an exhaustive manual.

## Why now / decisive constraint

The docs site is **already half-wired and currently failing**. `.github/workflows/docs.yml`
runs `pip install mkdocs-material`, then `mkdocs build --strict`, then deploys to GitHub
Pages on every push to `main`, but there is no `mkdocs.yml` and no published `docs/*.md`
content (only the internal `docs/ideas/schema-yaml-awareness.md` roadmap note). So:

- **Theme is decided for us:** Material for MkDocs.
- **The build must pass `--strict`** (zero warnings, no broken internal links, no
  pages-not-in-nav) or CI stays red.
- We are not choosing whether to deploy. We are filling in a site the CI is already
  waiting to publish.

## Audience & positioning (resolved with the user)

1. **Center of gravity: ethos-forward.** Lead with the philosophy/manifesto; the CLI
   is the proof-of-concept. Promote the *idea* that anyone can make a durable,
   self-describing archive, and longecho is how.
2. **Personal register: light touch plus link.** One or two honest, load-bearing lines
   (the "love that still responds" epigraph, a sentence on why durability is urgent),
   then link out to the metafunctor essays where the full personal story lives. The
   site promotes the ethos without becoming a memoir.
3. **Ecosystem scope: a short "Ecosystem" page.** Map the sibling toolkits (separate
   repos) that emit durable, self-describing exports longecho can orchestrate.
   Persona-synthesis / "digital afterlife" endpoints (e.g. longshade) are out of
   scope and are **not mentioned anywhere on the site.**

## Information architecture (Approach A: Manifesto + Field Guide)

Five pages. Ethos surface first, compact practical tier after.

| Nav title | File | Content |
|-----------|------|---------|
| Home | `docs/index.md` | The manifesto. Thesis ("a bet that with enough self-description and simple formats, your data can outlive the tools that created it"); the "Not resurrection. Not immortality. Just love that still responds." epigraph as a pull-quote, with one honest personal line plus an outbound link to the essays; the five principles distilled; the graceful-degradation ladder as the centerpiece; a punchy **"What longecho is NOT"** section (no daemon, no autonomous ghost, no content validation, no traversal into archives); a 30-second "what makes a directory compliant" teaser leading to a CTA to Quickstart. |
| Quickstart | `docs/quickstart.md` | `pip install longecho`; `longecho check ~/dir`; "make any directory compliant in 5 minutes" (add a README, keep durable files); `longecho build`, then open the single-file site from `file://`. Copy-pasteable, fast. |
| Specification | `docs/spec.md` | Canonical reference: the compliance rule (README plus durable formats, "no special files, no schema, no version numbers"); the durable-formats table; the README/frontmatter contract (name/description/`contents` cascade; dirs curate, files are informational); the recursive/fractal source model; the `site/` convention plus Single-File Application (SFA). Anchored sections; split only if it runs long. |
| CLI reference | `docs/cli.md` | The five shipped commands (`check`, `query`, `build`, `spec`, `formats`) with concise usage and the flags that matter (`--search`, `--json`, `--force`, `--depth`). Curated, not a `--help` dump. |
| Ecosystem | `docs/ecosystem.md` | The toolkit map (ctk/btk/ebk/mtk/ptk/memex feeding longecho orchestration), every sibling clearly labeled "separate repo" that emits durable, self-describing exports; how the graceful-degradation ladder connects them. Links out to the blog series and `posthumous`. No persona-synthesis / longshade mention. |

"What longecho is not" is a **section on Home**, not a standalone nav entry (user-approved).

## mkdocs.yml configuration decisions

- `site_name: longecho`, `site_description` from the tagline, `repo_url:
  https://github.com/queelius/longecho`, `repo_name: queelius/longecho`, `site_url`
  set to the GitHub Pages URL, `copyright` with the author's name.
- `theme: material` with: palette light/dark toggle; features `navigation.instant`,
  `navigation.top`, `content.code.copy`, `search.suggest`, `toc.follow`. Lean, no
  feature sprawl.
- `markdown_extensions`: `admonition`, `pymdownx.superfences`, `pymdownx.tabbed`
  (`alternate_style: true`), `attr_list`, `md_in_html`, `tables`, `toc`
  (`permalink: true`). All ship with mkdocs-material, so `--strict` stays green.
- **`exclude_docs:`** lists `ideas/` and `superpowers/` so the existing roadmap note
  and this design spec live in `docs/` under version control but never publish and
  never trip `--strict`'s page-not-in-nav check.
- `nav:` explicitly lists the five pages in order (Home, Quickstart, Specification,
  CLI reference, Ecosystem).
- Add `[project.optional-dependencies] docs = ["mkdocs-material"]` to `pyproject.toml`
  so `pip install -e ".[docs]"` works for local preview. CI keeps installing
  mkdocs-material directly (no change to `docs.yml` required).

## Editorial rules (baked into every page)

1. **Vocabulary anchors on the shipped CLI.** Use *longecho-compliant*, the `contents`
   frontmatter field, and the commands `check`/`query`/`build`/`spec`/`formats`. The
   blog-era terms ECHO-compliant, `manifest.yaml`, `serve`, `discover`, `search` are
   historical and do **not** appear in the docs.
2. **Durable-formats list is the current, broader one** from the repo/README:
   Structured (`.db .sqlite .sqlite3 .json .jsonl`), Documents (`.md .markdown .txt
   .text .rst .html .htm`), Archives (`.zip .gz .tgz`, opaque), Images (`.jpg .jpeg
   .png .webp .gif`), Tabular/data (`.csv .tsv .xml .yaml .yml`). Note the terminal-
   suffix rule for compound extensions (`.jsonl.gz` qualifies via `.gz`).
3. **Tone:** plain, declarative, anti-hype, technically precise, quietly emotional.
   Verbatim epigraphs as pull-quotes. The personal "why" is one honest line plus
   outbound links, never a memoir.
4. **Version-agnostic prose.** Don't hardcode version strings in body copy (the
   sources drift: README example shows v0.3.0, pyproject is v0.4.0). Refer to "the
   current release" and let `pip install longecho` be the source of truth.
5. **No invented capabilities.** Compliance checks *presence, not validity*. State
   this honestly. Do not claim content validation, archive traversal, or a query DSL.
6. **Voice: no em-dashes.** Use commas, periods, colons, or parentheses. A soul voice
   hook enforces this on every write.

## Source material map (where each page's facts come from)

- Repo: `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `src/longecho/*` (authoritative for
  the shipped CLI, compliance rule, formats, frontmatter contract, SFA behavior).
- metafunctor site (`~/github/repos/metafunctor`): `content/projects/longecho/index.md`
  (near-complete public spec), the `the-long-echo` series, and the personal essays.
  This is the source for voice, epigraphs, and the outbound links.
- Blog series source (`~/github/metafunctor-series/the-long-echo`): richest prose for
  the ethos; source for the graceful-degradation ladder framing and the echo metaphor.

## Verification plan

- **Primary gate:** `mkdocs build --strict` passes with zero warnings. Run locally
  before claiming done; this is exactly what CI enforces.
- `mkdocs serve` for visual preview during drafting.
- Sanity-check every internal link and the nav (strict mode fails on broken links and
  orphan pages).
- Confirm the existing `docs/ideas/...` note and this spec are excluded from the built
  `site/`.

## Out of scope (non-goals)

- No changes to longecho's code or CLI behavior. Docs only.
- No new blog posts; the metafunctor essays are linked, not duplicated.
- No documentation of unshipped or sensitive forward-looking features. Persona-
  synthesis / "digital afterlife" endpoints (e.g. longshade) are **not mentioned on
  the site at all.** Ecosystem contract details that live in other repos are
  summarized, not specified.
- No Diátaxis ceremony, no versioned-docs (mike), no API autodoc. All out of
  proportion for a ~1000-line tool.

## Implementation approach

The five pages are independent prose. Draft them in parallel (a workflow with one
agent per page, each grounded in the exact source facts above and the editorial rules),
then reconcile cross-links, write `mkdocs.yml` and the `pyproject.toml` docs extra, and
run one `mkdocs build --strict`. Fix any strict warnings before completion.
