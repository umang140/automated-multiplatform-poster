import httpx

from app.platforms.base import BasePlatform


class DiscordPlatform(BasePlatform):
    name = "Discord"

    def missing_credentials(self):
        return self._need(("DISCORD_WEBHOOK_URL", self.settings.discord_webhook_url))

    async def publish(self, client: httpx.AsyncClient, message: str):
        # wait=true so we get the created message back
        url = self.settings.discord_webhook_url.rstrip("/") + "?wait=true"
        resp = await client.post(url, json={"content": message})
        resp.raise_for_status()

        posted_url = None
        if resp.content:
            data = resp.json()
            guild_id = data.get("guild_id") or "@me"
            channel_id = data.get("channel_id")
            msg_id = data.get("id")
            if channel_id and msg_id:
                posted_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"

        # discord servers are not really public websites
        return posted_url, False
