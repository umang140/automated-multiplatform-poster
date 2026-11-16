from abc import ABC, abstractmethod
import logging
from typing import Tuple

import httpx

from app.schemas import PlatformResult, now_parts

logger = logging.getLogger("platform")


class BasePlatform(ABC):
    """
    Abstract base adapter for third-party platform integrations.
    Handles credential verification, execution safety, and standardized error mapping.
    """
    name: str = "unknown"

    def __init__(self, settings):
        self.settings = settings

    @abstractmethod
    def missing_credentials(self) -> str | None:
        """Returns missing configuration description, or None if credentials are present."""
        pass

    @abstractmethod
    async def publish(self, client: httpx.AsyncClient, message: str) -> Tuple[str | None, bool]:
        """
        Executes platform-specific API call to post the message.
        Returns a tuple of (posted_url, is_public_access).
        """
        pass

    async def post(self, client: httpx.AsyncClient, message: str) -> PlatformResult:
        """
        Wraps platform publishing with credential checking and error handling,
        ensuring an individual failure never crashes the application.
        """
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
            # Test spec specifically looks for 'Authentication failed' on 401/403
            if code in (401, 403):
                return self._fail("Authentication failed")
            response_snippet = e.response.text[:200] if e.response is not None else str(e)
            return self._fail(f"HTTP {code}: {response_snippet}")
        except httpx.TimeoutException:
            return self._fail("Request timed out")
        except httpx.HTTPError as e:
            return self._fail(f"Network error: {e}")
        except Exception as e:
            logger.exception("Unexpected error in platform %s", self.name)
            return self._fail(str(e))

    def _fail(self, error: str) -> PlatformResult:
        """Constructs standardized failed result matching the practical test specification."""
        return PlatformResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error=error,
        )

    def _need(self, *items: Tuple[str, str | None]) -> str | None:
        """Helper to collect and format missing environment variable names."""
        missing = [name for name, value in items if not str(value or "").strip()]
        if missing:
            return "Missing credentials: " + ", ".join(missing)
        return None
