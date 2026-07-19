from wishwright.cli import main


def test_evaluate_prints_ranked_shortlist(capsys):
    exit_code = main(["evaluate", "--input", "fixtures/sample_posts.jsonl"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "id" in out
    assert "score" in out


def test_evaluate_empty_input_does_not_crash(tmp_path, capsys):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    exit_code = main(["evaluate", "--input", str(empty)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "no candidates" in out


def test_status_reports_zero_counts_for_empty_ledger(tmp_path, capsys):
    exit_code = main(["status", "--ledger", str(tmp_path / "ledger.json")])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "discovered" in out
