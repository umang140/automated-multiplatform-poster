from fastapi.testclient import TestClient

from app.main import app, get_posting_service
from app.schemas import PlatformResult, PostingResponse, SAMPLE_MESSAGE

# Mock the posting service so validation tests evaluate the endpoint quickly and offline
class DummyFastPostingService:
    async def post_message(self, message: str, client=None) -> PostingResponse:
        return PostingResponse(
            success=True,
            results=[
                PlatformResult(
                    platform="TestPlatform",
                    status="success",
                    posted_url="https://example.com/mock",
                    public_access=True,
                    date="2026-11-16",
                    time="12:00:00",
                    error=None,
                )
            ],
        )

app.dependency_overrides[get_posting_service] = lambda: DummyFastPostingService()
client = TestClient(app)


def test_valid_message_is_accepted():
    r = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["results"]) == 1
    assert body["results"][0]["status"] == "success"


def test_exactly_200_chars_accepted():
    link = "https://example.com"
    padding = "a" * (200 - len(link) - 1)
    msg = padding + " " + link
    assert len(msg) == 200
    r = client.post("/posting", json={"message": msg})
    assert r.status_code == 200


def test_201_chars_rejected():
    link = "https://example.com"
    msg = "a" * (201 - len(link)) + link
    assert len(msg) == 201
    r = client.post("/posting", json={"message": msg})
    assert r.status_code == 400
    assert r.json()["success"] is False
    assert "200" in r.json()["error"]
    assert r.json()["results"] == []


def test_no_cta_link_rejected():
    r = client.post("/posting", json={"message": "check our product launch now"})
    assert r.status_code == 400
    assert "CTA link" in r.json()["error"]


def test_multiple_cta_links_rejected():
    r = client.post(
        "/posting",
        json={"message": "visit https://first.com and also https://second.com"},
    )
    assert r.status_code == 400
    assert "CTA link" in r.json()["error"]


def test_invalid_url_no_tld_rejected():
    r = client.post("/posting", json={"message": "visit http://internal_server"})
    assert r.status_code == 400
    assert "valid URL" in r.json()["error"]


def test_invalid_url_leading_dot_rejected():
    r = client.post("/posting", json={"message": "visit https://.com/test"})
    assert r.status_code == 400
    assert "valid URL" in r.json()["error"]


def test_ftp_protocol_rejected():
    r = client.post("/posting", json={"message": "download at ftp://ftp.example.com/file.zip"})
    assert r.status_code == 400


def test_empty_message_rejected():
    r = client.post("/posting", json={"message": ""})
    assert r.status_code == 400
    assert "empty" in r.json()["error"].lower() or "required" in r.json()["error"].lower()


def test_whitespace_message_rejected():
    r = client.post("/posting", json={"message": "     "})
    assert r.status_code == 400


def test_missing_message_field():
    r = client.post("/posting", json={})
    assert r.status_code == 400
    assert "message" in r.json()["error"].lower()


def test_not_json_body():
    r = client.post("/posting", content="raw text payload", headers={"Content-Type": "application/json"})
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_url_with_query_params_and_path_accepted():
    r = client.post(
        "/posting",
        json={"message": "New release available at https://github.com/org/repo?tag=v1.0.0"},
    )
    assert r.status_code == 200
