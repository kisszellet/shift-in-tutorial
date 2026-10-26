"""Unit tests for snip.models."""

import pytest
from pydantic import ValidationError

from snip.models import CreateLinkRequest, LinkResponse
from snip.store import LinkRecord

# --- SLI 4: create validation ---

BAD_URLS = [
    "javascript:alert(1)",
    "data:text/html,hi",
    "file:///etc/passwd",
    "",
    "not a url",
    "http://",
    "//evil.example",
    "https://example.com/" + "a" * 100_000,
]


@pytest.mark.xfail(
    strict=True,
    reason="review finding #2: CreateLinkRequest.url is a bare str, nothing is rejected. "
    "strict, so this goes red the moment validation is added: remove the mark then.",
)
@pytest.mark.parametrize("url", BAD_URLS)
def test_invalid_or_unsafe_url_is_rejected(url):
    with pytest.raises(ValidationError):
        CreateLinkRequest(url=url)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com",
        "https://example.com/a/b?q=1&r=2#frag",
        "http://example.com:8080/",
    ],
)
def test_well_formed_http_and_https_urls_are_accepted(url):
    assert CreateLinkRequest(url=url).url == url


def test_missing_url_is_rejected():
    with pytest.raises(ValidationError):
        CreateLinkRequest()


def test_non_string_url_is_rejected():
    with pytest.raises(ValidationError):
        CreateLinkRequest(url=123)


# --- SLI 3 / 5: the response shows exactly what is stored ---


def test_link_response_carries_code_url_and_clicks_unchanged():
    record = LinkRecord(code="abc123", url="https://example.com/a?b=c#d", clicks=4)

    response = LinkResponse.from_record(record)

    assert (response.code, response.url, response.clicks) == (
        "abc123",
        "https://example.com/a?b=c#d",
        4,
    )
