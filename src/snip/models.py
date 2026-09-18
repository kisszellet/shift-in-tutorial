"""Request/response models."""

from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

ALLOWED_SCHEMES = {"http", "https"}


class CreateLinkRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_be_safe(cls, value: str) -> str:
        # Validate with urlparse rather than pydantic's HttpUrl: HttpUrl silently
        # normalizes (adds a trailing slash, lowercases the host, strips default
        # ports) and caps length at 2083 chars, both of which would break "resolves
        # to the exact URL it was created for" and reject the long SSO/signed-URL
        # links this app exists to shorten. This checks safety without rewriting input.
        parsed = urlparse(value)
        if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
            raise ValueError("url must be a well-formed http:// or https:// URL")
        return value


class LinkResponse(BaseModel):
    code: str
    url: str
    clicks: int

    @classmethod
    def from_record(cls, record: "object") -> "LinkResponse":
        return cls(code=record.code, url=record.url, clicks=record.clicks)
