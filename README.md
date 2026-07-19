# Wishwright

**Wishwright** finds public "I wish this existed" posts on X, evaluates whether the request is
safe and broadly useful to build, and — for the ones that clear the bar — turns them into a
finished, published product with a reply back to the original poster.

It is the pipeline that sits *in front of* a build system: discovery and evaluation are fully
scoped here; build/publish/reply stages hand off to whatever project-generation tooling produces
the actual product (see [`docs/VISION.md`](docs/VISION.md) for the full design).

## Why

People ask for tools publicly all the time — "does anyone know an app that...", "I wish someone
would build...", "someone should make a...". Almost none of those requests get built. Wishwright
is a system for closing that loop automatically, safely, and transparently: every step from
"found the post" to "shipped the reply" is auditable.

## Planned features

- **Discovery** — pluggable sources (X API, fixtures for testing) driven by configurable search
  phrases.
- **Evaluation** — a scoring rubric (safety, feasibility, breadth of usefulness) with a hard
  deny-list; nothing unsafe or narrowly personal gets built.
- **Ledger** — every candidate is tracked exactly once; nothing is re-processed or lost across
  restarts.
- **Build handoff** — approved candidates are converted into a structured project brief ready to
  feed a build pipeline.
- **Publish checks** — a repo isn't marked publishable until it has the basics (README, LICENSE,
  CI) in place.
- **Reply drafting** — a short, honest reply linking back to the finished product.
- **Status & audit log** — `wishwright status` reports pipeline-stage counts; every transition is
  appended to a structured run log.

## Stack

Python 3.12, standard library + PyYAML for config. No network calls or paid APIs are required to
run the test suite — discovery and evaluation are exercised against local fixtures.

## Getting started

```bash
pip install -e ".[dev]"
wishwright --help
wishwright evaluate --input fixtures/sample_posts.jsonl
```

## Status

Early scope/build stage — see [`docs/BACKLOG.md`](docs/BACKLOG.md) for what's implemented vs.
planned.

## License

MIT — see [`LICENSE`](LICENSE).
