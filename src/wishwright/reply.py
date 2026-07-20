"""Drafts the reply posted back to the original request once the product
is shipped."""

from __future__ import annotations

import fcntl
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib.request import Request, urlopen

from .models import Candidate

MAX_REPLY_LENGTH = 280


def draft_reply(candidate: Candidate, repo_url: str) -> str:
    if not repo_url.startswith("https://"):
        raise ValueError(f"repo_url must be an https:// URL, got {repo_url!r}")

    message = f"You asked, so I built it: {repo_url}"
    if len(message) > MAX_REPLY_LENGTH:
        raise ValueError(f"drafted reply exceeds {MAX_REPLY_LENGTH} chars: {len(message)}")
    return message


class ReplyClient(Protocol):
    def create_reply(self, candidate: Candidate, text: str) -> str: ...


class XReplyClient:
    """Authenticated X API client that replies to the source post."""

    endpoint = "https://api.x.com/2/tweets"

    def __init__(
        self,
        bearer_token: str,
        request: Callable[[Request], Mapping[str, Any]] | None = None,
    ):
        if not bearer_token.strip():
            raise ValueError("X API bearer token is required")
        self.bearer_token = bearer_token
        self._request = request or self._live_request

    def create_reply(self, candidate: Candidate, text: str) -> str:
        request = Request(
            self.endpoint,
            data=json.dumps(
                {"text": text, "reply": {"in_reply_to_tweet_id": candidate.id}}
            ).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            },
        )
        payload = self._request(request)
        remote_id = payload.get("data", {}).get("id") if isinstance(payload, Mapping) else None
        if not isinstance(remote_id, str) or not remote_id.strip():
            raise ValueError("X API reply response is missing a post ID")
        return remote_id

    @staticmethod
    def _live_request(request: Request) -> Mapping[str, Any]:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed X API endpoint
            try:
                payload = json.load(response)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("X API returned invalid reply JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("X API returned an invalid reply response")
        return payload


class ReplyStore:
    """Durably map source candidates to their remote reply IDs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get(self, candidate_id: str) -> str | None:
        return self._load().get(candidate_id)

    def save(self, candidate_id: str, remote_id: str) -> None:
        if not isinstance(remote_id, str) or not remote_id.strip():
            raise ValueError("remote reply ID is required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(f"{self.path.name}.lock")
        with lock_path.open("a") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                replies = self._load()
                replies.setdefault(candidate_id, remote_id)
                temporary = self.path.with_suffix(self.path.suffix + ".tmp")
                temporary.write_text(json.dumps(replies, indent=2, sort_keys=True))
                temporary.replace(self.path)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            replies = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid reply store at {self.path}") from exc
        if not isinstance(replies, dict) or any(
            not isinstance(candidate_id, str)
            or not candidate_id.strip()
            or not isinstance(remote_id, str)
            or not remote_id.strip()
            for candidate_id, remote_id in replies.items()
        ):
            raise ValueError(f"invalid reply store at {self.path}")
        return replies


class ReplyDelivery:
    """Send only explicitly authorized replies and reuse persisted remote IDs."""

    def __init__(self, client: ReplyClient, store_path: str | Path):
        self.client = client
        self.store = ReplyStore(store_path)

    def deliver(self, candidate: Candidate, repo_url: str, *, authorized: bool) -> str | None:
        if authorized is not True:
            return None
        existing = self.store.get(candidate.id)
        if existing:
            return existing
        remote_id = self.client.create_reply(candidate, draft_reply(candidate, repo_url))
        self.store.save(candidate.id, remote_id)
        return remote_id
