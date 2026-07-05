from typing import Any, Dict, List, Optional

import requests


class GitHubClientError(Exception):
    pass


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, timeout: int = 20) -> None:
        self.token = token
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GISA-local-mvp",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def _get(self, path: str) -> Any:
        url = f"{self.BASE_URL}{path}"

        try:
            response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as exc:
            raise GitHubClientError(f"GitHub request failed: {exc}") from exc

        if response.status_code == 404:
            raise GitHubClientError("GitHub resource not found. Check the repo name and issue number.")

        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubClientError(
                "GitHub API rate limit reached. Add GITHUB_TOKEN to your local .env file or wait for reset."
            )

        if response.status_code >= 400:
            raise GitHubClientError(
                f"GitHub API error {response.status_code}: {response.text[:500]}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise GitHubClientError("GitHub returned invalid JSON.") from exc

    def fetch_issue(self, repo: str, issue_number: int, max_comments: int = 20) -> Dict[str, Any]:
        if "/" not in repo or repo.count("/") != 1:
            raise GitHubClientError("Repo must use the format owner/repo.")

        if max_comments < 0:
            raise GitHubClientError("max_comments must be 0 or greater.")

        issue = self._get(f"/repos/{repo}/issues/{issue_number}")

        if "pull_request" in issue:
            raise GitHubClientError("This GitHub item is a pull request, not a plain issue.")

        comments: List[Dict[str, Any]] = []
        if max_comments > 0:
            comments_to_fetch = min(max_comments, 100)
            comments = self._get(f"/repos/{repo}/issues/{issue_number}/comments?per_page={comments_to_fetch}")

        return {
            "repo": repo,
            "number": issue.get("number"),
            "title": issue.get("title") or "",
            "body": issue.get("body") or "",
            "state": issue.get("state") or "",
            "author": (issue.get("user") or {}).get("login") or "",
            "labels": [label.get("name", "") for label in issue.get("labels", [])],
            "created_at": issue.get("created_at") or "",
            "updated_at": issue.get("updated_at") or "",
            "closed_at": issue.get("closed_at") or "",
            "total_comments": issue.get("comments") or 0,
            "fetched_comments": [
                {
                    "author": (comment.get("user") or {}).get("login") or "",
                    "body": comment.get("body") or "",
                    "created_at": comment.get("created_at") or "",
                    "updated_at": comment.get("updated_at") or "",
                }
                for comment in comments
            ],
            "token_used": bool(self.token),
        }
