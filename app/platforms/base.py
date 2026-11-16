from abc import ABC, abstractmethod

import httpx

from app.schemas import PlatformResult, now_parts


class BasePlatform(ABC):
    name = "unknown"

    def __init__(self, settings):
        self.settings = settings

    @abstractmethod
    def missing_credentials(self):
        pass

    @abstractmethod
    async def publish(self, client: httpx.AsyncClient, message: str):
        pass

    async def post(self, client: httpx.AsyncClient, message: str) -> PlatformResult:
        missing = self.missing_credentials()
        if missing:
            return self._fail(missing)

        try:
            posted_url, public_access = await self.publish(client, message)
            date, time = now_parts()
            return PlatformResult(
                platform=self.name,
                status="success",
                posted_url=posted_url,
                public_access=public_access,
                date=date,
                time=time,
                error=None,
            )
        except httpx.HTTPStatusError as e:
            code = e.response.status_code if e.response is not None else 0
            if code in (401, 403):
                return self._fail("Authentication failed")
            text = e.response.text[:300] if e.response is not None else str(e)
            return self._fail(f"HTTP {code}: {text}")
        except httpx.TimeoutException:
            return self._fail("Request timed out")
        except httpx.HTTPError as e:
            return self._fail(f"Network error: {e}")
        except Exception as e:
            return self._fail(str(e))

    def _fail(self, error: str) -> PlatformResult:
        return PlatformResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error=error,
        )

    def _need(self, *items):
        missing = [name for name, value in items if not str(value or "").strip()]
        if missing:
            return "Missing credentials: " + ", ".join(missing)
        return None
