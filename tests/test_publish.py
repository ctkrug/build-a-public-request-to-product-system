from wishwright.publish import check_ready


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
