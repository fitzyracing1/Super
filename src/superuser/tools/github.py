"""Least-privilege GitHub access.

Uses a fine-grained token supplied via config/env. Reads are restricted to an
explicit repo allowlist; writes additionally require ``allow_writes`` to be on
*and* pass the guard's approval gate. The client never falls back to ambient
credentials, so an unconfigured agent simply cannot reach GitHub.
"""

from __future__ import annotations

from typing import Any

import requests

from ..config import GitHubConfig


class GitHubError(Exception):
    pass


class GitHubClient:
    def __init__(self, config: GitHubConfig) -> None:
        self.config = config

    def _headers(self) -> dict[str, str]:
        if not self.config.token:
            raise GitHubError(
                "No GitHub token configured. Set GITHUB_TOKEN to a fine-grained, "
                "least-privilege token scoped to the repositories you allow."
            )
        return {
            "Authorization": f"Bearer {self.config.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _check_repo(self, repo: str) -> None:
        if not self.config.repo_allowed(repo):
            raise GitHubError(
                f"Repository {repo!r} is not in the allowlist. "
                "Add it to GITHUB_ALLOWED_REPOS to permit access."
            )

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.config.api_url}{path}"
        resp = requests.request(method, url, headers=self._headers(), timeout=30, **kwargs)
        if resp.status_code >= 400:
            raise GitHubError(f"GitHub API {resp.status_code}: {resp.text[:500]}")
        if resp.text:
            return resp.json()
        return {}

    def get_repo(self, repo: str) -> dict[str, Any]:
        self._check_repo(repo)
        data = self._request("GET", f"/repos/{repo}")
        return {
            "full_name": data.get("full_name"),
            "private": data.get("private"),
            "default_branch": data.get("default_branch"),
            "open_issues": data.get("open_issues_count"),
            "pushed_at": data.get("pushed_at"),
            "permissions": data.get("permissions"),
        }

    def list_issues(self, repo: str, state: str = "open", limit: int = 20) -> dict[str, Any]:
        self._check_repo(repo)
        items = self._request(
            "GET", f"/repos/{repo}/issues",
            params={"state": state, "per_page": max(1, min(limit, 100))},
        )
        return {
            "repo": repo,
            "issues": [
                {"number": i["number"], "title": i["title"], "state": i["state"],
                 "user": i["user"]["login"], "url": i["html_url"]}
                for i in items if "pull_request" not in i
            ],
        }

    def create_issue_comment(self, repo: str, issue_number: int, body: str) -> dict[str, Any]:
        self._check_repo(repo)
        if not self.config.allow_writes:
            raise GitHubError(
                "GitHub writes are disabled. Set GITHUB_ALLOW_WRITES=true to permit them."
            )
        data = self._request(
            "POST", f"/repos/{repo}/issues/{issue_number}/comments", json={"body": body}
        )
        return {"id": data.get("id"), "url": data.get("html_url")}
