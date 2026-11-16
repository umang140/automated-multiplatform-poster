import httpx

from app.platforms.base import BasePlatform


class SlackPlatform(BasePlatform):
    """
    Publishes to Slack using Incoming Webhooks.
    Slack returns plain text 'ok' on successful webhook delivery.
    """
    name = "Slack"

    def missing_credentials(self) -> str | None:
        return self._need(("SLACK_WEBHOOK_URL", self.settings.slack_webhook_url))

    async def publish(self, client: httpx.AsyncClient, message: str):
        resp = await client.post(
            self.settings.slack_webhook_url,
            json={"text": message},
        )
        resp.raise_for_status()

        # Slack incoming webhooks respond with body text "ok"
        body = resp.text.strip()
        if body.lower() not in ("ok", ""):
            try:
                data = resp.json()
            except ValueError:
                data = {}
            if isinstance(data, dict) and data.get("ok") is False:
                raise RuntimeError(data.get("error", "Slack webhook delivery failed"))

        # Slack workspace channels are private, no direct public link
        return None, False
