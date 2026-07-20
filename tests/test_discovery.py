import pytest
from urllib.parse import parse_qs, urlparse

from wishwright.discovery import FixtureSource, XApiSource


def test_fixture_source_yields_candidates(tmp_path):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text(
        '{"id": "1", "author": "a", "text": "wish", "url": "https://x.com/a/1", "created_at": "2026-07-10T00:00:00Z"}\n'
    )
    candidates = list(FixtureSource(fixture).fetch(search_phrases=["wish"]))
    assert len(candidates) == 1
    assert candidates[0].id == "1"


def test_fixture_source_missing_file_yields_nothing(tmp_path):
    candidates = list(FixtureSource(tmp_path / "missing.jsonl").fetch(search_phrases=[]))
    assert candidates == []


def test_fixture_source_raises_on_bad_json(tmp_path):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text("not json\n")
    with pytest.raises(ValueError, match="invalid JSON"):
        list(FixtureSource(fixture).fetch(search_phrases=[]))


def test_fixture_source_reports_invalid_utf8_with_path_and_line(tmp_path):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_bytes(
        b'{"id": "1", "author": "a", "text": "wish", '
        b'"url": "https://x.com/a/1", "created_at": "2026-07-10T00:00:00Z"}\n\xff'
    )

    with pytest.raises(ValueError, match=rf"{fixture}:2: invalid UTF-8"):
        list(FixtureSource(fixture).fetch(search_phrases=[]))


def test_fixture_source_raises_on_missing_required_field(tmp_path):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text('{"id": "1", "author": "a"}\n')
    with pytest.raises(ValueError, match="missing required field"):
        list(FixtureSource(fixture).fetch(search_phrases=[]))


def test_x_api_source_requires_a_bearer_token():
    with pytest.raises(ValueError, match="bearer token"):
        list(XApiSource().fetch(search_phrases=["wish"]))


def test_x_api_source_normalizes_paginated_search_results():
    requests = []
    pages = [
        {
            "data": [
                {
                    "id": "10",
                    "author_id": "42",
                    "text": "I wish there were a tool",
                    "created_at": "2026-07-20T00:00:00Z",
                }
            ],
            "includes": {"users": [{"id": "42", "username": "alice"}]},
            "meta": {"next_token": "page-two"},
        },
        {
            "data": [
                {
                    "id": "11",
                    "author_id": "43",
                    "text": "Someone should build this",
                    "created_at": "2026-07-20T01:00:00Z",
                }
            ],
            "includes": {"users": [{"id": "43", "username": "bob"}]},
            "meta": {},
        },
    ]

    def request(request):
        requests.append(request)
        return pages.pop(0)

    candidates = list(XApiSource("token", request=request).fetch(["wish tool"]))

    assert [(candidate.id, candidate.author, candidate.url) for candidate in candidates] == [
        ("10", "alice", "https://x.com/alice/status/10"),
        ("11", "bob", "https://x.com/bob/status/11"),
    ]
    assert requests[0].get_header("Authorization") == "Bearer token"
    assert parse_qs(urlparse(requests[1].full_url).query)["next_token"] == ["page-two"]
