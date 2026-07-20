"""Checks that a built project directory has the basics before it's
allowed to be marked publishable."""

from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = ("README.md", "LICENSE")
REQUIRED_CI_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")


def check_ready(path: str | Path) -> list[str]:
    """Returns a list of human-readable reasons the project isn't ready to
    publish. An empty list means it's ready."""
    root = Path(path)
    reasons = []

    if not root.is_dir():
        return [f"{root} is not a directory"]

    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            reasons.append(f"missing {name}")

    if not any(
        workflow.is_file() for pattern in REQUIRED_CI_GLOBS for workflow in root.glob(pattern)
    ):
        reasons.append("missing a CI workflow under .github/workflows/")

    return reasons
