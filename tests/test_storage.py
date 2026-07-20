import json

import pytest

from wishwright.storage import Ledger


def test_mark_seen_then_has_seen(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    assert ledger.has_seen("1") is False
    ledger.mark_seen("1")
    assert ledger.has_seen("1") is True


def test_ledger_persists_across_instances(tmp_path):
    path = tmp_path / "ledger.json"
    Ledger(path).mark_seen("1", stage="evaluated")

    reloaded = Ledger(path)
    assert reloaded.stage_of("1") == "evaluated"


def test_stale_ledger_instances_do_not_overwrite_each_others_entries(tmp_path):
    path = tmp_path / "ledger.json"
    first_tab = Ledger(path)
    second_tab = Ledger(path)

    first_tab.mark_seen("one")
    second_tab.mark_seen("two", stage="evaluated")

    reloaded = Ledger(path)
    assert reloaded.stage_of("one") == "discovered"
    assert reloaded.stage_of("two") == "evaluated"


def test_counts_by_stage(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.mark_seen("1", stage="discovered")
    ledger.mark_seen("2", stage="discovered")
    ledger.mark_seen("3", stage="built")

    counts = ledger.counts_by_stage()
    assert counts["discovered"] == 2
    assert counts["built"] == 1
    assert counts["replied"] == 0


@pytest.mark.parametrize(
    "contents",
    ["{not-json", json.dumps(["not", "a", "ledger"]), json.dumps({"1": "unknown"})],
)
def test_ledger_rejects_corrupt_or_unknown_persisted_state(tmp_path, contents):
    path = tmp_path / "ledger.json"
    path.write_text(contents)

    with pytest.raises(ValueError, match=rf"invalid ledger .*{path}"):
        Ledger(path)


@pytest.mark.parametrize("candidate_id", ["", "  ", 1])
def test_mark_seen_rejects_invalid_candidate_ids_without_persisting(
    tmp_path, candidate_id
):
    path = tmp_path / "ledger.json"
    ledger = Ledger(path)

    with pytest.raises(ValueError, match="candidate_id"):
        ledger.mark_seen(candidate_id)

    assert ledger.counts_by_stage() == {
        stage: 0
        for stage in ("discovered", "evaluated", "built", "published", "replied")
    }
    assert not path.exists()
