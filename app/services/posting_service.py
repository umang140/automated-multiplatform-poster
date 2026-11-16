import asyncio
import json
from pathlib import Path

import httpx
import truststore

truststore.inject_into_ssl()

from app.config import get_settings
from app.platforms import (
    BlueskyPlatform,
    DevToPlatform,
    DiscordPlatform,
    DPastePlatform,
    GitHubGistPlatform,
    HuggingFacePlatform,
    MastodonPlatform,
    SlackPlatform,
    TelegramPlatform,
)
from app.schemas import PlatformResult, PostingResponse

LOG_PATH = Path("logs/posting.log")


def default_platforms(settings=None):
    settings = settings or get_settings()
    return [
        TelegramPlatform(settings),
        DiscordPlatform(settings),
        SlackPlatform(settings),
        MastodonPlatform(settings),
        GitHubGistPlatform(settings),
        BlueskyPlatform(settings),
        HuggingFacePlatform(settings),
        DevToPlatform(settings),
        DPastePlatform(settings),
    ]


class PostingService:
    def __init__(self, platforms=None):
        self.platforms = platforms or default_platforms()

    async def post_message(
        self, message: str, client: httpx.AsyncClient | None = None
    ) -> PostingResponse:
        timeout = httpx.Timeout(20.0, connect=10.0)
        headers = {"User-Agent": "practical-test-poster/1.0"}

        if client is not None:
            raw = await asyncio.gather(
                *[p.post(client, message) for p in self.platforms],
                return_exceptions=True,
            )
        else:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True, headers=headers
            ) as session:
                raw = await asyncio.gather(
                    *[p.post(session, message) for p in self.platforms],
                    return_exceptions=True,
                )

        results = []
        for platform, item in zip(self.platforms, raw):
            if isinstance(item, Exception):
                results.append(platform._fail(str(item)))
            else:
                results.append(item)

        any_ok = any(item.status == "success" for item in results)
        response = PostingResponse(success=any_ok, results=results)
        _write_log(response)
        return response


def _write_log(response: PostingResponse):
    try:
        LOG_PATH.parent.mkdir(exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(response.model_dump()) + "\n")
    except OSError:
        pass
