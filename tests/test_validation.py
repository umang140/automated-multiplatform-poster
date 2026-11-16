from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SAMPLE_MESSAGE

client = TestClient(app)


def test_valid_message_is_accepted():
    r = client.post("/posting", json={"message": SAMPLE_MESSAGE})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert "success" in body


def test_exactly_200_chars_ok():
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


def test_no_cta_link():
    r = client.post("/posting", json={"message": "hello without a link"})
    assert r.status_code == 400
    assert "CTA link" in r.json()["error"]


def test_two_cta_links():
    r = client.post(
        "/posting",
        json={"message": "see https://example.com and https://other.example"},
    )
    assert r.status_code == 400
    assert "CTA link" in r.json()["error"]


def test_invalid_url():
    r = client.post("/posting", json={"message": "visit http://invalid"})
    assert r.status_code == 400
    assert "valid URL" in r.json()["error"]


def test_ftp_url_rejected():
    r = client.post("/posting", json={"message": "file at ftp://files.example.com/a"})
    assert r.status_code == 400


def test_empty_message():
    r = client.post("/posting", json={"message": ""})
    assert r.status_code == 400


def test_whitespace_message():
    r = client.post("/posting", json={"message": "   "})
    assert r.status_code == 400


def test_missing_message_field():
    r = client.post("/posting", json={})
    assert r.status_code == 400
    assert "message" in r.json()["error"].lower()


def test_not_json():
    r = client.post("/posting", content="nope", headers={"Content-Type": "application/json"})
    assert r.status_code == 400


def test_https_link_ok():
    r = client.post("/posting", json={"message": "try this https://example.org/path?x=1"})
    assert r.status_code == 200
