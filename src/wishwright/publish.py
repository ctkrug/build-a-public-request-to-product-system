"""Checks that a built project directory has the basics before it's
allowed to be marked publishable."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

from .orchestrator import BuildResult

REQUIRED_FILES = ("README.md", "LICENSE")
REQUIRED_CI_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")


def check_ready(path: str | Path) -> list[str]:
    """Returns a list of human-readable reasons the project isn't ready to
    publish. An empty list means it's ready."""
    root = Path(path)
    reasons = [f"missing {name}" for name in REQUIRED_FILES if not (root / name).is_file()]

    if not root.is_dir():
        return [f"{root} is not a directory"]

    if not any(
        workflow.is_file() for pattern in REQUIRED_CI_GLOBS for workflow in root.glob(pattern)
    ):
        reasons.append("missing a CI workflow under .github/workflows/")

    return reasons


class ResumablePublisher:
    """Publish only targets that are not already publicly verifiable."""

    def __init__(
        self,
        push_repository: Callable[[Path], None],
        deploy_site: Callable[[Path], None],
        verify_url: Callable[[str], bool],
    ):
        self._push_repository = push_repository
        self._deploy_site = deploy_site
        self._verify_url = verify_url

    def publish(self, build: BuildResult) -> bool:
        repo_path = build.repo_path
        repo_url = build.repo_url
        site_path = build.site_path
        site_url = build.site_url
        if (
            not build.completed
            or repo_path is None
            or not repo_url
            or site_path is None
            or not site_url
        ):
            raise ValueError("a completed build with publication details is required")
        if not self._verify_url(repo_url):
            self._push_repository(repo_path)
            if not self._verify_url(repo_url):
                return False
        if not self._verify_url(site_url):
            self._deploy_site(site_path)
            if not self._verify_url(site_url):
                return False
        return True


def git_push_repository(path: Path) -> None:
    """Push the built repository to its configured origin."""
    subprocess.run(["git", "-C", str(path), "push", "origin", "HEAD"], check=True)


class CommandSiteDeployer:
    """Run an explicitly configured static-site deployment command safely."""

    def __init__(
        self, command: tuple[str, ...], run: Callable[[tuple[str, ...]], None] | None = None
    ):
        if not command or any(not isinstance(part, str) or not part for part in command):
            raise ValueError("site deployment command must contain non-empty arguments")
        if "{site_path}" not in command:
            raise ValueError("site deployment command must include a {site_path} argument")
        self.command = command
        self._run = run or self._run_command

    def __call__(self, path: Path) -> None:
        self._run(tuple(str(path) if part == "{site_path}" else part for part in self.command))

    @staticmethod
    def _run_command(command: tuple[str, ...]) -> None:
        subprocess.run(command, check=True)


def verify_public_url(url: str) -> bool:
    """Return whether a public repository or deployed site responds successfully."""
    if not url.startswith("https://"):
        raise ValueError("publication URL must use https://")
    try:
        with urlopen(Request(url, method="HEAD"), timeout=20) as response:  # noqa: S310
            return 200 <= response.status < 400
    except OSError:
        return False
