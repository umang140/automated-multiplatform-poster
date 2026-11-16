import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator

URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
SAMPLE_MESSAGE = (
    "Check out our latest business platform and grow your online visibility. https://example.com"
)


class PostingRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": SAMPLE_MESSAGE}}
    )

    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, message: str) -> str:
        if message is None or not str(message).strip():
            raise ValueError("Message cannot be empty.")

        if len(message) > 200:
            raise ValueError("Message must not exceed 200 characters.")

        urls = [u.rstrip(".,;:!?)]}>'\"") for u in URL_RE.findall(message)]
        urls = [u for u in urls if u]

        if len(urls) == 0:
            raise ValueError("Exactly one CTA link must be included in the message.")
        if len(urls) > 1:
            raise ValueError("Exactly one CTA link must be included in the message.")

        parsed = urlparse(urls[0])
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http", "https") or not host:
            raise ValueError("CTA link is not a valid URL.")

        labels = host.split(".")
        if len(labels) < 2 or any(not label for label in labels):
            raise ValueError("CTA link is not a valid URL.")

        return message


class PlatformResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None = None
    public_access: bool = False
    date: str | None = None
    time: str | None = None
    error: str | None = None


class PostingResponse(BaseModel):
    success: bool
    results: list[PlatformResult]


def now_parts():
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
