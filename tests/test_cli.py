import json

import pytest

from wishwright.cli import build_parser, main


def test_evaluate_applies_config_deny_terms_end_to_end(tmp_path, capsys):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text(
        '{"id": "1", "author": "a", "text": "i wish there was an app that helped '
        'everyone plan a birthday party", "url": "https://x.com/a/1", '
        '"created_at": "2026-07-10T00:00:00Z"}\n'
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text("policy:\n  deny_terms:\n    - birthday party\n")

    exit_code = main(
        [
            "evaluate",
            "--input",
            str(fixture),
            "--config",
            str(config_path),
            "--log",
            str(tmp_path / "run.jsonl"),
        ]
    )
    out = capsys.readouterr().out

    assert exit_code == 0
    lines = [line for line in out.splitlines() if line.startswith("1")]
    assert len(lines) == 1
    assert "0.00" in lines[0]


def test_evaluate_prints_ranked_shortlist(tmp_path, capsys):
    exit_code = main(
        [
            "evaluate",
            "--input",
            "fixtures/sample_posts.jsonl",
            "--log",
            str(tmp_path / "run.jsonl"),
        ]
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "id" in out
    assert "score" in out


def test_evaluate_appends_run_log_entry_per_candidate(tmp_path, capsys):
    log_path = tmp_path / "nested" / "run.jsonl"
    exit_code = main(
        [
            "evaluate",
            "--input",
            "fixtures/sample_posts.jsonl",
            "--log",
            str(log_path),
        ]
    )
    capsys.readouterr()

    assert exit_code == 0
    lines = log_path.read_text().splitlines()
    assert len(lines) == 4
    for line in lines:
        entry = json.loads(line)
        assert entry.keys() >= {"timestamp", "stage", "candidate_id", "result"}
        assert entry["stage"] == "evaluated"


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


def test_help_lists_every_subcommand_with_a_description(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    out = capsys.readouterr().out

    subparsers_action = next(
        action for action in parser._actions if action.dest == "command"
    )
    assert subparsers_action.choices, "no subcommands registered"
    # each subcommand needs a name AND a non-empty one-line description, and
    # both must actually show up in --help output
    for choice_pseudo_action in subparsers_action._choices_actions:
        assert choice_pseudo_action.dest in out
        assert choice_pseudo_action.help, f"{choice_pseudo_action.dest} has no help text"
        assert choice_pseudo_action.help in out


def test_evaluate_output_columns_stay_aligned_for_varied_text_lengths(tmp_path, capsys):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text(
        "\n".join(
            [
                '{"id": "short", "author": "a", "text": "wish", '
                '"url": "https://x.com/a/1", "created_at": "2026-07-10T00:00:00Z"}',
                '{"id": "much-longer-id", "author": "b", '
                '"text": "i wish there was an app that everyone could use for '
                'something with a much much longer piece of request text here", '
                '"url": "https://x.com/b/2", "created_at": "2026-07-11T00:00:00Z"}',
            ]
        )
        + "\n"
    )

    exit_code = main(
        ["evaluate", "--input", str(fixture), "--log", str(tmp_path / "run.jsonl")]
    )
    out = capsys.readouterr().out
    assert exit_code == 0

    lines = out.splitlines()
    data_lines = [line for line in lines if line.startswith(("short", "much-longer-id"))]
    assert len(data_lines) == 2

    # score is formatted "%5.2f" (one digit before the decimal point, since
    # scores are in [0, 1]), so the decimal point lands in the same column
    # on every row regardless of how long the candidate id or text is.
    decimal_columns = {line.index(".") for line in data_lines}
    assert len(decimal_columns) == 1


def test_evaluate_reports_malformed_fixture_without_a_traceback(tmp_path, capsys):
    fixture = tmp_path / "posts.jsonl"
    fixture.write_text("not json\n")

    exit_code = main(["evaluate", "--input", str(fixture)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid JSON" in captured.err


def test_status_reports_corrupt_ledger_without_a_traceback(tmp_path, capsys):
    ledger = tmp_path / "ledger.json"
    ledger.write_text("not json")

    exit_code = main(["status", "--ledger", str(ledger)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid ledger" in captured.err
