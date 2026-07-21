from wishwright.models import Candidate, Evaluation
from wishwright.orchestrator import BuildResult, HttpBuildSystem, Orchestrator
from wishwright.publish import ResumablePublisher
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


def test_http_build_system_posts_idempotent_brief_and_normalizes_completion(tmp_path):
    sent = []

    def request(request):
        sent.append(request)
        return {
            "completed": True,
            "repo_path": str(tmp_path / "repo"),
            "repo_url": "https://github.com/ctkrug/grocery-tool",
            "site_path": str(tmp_path / "site"),
            "site_url": "https://apps.charliekrug.com/grocery-tool/",
        }

    result = HttpBuildSystem("https://factory.example/builds", "secret", request=request).submit(
        {"title": "Grocery tool"}, "candidate-1"
    )

    assert result.completed is True
    assert result.repo_url == "https://github.com/ctkrug/grocery-tool"
    assert sent[0].get_header("Authorization") == "Bearer secret"
    assert sent[0].get_header("Idempotency-key") == "candidate-1"


def test_orchestrator_persists_build_result_for_a_resumed_publish(tmp_path):
    repo_path = tmp_path / "repo"
    (repo_path / ".github" / "workflows").mkdir(parents=True)
    (repo_path / "README.md").write_text("# Tool")
    (repo_path / "LICENSE").write_text("MIT")
    (repo_path / ".github" / "workflows" / "ci.yml").write_text("name: CI")
    (tmp_path / "site").mkdir()

    class CompleteBuild:
        calls = 0

        def submit(self, brief, idempotency_key):
            self.calls += 1
            return BuildResult(
                completed=True,
                repo_path=repo_path,
                repo_url="https://github.com/ctkrug/tool",
                site_path=tmp_path / "site",
                site_url="https://apps.charliekrug.com/tool/",
            )

    build_system = CompleteBuild()
    publisher = ResumablePublisher(lambda path: None, lambda path: None, lambda url: False)
    orchestrator = Orchestrator(
        Ledger(tmp_path / "ledger.json"),
        build_system,
        publisher=publisher,
        artifacts_path=tmp_path / "artifacts.json",
    )

    assert orchestrator.process(_candidate(), _evaluation()) == "built"
    assert orchestrator.process(_candidate(), _evaluation()) == "built"
    assert build_system.calls == 1
