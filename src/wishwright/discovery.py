"""Pluggable candidate sources.

XApiSource is the real production source (not wired up yet because it needs API
credentials, tracked in the backlog). FixtureSource lets the rest of the
pipeline be built and tested against realistic data now, without network
access or a live API key.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from .models import Candidate


class CandidateSource(Protocol):
    def fetch(self, search_phrases: Iterable[str]) -> Iterator[Candidate]: ...


class FixtureSource:
    """Reads candidates from a local JSONL file, one JSON object per line."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self, search_phrases: Iterable[str]) -> Iterator[Candidate]:
        if not self.path.exists():
            return
        with self.path.open("rb") as handle:
            for line_no, byte_line in enumerate(handle, start=1):
                try:
                    line = byte_line.decode("utf-8").strip()
                except UnicodeDecodeError as exc:
                    raise ValueError(f"{self.path}:{line_no}: invalid UTF-8") from exc
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{self.path}:{line_no}: invalid JSON") from exc
                yield Candidate.from_dict(data)


class XApiSource:
    """Placeholder for the real X API source. Raises until credentials and
    the search integration are implemented (tracked in docs/BACKLOG.md)."""

    def __init__(self, bearer_token: str | None = None):
        self.bearer_token = bearer_token

    def fetch(self, search_phrases: Iterable[str]) -> Iterator[Candidate]:
        raise NotImplementedError("XApiSource is not implemented yet; use FixtureSource")
