import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.platforms.base import BasePlatform
from app.schemas import SAMPLE_MESSAGE
from app.services.posting_service import PostingService

client = TestClient(app)

REQUIRED = [
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
    def __init__(self, name, fail=False, err="failed", delay_error=None):
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
        return "https://example.com/p", True


class AuthFailPlatform(BasePlatform):
    name = "AuthTest"

    def missing_credentials(self):
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        req = httpx.Request("POST", "https://example.com")
        resp = httpx.Response(401, request=req)
        raise httpx.HTTPStatusError("auth", request=req, response=resp)


class TimeoutPlatform(BasePlatform):
    name = "Slow"

    def missing_credentials(self):
        return None

    async def publish(self, client: httpx.AsyncClient, message: str):
        raise httpx.TimeoutException("timeout")


async def test_one_fail_does_not_stop_others():
    ok = DummyPlatform("A")
    bad = DummyPlatform("B", fail=True, err="Authentication failed")
    later = DummyPlatform("C")
    out = await PostingService(platforms=[ok, bad, later]).post_message(SAMPLE_MESSAGE)

    assert ok.called and bad.called and later.called
    assert out.success is True
    assert [r.status for r in out.results] == ["success", "failed", "success"]
    assert out.results[1].error == "Authentication failed"
    assert out.results[1].posted_url is None
    assert out.results[0].date and out.results[0].time


async def test_all_failed():
    out = await PostingService(
        platforms=[
            DummyPlatform("A", fail=True, err="down"),
            DummyPlatform("B", fail=True, err="down"),
        ]
    ).post_message(SAMPLE_MESSAGE)
    assert out.success is False


async def test_auth_error_mapped():
    out = await PostingService(platforms=[AuthFailPlatform(None)]).post_message(
        SAMPLE_MESSAGE
    )
    assert out.results[0].status == "failed"
    assert out.results[0].error == "Authentication failed"


async def test_timeout_mapped():
    out = await PostingService(platforms=[TimeoutPlatform(None)]).post_message(
        SAMPLE_MESSAGE
    )
    assert out.results[0].error == "Request timed out"


def test_home():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_posting_returns_all_platforms_and_fields():
    r = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert r.status_code == 200
    data = r.json()
    names = [row["platform"] for row in data["results"]]
    assert len(names) >= 5
    for name in REQUIRED:
        assert name in names
    for row in data["results"]:
        for key in [
            "platform",
            "status",
            "posted_url",
            "public_access",
            "date",
            "time",
            "error",
        ]:
            assert key in row
        assert row["status"] in ("success", "failed")
        if row["status"] == "failed":
            assert row["error"]
            assert row["posted_url"] is None
        if row["status"] == "success":
            assert row["error"] is None
            assert row["date"]
            assert row["time"]
