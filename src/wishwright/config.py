"""Loads config.yaml: search phrases and the safety/scoring policy."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path

import yaml

DEFAULT_DENY_TERMS = (
    "weapon",
    "explosive",
    "exploit for",
    "hack into",
    "malware",
    "surveil my",
    "stalk",
)

DEFAULT_SEARCH_PHRASES = (
    "i wish there was an app that",
    "i wish someone would build",
    "someone should build a tool that",
    "does anyone know a tool that",
)


@dataclass(frozen=True)
class PolicySet:
    """Safety and scoring thresholds. deny_terms are matched case-insensitively."""

    deny_terms: tuple[str, ...] = DEFAULT_DENY_TERMS
    min_total_score: float = 0.5

    def is_denied(self, text: str) -> bool:
        lowered = text.lower()
        return any(term.lower() in lowered for term in self.deny_terms)


@dataclass(frozen=True)
class Config:
    search_phrases: tuple[str, ...] = DEFAULT_SEARCH_PHRASES
    policy: PolicySet = field(default_factory=PolicySet)


def load_config(path: str | Path | None) -> Config:
    """Loads Config from a YAML file, falling back to defaults if path is None
    or the file doesn't exist yet (first run, before config.yaml is created)."""
    if path is None:
        return Config()
    file_path = Path(path)
    if not file_path.exists():
        return Config()

    try:
        raw = yaml.safe_load(file_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid config YAML in {file_path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("config root must be a mapping")

    phrases = _text_list(
        raw.get("search_phrases", DEFAULT_SEARCH_PHRASES), "search_phrases"
    )
    policy_raw = raw.get("policy", {})
    if not isinstance(policy_raw, dict):
        raise ValueError("config policy must be a mapping")
    deny_terms = _text_list(
        policy_raw.get("deny_terms", DEFAULT_DENY_TERMS), "policy.deny_terms"
    )
    try:
        min_total_score = float(policy_raw.get("min_total_score", 0.5))
    except (TypeError, ValueError) as exc:
        raise ValueError("config policy.min_total_score must be a number") from exc
    if not math.isfinite(min_total_score) or not 0 <= min_total_score <= 1:
        raise ValueError("config policy.min_total_score must be between 0 and 1")
    policy = PolicySet(
        deny_terms=deny_terms,
        min_total_score=min_total_score,
    )
    return Config(search_phrases=phrases, policy=policy)


def _text_list(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"config {name} must be a list of non-empty strings")
    return tuple(value)
