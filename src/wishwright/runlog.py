"""Structured JSONL audit log of pipeline stage transitions, so a stuck or
misbehaving run can be debugged after the fact."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .models import STAGES

DEFAULT_LOG_PATH = "logs/run.jsonl"


def log_event(path: str | Path, *, stage: str, candidate_id: str, result: str) -> None:
    """Appends one JSON line recording a pipeline stage transition. Creates
    the parent directory (e.g. logs/) if it doesn't exist yet."""
    if (
        stage not in STAGES
        or not isinstance(candidate_id, str)
        or not candidate_id.strip()
        or not isinstance(result, str)
        or not result.strip()
    ):
        raise ValueError("invalid run-log event fields")
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "stage": stage,
        "candidate_id": candidate_id,
        "result": result,
    }
    with log_path.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
