import httpx

from app.platforms.base import BasePlatform


class TelegramPlatform(BasePlatform):
    name = "Telegram"

    def missing_credentials(self):
        return self._need(
            ("TELEGRAM_BOT_TOKEN", self.settings.telegram_bot_token),
            ("TELEGRAM_CHAT_ID", self.settings.telegram_chat_id),
        )

    async def publish(self, client: httpx.AsyncClient, message: str):
        token = self.settings.telegram_bot_token
        resp = await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": self.settings.telegram_chat_id, "text": message},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "telegram error"))

        result = data.get("result") or {}
        msg_id = result.get("message_id")
        chat = result.get("chat") or {}
        username = (self.settings.telegram_channel_username or chat.get("username") or "").lstrip("@")

        posted_url = None
        if username and msg_id:
            posted_url = f"https://t.me/{username}/{msg_id}"

        return posted_url, bool(username)
