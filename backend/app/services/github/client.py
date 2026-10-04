from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class GitHubClient:
    """
    GitHub App API client for retrieving repository & pull request metadata.
    """
    def __init__(self, api_url: Optional[str] = None, token: Optional[str] = None):
        self.api_url = api_url or settings.GITHUB_API_URL
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"{settings.APP_NAME}-Integration/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_repository_metadata(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        url = f"{self.api_url}/repos/{owner}/{repo}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"GitHub API returned {resp.status_code} for repo {owner}/{repo}")
        except Exception as e:
            logger.error(f"Failed to query GitHub API for repo {owner}/{repo}: {str(e)}")
        return None

    async def get_pull_request_metadata(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"GitHub API returned {resp.status_code} for PR {owner}/{repo}#{pr_number}")
        except Exception as e:
            logger.error(f"Failed to query GitHub API for PR {owner}/{repo}#{pr_number}: {str(e)}")
        return None


github_client = GitHubClient()
