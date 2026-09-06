"""Unit tests for CreateLinkRequest's URL and expiry validation - the
highest-value suite in the app (docs/test-strategy.md): this is where the
one significant security risk lives, and where M2's own review found a
validation approach that looked right but silently rewrote input (see
main.py history)."""
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from snip.models import CreateLinkRequest

VALID_URLS = [
    "https://example.com",
    "http://example.com/path?query=1",
    "https://example.com:8443/path",
    "https://Example.COM/MixedCase",
]

INVALID_URLS = [
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "not a url",
    "ftp://example.com",
    "",
]


@pytest.mark.parametrize("url", VALID_URLS)
def test_accepts_well_formed_http_urls(url):
    # Stored exactly as submitted - not normalized/rewritten.
    assert CreateLinkRequest(url=url).url == url


@pytest.mark.parametrize("url", INVALID_URLS)
def test_rejects_unsafe_or_malformed_urls(url):
    with pytest.raises(ValidationError):
        CreateLinkRequest(url=url)


# Link expiry (docs/link-expiry-acceptance-criteria.md, Rules 1-2)


def test_expires_at_defaults_to_none():
    assert CreateLinkRequest(url="https://example.com").expires_at is None


def test_accepts_future_expiry_with_utc_offset():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    req = CreateLinkRequest(url="https://example.com", expires_at=future.isoformat())
    assert req.expires_at == future


def test_naive_expiry_is_assumed_utc():
    future_naive = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    req = CreateLinkRequest(url="https://example.com", expires_at=future_naive.isoformat())
    assert req.expires_at.tzinfo is not None
    assert req.expires_at.utcoffset() == timedelta(0)


def test_rejects_expiry_in_the_past():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValidationError):
        CreateLinkRequest(url="https://example.com", expires_at=past.isoformat())
