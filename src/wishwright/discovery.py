"""Pluggable fixture and authenticated X candidate sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Candidate


class CandidateSource(Protocol):
    def fetch(self, search_phrases: Iterable[str]) -> Iterator[Candidate]: ...


class FixtureSource:
    """Reads candidates from a local JSONL file, one JSON object per line."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self, search_phrases: Iterable[str]) -> Iterator[Candidate]:
        if not self.path.exists():
            return
        with self.path.open("rb") as handle:
            for line_no, byte_line in enumerate(handle, start=1):
                try:
                    line = byte_line.decode("utf-8").strip()
                except UnicodeDecodeError as exc:
                    raise ValueError(f"{self.path}:{line_no}: invalid UTF-8") from exc
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{self.path}:{line_no}: invalid JSON") from exc
                yield Candidate.from_dict(data)


class XApiSource:
    """Fetches public request posts from X's recent-search API."""

    endpoint = "https://api.x.com/2/tweets/search/recent"

    def __init__(
        self,
        bearer_token: str | None = None,
        request: Callable[[Request], Mapping[str, Any]] | None = None,
    ):
        self.bearer_token = bearer_token
        self._request = request or self._live_request

    def fetch(self, search_phrases: Iterable[str]) -> Iterator[Candidate]:
        bearer_token = self.bearer_token
        if not isinstance(bearer_token, str) or not bearer_token.strip():
            raise ValueError("X API bearer token is required")
        seen_ids = set()
        for phrase in search_phrases:
            if not isinstance(phrase, str) or not phrase.strip():
                continue
            next_token = None
            while True:
                page = self._search_page(phrase.strip(), next_token, bearer_token.strip())
                for candidate in self._candidates(page):
                    if candidate.id not in seen_ids:
                        seen_ids.add(candidate.id)
                        yield candidate
                next_token = page.get("meta", {}).get("next_token")
                if not isinstance(next_token, str) or not next_token:
                    break

    def _search_page(
        self, phrase: str, next_token: str | None, bearer_token: str
    ) -> Mapping[str, Any]:
        query = f"({phrase}) -is:retweet"
        params = {
            "query": query,
            "max_results": "100",
            "tweet.fields": "author_id,created_at",
            "expansions": "author_id",
            "user.fields": "username",
        }
        if next_token:
            params["next_token"] = next_token
        request = Request(
            f"{self.endpoint}?{urlencode(params)}",
            headers={"Authorization": f"Bearer {bearer_token}"},
        )
        page = self._request(request)
        if not isinstance(page, Mapping):
            raise ValueError("X API returned a non-object response")
        return page

    @staticmethod
    def _live_request(request: Request) -> Mapping[str, Any]:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed X API endpoint
            try:
                payload = json.load(response)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("X API returned invalid JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("X API returned a non-object response")
        return payload

    @staticmethod
    def _candidates(page: Mapping[str, Any]) -> Iterator[Candidate]:
        data = page.get("data", [])
        users = page.get("includes", {}).get("users", [])
        if not isinstance(data, list) or not isinstance(users, list):
            raise ValueError("X API response has invalid data or includes.users")
        usernames = {
            user.get("id"): user.get("username") for user in users if isinstance(user, Mapping)
        }
        for tweet in data:
            if not isinstance(tweet, Mapping):
                raise ValueError("X API response contains an invalid tweet")
            author = usernames.get(tweet.get("author_id"))
            if not isinstance(author, str) or not author.strip():
                raise ValueError("X API response is missing a tweet author username")
            try:
                yield Candidate.from_dict(
                    {
                        "id": tweet.get("id"),
                        "author": author,
                        "text": tweet.get("text"),
                        "url": f"https://x.com/{author}/status/{tweet.get('id')}",
                        "created_at": tweet.get("created_at"),
                    }
                )
            except ValueError as exc:
                raise ValueError("X API response contains an invalid tweet") from exc
