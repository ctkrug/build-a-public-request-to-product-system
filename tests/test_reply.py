import pytest

from wishwright.models import Candidate
from wishwright.reply import ReplyDelivery, draft_reply


def _candidate() -> Candidate:
    return Candidate(
        id="1",
        author="alice",
        text="wish",
        url="https://x.com/alice/1",
        created_at="2026-07-10T00:00:00Z",
    )


def test_draft_reply_includes_repo_url_and_fits_length():
    reply = draft_reply(_candidate(), "https://github.com/ctkrug/example")
    assert "https://github.com/ctkrug/example" in reply
    assert len(reply) <= 280


def test_draft_reply_rejects_non_https_url():
    with pytest.raises(ValueError, match="https"):
        draft_reply(_candidate(), "http://github.com/ctkrug/example")


def test_reply_delivery_requires_authorization_and_persists_remote_id(tmp_path):
    class Client:
        calls = 0

        def create_reply(self, candidate, text):
            self.calls += 1
            return "remote-55"

    client = Client()
    delivery = ReplyDelivery(client, tmp_path / "replies.json")

    assert (
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=False)
        is None
    )
    assert (
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)
        == "remote-55"
    )
    assert (
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)
        == "remote-55"
    )
    assert client.calls == 1
