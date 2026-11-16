import httpx
import pytest

from app.config import Settings
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.devto import DevToPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.dpaste import DPastePlatform
from app.platforms.github_gist import GitHubGistPlatform
from app.platforms.huggingface import HuggingFacePlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.slack import SlackPlatform
from app.platforms.telegram import TelegramPlatform
from app.schemas import SAMPLE_MESSAGE

FILLED = Settings(
    telegram_bot_token="t",
    telegram_chat_id="1",
    telegram_channel_username="demo",
    discord_webhook_url="https://discord.com/api/webhooks/1/abc",
    slack_webhook_url="https://hooks.slack.com/services/x",
    mastodon_instance_url="https://mastodon.social",
    mastodon_access_token="m",
    github_token="g",
    bluesky_handle="user.bsky.social",
    bluesky_app_password="pw",
    hf_token="hf_x",
    hf_repo_id="user/model",
    hf_repo_type="models",
    devto_api_key="dev",
)


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_telegram_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True, "result": {"message_id": 9, "chat": {"username": "demo"}}},
        )

    async with _client(handler) as client:
        url, public = await TelegramPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url == "https://t.me/demo/9"
    assert public is True


@pytest.mark.asyncio
async def test_discord_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "wait=true" in str(request.url)
        return httpx.Response(
            200, json={"id": "2", "channel_id": "1", "guild_id": "9"}
        )

    async with _client(handler) as client:
        url, public = await DiscordPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url.endswith("/9/1/2")
    assert public is False


@pytest.mark.asyncio
async def test_slack_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok")

    async with _client(handler) as client:
        url, public = await SlackPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url is None
    assert public is False


@pytest.mark.asyncio
async def test_mastodon_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"url": "https://mastodon.social/@u/1", "visibility": "public"},
        )

    async with _client(handler) as client:
        url, public = await MastodonPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url == "https://mastodon.social/@u/1"
    assert public is True


@pytest.mark.asyncio
async def test_gist_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"html_url": "https://gist.github.com/abc"})

    async with _client(handler) as client:
        url, public = await GitHubGistPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url == "https://gist.github.com/abc"
    assert public is True


@pytest.mark.asyncio
async def test_bluesky_ok():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if "createSession" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "accessJwt": "jwt",
                    "did": "did:plc:1",
                    "handle": "user.bsky.social",
                },
            )
        return httpx.Response(
            200, json={"uri": "at://did:plc:1/app.bsky.feed.post/abc123"}
        )

    async with _client(handler) as client:
        url, public = await BlueskyPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert calls["n"] == 2
    assert url == "https://bsky.app/profile/user.bsky.social/post/abc123"
    assert public is True


@pytest.mark.asyncio
async def test_huggingface_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/models/user/model/discussions" in str(request.url)
        return httpx.Response(200, json={"num": 4, "url": None})

    async with _client(handler) as client:
        url, public = await HuggingFacePlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url == "https://huggingface.co/user/model/discussions/4"
    assert public is True


@pytest.mark.asyncio
async def test_devto_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"url": "https://dev.to/me/post-1"})

    async with _client(handler) as client:
        url, public = await DevToPlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url == "https://dev.to/me/post-1"
    assert public is True


@pytest.mark.asyncio
async def test_dpaste_ok():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            201,
            text="https://dpaste.com/ABC",
            headers={"Location": "https://dpaste.com/ABC"},
        )

    async with _client(handler) as client:
        url, public = await DPastePlatform(FILLED).publish(client, SAMPLE_MESSAGE)
    assert url == "https://dpaste.com/ABC"
    assert public is True


@pytest.mark.asyncio
async def test_missing_keys_fail_without_http():
    p = TelegramPlatform(Settings())
    result = await p.post(httpx.AsyncClient(), SAMPLE_MESSAGE)
    assert result.status == "failed"
    assert "TELEGRAM_BOT_TOKEN" in result.error
