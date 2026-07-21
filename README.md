# Wishwright

**▶ Live page: [apps.charliekrug.com/build-a-public-request-to-product-system](https://apps.charliekrug.com/build-a-public-request-to-product-system/)**

[![CI](https://github.com/ctkrug/build-a-public-request-to-product-system/actions/workflows/ci.yml/badge.svg)](https://github.com/ctkrug/build-a-public-request-to-product-system/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-b52f28.svg)](LICENSE)

**Turn public wishes into safer build briefs.**

Wishwright is a Python CLI and library for indie developers who want product ideas grounded in
public requests. It ranks request-shaped posts, blocks configured safety terms, records an audit
trail, and converts approved candidates into structured briefs for a downstream build system.

The local CLI works from JSONL fixtures. Production integrations are explicit library boundaries:
an authenticated X search source, idempotent build-service client, resumable publisher, and an
explicitly authorized X reply delivery service for posts eligible under X's reply rules.

## See the result

Run the included fixture batch:

```console
$ wishwright evaluate --input fixtures/sample_posts.jsonl
id  score  text
---------------
1   1.00  I wish there was an app that everyone could use to split gr…
4   1.00  does anyone know a tool that lets people compare grocery pr…
2   0.67  someone should build a tool that reminds just for me about …
3   0.00  i wish there was an app that could hack into my ex's email …
```

The denied request receives a zero before any build handoff. Approved rows can be converted to the
project-factory backlog shape with `wishwright.pipeline.to_backlog_entry`.

## What it gives you

- **A ranked shortlist from real request text.** `evaluate` scores safety, feasibility, and breadth
  on a 0 to 1 scale and prints the strongest candidates first.
- **A hard safety stop.** Any configured deny-list match forces the total to `0.0`; usefulness
  cannot outweigh a safety match.
- **Restart-safe stage tracking.** The locked JSON ledger preserves one stage per candidate and
  prevents stale processes from overwriting each other's entries.
- **Build-ready records.** Approved candidates become dictionaries containing the title, source,
  rationale, and component scores expected by a downstream project backlog.
- **Auditable local runs.** Each evaluation appends a timestamped JSONL event that can be inspected
  without a database or hosted service.
- **Confirmed production transitions.** Build artifacts, verified publication, and X reply IDs are
  recorded durably; a restart resumes the remaining work instead of advancing optimistically.

## Install

Wishwright requires Python 3.11 or newer.

```bash
git clone https://github.com/ctkrug/build-a-public-request-to-product-system.git
cd build-a-public-request-to-product-system
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For tests and quality checks, install the development extra:

```bash
pip install -e ".[dev]"
```

## Use it

### Rank a fixture batch

Each non-empty line must be a JSON object with `id`, `author`, `text`, `url`, and `created_at`.

```bash
wishwright evaluate \
  --input fixtures/sample_posts.jsonl \
  --config config.example.yaml \
  --log logs/run.jsonl
```

Malformed JSON, invalid UTF-8, invalid configuration, and corrupt ledgers return a concise error
and a nonzero exit code instead of a traceback.

### Inspect pipeline state

```bash
wishwright status --ledger state/ledger.json
```

```text
discovered  0
evaluated   0
built       0
published   0
replied     0
```

### Create a downstream build brief

```python
from wishwright.config import PolicySet
from wishwright.evaluation import score_candidate
from wishwright.models import Candidate
from wishwright.pipeline import to_backlog_entry

candidate = Candidate.from_dict(
    {
        "id": "123",
        "author": "maker",
        "text": "I wish there were a tool people could use to compare grocery prices",
        "url": "https://x.com/maker/status/123",
        "created_at": "2026-07-20T10:00:00Z",
    }
)
evaluation = score_candidate(candidate, PolicySet())
brief = to_backlog_entry(candidate, evaluation)
```

### Run production integrations

Construct the production collaborators with credentials supplied by your deployment environment;
the library never reads secrets from files or posts a reply without `authorized_reply=True`.
X currently permits API replies only when the authenticated account was mentioned or quoted by the
original author. Use `draft_reply` for a human-posted response when a discovered post is not eligible.

```python
import os

from wishwright.config import load_config
from wishwright.discovery import XApiSource
from wishwright.evaluation import score_candidate
from wishwright.orchestrator import HttpBuildSystem, Orchestrator
from wishwright.publish import (
    CommandSiteDeployer,
    ResumablePublisher,
    git_push_repository,
    verify_public_url,
)
from wishwright.reply import ReplyDelivery, XReplyClient
from wishwright.storage import Ledger

config = load_config("config.yaml")
x_token = os.environ["X_BEARER_TOKEN"]
source = XApiSource(x_token)
builder = HttpBuildSystem(os.environ["BUILD_ENDPOINT"], os.environ["BUILD_BEARER_TOKEN"])
publisher = ResumablePublisher(
    git_push_repository,
    CommandSiteDeployer(("deploy-static", "{site_path}")),
    verify_public_url,
)
replies = ReplyDelivery(XReplyClient(x_token), "state/replies.json")
orchestrator = Orchestrator(
    Ledger("state/ledger.json"),
    builder,
    publisher=publisher,
    reply_delivery=replies,
)

candidate = next(source.fetch(config.search_phrases))
evaluation = score_candidate(candidate, config.policy)

# Keep this false until a human approves the public reply.
stage = orchestrator.process(candidate, evaluation, authorized_reply=False)
```

Replace `deploy-static` with your configured static-site command. The deployer accepts an argument
vector rather than a shell string. Publication checks README, license, and CI readiness before a
repository push; skips destinations already public; and only moves the ledger to `published` after
both URLs verify. Run `process` again with `authorized_reply=True` only after reviewing the reply and
confirming that X allows the authenticated account to answer that post. A stored remote ID makes
confirmed retries safe. If X accepts a reply but its response is lost, reconcile the account before
retrying because the create-post endpoint has no documented idempotency key. Wishwright records a
pending marker before delivery and blocks another attempt until it is resolved:

```python
# Record the post found during reconciliation.
replies.store.resolve_pending(candidate.id, "remote-post-id")

# Or allow a retry after confirming that X did not create a post.
replies.store.resolve_pending(candidate.id, None)
```

## Configure the policy

Copy `config.example.yaml` to `config.yaml`, which is ignored by Git. Search phrases and safety
terms are case-insensitive substring matches; `min_total_score` accepts values from `0` through
`1`.

```yaml
search_phrases:
  - i wish someone would build

policy:
  deny_terms:
    - malware
    - hack into
  min_total_score: 0.5
```

## Project map

- [`docs/VISION.md`](docs/VISION.md) defines the request-to-product goal and the completed v1
  boundaries.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) follows data through discovery, scoring, storage,
  handoff, readiness checks, and reply drafting.
- [`docs/BACKLOG.md`](docs/BACKLOG.md) records the completed acceptance criteria.
- [`docs/DESIGN.md`](docs/DESIGN.md) specifies the landing page's risograph dispatch system.
- [`docs/POSITIONING.md`](docs/POSITIONING.md) locks the audience, name, promise, and copy voice.

## Develop

```bash
ruff check src tests
ruff format --check src tests
mypy
pytest -q --cov --cov-report=term-missing
```

The suite uses local files only. CI runs on Python 3.11 and 3.12 and enforces an 85% coverage floor.

## License

[MIT](LICENSE) © Charlie Krug

More of Charlie's projects: [apps.charliekrug.com](https://apps.charliekrug.com)
