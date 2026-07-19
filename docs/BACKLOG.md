# Backlog

Epic/story breakdown for the build. Every story has concrete, verifiable acceptance criteria.
The first story of Epic 1 is the wow moment — it must be reachable without live X API
credentials, since none exist yet.

## Epic 1 — Discovery & Evaluation Pipeline

- [ ] **1. [WOW] Ranked shortlist from a fixture batch** — `wishwright evaluate --input
  fixtures/sample_posts.jsonl` scores a batch of sample posts and prints a ranked shortlist of
  buildable requests with safety/feasibility/breadth scores.
  - AC: running the command against `fixtures/sample_posts.jsonl` prints a table with candidate
    id, score, and text, sorted by score descending.
  - AC: running against an empty input file exits 0 and prints "no candidates" instead of
    crashing or printing an empty table.

- [ ] **2. Pluggable discovery sources** — a `CandidateSource` interface with a fixture-backed
  implementation for development/testing and a stubbed real-source implementation for X.
  - AC: `config.yaml` defines a list of search phrases that `discovery.FixtureSource.fetch`
    receives and can be asserted against in a test.
  - AC: `FixtureSource` returns `Candidate` objects with all of `id`, `author`, `text`, `url`,
    `created_at` populated; a fixture row missing one of those fields raises a `ValueError` with
    a message naming the missing field.

- [ ] **3. Safety/usefulness scoring rubric** — a pure function that scores a candidate on
  safety, feasibility, and breadth, each in `[0, 1]`, with configurable weights/thresholds.
  - AC: `evaluation.score_candidate` returns safety, feasibility, breadth, and total scores all
    within `[0, 1]`.
  - AC: a candidate whose text matches a policy deny-list term scores `total == 0.0` regardless
    of its feasibility/breadth scores.

- [ ] **4. Dedup ledger** — the same X post is never evaluated twice across process restarts.
  - AC: `storage.Ledger.has_seen(id)` returns `True` after `mark_seen(id)` is called on the same
    ledger instance.
  - AC: a ledger written by one `Ledger` instance and reloaded by a fresh instance against the
    same path reports the same `stage_of(id)` (round-trip persistence).

## Epic 2 — Build & Publish Automation

- [ ] **5. Build handoff to project-factory format** — approved candidates convert into a
  project brief shaped like a `project-factory` `backlog/ideas.yaml` entry.
  - AC: `pipeline.to_backlog_entry(candidate, evaluation)` returns a dict containing `title`,
    `category`, and `why_impressive` keys.
  - AC: calling `to_backlog_entry` with an unapproved evaluation (`total == 0`) raises
    `ValueError` instead of silently producing a backlog entry.

- [ ] **6. Publish readiness check** — a built project directory isn't marked publishable until
  it has README, LICENSE, and a CI workflow.
  - AC: `publish.check_ready(path)` returns `[]` for a fixture repo directory containing
    `README.md`, `LICENSE`, and `.github/workflows/*.yml`.
  - AC: removing `LICENSE` from that fixture directory causes `check_ready` to return a non-empty
    list naming the missing file.

- [ ] **7. Reply drafting** — a short reply message linking to the finished product for a given
  candidate.
  - AC: `reply.draft_reply(candidate, repo_url)` returns a string containing `repo_url` and no
    longer than 280 characters.
  - AC: calling `draft_reply` with a non-`https://` `repo_url` raises `ValueError`.

- [ ] **8. End-to-end stage tracking** — a state machine that ties discover -> evaluate -> build
  -> publish -> replied together with one ledger entry per candidate.
  - AC: `pipeline.advance(ledger, id)` moves a candidate exactly one stage forward per call
    (`discovered` -> `evaluated` -> `built` -> `published` -> `replied`).
  - AC: calling `advance` on a candidate already at `replied` does not raise and returns
    `replied` unchanged (no-op at the terminal stage).

## Epic 3 — Safety, Config & Observability

- [ ] **9. Configurable safety policy** — deny-list and score thresholds loaded from
  `config.yaml`, overridable per run.
  - AC: `config.load_policy()` (or equivalent) returns a `PolicySet` whose `deny_terms` reflect
    what's in the loaded YAML file.
  - AC: adding a new term to `deny_terms` in `config.yaml` and re-running `evaluate` against a
    fixture candidate containing that term causes its total score to drop to `0.0` (integration
    test, not just a unit test of the scoring function in isolation).

- [ ] **10. `wishwright status` stage counts** — reports how many candidates are sitting in each
  pipeline stage.
  - AC: run against a ledger fixture with a known mix of stages (e.g. 3 discovered, 1 evaluated,
    1 built) and the printed counts match the fixture exactly.
  - AC: run against an empty/missing ledger file, exits 0, and prints all-zero counts rather than
    erroring on a missing file.

- [ ] **11. Structured run log** — every pipeline stage transition is appended to a JSONL audit
  log for later debugging.
  - AC: after running `wishwright evaluate`, `logs/run.jsonl` contains at least one new line with
    `timestamp`, `stage`, `candidate_id`, and `result` keys.
  - AC: running with no pre-existing `logs/` directory creates it automatically rather than
    raising `FileNotFoundError`.

- [ ] **12. Design polish: consistent CLI output** — every subcommand's output is aligned and
  self-describing.
  - AC: `wishwright --help` lists every subcommand (`evaluate`, `status`, and any added by
    stories 9-11) each with a one-line description.
  - AC: `evaluate` output columns stay aligned (no ragged whitespace) for a fixture set with
    candidate texts of noticeably different lengths.
