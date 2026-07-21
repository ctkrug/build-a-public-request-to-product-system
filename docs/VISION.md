# Vision

## The problem

Every day, people post public requests on X for tools that don't exist yet: "I wish there was
an app that...", "someone should build...", "does anyone know a tool that...". A tiny fraction
of these get built, usually by whoever happens to see the post and feels like it. Most just
scroll past. The gap isn't a lack of demand signal or a lack of build capacity. It is that
nobody is watching the signal and turning it into product on a reliable cadence.

## Who it's for

Two audiences, one system:

- **The requester:** someone who voiced a real, public need and gets a working product plus a
  drafted response linking to it. Eligible posts can receive that response through the X API;
  other posts require a human to send it.
- **Charlie:** wants a standing system that surfaces genuinely useful build ideas sourced
  from real demand, filters out anything unsafe or narrowly personal, and hands the good ones to
  a build pipeline (this repo's own parent project, `project-factory`, is a natural downstream
  consumer via `to_backlog_entry`).

## The core idea

A five-stage pipeline, each stage independently testable and each candidate tracked through
exactly one stage at a time in a durable ledger:

1. **Discover:** pull candidate posts from X search, matched against a configurable list of
   request-shaped phrases.
2. **Evaluate:** score each candidate on safety, feasibility, and breadth of usefulness. Safety
   is a hard gate (deny-list match => automatic rejection, not just a lower score), so nothing that
   could enable harm gets built, no matter how "useful" it scores otherwise.
3. **Build:** approved candidates become a structured brief (title, category, rationale, source
   scores) shaped to slot into an existing build pipeline.
4. **Publish:** before a built project can be marked done, it must have the basics: README,
   LICENSE, CI. This is enforced by checking the filesystem, not by trusting the build stage's
   self-report.
5. **Reply:** a short, honest reply is drafted linking back to the finished product.

## Key design decisions

- **Safety is a gate, not a score input.** A candidate that matches the deny-list gets
  `total = 0` outright. Averaging safety in with feasibility/breadth would let a sufficiently
  "useful"-sounding unsafe request slip through; a gate can't be outvoted.
- **Sources are pluggable via a `Protocol`.** `FixtureSource` (local JSONL) lets every other
  stage be built, tested, and demoed without an X API key. `XApiSource` is the real source,
  with authenticated pagination and response normalization behind the same interface. Swapping
  sources requires no scoring or storage changes.
- **The ledger is the source of truth for confirmed progress.** Stage writes cannot move a
  candidate backward; `advance()` moves a candidate forward exactly one stage and is safe to call
  blindly (no-ops at the terminal stage instead of raising).
- **Zero paid dependencies to run or test.** Runtime dependency surface is PyYAML only; the full
  test suite runs against local fixtures with no network access, matching the parent factory's
  $0-cost discipline.
- **Not servable.** This is a backend pipeline tool, not a web product. Its output (built
  products) may be servable, but wishwright itself is a CLI.

## What v1 includes

- `XApiSource` performs authenticated, paginated recent search and normalizes expanded authors
  into `Candidate` records. The local `evaluate` command stays fixture-based for repeatable runs.
- `HttpBuildSystem` submits approved briefs with an idempotency key, while `BuildArtifactStore`
  retains confirmed repository and site coordinates across restarts.
- `ResumablePublisher` verifies repository and site URLs independently and retries only the
  destination that is not yet public.
- `ReplyDelivery` requires explicit authorization, persists a confirmed remote X post ID under a
  lock, and advances the ledger only after the receipt exists. X API eligibility and ambiguous
  create-post responses remain production constraints described in [`BACKLOG.md`](BACKLOG.md).
- `wishwright status` gives an at-a-glance view of how many candidates are sitting in each stage,
  so a stuck pipeline is visible immediately rather than silently piling up in one stage.
