import httpx

from app.platforms.base import BasePlatform


class DiscordPlatform(BasePlatform):
    """
    Publishes to Discord via Incoming Webhook.
    Appends ?wait=true to the webhook URL so Discord returns the created
    message object containing message ID and channel ID.
    """
    name = "Discord"

    def missing_credentials(self) -> str | None:
        return self._need(("DISCORD_WEBHOOK_URL", self.settings.discord_webhook_url))

    async def publish(self, client: httpx.AsyncClient, message: str):
        # wait=true is required by Discord API to receive message JSON payload in the response
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

        # Discord channels require authentication, so public_access is False
        return posted_url, False
