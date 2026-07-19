from hypothesis import given, strategies as st

from wishwright.config import PolicySet
from wishwright.evaluation import score_candidate
from wishwright.models import Candidate


def _candidate(text: str) -> Candidate:
    return Candidate(id="1", author="a", text=text, url="https://x.com/a/1", created_at="2026-07-10T00:00:00Z")


def test_denied_candidate_scores_zero_total_regardless_of_other_signals():
    policy = PolicySet(deny_terms=("hack into",))
    candidate = _candidate(
        "i wish there was an app that everyone could use, hack into accounts for me please"
    )
    evaluation = score_candidate(candidate, policy)
    assert evaluation.total == 0.0
    assert evaluation.approved is False
    assert "deny-list" in evaluation.reasons[0]


def test_broadly_useful_tool_request_scores_above_threshold():
    policy = PolicySet(min_total_score=0.5)
    candidate = _candidate("i wish there was an app that everyone could use for splitting bills")
    evaluation = score_candidate(candidate, policy)
    assert evaluation.total > 0
    assert evaluation.approved is True


def test_narrow_personal_request_scores_lower_than_broad_one():
    policy = PolicySet(min_total_score=0.0)
    broad = score_candidate(
        _candidate("i wish there was an app that everyone could use for splitting bills"), policy
    )
    narrow = score_candidate(
        _candidate("someone build a tool just for me, for my specific workflow"), policy
    )
    assert narrow.breadth < broad.breadth


@given(st.text())
def test_scoring_stays_within_its_public_score_range(text):
    evaluation = score_candidate(_candidate(text), PolicySet(deny_terms=()))

    assert 0.0 <= evaluation.safety <= 1.0
    assert 0.0 <= evaluation.feasibility <= 1.0
    assert 0.0 <= evaluation.breadth <= 1.0
    assert 0.0 <= evaluation.total <= 1.0


@given(st.text())
def test_deny_terms_are_a_hard_gate_for_all_request_text(text):
    evaluation = score_candidate(_candidate(f"{text} unsafe"), PolicySet(deny_terms=("unsafe",)))

    assert evaluation.total == 0.0
    assert evaluation.safety == 0.0
