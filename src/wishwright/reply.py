"""Drafts the reply posted back to the original request once the product
is shipped."""

from __future__ import annotations

from .models import Candidate

MAX_REPLY_LENGTH = 280


def draft_reply(candidate: Candidate, repo_url: str) -> str:
    if not repo_url.startswith("https://"):
        raise ValueError(f"repo_url must be an https:// URL, got {repo_url!r}")

    message = f"You asked, so I built it: {repo_url}"
    if len(message) > MAX_REPLY_LENGTH:
        raise ValueError(
            f"drafted reply exceeds {MAX_REPLY_LENGTH} chars: {len(message)}"
        )
    return message
