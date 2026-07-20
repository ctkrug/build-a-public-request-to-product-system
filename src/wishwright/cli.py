"""wishwright command-line entrypoint."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import load_config
from .discovery import FixtureSource
from .evaluation import score_candidate
from .models import STAGES
from .runlog import DEFAULT_LOG_PATH, log_event
from .storage import Ledger

DEFAULT_LEDGER_PATH = "state/ledger.json"
DEFAULT_CONFIG_PATH = "config.yaml"


def _cmd_evaluate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    source = FixtureSource(args.input)
    candidates = list(source.fetch(config.search_phrases))

    if not candidates:
        print("no candidates found")
        return 0

    rows = []
    for candidate in candidates:
        evaluation = score_candidate(candidate, config.policy)
        rows.append((evaluation.total, candidate, evaluation))
        log_event(
            args.log,
            stage="evaluated",
            candidate_id=candidate.id,
            result="approved" if evaluation.approved else "rejected",
        )
    rows.sort(key=lambda row: row[0], reverse=True)

    id_width = max(len(c.id) for _, c, _ in rows)
    text_width = min(60, max(len(c.text) for _, c, _ in rows))
    header = f"{'id':<{id_width}}  {'score':>5}  text"
    print(header)
    print("-" * len(header))
    for total, candidate, _evaluation in rows:
        text = (
            candidate.text
            if len(candidate.text) <= text_width
            else candidate.text[: text_width - 1] + "…"
        )
        print(f"{candidate.id:<{id_width}}  {total:>5.2f}  {text}")

    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    ledger = Ledger(args.ledger)
    counts = ledger.counts_by_stage()
    width = max(len(stage) for stage in STAGES)
    for stage in STAGES:
        print(f"{stage:<{width}}  {counts[stage]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wishwright", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate = subparsers.add_parser("evaluate", help="score candidates from a fixture file")
    evaluate.add_argument("--input", required=True, help="path to a JSONL candidate fixture")
    evaluate.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"path to config.yaml (default: {DEFAULT_CONFIG_PATH}; falls back to built-in defaults if absent)",
    )
    evaluate.add_argument(
        "--log",
        default=DEFAULT_LOG_PATH,
        help=f"path to the JSONL run log (default: {DEFAULT_LOG_PATH})",
    )
    evaluate.set_defaults(func=_cmd_evaluate)

    status = subparsers.add_parser("status", help="report ledger counts per pipeline stage")
    status.add_argument(
        "--ledger", default=DEFAULT_LEDGER_PATH, help="path to the ledger JSON file"
    )
    status.set_defaults(func=_cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
