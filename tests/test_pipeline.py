import pytest

from wishwright.models import Candidate, Evaluation
from wishwright.pipeline import advance, to_backlog_entry
from wishwright.storage import Ledger


def test_advance_moves_exactly_one_stage(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.mark_seen("1", stage="discovered")

    assert advance(ledger, "1") == "evaluated"
    assert advance(ledger, "1") == "built"


def test_advance_is_noop_at_terminal_stage(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.mark_seen("1", stage="replied")

    assert advance(ledger, "1") == "replied"


def test_advance_on_unknown_candidate_returns_none(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    assert advance(ledger, "missing") is None


def _candidate() -> Candidate:
    return Candidate(
        id="1", author="alice", text="i wish there was a tool", url="https://x.com/alice/1", created_at="2026-07-10T00:00:00Z"
    )


def test_to_backlog_entry_matches_expected_schema():
    evaluation = Evaluation(candidate_id="1", safety=1.0, feasibility=0.8, breadth=0.9, total=0.9)
    entry = to_backlog_entry(_candidate(), evaluation)
    assert entry["title"] == "i wish there was a tool"
    assert entry["category"] == "misc"
    assert "why_impressive" in entry


def test_to_backlog_entry_rejects_unapproved_candidate():
    evaluation = Evaluation(candidate_id="1", safety=0.0, feasibility=0.0, breadth=0.0, total=0.0)
    with pytest.raises(ValueError, match="not approved"):
        to_backlog_entry(_candidate(), evaluation)
