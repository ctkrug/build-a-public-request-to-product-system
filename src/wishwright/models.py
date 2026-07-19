"""Core data types shared across pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field

REQUIRED_CANDIDATE_FIELDS = ("id", "author", "text", "url", "created_at")

STAGES = ("discovered", "evaluated", "built", "published", "replied")


@dataclass(frozen=True)
class Candidate:
    """A single public post that looks like a build request."""

    id: str
    author: str
    text: str
    url: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Candidate":
        missing = [f for f in REQUIRED_CANDIDATE_FIELDS if not data.get(f)]
        if missing:
            raise ValueError(f"candidate missing required field(s): {', '.join(missing)}")
        return cls(**{f: data[f] for f in REQUIRED_CANDIDATE_FIELDS})


@dataclass(frozen=True)
class Evaluation:
    """Scoring result for a single candidate, each axis in [0, 1]."""

    candidate_id: str
    safety: float
    feasibility: float
    breadth: float
    total: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def approved(self) -> bool:
        return self.total > 0
