"""JSON-backed ledger so every candidate is processed exactly once and
its pipeline stage survives process restarts."""

from __future__ import annotations

import json
from pathlib import Path

from .models import STAGES


class Ledger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._entries: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            entries = json.loads(self.path.read_text() or "{}")
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid ledger at {self.path}") from exc
        if (
            not isinstance(entries, dict)
            or any(
                not isinstance(candidate_id, str)
                or not candidate_id.strip()
                or stage not in STAGES
                for candidate_id, stage in entries.items()
            )
        ):
            raise ValueError(f"invalid ledger at {self.path}")
        self._entries = entries

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._entries, indent=2, sort_keys=True))
        tmp.replace(self.path)

    def has_seen(self, candidate_id: str) -> bool:
        return candidate_id in self._entries

    def mark_seen(self, candidate_id: str, stage: str = "discovered") -> None:
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("candidate_id must be a non-empty string")
        if stage not in STAGES:
            raise ValueError(f"unknown stage {stage!r}, expected one of {STAGES}")
        self._entries[candidate_id] = stage
        self._save()

    def stage_of(self, candidate_id: str) -> str | None:
        return self._entries.get(candidate_id)

    def counts_by_stage(self) -> dict[str, int]:
        counts = {stage: 0 for stage in STAGES}
        for stage in self._entries.values():
            counts[stage] = counts.get(stage, 0) + 1
        return counts
