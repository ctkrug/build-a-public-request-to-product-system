from pathlib import Path

from wishwright.config import PolicySet, load_config


def test_load_config_defaults_when_path_is_none():
    config = load_config(None)
    assert config.search_phrases
    assert config.policy.min_total_score == 0.5


def test_load_config_defaults_when_file_missing(tmp_path):
    config = load_config(tmp_path / "does-not-exist.yaml")
    assert config.search_phrases


def test_load_config_reads_custom_deny_terms(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "search_phrases:\n  - custom phrase\n"
        "policy:\n  deny_terms:\n    - forbidden-term\n  min_total_score: 0.7\n"
    )
    config = load_config(config_path)
    assert config.search_phrases == ("custom phrase",)
    assert config.policy.deny_terms == ("forbidden-term",)
    assert config.policy.min_total_score == 0.7


def test_policy_is_denied_case_insensitive():
    policy = PolicySet(deny_terms=("Forbidden",))
    assert policy.is_denied("this has FORBIDDEN in it")
    assert not policy.is_denied("this is fine")
