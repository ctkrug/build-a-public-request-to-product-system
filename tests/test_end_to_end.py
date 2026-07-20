from wishwright.discovery import FixtureSource
from wishwright.config import PolicySet
from wishwright.evaluation import score_candidate
from wishwright.orchestrator import BuildResult, Orchestrator
from wishwright.publish import ResumablePublisher
from wishwright.reply import ReplyDelivery
from wishwright.storage import Ledger


def test_approved_request_travels_from_source_to_confirmed_reply(tmp_path):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text(
        '{"id":"42","author":"alice","text":"I wish there was an app that everyone could use to split grocery bills","url":"https://x.com/alice/status/42","created_at":"2026-07-20T00:00:00Z"}\n'
    )
    candidate = next(FixtureSource(fixture).fetch(["wish"]))
    evaluation = score_candidate(candidate, policy=PolicySet())

    class Builder:
        def submit(self, brief, idempotency_key):
            return BuildResult(
                completed=True,
                repo_path=tmp_path / "repo",
                repo_url="https://github.com/ctkrug/grocery-tool",
                site_path=tmp_path / "site",
                site_url="https://apps.charliekrug.com/grocery-tool/",
            )

    class ReplyClient:
        def create_reply(self, candidate, text):
            return "9001"

    publisher = ResumablePublisher(lambda path: None, lambda path: None, lambda url: True)
    reply_delivery = ReplyDelivery(ReplyClient(), tmp_path / "replies.json")
    orchestrator = Orchestrator(
        Ledger(tmp_path / "ledger.json"),
        Builder(),
        publisher=publisher,
        reply_delivery=reply_delivery,
        artifacts_path=tmp_path / "artifacts.json",
    )

    assert orchestrator.process(candidate, evaluation, authorized_reply=True) == "replied"
    assert reply_delivery.store.get(candidate.id) == "9001"
