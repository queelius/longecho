# Quickstart

In a few minutes you can turn any directory into a durable, self-describing archive: one that a human or an LLM can still read decades from now, with no special software.

## Install

```bash
pip install longecho
```

This installs the current release and gives you the `longecho` command.

## Check a directory

Point `longecho check` at any directory to see whether it is longecho-compliant.

```bash
longecho check ~/some/dir
```

The check verifies exactly two things: a `README.md` or `README.txt` at the root, and at least one file in a durable format.

That's it. No special files, no schema, no version numbers.

!!! note
    `check` confirms the README and durable files are *present*. It does not validate their contents. That is the point: presence is cheap to verify and easy to trust.

## Make it compliant

If the check fails, you are usually one step away. Do two things:

1. Add a `README.md` at the root that says, in plain words, what the data is and where it came from.
2. Keep your data in durable formats: SQLite, JSON, JSONL, Markdown, CSV, plain text, common image formats, and similar.

See the [Specification](spec.md) for the full format list and the README conventions, including the optional `contents` frontmatter field.

## Build a browsable site

Once a directory is compliant, generate a single-file site for it.

```bash
longecho build ~/some/dir
```

This writes `site/index.html` inside the directory. Open that file directly in a browser:

```bash
xdg-open ~/some/dir/site/index.html   # or just double-click it
```

It works from `file://` with no server and no external dependencies. All content, styles, and navigation are inlined into the one file, so it keeps working even if it is copied to a thumb drive or read fifty years from now.

## Search across an archive

To find sources across a whole tree, use `query` with a search term.

```bash
longecho query ~/ --search "term"
```

For structured output you can pipe into other tools, add `--json`:

```bash
longecho query ~/ --json | jq '.[].name'
```

Search is plain text over names, descriptions, and README bodies. There is no query language to learn; `--json` plus `jq` covers the structured cases.

## Next steps

Read the [Specification](spec.md) for the full contract: what counts as compliant, every durable format, and how the README and `contents` field work. Or step back and read [the philosophy](index.md) behind durable personal archives.
