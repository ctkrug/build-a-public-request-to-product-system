import json

import pytest

from wishwright.runlog import log_event


def test_log_event_appends_jsonl_line_with_required_keys(tmp_path):
    log_path = tmp_path / "logs" / "run.jsonl"
    log_event(log_path, stage="evaluated", candidate_id="1", result="approved")

    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["stage"] == "evaluated"
    assert entry["candidate_id"] == "1"
    assert entry["result"] == "approved"
    assert "timestamp" in entry


def test_log_event_creates_missing_parent_directory(tmp_path):
    log_path = tmp_path / "does" / "not" / "exist" / "run.jsonl"
    assert not log_path.parent.exists()

    log_event(log_path, stage="discovered", candidate_id="1", result="new")

    assert log_path.exists()


def test_log_event_appends_without_truncating_prior_entries(tmp_path):
    log_path = tmp_path / "run.jsonl"
    log_event(log_path, stage="discovered", candidate_id="1", result="new")
    log_event(log_path, stage="evaluated", candidate_id="1", result="approved")

    lines = log_path.read_text().splitlines()
    assert len(lines) == 2


@pytest.mark.parametrize(
    "stage,candidate_id,result",
    [("unknown", "1", "approved"), ("evaluated", " ", "approved"), ("evaluated", "1", "")],
)
def test_log_event_rejects_invalid_event_fields(tmp_path, stage, candidate_id, result):
    with pytest.raises(ValueError, match="invalid run-log"):
        log_event(tmp_path / "run.jsonl", stage=stage, candidate_id=candidate_id, result=result)
