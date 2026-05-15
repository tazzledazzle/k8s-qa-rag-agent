"""Git repository management for indexing."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class GitClientError(Exception):
    """Base exception for Git operations."""

    pass


class RepositoryNotFoundError(GitClientError):
    """Raised when repository cannot be cloned."""

    pass


class BranchNotFoundError(GitClientError):
    """Raised when specified branch does not exist."""

    pass


class GitClient:
    """Manages Git repository operations for indexing."""

    def __init__(self, cache_dir: str = "/app/repos"):
        """
        Initialize Git client.

        Args:
            cache_dir: Directory to cache cloned repositories.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.github_token = os.getenv("GITHUB_TOKEN")

    def _is_file_remote(self, repo_url: str) -> bool:
        return repo_url.strip().lower().startswith("file:")

    def _normalize_file_clone_url(self, repo_url: str) -> str:
        """Return a file:/// URI suitable for GitPython clone_from (absolute path)."""
        parsed = urlparse(repo_url.strip())
        if parsed.scheme != "file":
            raise ValueError(f"Expected file: scheme, got: {repo_url!r}")
        path = Path(parsed.path)
        if not path.is_absolute():
            raise ValueError(f"file:// repository paths must be absolute: {repo_url!r}")
        resolved = path.resolve()
        if not resolved.exists():
            raise RepositoryNotFoundError(f"Local repository path does not exist: {resolved}")
        if not (resolved / ".git").exists():
            raise RepositoryNotFoundError(
                f"Path is not a git repository (missing .git): {resolved}. "
                "Run tests/fixtures/sample-repo/bootstrap.sh on the host first."
            )
        return resolved.as_uri()

    def _get_authenticated_url(self, repo_url: str) -> str:
        """
        Convert repo URL to authenticated HTTPS format using GitHub token.

        Args:
            repo_url: Repository URL (supports https://, git@, shorthand, or file://).

        Returns:
            Authenticated HTTPS URL with embedded token, or file:/// URI unchanged.

        Raises:
            ValueError: If repo URL format is invalid.
        """
        if self._is_file_remote(repo_url):
            return self._normalize_file_clone_url(repo_url)

        # Normalize different GitHub URL formats
        if repo_url.startswith("git@github.com:"):
            # Convert git@github.com:owner/repo.git to https format
            repo_path = repo_url.replace("git@github.com:", "").rstrip(".git")
            repo_url = f"https://github.com/{repo_path}"
        elif repo_url.startswith("https://github.com/"):
            # Already in https format
            pass
        elif "/" in repo_url and "." not in repo_url:
            # Shorthand: owner/repo
            repo_url = f"https://github.com/{repo_url}"
        else:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

        # Add token if available
        if self.github_token:
            repo_url = repo_url.replace(
                "https://github.com/", f"https://x-access-token:{self.github_token}@github.com/"
            )

        return repo_url

    def _get_local_path(self, repo_url: str) -> Path:
        """
        Derive local cache path from repository URL.

        Args:
            repo_url: Repository URL.

        Returns:
            Path to local repository cache.
        """
        if self._is_file_remote(repo_url):
            digest = hashlib.sha256(repo_url.strip().encode("utf-8")).hexdigest()[:24]
            return self.cache_dir / "file" / digest

        # Extract owner/repo from URL
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        repo = repo.rstrip(".git")
        return self.cache_dir / owner / repo

    def clone_or_update(self, repo_url: str, branch: str = "main", force: bool = False) -> Path:
        """
        Clone a repository or update it if already exists.

        Args:
            repo_url: GitHub HTTPS/git@/shorthand URL, or ``file:///absolute/path`` to a local git repo.
            branch: Git branch to clone/checkout.
            force: If True, remove and re-clone existing repository.

        Returns:
            Path to local repository.

        Raises:
            RepositoryNotFoundError: If repository cannot be cloned.
            BranchNotFoundError: If specified branch does not exist.
            GitClientError: If git operations fail.
        """
        if self._is_file_remote(repo_url):
            return self._clone_or_update_file(repo_url, branch, force)

        local_path = self._get_local_path(repo_url)
        auth_url = self._get_authenticated_url(repo_url)

        try:
            if local_path.exists() and force:
                logger.info(f"Removing existing repository at {local_path}")
                shutil.rmtree(local_path)

            if not local_path.exists():
                # Clone new repository
                logger.info(f"Cloning {repo_url} to {local_path}")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                repo = Repo.clone_from(
                    auth_url, local_path, branch=branch, depth=1  # Shallow clone to save bandwidth
                )
                logger.info(f"Successfully cloned {repo_url}")
            else:
                # Update existing repository
                logger.info(f"Updating repository at {local_path}")
                repo = Repo(local_path)

                # Verify branch exists
                if branch not in repo.heads:
                    raise BranchNotFoundError(f"Branch '{branch}' not found in {repo_url}")

                # Checkout branch if not current
                if repo.active_branch.name != branch:
                    repo.heads[branch].checkout()

                # Fetch and merge latest changes
                origin = repo.remote("origin")
                origin.fetch()
                repo.heads[branch].set_tracking_branch(origin.heads[branch])
                repo.heads[branch].commit = origin.heads[branch].commit

                logger.info(f"Successfully updated {repo_url} on branch {branch}")

            return local_path

        except GitCommandError as e:
            # Detect 404/auth errors indicating repository not found
            if "Repository not found" in str(e) or "404" in str(e):
                raise RepositoryNotFoundError(
                    f"Repository not found: {repo_url}. Verify URL and permissions."
                ) from e
            elif "not found in upstream origin" in str(e):
                raise BranchNotFoundError(f"Branch '{branch}' not found in {repo_url}") from e
            else:
                raise GitClientError(f"Git operation failed: {str(e)}") from e
        except Exception as e:
            raise GitClientError(f"Unexpected error during git operation: {str(e)}") from e

    def _clone_or_update_file(self, repo_url: str, branch: str, force: bool) -> Path:
        """Clone from a local file:// git repo into the cache (read-only sources supported)."""
        auth_url = self._get_authenticated_url(repo_url)
        local_path = self._get_local_path(repo_url)
        try:
            if local_path.exists() and force:
                logger.info("Removing existing file-remote cache at %s", local_path)
                shutil.rmtree(local_path)

            if not local_path.exists():
                logger.info("Cloning file remote %s -> %s", repo_url, local_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                Repo.clone_from(auth_url, local_path, branch=branch, depth=1)
                logger.info("Successfully cloned file remote")
                return local_path

            # Cached clone: refresh from read-only file remote (simplest — re-clone)
            logger.info("Refreshing file-remote cache at %s", local_path)
            shutil.rmtree(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            Repo.clone_from(auth_url, local_path, branch=branch, depth=1)
            logger.info("Successfully re-cloned file remote")
            return local_path

        except GitCommandError as e:
            if "not found in upstream origin" in str(e):
                raise BranchNotFoundError(f"Branch '{branch}' not found in {repo_url}") from e
            raise GitClientError(f"Git operation failed: {str(e)}") from e
        except Exception as e:
            raise GitClientError(f"Unexpected error during file-remote clone: {str(e)}") from e

    def get_files(
        self,
        repo_path: Path,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> list[Path]:
        """
        Get list of files in repository matching patterns.

        Args:
            repo_path: Path to local repository.
            include_patterns: Glob patterns for files to include.
            exclude_patterns: Glob patterns for files to exclude.

        Returns:
            List of file paths in repository.
        """
        if not repo_path.exists():
            raise GitClientError(f"Repository path does not exist: {repo_path}")

        files = []

        # Default patterns: include all code files, exclude common non-code directories
        default_exclude = {
            ".git",
            ".github",
            ".venv",
            "venv",
            "node_modules",
            ".env*",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            "*.egg-info",
            ".vscode",
            ".idea",
            "coverage*",
            ".tox",
        }

        for file_path in repo_path.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip hidden files and git internals
            if any(part.startswith(".") for part in file_path.relative_to(repo_path).parts):
                # Allow .github*, .gitignore, but not .git/
                if not any(
                    part in {".github", ".gitignore"}
                    for part in file_path.relative_to(repo_path).parts
                ):
                    continue

            # Apply exclusion patterns
            relative_path = file_path.relative_to(repo_path)
            skip = False
            for pattern in exclude_patterns or []:
                if relative_path.match(pattern):
                    skip = True
                    break
            if skip:
                continue

            # Check default exclusions
            if any(relative_path.match(pattern) for pattern in default_exclude):
                continue

            # Apply inclusion patterns if specified
            if include_patterns:
                matched = any(relative_path.match(pattern) for pattern in include_patterns)
                if not matched:
                    continue

            files.append(file_path)

        return sorted(files)

    def get_file_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to file.

        Returns:
            Language name (e.g., 'python', 'javascript', 'markdown').
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".kt": "kotlin",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".m": "objective-c",
            ".scala": "scala",
            ".sh": "shell",
            ".bash": "shell",
            ".md": "markdown",
            ".rst": "rst",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
        }

        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, "unknown")

    def cleanup(self, repo_url: str) -> None:
        """
        Remove cached repository.

        Args:
            repo_url: Repository URL to clean up.
        """
        local_path = self._get_local_path(repo_url)
        if local_path.exists():
            logger.info(f"Removing cached repository: {local_path}")
            shutil.rmtree(local_path)
