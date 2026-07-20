from wishwright.models import Candidate, Evaluation
from wishwright.orchestrator import BuildResult, Orchestrator
from wishwright.storage import Ledger


def _candidate() -> Candidate:
    return Candidate(
        id="1",
        author="alice",
        text="I wish there were a shared grocery-price tool",
        url="https://x.com/alice/status/1",
        created_at="2026-07-20T00:00:00Z",
    )


def _evaluation() -> Evaluation:
    return Evaluation(candidate_id="1", safety=1, feasibility=1, breadth=1, total=1)


def test_orchestrator_keeps_evaluated_candidate_until_build_completes(tmp_path):
    class PendingBuild:
        def submit(self, brief, idempotency_key):
            return BuildResult.pending()

    orchestrator = Orchestrator(Ledger(tmp_path / "ledger.json"), PendingBuild())

    assert orchestrator.process(_candidate(), _evaluation()) == "evaluated"
