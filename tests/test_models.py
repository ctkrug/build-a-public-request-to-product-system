import pytest

from wishwright.models import Candidate


def test_candidate_from_dict_round_trips_required_fields():
    data = {
        "id": "1",
        "author": "alice",
        "text": "wish text",
        "url": "https://x.com/alice/status/1",
        "created_at": "2026-07-10T00:00:00Z",
    }
    candidate = Candidate.from_dict(data)
    assert candidate.id == "1"
    assert candidate.author == "alice"


def test_candidate_from_dict_raises_on_missing_field():
    data = {"id": "1", "author": "alice", "text": "wish text"}
    with pytest.raises(ValueError, match="missing required field"):
        Candidate.from_dict(data)


@pytest.mark.parametrize(
    "field,value",
    [("id", "   "), ("author", 7), ("text", "\t"), ("url", None), ("created_at", [])],
)
def test_candidate_from_dict_rejects_blank_or_non_string_fields(field, value):
    data = {
        "id": "1",
        "author": "alice",
        "text": "wish text",
        "url": "https://x.com/alice/status/1",
        "created_at": "2026-07-10T00:00:00Z",
    }
    data[field] = value

    with pytest.raises(ValueError, match="invalid required field"):
        Candidate.from_dict(data)


def test_candidate_from_dict_rejects_non_object_payload():
    with pytest.raises(ValueError, match="object"):
        Candidate.from_dict(["not", "a", "candidate"])
