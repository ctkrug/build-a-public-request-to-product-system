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


def test_counts_by_stage(tmp_path):
    ledger = Ledger(tmp_path / "ledger.json")
    ledger.mark_seen("1", stage="discovered")
    ledger.mark_seen("2", stage="discovered")
    ledger.mark_seen("3", stage="built")

    counts = ledger.counts_by_stage()
    assert counts["discovered"] == 2
    assert counts["built"] == 1
    assert counts["replied"] == 0
