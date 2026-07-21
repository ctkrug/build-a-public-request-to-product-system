# Backlog

Epic/story breakdown for the local pipeline core. Every story has concrete, verifiable acceptance
criteria. The first story of Epic 1 is the fixture-driven proof and does not require X API
credentials.

## Epic 1: Discovery & Evaluation Pipeline

- [x] **1. [WOW] Ranked shortlist from a fixture batch**: `wishwright evaluate --input
  fixtures/sample_posts.jsonl` scores a batch of sample posts and prints a ranked shortlist of
  buildable requests with safety/feasibility/breadth scores.
  - AC: running the command against `fixtures/sample_posts.jsonl` prints a table with candidate
    id, score, and text, sorted by score descending.
  - AC: running against an empty input file exits 0 and prints "no candidates" instead of
    crashing or printing an empty table.

- [x] **2. Pluggable discovery sources**: a `CandidateSource` interface with a fixture-backed
  implementation for development/testing and an authenticated recent-search implementation for X.
  - AC: `config.yaml` defines a list of search phrases that `discovery.FixtureSource.fetch`
    receives and can be asserted against in a test.
  - AC: `FixtureSource` returns `Candidate` objects with all of `id`, `author`, `text`, `url`,
    `created_at` populated; a fixture row missing one of those fields raises a `ValueError` with
    a message naming the missing field.

- [x] **3. Safety/usefulness scoring rubric**: a pure function that scores a candidate on
  safety, feasibility, and breadth, each in `[0, 1]`, with configurable weights/thresholds.
  - AC: `evaluation.score_candidate` returns safety, feasibility, breadth, and total scores all
    within `[0, 1]`.
  - AC: a candidate whose text matches a policy deny-list term scores `total == 0.0` regardless
    of its feasibility/breadth scores.

- [x] **4. Dedup ledger**: the same X post is never evaluated twice across process restarts.
  - AC: `storage.Ledger.has_seen(id)` returns `True` after `mark_seen(id)` is called on the same
    ledger instance.
  - AC: a ledger written by one `Ledger` instance and reloaded by a fresh instance against the
    same path reports the same `stage_of(id)` (round-trip persistence).

## Epic 2: Build & Publish Automation

- [x] **5. Build handoff to project-factory format**: approved candidates convert into a
  project brief shaped like a `project-factory` `backlog/ideas.yaml` entry.
  - AC: `pipeline.to_backlog_entry(candidate, evaluation)` returns a dict containing `title`,
    `category`, and `why_impressive` keys.
  - AC: calling `to_backlog_entry` with an unapproved evaluation (`total == 0`) raises
    `ValueError` instead of silently producing a backlog entry.

- [x] **6. Publish readiness check**: a built project directory isn't marked publishable until
  it has README, LICENSE, and a CI workflow.
  - AC: `publish.check_ready(path)` returns `[]` for a fixture repo directory containing
    `README.md`, `LICENSE`, and `.github/workflows/*.yml`.
  - AC: removing `LICENSE` from that fixture directory causes `check_ready` to return a non-empty
    list naming the missing file.

- [x] **7. Reply drafting**: a short reply message linking to the finished product for a given
  candidate.
  - AC: `reply.draft_reply(candidate, repo_url)` returns a string containing `repo_url` and no
    longer than 280 characters.
  - AC: calling `draft_reply` with a non-`https://` `repo_url` raises `ValueError`.

- [x] **8. End-to-end stage tracking**: a state machine that ties discover -> evaluate -> build
  -> publish -> replied together with one ledger entry per candidate.
  - AC: `pipeline.advance(ledger, id)` moves a candidate exactly one stage forward per call
    (`discovered` -> `evaluated` -> `built` -> `published` -> `replied`).
  - AC: calling `advance` on a candidate already at `replied` does not raise and returns
    `replied` unchanged (no-op at the terminal stage).

## Epic 3: Safety, Config & Observability

- [x] **9. Configurable safety policy**: deny-list and score thresholds loaded from
  `config.yaml`, overridable per run.
  - AC: `config.load_policy()` (or equivalent) returns a `PolicySet` whose `deny_terms` reflect
    what's in the loaded YAML file.
  - AC: adding a new term to `deny_terms` in `config.yaml` and re-running `evaluate` against a
    fixture candidate containing that term causes its total score to drop to `0.0` (integration
    test, not just a unit test of the scoring function in isolation).

- [x] **10. `wishwright status` stage counts**: reports how many candidates are sitting in each
  pipeline stage.
  - AC: run against a ledger fixture with a known mix of stages (e.g. 3 discovered, 1 evaluated,
    1 built) and the printed counts match the fixture exactly.
  - AC: run against an empty/missing ledger file, exits 0, and prints all-zero counts rather than
    erroring on a missing file.

- [x] **11. Structured run log**: every pipeline stage transition is appended to a JSONL audit
  log for later debugging.
  - AC: after running `wishwright evaluate`, `logs/run.jsonl` contains at least one new line with
    `timestamp`, `stage`, `candidate_id`, and `result` keys.
  - AC: running with no pre-existing `logs/` directory creates it automatically rather than
    raising `FileNotFoundError`.

- [x] **12. Design polish: consistent CLI output**: every subcommand's output is aligned and
  self-describing.
  - AC: `wishwright --help` lists every subcommand (`evaluate`, `status`, and any added by
    stories 9-11) each with a one-line description.
  - AC: `evaluate` output columns stay aligned (no ragged whitespace) for a fixture set with
    candidate texts of noticeably different lengths.

## Epic 4: Production request-to-product integrations

- [x] **13. Live X discovery**: authenticated, paginated search and normalized public posts.
  - AC: the `XApiSource` adapter fetches and normalizes live posts for configured request phrases.
  - AC: mocked API tests cover pagination, malformed responses, authorization failure, and rate
    limits without making network calls in the suite.

- [x] **14. Idempotent build invocation**: submit approved briefs to the downstream build system
  with a candidate-derived idempotency key and durable build artifacts.
  - AC: retries cannot create a second build for the same candidate.
  - AC: the ledger advances to `built` only after the downstream system confirms completion.

- [x] **15. Verified publishing**: enforce local repository readiness, publish the built repository
  and site, then verify both public locations.
  - AC: partial failures can resume without recreating the repository or deployment.
  - AC: the ledger advances to `published` only after both destinations are reachable.

- [x] **16. Authorized reply delivery**: post the drafted reply through X with an explicit approval
  control and a durable remote-ID record.
  - AC: a retry after an uncertain response cannot post a duplicate reply.
  - AC: the ledger advances to `replied` only after the remote post identifier is persisted.
