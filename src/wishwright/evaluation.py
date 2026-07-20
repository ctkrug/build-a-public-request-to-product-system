"""Scores a candidate on safety, feasibility, and breadth of usefulness.

A candidate that matches the policy's deny-list is auto-rejected (total=0)
regardless of how well it scores on the other axes — safety is a gate, not
one input averaged in with the rest.
"""

from __future__ import annotations

from .config import PolicySet
from .models import Candidate, Evaluation

# Signals that a request is broadly useful rather than a one-off personal need.
BREADTH_HINTS = ("anyone", "everyone", "people", "we all", "so many of us")
PERSONAL_HINTS = ("for my", "just for me", "my specific", "my own use case")

FEASIBILITY_HINTS = ("app", "tool", "extension", "bot", "script", "site", "dashboard")


def _keyword_score(
    text: str, positive: tuple[str, ...], negative: tuple[str, ...] = ()
) -> float:
    lowered = text.lower()
    score = 0.5
    if any(term in lowered for term in positive):
        score += 0.5
    if any(term in lowered for term in negative):
        score -= 0.5
    return max(0.0, min(1.0, score))


def score_candidate(candidate: Candidate, policy: PolicySet) -> Evaluation:
    if policy.is_denied(candidate.text):
        return Evaluation(
            candidate_id=candidate.id,
            safety=0.0,
            feasibility=0.0,
            breadth=0.0,
            total=0.0,
            reasons=("matched safety deny-list",),
        )

    safety = 1.0
    feasibility = _keyword_score(candidate.text, FEASIBILITY_HINTS)
    breadth = _keyword_score(candidate.text, BREADTH_HINTS, PERSONAL_HINTS)

    total = round((safety + feasibility + breadth) / 3, 4)
    reasons: tuple[str, ...] = ()
    if total < policy.min_total_score:
        reasons = (f"total {total} below min_total_score {policy.min_total_score}",)
        total = 0.0

    return Evaluation(
        candidate_id=candidate.id,
        safety=safety,
        feasibility=feasibility,
        breadth=breadth,
        total=total,
        reasons=reasons,
    )
