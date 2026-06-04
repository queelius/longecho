# longecho

**A philosophy and a tool for durable personal archives.**

longecho is a bet that with enough self-description and simple formats, your data can outlive the tools that created it. The name evokes what we're after: your voice, echoing forward through time.

> Not resurrection. Not immortality. Just love that still responds.

I build these tools under no illusion of unlimited time, which is exactly why they have to keep working without me. For the longer case, see the [The Long Echo essays](https://metafunctor.com/series/the-long-echo/).

## Five principles

**Self-Describing.** Every collection explains itself: a human or LLM finding your data in 50 years, with no context, should be able to understand what they're looking at.

**Durable Formats.** Store data in formats readable without proprietary software, with multiple implementations and proven longevity.

**Graceful Degradation.** An archive stays useful as technology disappears, layer by layer, down to the plain text underneath.

**Local-First.** The archive works entirely offline. Cloud services can sync or back up, but nothing essential lives only in the cloud.

**Trust the Future.** Future humans will be smarter and future LLMs more capable, so preserve content and context rather than infrastructure. If you have to choose between a simple format and a "more correct" one, choose simple.

## Graceful degradation

The whole design rests on this table. Each row survives the loss of the row above it.

| If you have... | You can still... |
|----------------|------------------|
| Modern LLMs | Have conversations with the archive |
| A web browser | Navigate a generated site |
| A file browser | Explore organized directories |
| A text editor | Read plain text files |
| Only fragments | Understand each piece independently |

A directory is **longecho-compliant** when it has a README explaining what the data is plus data stored in durable formats. That is the entire contract. No schema, no version numbers, no special files.

## What longecho is not

The boundaries here are deliberate. Each one is a choice about what durability actually requires.

It is not an autonomous daemon or a "digital ghost." It runs when you run it and stops when you stop. It creates no fake presence and speaks for no one. The archive responds because you and your tools made it legible, not because anything is pretending to be alive.

It does not validate your file contents. `longecho check` confirms that a README and durable files are present, not that the bytes inside them are correct or complete. Presence, not validity. The future reader judges the contents; longecho only makes sure they are there to be judged.

It does not read inside archives. A `.zip`, `.gz`, or `.tgz` counts as a durable format, but longecho treats it as an opaque transport container and never traverses into it. To work with what is inside, extract first.

It has no query language. `longecho query` does plain substring search across names, descriptions, and README text. When you need structure, pipe `longecho query --json` to `jq`. The tool stays small so the data stays in front.

> The archive is not a monument. It is a conversation that outlasts its participants.

Ready to build one? Start with the [Quickstart](quickstart.md), or read the full [Specification](spec.md). Install the current release with `pip install longecho`.
