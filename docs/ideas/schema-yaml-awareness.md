# schema.yaml as a recognized self-description convention

**Status:** Tentative. Not on the roadmap. Not implemented.
**Origin:** April 2026 conversation about how arkiv and longecho compose.

## The shape of the idea

longecho currently treats `schema.yaml` as a recognized durable
extension (`.yaml`) but does not parse it or use its contents. This
note proposes that longecho could optionally recognize `schema.yaml`
as a generic self-description convention, the same way it recognizes
`README.md` today, and surface its contents in `--verbose` output and
in generated SFA cards.

The key design constraint: this would be a recognition of a
**convention**, not of any specific producer. longecho would not
import any arkiv code, would not depend on the arkiv package, and
would not have arkiv-specific branches. Other projects could produce
`schema.yaml` files in the same general shape and longecho would
treat them identically.

## What it would look like

### Convention

A `schema.yaml` at the root of a longecho-compliant source describes
its data dictionary. Top-level keys are collection or dataset names.
Each value is an object with at least:

```yaml
my_collection:
  record_count: 12847
  metadata_keys:
    role:
      type: string
      count: 12847
      values: [user, assistant]
      description: Speaker identity
```

This is the shape arkiv produces today, but the convention is
intentionally underspecified beyond the top-level structure. longecho
should be tolerant of missing fields: only render what is present.

### longecho check --verbose

Today this prints the README and detected formats. With schema.yaml
awareness, it could also print:

```
Data dictionary (from schema.yaml):
  my_collection: 12,847 records
    role           string   user, assistant
    conversation_id string  (12,847 unique)
    topic          string   e.g., "category theory"
```

This matches the rendered tables that arkiv's auto-generated README
already contains, but reaches them through the structured file rather
than parsing the README body.

### longecho build (SFA)

Each source card in the generated site could include a brief data
dictionary section if schema.yaml exists. Same rendering logic as
above, but inlined into the HTML.

### longecho query

Plain-text search currently scans README content. It could optionally
also scan `schema.yaml` field descriptions, so a search for "speaker"
finds sources whose schema describes a key as "Speaker identity."

## What it would NOT include

- No validation. longecho does not enforce that `schema.yaml` fields
  match what is actually in the data files. That is the producer's job.
- No type checking. longecho displays the declared type; it does not
  verify it.
- No arkiv-specific assumptions. The format is YAML with a loose
  shape; producers other than arkiv (Hugo data files, Obsidian
  metadata, hand-written notes) can adopt the same convention.
- No hard requirement on producers. A longecho source without a
  `schema.yaml` works exactly as it does today.

## Why this is tentative

1. **Real demand unknown.** Right now arkiv is the only producer of
   structured `schema.yaml` files. Adding longecho support before
   there are multiple producers risks overfitting to arkiv's choices
   and undermining the convention's portability.
2. **Belongs on longecho's roadmap, not arkiv's.** This is purely a
   longecho enhancement. arkiv produces `schema.yaml` whether or not
   longecho reads it.
3. **The convention itself needs more thought.** What top-level shape
   is most flexible? Should `metadata_keys` be the only structure, or
   are other shapes (column lists for tabular data, field
   descriptions for forms) worth supporting? Better to wait for two
   or three producers and find the natural overlap than to lock in a
   shape based on one.
4. **Risk of feature creep.** Each capability above (verbose output,
   SFA cards, search) is a separate small project. Worth doing if
   each is independently valuable.

## When to revisit

Trigger conditions for moving this from "tentative idea" to "actual
feature":

- A second producer (not arkiv) starts emitting `schema.yaml` and the
  shapes are similar enough to share rendering logic.
- A user explicitly asks longecho to surface schema information that
  is already in the file but invisible in current output.
- arkiv's `schema.yaml` shape stabilizes for a couple of releases
  without major changes, suggesting it is a useful target convention.

If none of these happen, this idea can stay parked indefinitely.
longecho works fine without it.
