"""Checks that a built project directory has the basics before it's
allowed to be marked publishable."""

from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = ("README.md", "LICENSE")
REQUIRED_CI_GLOB = ".github/workflows/*.yml"


def check_ready(path: str | Path) -> list[str]:
    """Returns a list of human-readable reasons the project isn't ready to
    publish. An empty list means it's ready."""
    root = Path(path)
    reasons = []

    if not root.is_dir():
        return [f"{root} is not a directory"]

    for name in REQUIRED_FILES:
        if not (root / name).exists():
            reasons.append(f"missing {name}")

    if not list(root.glob(REQUIRED_CI_GLOB)):
        reasons.append("missing a CI workflow under .github/workflows/")

    return reasons
