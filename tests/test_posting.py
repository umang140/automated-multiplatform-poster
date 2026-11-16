import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.platforms.base import BasePlatform
from app.schemas import SAMPLE_MESSAGE
from app.services.posting_service import PostingService, default_platforms

client = TestClient(app)

REQUIRED_PLATFORMS = [
    "Telegram",
    "Discord",
    "Slack",
    "Mastodon",
    "GitHub Gist",
    "Bluesky",
    "Hugging Face",
    "Dev.to",
    "dpaste",
]


class DummyPlatform(BasePlatform):
    def __init__(self, name: str, fail: bool = False, err: str = "failed"):
        self.name = name
        self.fail = fail
        self.err = err
        self.called = False

    def missing_credentials(self):
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        self.called = True
        if self.fail:
            raise RuntimeError(self.err)
        return "https://example.com/post/123", True


class AuthFailPlatform(BasePlatform):
    name = "AuthTest"

    def missing_credentials(self):
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        req = httpx.Request("POST", "https://example.com/auth")
        resp = httpx.Response(401, request=req)
        raise httpx.HTTPStatusError("Unauthorized", request=req, response=resp)


class TimeoutPlatform(BasePlatform):
    name = "TimeoutTest"

    def missing_credentials(self):
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        raise httpx.TimeoutException("Connection timed out")


@pytest.mark.asyncio
async def test_one_failure_does_not_stop_others():
    platform_a = DummyPlatform("PlatformA")
    platform_b = DummyPlatform("PlatformB", fail=True, err="Authentication failed")
    platform_c = DummyPlatform("PlatformC")

    service = PostingService(platforms=[platform_a, platform_b, platform_c])
    out = await service.post_message(SAMPLE_MESSAGE)

    assert platform_a.called and platform_b.called and platform_c.called
    assert out.success is True
    assert [r.status for r in out.results] == ["success", "failed", "success"]
    assert out.results[1].error == "Authentication failed"
    assert out.results[1].posted_url is None
    assert out.results[0].date and out.results[0].time


@pytest.mark.asyncio
async def test_all_platforms_failed():
    service = PostingService(
        platforms=[
            DummyPlatform("A", fail=True, err="network down"),
            DummyPlatform("B", fail=True, err="auth failure"),
        ]
    )
    out = await service.post_message(SAMPLE_MESSAGE)
    assert out.success is False
    assert all(r.status == "failed" for r in out.results)


@pytest.mark.asyncio
async def test_auth_error_status_mapping():
    service = PostingService(platforms=[AuthFailPlatform(None)])
    out = await service.post_message(SAMPLE_MESSAGE)
    assert out.results[0].status == "failed"
    assert out.results[0].error == "Authentication failed"


@pytest.mark.asyncio
async def test_timeout_error_mapping():
    service = PostingService(platforms=[TimeoutPlatform(None)])
    out = await service.post_message(SAMPLE_MESSAGE)
    assert out.results[0].status == "failed"
    assert out.results[0].error == "Request timed out"


def test_health_check_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "docs" in data


@pytest.mark.asyncio
async def test_all_9_platforms_structured_properly():
    """
    Tests the real default_platforms list without relying on live external networks.
    Mocking dpaste ensures offline safety while remaining platforms report missing keys.
    """
    def mock_handler(request: httpx.Request) -> httpx.Response:
        if "dpaste.com" in str(request.url):
            return httpx.Response(
                201,
                text="https://dpaste.com/MOCK123",
                headers={"Location": "https://dpaste.com/MOCK123"},
            )
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as mock_client:
        service = PostingService(platforms=default_platforms())
        response = await service.post_message(SAMPLE_MESSAGE, client=mock_client)

    names = [r.platform for r in response.results]
    assert len(names) == 9
    for name in REQUIRED_PLATFORMS:
        assert name in names

    # dpaste has no credentials requirement, so with mock transport it succeeds
    dpaste_result = next(r for r in response.results if r.platform == "dpaste")
    assert dpaste_result.status == "success"
    assert dpaste_result.posted_url == "https://dpaste.com/MOCK123"
    assert dpaste_result.public_access is True
    assert dpaste_result.date is not None
    assert dpaste_result.time is not None

    # Remaining 8 platforms cleanly report missing credentials
    for r in response.results:
        if r.platform != "dpaste":
            assert r.status == "failed"
            assert "Missing credentials" in r.error
            assert r.posted_url is None
            assert r.public_access is False
            assert r.date is None
            assert r.time is None
