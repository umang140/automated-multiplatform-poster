import httpx

from app.platforms.base import BasePlatform


class DPastePlatform(BasePlatform):
    name = "dpaste"

    def missing_credentials(self):
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        resp = await client.post(
            "https://dpaste.com/api/v2/",
            data={
                "content": message,
                "title": "practical-test-post",
                "expiry_days": "7",
            },
        )
        resp.raise_for_status()
        url = (resp.headers.get("Location") or resp.text or "").strip()
        if not url:
            raise RuntimeError("dpaste did not return a url")
        return url, True
