import httpx

from app.platforms.base import BasePlatform


class DPastePlatform(BasePlatform):
    """
    Publishes to dpaste.com via REST API v2.
    Requires no API keys, guaranteeing that any local execution
    produces at least one verifiable, live public URL out of the box.
    """
    name = "dpaste"

    def missing_credentials(self) -> str | None:
        # Zero-credential platform: always eligible to execute
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        resp = await client.post(
            "https://dpaste.com/api/v2/",
            data={
                "content": message,
                "title": "Automated Multi-Platform Post",
                "expiry_days": "7",
            },
        )
        resp.raise_for_status()

        # dpaste returns the created URL in Location header and response body
        url = (resp.headers.get("Location") or resp.text or "").strip()
        if not url:
            raise RuntimeError("dpaste did not return a valid URL")
        return url, True
