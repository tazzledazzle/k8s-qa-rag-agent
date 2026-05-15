"""GitClient file:// remote path behavior."""

from services.indexer.git_client import GitClient


def test_file_remote_cache_path_is_stable() -> None:
    c = GitClient(cache_dir="/tmp/k8s-qa-rag-agent-test-cache")
    p1 = c._get_local_path("file:///fixtures/sample-repo")
    p2 = c._get_local_path("file:///fixtures/sample-repo")
    assert p1 == p2
    assert p1.parts[-2] == "file"
