# Architecture

A map of the codebase for anyone picking this up cold. See [`VISION.md`](VISION.md) for *why*
these stages exist and [`BACKLOG.md`](BACKLOG.md) for what's done vs. planned.

## Layout

```
src/wishwright/
  models.py       # Candidate, Evaluation dataclasses; validates required text fields; STAGES order
  config.py       # load_config() reads and validates config.yaml -> Config(search_phrases, PolicySet)
  discovery.py    # CandidateSource protocol; FixtureSource (JSONL, works today);
                  #   XApiSource (stub, raises NotImplementedError until credentials exist)
  evaluation.py   # score_candidate(candidate, policy) -> Evaluation; safety is a hard gate
  storage.py      # Ledger: validated JSON-backed {candidate_id: stage} map, locked atomic writes
  pipeline.py     # advance(ledger, id) steps one stage forward; to_backlog_entry() builds
                  #   a project-factory-shaped brief from an approved candidate
  publish.py      # check_ready(path) verifies README/LICENSE/CI exist on disk before publish
  reply.py        # draft_reply(candidate, repo_url) -> short reply string, <=280 chars
  runlog.py       # log_event() validates and appends one JSONL line per stage transition
  cli.py          # argparse entrypoint: `evaluate` and `status`; reports local input errors cleanly

fixtures/sample_posts.jsonl   # sample candidates for local dev/demo/tests, no network needed
config.example.yaml           # copy to config.yaml (gitignored) to override phrases/policy
tests/                        # one test file per module, mirrors src/wishwright/ 1:1
```

## Data flow

```
FixtureSource.fetch(search_phrases)  ->  Candidate
        |
        v
score_candidate(candidate, policy)   ->  Evaluation (safety/feasibility/breadth/total, [0,1])
        |                                  deny-list match => total forced to 0, no averaging
        v
Ledger.mark_seen(id, stage)          ->  durable {id: stage} record (state/ledger.json)
        |
        v
pipeline.advance(ledger, id)         ->  discovered -> evaluated -> built -> published -> replied
        |                                  one stage per call, no-op at "replied"
        v
to_backlog_entry(candidate, eval)    ->  dict shaped for project-factory's backlog/ideas.yaml
        |
        v
publish.check_ready(built_repo_path) ->  [] if README+LICENSE+CI all present, else reasons
        |
        v
reply.draft_reply(candidate, url)    ->  reply text linking back to the shipped repo
```

Every `evaluate` run also calls `runlog.log_event` per candidate, appending to
`logs/run.jsonl` — an audit trail independent of the ledger's current-state view.

## Config

`config.yaml` (gitignored; copy from `config.example.yaml`) holds `search_phrases` and the
`policy` block (`deny_terms`, `min_total_score`). `load_config` tolerates a missing file and
falls back to the in-code defaults in `config.py`, so a fresh checkout works with zero setup.
Present configuration must be a mapping with non-empty string lists and a finite score threshold
from 0 through 1; malformed files produce a concise CLI error instead of a traceback.

## How to run / test

```bash
pip install -e ".[dev]"
wishwright evaluate --input fixtures/sample_posts.jsonl
wishwright status
pytest -q
pytest --cov=wishwright --cov-report=term-missing
```

No network access or paid API is required to run the full test suite — everything exercises
`FixtureSource` and local fixtures. Tests include property checks for scoring invariants. Fixture,
ledger, and audit-log boundaries reject malformed data before it can reach the state machine.
Ledger writes take an exclusive lock and refresh state first, preventing stale processes from
overwriting each other's entries.
`XApiSource` is a stub; wiring it up is tracked in
`BACKLOG.md` and requires no changes to `evaluation.py`, `storage.py`, `pipeline.py`,
`publish.py`, or `reply.py` — only a new `CandidateSource` implementation.

## Not yet wired up

- `XApiSource` — needs real X API credentials.
- Build/publish stages currently produce data structures (`to_backlog_entry`, `check_ready`)
  but nothing yet calls out to an actual build pipeline or pushes a reply to X.
