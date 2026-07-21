"""Ties the discover -> evaluate -> build -> publish -> replied stages
together, tracking each candidate's progress in a Ledger."""

from __future__ import annotations

from .models import STAGES, Candidate, Evaluation

_NEXT_STAGE = dict(zip(STAGES, STAGES[1:], strict=False))


def advance(ledger, candidate_id: str) -> str | None:
    """Moves a candidate exactly one stage forward. No-ops (returns the
    current stage) if the candidate is already at the terminal stage or
    isn't in the ledger yet."""
    current = ledger.stage_of(candidate_id)
    if current is None or current == STAGES[-1]:
        return current
    next_stage = _NEXT_STAGE[current]
    ledger.mark_seen(candidate_id, next_stage)
    return ledger.stage_of(candidate_id)


def to_backlog_entry(candidate: Candidate, evaluation: Evaluation) -> dict:
    """Converts an approved candidate into a project-factory-style backlog
    entry: title, category, and why_impressive are the fields the factory's
    ideas.yaml schema requires."""
    if not evaluation.approved:
        raise ValueError(f"candidate {candidate.id} was not approved (total={evaluation.total})")

    return {
        "title": candidate.text.strip(),
        "category": "misc",
        "why_impressive": (f"Directly requested publicly by @{candidate.author}: {candidate.url}"),
        "source_candidate_id": candidate.id,
        "source_url": candidate.url,
        "scores": {
            "safety": evaluation.safety,
            "feasibility": evaluation.feasibility,
            "breadth": evaluation.breadth,
            "total": evaluation.total,
        },
    }
