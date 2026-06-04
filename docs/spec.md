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

## Durable formats

A durable format is one you can read without proprietary software, that has multiple independent implementations, and that has proven longevity. These are the formats the current release recognizes:

| Category | Formats |
|----------|---------|
| Structured data | `.db`, `.sqlite`, `.sqlite3`, `.json`, `.jsonl` |
| Documents | `.md`, `.markdown`, `.txt`, `.text`, `.rst`, `.html`, `.htm` |
| Archives | `.zip`, `.gz`, `.tgz` |
| Images | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` |
| Tabular / data | `.csv`, `.tsv`, `.xml`, `.yaml`, `.yml` |

Run `longecho formats` to print the recognized set from your installed release.

**Terminal-suffix rule.** Format detection looks at the last extension only. A compound name like `conversations.jsonl.gz` or `backup.tar.gz` qualifies via its terminal `.gz`, not via `.jsonl.gz` or `.tar.gz`. The `.tgz` form is the compact tar-gzip spelling and qualifies directly. One consequence: a source's reported `durable_formats` lumps every `*.gz` file under `.gz` regardless of what is inside.

**Archives are opaque.** The presence of a `.zip`, `.gz`, or `.tgz` file satisfies the durable requirement, but longecho never reads inside it. A directory holding only an archive plus a README is compliant, and the archive is treated as a single opaque durable artifact: longecho does not extract, inspect, validate, or index its contents. This matches how archives work everywhere else: they are transport containers, not working formats. To operate on what is inside, extract first and run longecho on the resulting directory.

## The README is the interface

The README is the interface. A human or an LLM can understand any longecho source by reading its README alone. Everything else is optional.

A README may begin with optional YAML frontmatter for structured metadata. With no frontmatter, a README is still perfectly valid: the heading and first paragraph supply the name and description, and the directory name is the final fallback.

The **name cascade** is: frontmatter `name`, then the first level-one (`#`) heading, then the directory name.

The **description cascade** is: frontmatter `description`, then the first paragraph after the heading.

Identity always comes from a source's own README. A parent never overrides a child's name or description. This is what keeps fragments legible: pull any subdirectory out of the tree and it still explains itself.

## The contents field

The `contents` frontmatter field lists what is in a directory. Each entry uses the explicit `path:` form, with an optional `description`. The field plays two roles, and they depend on whether the entry points at a directory or a file.

- **Directory entries** curate and order sub-sources for `longecho build`. Only listed directories become navigable sub-sources, and they appear in the order you list them.
- **File entries** are informational metadata only. They tell a reader what the directory holds, but they do not change the build structure and are not surfaced separately in the generated site.

Without a `contents` field, sub-source discovery is automatic: every longecho-compliant subdirectory appears, in alphabetical order.

## Recursive structure

A longecho source can contain other longecho sources, and the structure is the same at every level. Each directory is a self-describing source with its own README. Archives may nest arbitrarily.

Data files are source-scoped. Each source owns only the durable files it directly contains. When the tool gathers a source's data files it walks down but stops at any nested source, so a child's files belong to the child's detail view, not the parent's.

## The site convention

`longecho build` emits a single self-contained `site/index.html`: a single-file application with all content, CSS, and JavaScript inlined. README content and metadata are embedded as JSON, and client-side JavaScript handles navigation and search. Actual data files are linked by relative path so the browser can open or download them. Because everything is inlined or relative, the site works from `file://` with no server.

The generated `site/` directory is itself longecho-compliant: longecho writes it a `README.md` with frontmatter, so it appears in query results like any other source.

The build refuses to clobber a `site/` produced by another tool. If the output directory's `README.md` carries a `generator` field that does not begin with "longecho build", the build stops and tells you which tool owns it. Pass `--force` to override and overwrite anyway.
