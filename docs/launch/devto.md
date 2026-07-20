---
title: "Building Wishwright: a safety gate before the build queue"
published: false
description: "How I built a local pipeline that ranks public product requests and keeps unsafe ideas out of the build queue."
tags: python, cli, sideproject, opensource
---

People publish product ideas every day without calling them product ideas. They write, "I wish
there were an app that..." or ask if a tool exists for a problem they just hit. That is useful
demand evidence, but collecting those posts is only the first step. A builder still has to decide
which requests are safe, feasible, and useful beyond one person's exact situation.

I built [Wishwright](https://github.com/ctkrug/build-a-public-request-to-product-system) to make
that decision traceable. The current version is a Python CLI and library that reads request-shaped
posts from JSONL, scores them, writes an audit event, and converts approved candidates into a
structured build brief. The [project page](https://apps.charliekrug.com/build-a-public-request-to-product-system/)
shows a complete run against the included fixture.

## Safety is not an average

The most important implementation choice was keeping safety outside the weighted score. It is
tempting to average safety, feasibility, and breadth into one number. That creates a bad failure
mode: a dangerous request can recover from a low safety score by sounding easy to build and useful
to many people.

Wishwright treats a configured deny-list match as a hard gate. A match returns zero for every axis
and records the reason. Only non-matches continue to feasibility and breadth scoring. The current
rubric is intentionally small and readable. It uses explicit phrase sets, clamps every component
to the 0 to 1 range, and has property tests for those bounds. I can inspect why a row moved instead
of trusting an unexplained ranking.

## The ledger has to survive two processes

The first ledger implementation used atomic file replacement, but atomic replacement alone does
not prevent a lost update. Two long-lived processes can each load the same old JSON, add different
candidates, and let the last writer erase the first writer's addition.

The current ledger takes an exclusive `fcntl` lock before a write, reloads the persisted entries
while holding that lock, applies the new stage, and replaces the JSON file. A regression test opens
two stale `Ledger` instances and verifies that both updates remain. This is still a deliberately
small local store, but its concurrency behavior now matches the promise made by the stage tracker.

## Fixtures first, network later

Discovery is defined by a `CandidateSource` protocol. The working `FixtureSource` reads JSONL and
rejects malformed JSON, invalid UTF-8, missing fields, and blank required values with line-aware
errors. An `XApiSource` marks the future network boundary, but it raises today. That split let me
test scoring, storage, handoff, readiness checks, and reply drafting without credentials or paid
calls.

This boundary matters because Wishwright is not yet the unattended request-to-product bot in the
full vision. X search, build-system invocation, repository publishing, and reply posting still
need adapters and idempotent orchestration. The README and landing page state that plainly.

## What I would change next

I would replace substring scoring with a versioned policy engine that stores the rule version on
each evaluation. I would also add an outbox around external actions, so a crash after publishing
but before a ledger update cannot publish the same product twice. Finally, I would run a shadow X
adapter that records candidates without replying, then compare its decisions with human review
before enabling any public action.

The local core is small on purpose: 308 statements, 67 tests, and 95% branch-aware coverage in the
closeout run. The harder next step is not more scoring code. It is proving that every external
side effect is authorized, repeatable, and recoverable.
