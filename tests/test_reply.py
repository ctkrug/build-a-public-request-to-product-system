import pytest
import json

from wishwright.models import Candidate
from wishwright.reply import PendingReplyError, ReplyDelivery, XReplyClient, draft_reply


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


def test_reply_delivery_blocks_retry_after_an_ambiguous_failure(tmp_path):
    class AmbiguousClient:
        calls = 0

        def create_reply(self, candidate, text):
            self.calls += 1
            raise OSError("connection closed before the response")

    client = AmbiguousClient()
    delivery = ReplyDelivery(client, tmp_path / "replies.json")

    with pytest.raises(OSError, match="connection closed"):
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)
    with pytest.raises(PendingReplyError, match="needs reconciliation"):
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)

    assert client.calls == 1


def test_pending_reply_can_be_resolved_with_a_remote_id(tmp_path):
    class AmbiguousClient:
        def create_reply(self, candidate, text):
            raise OSError("connection closed before the response")

    delivery = ReplyDelivery(AmbiguousClient(), tmp_path / "replies.json")
    with pytest.raises(OSError):
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)

    delivery.store.resolve_pending(_candidate().id, "remote-99")

    assert (
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)
        == "remote-99"
    )


def test_pending_reply_can_be_cleared_after_confirming_no_post_exists(tmp_path):
    class RecoveringClient:
        calls = 0

        def create_reply(self, candidate, text):
            self.calls += 1
            if self.calls == 1:
                raise OSError("connection closed before the response")
            return "remote-100"

    client = RecoveringClient()
    delivery = ReplyDelivery(client, tmp_path / "replies.json")
    with pytest.raises(OSError):
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)

    delivery.store.resolve_pending(_candidate().id, None)

    assert (
        delivery.deliver(_candidate(), "https://github.com/ctkrug/example", authorized=True)
        == "remote-100"
    )


def test_x_reply_client_posts_to_source_candidate():
    sent = []

    def request(request):
        sent.append(request)
        return {"data": {"id": "remote-99"}}

    remote_id = XReplyClient("token", request=request).create_reply(_candidate(), "Built it")

    assert remote_id == "remote-99"
    assert sent[0].get_header("Authorization") == "Bearer token"
    assert json.loads(sent[0].data) == {
        "text": "Built it",
        "reply": {"in_reply_to_tweet_id": "1"},
    }


def test_x_reply_client_rejects_missing_credentials_and_response_id():
    with pytest.raises(ValueError, match="bearer token"):
        XReplyClient(" ")

    with pytest.raises(ValueError, match="post ID"):
        XReplyClient("token", request=lambda request: {"data": {}}).create_reply(
            _candidate(), "Built it"
        )
