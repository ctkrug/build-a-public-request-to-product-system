---
title: "Building Wishwright: a safety gate before the build queue"
published: false
description: "How I built a Python pipeline that ranks public product requests and keeps unsafe ideas out of the build queue."
tags: python, cli, sideproject, opensource
---

People publish product ideas every day without calling them product ideas. They write, "I wish
there were an app that..." or ask if a tool exists for a problem they just hit. Those posts are
useful demand evidence, but collecting them is only the first step. A builder still has to decide
which requests are safe, feasible, and useful beyond one person's exact situation.

I built [Wishwright](https://github.com/ctkrug/build-a-public-request-to-product-system) to make
that decision traceable. It is a Python CLI and library that reads request-shaped posts, scores
them, records an audit event, and converts approved candidates into structured build briefs. The
[project page](https://apps.charliekrug.com/build-a-public-request-to-product-system/) shows a
complete fixture run, including the unsafe request that is stopped before handoff.

## Safety is not an average

The most important scoring decision was keeping safety outside the weighted total. Averaging
safety, feasibility, and breadth creates a bad failure mode: a dangerous request can recover from a
low safety score by sounding easy to build and useful to many people.

Wishwright treats a configured deny-list match as a hard gate. A match returns a total of zero.
Only non-matches continue to feasibility and breadth scoring. The rubric stays intentionally
small: explicit phrase sets, component values clamped to the 0 to 1 range, and property tests that
exercise arbitrary request text. I can inspect why a row moved instead of accepting an unexplained
ranking.

## Confirm first, advance second

External actions are where a tidy local state machine usually breaks. A build request might time
out after the remote service accepts it. A repository push can succeed while the site deployment
fails. A reply receipt can be written just before another worker wakes up.

I used a candidate-derived idempotency key for build submissions and store confirmed artifact
coordinates in a locked JSON file. Publication checks the repository URL and site URL separately,
then runs only the missing action. Before a push, it verifies that the repository contains a
README, license, and CI workflow. Before a site deployment, it verifies that the static build
directory exists. The ledger moves to the next stage only after the corresponding result is
confirmed.

Reply delivery follows the same rule. It requires an explicit authorization flag and writes the
remote X post ID while holding an exclusive `fcntl` lock. A retry reads that receipt instead of
posting again. The local stores use atomic replacement, but the lock matters just as much: atomic
replacement alone does not stop two stale processes from erasing each other's updates. Stage writes
are monotonic, so an old worker cannot move a published candidate back to built.

There is an important limit. X permits API replies only when the authenticated account was mentioned
or quoted by the original author. The create-post endpoint also has no documented idempotency key.
The adapter can therefore deliver an approved reply to an eligible post and safely reuse a confirmed
receipt, but arbitrary discovered posts need a human-posted response. An ambiguous timeout must be
reconciled before retrying. I would not hide those platform constraints behind an "exactly once"
claim.

## Real adapters, local tests

The default CLI reads JSONL fixtures so a checkout works without credentials or network calls. The
production library boundaries are concrete: `XApiSource` performs authenticated, paginated recent
search; `HttpBuildSystem` sends the brief and idempotency key; `ResumablePublisher` verifies both
destinations; and `XReplyClient` posts an approved, eligible reply. Tests inject request functions
and cover pagination, malformed payloads, authentication failures, rate limits, partial
publication, and resumed confirmed delivery without contacting those services.

That split keeps the demo repeatable without pretending the network does not exist. The full suite
also runs branch-aware coverage with an 85 percent floor on Python 3.11 and 3.12.

## What I would change next

I would replace substring scoring with a versioned policy engine and store the policy version on
each evaluation. I would also move the local JSON stores to SQLite if multiple workers became the
normal case. The file locks are correct for one host, but a database would make querying stuck runs
and enforcing transitions clearer. Before enabling unattended public replies, I would run the X
source in shadow mode and compare its decisions with human review for several batches.

Wishwright is deliberately conservative. Its useful result is not the largest list of ideas. It is
a smaller queue where each item has a public source, visible scores, and a recorded path from
request to response draft.
