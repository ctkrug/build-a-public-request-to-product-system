import json

from wishwright.cli import main


def test_evaluate_applies_config_deny_terms_end_to_end(tmp_path, capsys):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text(
        '{"id": "1", "author": "a", "text": "i wish there was an app that helped '
        'everyone plan a birthday party", "url": "https://x.com/a/1", '
        '"created_at": "2026-07-10T00:00:00Z"}\n'
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text("policy:\n  deny_terms:\n    - birthday party\n")

    exit_code = main(["evaluate", "--input", str(fixture), "--config", str(config_path)])
    out = capsys.readouterr().out

    assert exit_code == 0
    lines = [line for line in out.splitlines() if line.startswith("1")]
    assert len(lines) == 1
    assert "0.00" in lines[0]


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
    for line in out.splitlines():
        stage, _, count = line.rpartition(" ")
        assert count.strip() == "0"


def test_status_reports_known_stage_mix(tmp_path, capsys):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "1": "discovered",
                "2": "discovered",
                "3": "discovered",
                "4": "evaluated",
                "5": "built",
            }
        )
    )

    exit_code = main(["status", "--ledger", str(ledger_path)])
    out = capsys.readouterr().out

    assert exit_code == 0
    counts = {}
    for line in out.splitlines():
        stage, _, count = line.rpartition(" ")
        counts[stage.strip()] = int(count.strip())
    assert counts == {
        "discovered": 3,
        "evaluated": 1,
        "built": 1,
        "published": 0,
        "replied": 0,
    }
