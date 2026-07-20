"""Idempotently move approved requests through the external build boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import Candidate, Evaluation
from .pipeline import advance, to_backlog_entry
from .storage import Ledger


@dataclass(frozen=True)
class BuildResult:
    """The externally confirmed result of a build submission."""

    completed: bool
    repo_path: Path | None = None
    repo_url: str | None = None
    site_path: Path | None = None
    site_url: str | None = None

    @classmethod
    def pending(cls) -> "BuildResult":
        return cls(completed=False)


class BuildSystem(Protocol):
    def submit(self, brief: dict, idempotency_key: str) -> BuildResult: ...


class Orchestrator:
    """Submit approved briefs once, advancing only after build confirmation."""

    def __init__(self, ledger: Ledger, build_system: BuildSystem):
        self.ledger = ledger
        self.build_system = build_system

    def process(self, candidate: Candidate, evaluation: Evaluation) -> str:
        if candidate.id != evaluation.candidate_id:
            raise ValueError("candidate and evaluation IDs must match")
        if self.ledger.stage_of(candidate.id) is None:
            self.ledger.mark_seen(candidate.id)
        if self.ledger.stage_of(candidate.id) == "discovered":
            advance(self.ledger, candidate.id)
        if self.ledger.stage_of(candidate.id) != "evaluated" or not evaluation.approved:
            return self.ledger.stage_of(candidate.id) or "discovered"

        result = self.build_system.submit(to_backlog_entry(candidate, evaluation), candidate.id)
        if result.completed:
            if not result.repo_path or not result.repo_url or not result.site_path or not result.site_url:
                raise ValueError("completed build result must include repository and site details")
            advance(self.ledger, candidate.id)
        return self.ledger.stage_of(candidate.id) or "discovered"
