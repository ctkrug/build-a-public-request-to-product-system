"""Idempotently move approved requests through the external build boundary."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib.request import Request, urlopen

from .models import Candidate, Evaluation
from .pipeline import advance, to_backlog_entry
from .storage import Ledger


@dataclass(frozen=True)
class BuildResult:
    """The externally confirmed result of a build submission."""

    completed: bool
    repo_path: Path | None = None
    repo_url: str | None = None
    site_path: Path | None = None
    site_url: str | None = None

    @classmethod
    def pending(cls) -> "BuildResult":
        return cls(completed=False)


class BuildSystem(Protocol):
    def submit(self, brief: dict, idempotency_key: str) -> BuildResult: ...


class HttpBuildSystem:
    """Authenticated client for a build service that accepts backlog briefs."""

    def __init__(
        self,
        endpoint: str,
        bearer_token: str,
        request: Callable[[Request], Mapping[str, Any]] | None = None,
    ):
        if not endpoint.startswith("https://"):
            raise ValueError("build endpoint must be an https:// URL")
        if not bearer_token.strip():
            raise ValueError("build API bearer token is required")
        self.endpoint = endpoint
        self.bearer_token = bearer_token
        self._request = request or self._live_request

    def submit(self, brief: dict, idempotency_key: str) -> BuildResult:
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("build idempotency key is required")
        request = Request(
            self.endpoint,
            data=json.dumps(brief).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
        )
        payload = self._request(request)
        if not isinstance(payload, Mapping) or not isinstance(payload.get("completed"), bool):
            raise ValueError("build API returned an invalid completion response")
        if not payload["completed"]:
            return BuildResult.pending()
        fields = ("repo_path", "repo_url", "site_path", "site_url")
        if any(
            not isinstance(payload.get(field), str) or not payload[field].strip()
            for field in fields
        ):
            raise ValueError("build API completed response is missing artifact details")
        return BuildResult(
            completed=True,
            repo_path=Path(payload["repo_path"]),
            repo_url=payload["repo_url"],
            site_path=Path(payload["site_path"]),
            site_url=payload["site_url"],
        )

    @staticmethod
    def _live_request(request: Request) -> Mapping[str, Any]:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - configured HTTPS endpoint
            try:
                payload = json.load(response)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("build API returned invalid JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("build API returned an invalid response")
        return payload


class Orchestrator:
    """Submit approved briefs once, advancing only after build confirmation."""

    def __init__(self, ledger: Ledger, build_system: BuildSystem):
        self.ledger = ledger
        self.build_system = build_system

    def process(self, candidate: Candidate, evaluation: Evaluation) -> str:
        if candidate.id != evaluation.candidate_id:
            raise ValueError("candidate and evaluation IDs must match")
        if self.ledger.stage_of(candidate.id) is None:
            self.ledger.mark_seen(candidate.id)
        if self.ledger.stage_of(candidate.id) == "discovered":
            advance(self.ledger, candidate.id)
        if self.ledger.stage_of(candidate.id) != "evaluated" or not evaluation.approved:
            return self.ledger.stage_of(candidate.id) or "discovered"

        result = self.build_system.submit(to_backlog_entry(candidate, evaluation), candidate.id)
        if result.completed:
            if (
                not result.repo_path
                or not result.repo_url
                or not result.site_path
                or not result.site_url
            ):
                raise ValueError("completed build result must include repository and site details")
            advance(self.ledger, candidate.id)
        return self.ledger.stage_of(candidate.id) or "discovered"
