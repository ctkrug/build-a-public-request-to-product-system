import pytest

from wishwright.models import Candidate
from wishwright.reply import draft_reply


def _candidate() -> Candidate:
    return Candidate(id="1", author="alice", text="wish", url="https://x.com/alice/1", created_at="2026-07-10T00:00:00Z")


def test_draft_reply_includes_repo_url_and_fits_length():
    reply = draft_reply(_candidate(), "https://github.com/ctkrug/example")
    assert "https://github.com/ctkrug/example" in reply
    assert len(reply) <= 280


def test_draft_reply_rejects_non_https_url():
    with pytest.raises(ValueError, match="https"):
        draft_reply(_candidate(), "http://github.com/ctkrug/example")
