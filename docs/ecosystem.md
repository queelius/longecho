# Ecosystem

longecho is a convention before it is a program. The convention is small: a directory that carries a `README.md` (or `README.txt`) plus data in durable formats is a longecho-compliant source. Any tool that emits those two things produces one, whether or not it ever heard of longecho.

That is what makes longecho an orchestration layer rather than a framework. It does not own your data and it does not ask the tools to change. It walks the tree and reports on what is already there. `check` tells you whether a directory is compliant. `query` finds and searches sources across the whole tree. `build` generates a single-file site over them. None of these commands rewrite, migrate, or reformat the underlying data. The tools below stay independent: each is its own repository, with its own home, and each works without longecho installed.

## Sibling tools

These repositories carry the `longecho-ecosystem` GitHub topic. Each is independent, lives in its own repository, and produces longecho-compliant exports.

- [arkiv](https://github.com/queelius/arkiv): universal personal data format (JSONL in, SQL out), the data-format backbone several of the others build on.
- [memex](https://github.com/queelius/memex): personal conversation knowledge base across providers.
- [repoindex](https://github.com/queelius/repoindex): filesystem git catalog with project metadata.
- [chartfold](https://github.com/queelius/chartfold): personal health data consolidated from multiple record systems into SQLite.
- [jot](https://github.com/queelius/jot): plaintext journal, notes, and tasks.
- [pagevault](https://github.com/queelius/pagevault): password-protected content for static sites.

[posthumous](https://github.com/queelius/posthumous), a federated deadman-switch with TOTP check-in, is adjacent rather than a producer: it shares the same durable, local-first, self-hosted stack.

## Illustrative example producers

The personal toolkits below are not tagged ecosystem members. They are separate examples of how ordinary tools become producers: each exports durable files alongside a self-describing README, so the export is longecho-compliant by construction.

- `ctk`: conversation archives.
- `btk`: bookmark archives.
- `ebk`: ebook metadata.
- `mtk`: mail archives.
- `ptk`: photo libraries.

Markdown sources (Hugo, Obsidian, plain note folders) are compliant with no extra work, since Markdown is already a durable format.

## Fractal sites

The generated sites compose. A parent archive's site links out to each child's site, so an archive of archives stays navigable at every level. You can run `build` at the top and reach every interface below it without leaving the page.

## Read further

The broader narrative lives in [The Long Echo essays](https://metafunctor.com/series/the-long-echo/) and on the [longecho project page](https://metafunctor.com/projects/longecho/). For the convention itself, see [the philosophy](index.md) and the [Specification](spec.md).
