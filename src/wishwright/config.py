"""Loads config.yaml: search phrases and the safety/scoring policy."""

from __future__ import annotations

from dataclasses import dataclass, field
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

    raw = yaml.safe_load(file_path.read_text()) or {}
    phrases = tuple(raw.get("search_phrases", DEFAULT_SEARCH_PHRASES))
    policy_raw = raw.get("policy", {})
    policy = PolicySet(
        deny_terms=tuple(policy_raw.get("deny_terms", DEFAULT_DENY_TERMS)),
        min_total_score=float(policy_raw.get("min_total_score", 0.5)),
    )
    return Config(search_phrases=phrases, policy=policy)
