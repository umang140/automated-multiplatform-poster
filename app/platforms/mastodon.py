import httpx

from app.platforms.base import BasePlatform


class MastodonPlatform(BasePlatform):
    name = "Mastodon"

    def missing_credentials(self):
        return self._need(
            ("MASTODON_INSTANCE_URL", self.settings.mastodon_instance_url),
            ("MASTODON_ACCESS_TOKEN", self.settings.mastodon_access_token),
        )

    async def publish(self, client: httpx.AsyncClient, message: str):
        base = self.settings.mastodon_instance_url.rstrip("/")
        resp = await client.post(
            f"{base}/api/v1/statuses",
            headers={"Authorization": f"Bearer {self.settings.mastodon_access_token}"},
            json={"status": message, "visibility": "public"},
        )
        resp.raise_for_status()
        data = resp.json()
        url = data.get("url") or data.get("uri")
        public = data.get("visibility", "public") == "public"
        return url, public
