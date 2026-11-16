from datetime import datetime

import httpx

from app.platforms.base import BasePlatform


class GitHubGistPlatform(BasePlatform):
    """
    Publishes the message as a public GitHub Gist via GitHub REST API.
    Returns the permanent public URL (html_url).
    """
    name = "GitHub Gist"

    def missing_credentials(self) -> str | None:
        return self._need(("GITHUB_TOKEN", self.settings.github_token))

    async def publish(self, client: httpx.AsyncClient, message: str):
        filename = datetime.now().strftime("post-%Y%m%d-%H%M%S.md")
        resp = await client.post(
            "https://api.github.com/gists",
            headers={
                "Authorization": f"Bearer {self.settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "description": "Automated multi-platform post",
                "public": True,
                "files": {filename: {"content": message}},
            },
        )
        resp.raise_for_status()
        return resp.json().get("html_url"), True
