from datetime import datetime

import httpx

from app.platforms.base import BasePlatform


class DevToPlatform(BasePlatform):
    """
    Publishes an article update to Dev.to (Forem API v1).
    Posts are public on dev.to by default when published=True.
    """
    name = "Dev.to"

    def missing_credentials(self) -> str | None:
        return self._need(("DEVTO_API_KEY", self.settings.devto_api_key))

    async def publish(self, client: httpx.AsyncClient, message: str):
        title = "Update " + datetime.now().strftime("%Y-%m-%d %H:%M")
        resp = await client.post(
            "https://dev.to/api/articles",
            headers={
                "api-key": self.settings.devto_api_key,
                "Accept": "application/vnd.forem.api-v1+json",
                "Content-Type": "application/json",
            },
            json={
                "article": {
                    "title": title,
                    "body_markdown": message,
                    "published": True,
                }
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("url") or data.get("canonical_url"), True
