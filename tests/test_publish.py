from wishwright.orchestrator import BuildResult
import pytest

from wishwright import publish
from wishwright.publish import (
    CommandSiteDeployer,
    ResumablePublisher,
    check_ready,
    git_push_repository,
    verify_public_url,
)


def _make_ready_repo(path):
    (path / ".github" / "workflows").mkdir(parents=True)
    (path / "README.md").write_text("# hi")
    (path / "LICENSE").write_text("MIT")
    (path / ".github" / "workflows" / "ci.yml").write_text("name: ci")


def test_check_ready_returns_empty_for_well_formed_repo(tmp_path):
    _make_ready_repo(tmp_path)
    assert check_ready(tmp_path) == []


def test_check_ready_flags_missing_license(tmp_path):
    _make_ready_repo(tmp_path)
    (tmp_path / "LICENSE").unlink()
    reasons = check_ready(tmp_path)
    assert any("LICENSE" in r for r in reasons)


def test_check_ready_flags_missing_ci(tmp_path):
    _make_ready_repo(tmp_path)
    (tmp_path / ".github" / "workflows" / "ci.yml").unlink()
    reasons = check_ready(tmp_path)
    assert any("CI" in r for r in reasons)


def test_check_ready_non_directory(tmp_path):
    missing = tmp_path / "nope"
    assert check_ready(missing) == [f"{missing} is not a directory"]


def test_check_ready_accepts_yaml_ci_workflow(tmp_path):
    _make_ready_repo(tmp_path)
    (tmp_path / ".github" / "workflows" / "ci.yml").unlink()
    (tmp_path / ".github" / "workflows" / "ci.yaml").write_text("name: ci")

    assert check_ready(tmp_path) == []


def test_check_ready_rejects_directories_in_place_of_required_files(tmp_path):
    _make_ready_repo(tmp_path)
    (tmp_path / "README.md").unlink()
    (tmp_path / "README.md").mkdir()

    assert "missing README.md" in check_ready(tmp_path)


def test_resumable_publisher_retries_only_unverified_targets(tmp_path):
    calls = []
    visible = {"https://github.com/ctkrug/tool": True, "https://apps.charliekrug.com/tool/": False}
    site_path = tmp_path / "site"
    site_path.mkdir()

    publisher = ResumablePublisher(
        push_repository=lambda path: calls.append(("repo", path)),
        deploy_site=lambda path: calls.append(("site", path)),
        verify_url=lambda url: visible[url],
    )
    build = BuildResult(
        completed=True,
        repo_path=tmp_path / "repo",
        repo_url="https://github.com/ctkrug/tool",
        site_path=site_path,
        site_url="https://apps.charliekrug.com/tool/",
    )

    assert publisher.publish(build) is False
    assert calls == [("site", tmp_path / "site")]


def test_resumable_publisher_blocks_repository_that_fails_readiness(tmp_path):
    calls = []
    publisher = ResumablePublisher(
        push_repository=lambda path: calls.append(path),
        deploy_site=lambda path: None,
        verify_url=lambda url: False,
    )
    build = BuildResult(
        completed=True,
        repo_path=tmp_path / "repo",
        repo_url="https://github.com/ctkrug/tool",
        site_path=tmp_path / "site",
        site_url="https://apps.charliekrug.com/tool/",
    )

    with pytest.raises(ValueError, match="repository is not ready"):
        publisher.publish(build)

    assert calls == []


def test_resumable_publisher_requires_a_site_build_before_deploying(tmp_path):
    publisher = ResumablePublisher(
        push_repository=lambda path: None,
        deploy_site=lambda path: None,
        verify_url=lambda url: url.startswith("https://github.com/"),
    )
    build = BuildResult(
        completed=True,
        repo_path=tmp_path / "repo",
        repo_url="https://github.com/ctkrug/tool",
        site_path=tmp_path / "missing-site",
        site_url="https://apps.charliekrug.com/tool/",
    )

    with pytest.raises(ValueError, match="site build directory does not exist"):
        publisher.publish(build)


@pytest.mark.parametrize(
    "build",
    [
        BuildResult.pending(),
        BuildResult(completed=True),
    ],
)
def test_resumable_publisher_rejects_incomplete_build_details(build):
    publisher = ResumablePublisher(lambda path: None, lambda path: None, lambda url: True)

    with pytest.raises(ValueError, match="publication details"):
        publisher.publish(build)


def test_command_site_deployer_interpolates_only_the_site_path(tmp_path):
    calls = []
    deploy = CommandSiteDeployer(
        ("deploy-static", "--directory", "{site_path}"),
        run=lambda command: calls.append(command),
    )

    deploy(tmp_path / "site")

    assert calls == [("deploy-static", "--directory", str(tmp_path / "site"))]


def test_production_publish_helpers_use_argument_vectors(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(publish.subprocess, "run", lambda command, check: calls.append(command))

    git_push_repository(tmp_path / "repo")
    CommandSiteDeployer(("deploy-static", "{site_path}"))(tmp_path / "site")

    assert calls == [
        ["git", "-C", str(tmp_path / "repo"), "push", "origin", "HEAD"],
        ("deploy-static", str(tmp_path / "site")),
    ]
    with pytest.raises(ValueError, match="https"):
        verify_public_url("http://example.test")
