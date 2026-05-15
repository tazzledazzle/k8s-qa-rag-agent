"""Repository URL allowlist for indexer (SEC-03)."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _parse_csv(name: str) -> list[str]:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _parse_path_prefixes() -> list[str]:
    raw = (os.environ.get("INDEXER_ALLOWED_FILE_PATH_PREFIXES") or "/fixtures").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["/fixtures"]


def normalize_github_https(repo_url: str) -> str | None:
    """Return canonical https://github.com/owner/repo (lowercase, no .git) or None."""
    u = repo_url.strip()
    if not u:
        return None
    u = re.sub(r"/+$", "", u)
    u = re.sub(r"\.git$", "", u, flags=re.IGNORECASE)
    m = re.match(r"^git@github\.com:(.+)$", u, flags=re.IGNORECASE)
    if m:
        path = m.group(1).strip()
        u = f"https://github.com/{path}"
    elif "/" in u and not u.startswith("http") and "." not in u.split("/")[0]:
        u = f"https://github.com/{u}"
    lowered = u.lower()
    prefix = "https://github.com/"
    if not lowered.startswith(prefix):
        return None
    tail = lowered.removeprefix(prefix).strip("/")
    if "/" not in tail:
        return None
    owner, repo = tail.split("/", 1)
    owner = owner.strip().lower()
    repo = repo.strip().lower().removesuffix(".git")
    if not owner or not repo:
        return None
    return f"https://github.com/{owner}/{repo}"


def _github_owner(repo_url: str) -> str | None:
    norm = normalize_github_https(repo_url)
    if not norm:
        return None
    rest = norm.removeprefix("https://github.com/")
    return rest.split("/", 1)[0].lower()


def is_restrictive_mode() -> bool:
    return bool(
        _parse_csv("INDEXER_ALLOWED_GITHUB_ORGS") or _parse_csv("INDEXER_ALLOWED_REPO_URLS")
    )


def assert_repo_url_allowed(repo_url: str) -> None:
    """
    Raise ValueError with a short message if repo_url is not allowed.

    Used by HTTP /index and batch_index before any clone.
    """
    if not is_repo_url_allowed(repo_url):
        raise ValueError(f"Repository URL not allowed by policy: {repo_url!r}")


def is_repo_url_allowed(repo_url: str) -> bool:
    """Return True if indexing this repo_url is permitted."""
    raw = repo_url.strip()
    if not raw:
        return False

    if raw.lower().startswith("file:"):
        if os.environ.get("INDEXER_ALLOW_FILE_REMOTES", "").strip().lower() not in (
            "1",
            "true",
            "yes",
        ):
            logger.warning("file:// repo rejected: INDEXER_ALLOW_FILE_REMOTES not enabled")
            return False
        parsed = urlparse(raw)
        path = parsed.path or ""
        if not path:
            return False
        prefixes = _parse_path_prefixes()
        ok = any(path.startswith(p) for p in prefixes)
        if not ok:
            logger.warning("file:// path %s not under allowed prefixes %s", path, prefixes)
        return ok

    norm = normalize_github_https(raw)
    if norm is None:
        logger.warning("Non-GitHub HTTPS URL rejected: %s", raw)
        return False

    if not is_restrictive_mode():
        return True

    orgs = {o.lower() for o in _parse_csv("INDEXER_ALLOWED_GITHUB_ORGS")}
    urls = set()
    for entry in _parse_csv("INDEXER_ALLOWED_REPO_URLS"):
        n = normalize_github_https(entry)
        if n:
            urls.add(n)

    org_ok = not orgs or (_github_owner(raw) in orgs)
    url_ok = not urls or (norm in urls)
    return org_ok and url_ok
