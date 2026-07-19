"""Structured JSONL audit log of pipeline stage transitions, so a stuck or
misbehaving run can be debugged after the fact."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = "logs/run.jsonl"


def log_event(path: str | Path, *, stage: str, candidate_id: str, result: str) -> None:
    """Appends one JSON line recording a pipeline stage transition. Creates
    the parent directory (e.g. logs/) if it doesn't exist yet."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "candidate_id": candidate_id,
        "result": result,
    }
    with log_path.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
