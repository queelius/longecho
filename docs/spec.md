# Specification

This is the canonical reference for what makes a directory longecho-compliant and how the longecho tool reads it. The rules are small enough to hold in your head and stable enough to outlive the tool.

For how to run the commands, see [CLI reference](cli.md). For a gentle walkthrough, see [Quickstart](quickstart.md).

## Compliance

A directory is longecho-compliant if and only if it has both of these:

1. A root `README.md` or `README.txt` explaining what the data is.
2. At least one file in a durable format.

That's it. No special files, no schema, no version numbers.

Compliance checks **presence, not validity**. The tool confirms that a README exists and that at least one durable file exists. It does not parse, validate, or otherwise judge the contents of those files. An empty durable file still satisfies the rule: a zero-byte `data.jsonl` counts. Validity is a moving target that depends on tools and intent, while presence is something a future reader can verify with nothing but a file listing.

When a check fails, `longecho check` returns a human-readable reason, not just a boolean. You will see one of "No README.md or README.txt found", "No durable data formats found", "Path does not exist", or "Path is not a directory". The reason tells you exactly what to fix.

## Warnings

A check can also return warnings. They point at things a future reader might be unable to open, or might never receive, but they never change the verdict: a compliant directory with warnings is still compliant.

- **Unrecognized formats.** Files the source owns that are neither in a durable format nor plain text (a `.heic` photo, a `.docx` letter, a compiled program) are counted and grouped by extension. A file with an extension longecho does not know but whose content is UTF-8 text (a `.py` script, a `.tex` paper, a `LICENSE`) does not warn, because a text editor opens it. To tell the two apart, longecho reads the first 4 KB of each such file; this is the only time it looks inside a file, and it never affects the verdict. Nothing is hidden: the generated site lists every file, and marks the ones that warn.
- **SQLite sidecars at risk.** A SQLite database in write-ahead-log mode keeps recent changes in a `-wal` file next to it. Copy the `.db` alone and those changes may be lost. A non-empty `-wal`, or a leftover `-journal` from an interrupted write, raises a warning that says how to fold it back in. The `-shm` file is transient and never warns.

Warnings cover only the files a source owns, so a nested source's warnings show up when you check that source, not its parent.

## Durable formats

A format is durable when a future reader can still open it without the software that wrote it. longecho judges that against the Library of Congress sustainability factors, weighed together rather than as a checklist:

| Factor | The question |
|--------|--------------|
| Disclosure | Is the specification published and open to anyone? |
| Adoption | Is it widely used, so new readers keep being written? |
| Transparency | Can simple tools inspect it, ideally as plain text? |
| Self-documentation | Can a file carry its own descriptive metadata? |
| External dependencies | Does it need a particular program, platform, or service? |
| Impact of patents | Do patents limit who may write a reader? |
| Technical protection | Does DRM or mandatory encryption guard the content? |

These are the formats the current release recognizes:

| Category | Formats |
|----------|---------|
| Structured data | `.db`, `.sqlite`, `.sqlite3`, `.json`, `.jsonl` |
| Documents | `.md`, `.markdown`, `.txt`, `.text`, `.rst`, `.html`, `.htm`, `.pdf`, `.epub` |
| Mail | `.eml`, `.mbox` |
| Tabular / data | `.csv`, `.tsv`, `.xml`, `.yaml`, `.yml` |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.tif`, `.tiff` |
| Audio | `.wav`, `.flac`, `.mp3`, `.ogg`, `.opus` |
| Video | `.mp4`, `.webm` |
| Archives | `.zip`, `.gz`, `.tgz` |

Each format in the list records three things: its media type, a one-line reason it qualifies, and which readers can open it. A reader is one of three kinds, matching the rungs of the [degradation ladder](index.md):

- a **standard tool**: a free program that ships with or is packaged for every mainstream OS, such as `sqlite3`, `unzip`, an image viewer, or a PDF or ebook reader;
- a **web browser**, opening the file directly;
- a **text editor**, reading the file as plain text.

Run `longecho formats` to see every format with its readers and its reason, or `longecho formats --json` for the same list as data. The list is one table in the code, and everything else (this check, the `spec` summary, the site's previews) is derived from it. Adding a format means adding one entry and writing down why it qualifies.

Some formats were left out on purpose. HEIC is patent-encumbered and not decoded everywhere (most browsers cannot show it, and Windows needs an add-on). `.docx` and the other office formats are published standards, but faithful rendering still depends on one vendor's software. Keep them if you have them, but also keep a copy in a listed format (JPEG or PNG for photos, PDF or Markdown for documents) if you want a future reader to be able to open it.

**Terminal-suffix rule.** Format detection looks at the last extension only. A compound name like `conversations.jsonl.gz` or `backup.tar.gz` qualifies via its terminal `.gz`, not via `.jsonl.gz` or `.tar.gz`. The `.tgz` form is the compact tar-gzip spelling and qualifies directly. One consequence: a source's reported `durable_formats` lumps every `*.gz` file under `.gz` regardless of what is inside.

**Archives are opaque.** The presence of a `.zip`, `.gz`, or `.tgz` file satisfies the durable requirement, but longecho never reads inside it. A directory holding only an archive plus a README is compliant, and the archive is treated as a single opaque durable artifact: longecho does not extract, inspect, validate, or index its contents. This matches how archives work everywhere else: they are transport containers, not working formats. To operate on what is inside, extract first and run longecho on the resulting directory.

## The README is the interface

The README is the interface. A human or an LLM can understand any longecho source by reading its README alone. Everything else is optional.

A README may begin with optional YAML frontmatter for structured metadata. With no frontmatter, a README is still perfectly valid: the heading and first paragraph supply the name and description, and the directory name is the final fallback.

The **name cascade** is: frontmatter `name`, then the first level-one (`#`) heading, then the directory name.

The **description cascade** is: frontmatter `description`, then the first paragraph after the heading.

Identity always comes from a source's own README. A parent never overrides a child's name or description. This is what keeps fragments legible: pull any subdirectory out of the tree and it still explains itself.

### The top-level README

The README at the top of a whole archive (the root of a drive, or of the folder you would hand to someone) is where a reader with no context starts. There is no separate "start here" file: this README is that file. Write it for someone who has none of your tools and does not know you made them. Say what the archive is, who it belongs to, and how to open each kind of file in it, down to the plainest option. If you would rather not assume the reader knows Markdown, name it `README.txt`.

## The contents field

The `contents` frontmatter field lists what is in a directory. Each entry uses the explicit `path:` form, with an optional `description`. The field plays two roles, and they depend on whether the entry points at a directory or a file.

- **Directory entries** curate and order sub-sources for `longecho build`. Only listed directories become navigable sub-sources, and they appear in the order you list them.
- **File entries** are informational metadata only. They tell a reader what the directory holds, but they do not change the build structure and are not surfaced separately in the generated site.

Without a `contents` field, sub-source discovery is automatic: every longecho-compliant subdirectory appears, in alphabetical order.

## Recursive structure

A longecho source can contain other longecho sources, and the structure is the same at every level. Each directory is a self-describing source with its own README. Archives may nest arbitrarily.

Data files are source-scoped. Each source owns the files it directly contains, durable or not. When the tool gathers a source's files it walks down but stops at any nested source, `site/` directory, or tool directory (such as `node_modules`), so a child's files belong to the child's detail view, not the parent's.

## The site convention

`longecho build` emits a single self-contained `site/index.html`: a single-file application with all content, CSS, and JavaScript inlined. README content and metadata are embedded as JSON, and client-side JavaScript handles navigation and search. Actual data files are linked by relative path so the browser can open or download them. Images, audio, and video that a browser can play are previewed inline (lazily, so a large photo folder does not load all at once); which formats preview is derived from the format list. Files that are neither in a recognized format nor plain text are listed and marked rather than left out. Because everything is inlined or relative, the site works from `file://` with no server.

The generated `site/` directory is itself longecho-compliant: longecho writes it a `README.md` with frontmatter, so it appears in query results like any other source.

The build overwrites a non-empty `site/` only when its `README.md` carries a `generator` field beginning with "longecho build", meaning longecho made it. Any other `site/` (another tool's stamp, or a viewer with no README at all) stops the build, which tells you who owns it. Pass `--force` to overwrite anyway. Tools that write a viewer into `site/` should stamp it with `generator: <tool> <version>`.
