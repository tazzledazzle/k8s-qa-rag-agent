"""Tests for services.indexer.repo_allowlist (SEC-03)."""

from __future__ import annotations

import pytest

from services.indexer import repo_allowlist


@pytest.fixture(autouse=True)
def clear_allowlist_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "INDEXER_ALLOWED_GITHUB_ORGS",
        "INDEXER_ALLOWED_REPO_URLS",
        "INDEXER_ALLOW_FILE_REMOTES",
        "INDEXER_ALLOWED_FILE_PATH_PREFIXES",
    ):
        monkeypatch.delenv(name, raising=False)
    yield


def test_normalize_https_strip_git_suffix() -> None:
    assert (
        repo_allowlist.normalize_github_https("https://github.com/OctoCat/Hello-World.git")
        == "https://github.com/octocat/hello-world"
    )


def test_normalize_git_at_case_insensitive() -> None:
    assert (
        repo_allowlist.normalize_github_https("git@GitHub.com:acme/widget.git")
        == "https://github.com/acme/widget"
    )


def test_permissive_github_https() -> None:
    assert repo_allowlist.is_repo_url_allowed("https://github.com/octocat/Hello-World.git")


def test_restrictive_org_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOWED_GITHUB_ORGS", "octocat,other")
    assert repo_allowlist.is_repo_url_allowed("https://github.com/octocat/Hello-World")


def test_restrictive_org_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOWED_GITHUB_ORGS", "kubernetes")
    assert not repo_allowlist.is_repo_url_allowed("https://github.com/octocat/Hello-World")


def test_restrictive_url_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOWED_REPO_URLS", "https://github.com/foo/bar")
    assert repo_allowlist.is_repo_url_allowed("https://github.com/foo/bar.git")


def test_restrictive_both_requires_and(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOWED_GITHUB_ORGS", "octocat")
    monkeypatch.setenv(
        "INDEXER_ALLOWED_REPO_URLS",
        "https://github.com/kubernetes/kubernetes",
    )
    assert not repo_allowlist.is_repo_url_allowed("https://github.com/octocat/Hello-World")


def test_file_denied_without_flag() -> None:
    assert not repo_allowlist.is_repo_url_allowed("file:///fixtures/sample-repo")


def test_file_allowed_with_flag_and_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOW_FILE_REMOTES", "true")
    monkeypatch.setenv("INDEXER_ALLOWED_FILE_PATH_PREFIXES", "/fixtures")
    assert repo_allowlist.is_repo_url_allowed("file:///fixtures/sample-repo")


def test_file_wrong_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOW_FILE_REMOTES", "true")
    monkeypatch.setenv("INDEXER_ALLOWED_FILE_PATH_PREFIXES", "/fixtures")
    assert not repo_allowlist.is_repo_url_allowed("file:///tmp/leak")


def test_non_github_denied() -> None:
    assert not repo_allowlist.is_repo_url_allowed("https://gitlab.com/a/b.git")


def test_assert_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_ALLOWED_GITHUB_ORGS", "kubernetes")
    with pytest.raises(ValueError, match="not allowed"):
        repo_allowlist.assert_repo_url_allowed("https://github.com/octocat/Hello-World")
