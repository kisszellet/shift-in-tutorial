"""Unit tests for shortener.py - the highest-risk logic in the app, and
mutmut's target (see docs/test-strategy.md)."""
from datetime import datetime, timedelta, timezone

import pytest

from snip import shortener
from snip.shortener import LinkExpiredError, LinkNotFoundError


def test_generate_code_length_and_alphabet():
    code = shortener.generate_code()
    assert len(code) == shortener.CODE_LENGTH
    assert set(code) <= set(shortener.ALPHABET)


def test_create_link_stores_exact_url():
    record = shortener.create_link("https://example.com/a/b?c=1")
    assert record.url == "https://example.com/a/b?c=1"
    assert record.clicks == 0


def test_create_link_assigns_a_resolvable_code():
    record = shortener.create_link("https://example.com")
    assert shortener.resolve(record.code).url == "https://example.com"


def test_resolve_increments_click_count():
    record = shortener.create_link("https://example.com")
    assert record.clicks == 0
    shortener.resolve(record.code)
    shortener.resolve(record.code)
    assert shortener.stats(record.code).clicks == 2


def test_resolve_unknown_code_raises_link_not_found():
    with pytest.raises(LinkNotFoundError):
        shortener.resolve("doesnotexist")


def test_stats_unknown_code_raises_link_not_found():
    with pytest.raises(LinkNotFoundError):
        shortener.stats("doesnotexist")


def test_list_links_returns_all_created_links():
    shortener.create_link("https://example.com/1")
    shortener.create_link("https://example.com/2")
    assert {r.url for r in shortener.list_links()} == {
        "https://example.com/1",
        "https://example.com/2",
    }


def test_create_link_retries_on_code_collision(monkeypatch):
    # generate_code returns the same value twice, then a distinct one. A
    # correct create_link must not let the second call silently overwrite
    # the first link - this collision gap was deliberately left unfixed
    # during M2's review for a closer look here.
    codes = iter(["dupe12", "dupe12", "uniq99"])
    monkeypatch.setattr(shortener, "generate_code", lambda: next(codes))

    first = shortener.create_link("https://example.com/first")
    second = shortener.create_link("https://example.com/second")

    assert first.code != second.code
    assert second.code == "uniq99"  # retried via generate_code(), not left blank
    assert shortener.resolve(first.code).url == "https://example.com/first"
    assert shortener.resolve(second.code).url == "https://example.com/second"


# Link expiry (docs/link-expiry-acceptance-criteria.md)


@pytest.fixture
def expired_link():
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    return shortener.create_link("https://example.com", expires_at=past)


def test_create_link_without_expiry_never_expires():
    record = shortener.create_link("https://example.com")
    assert record.expires_at is None
    assert shortener.resolve(record.code).url == "https://example.com"  # doesn't raise


def test_create_link_stores_expiry():
    expiry = datetime.now(timezone.utc) + timedelta(days=1)
    record = shortener.create_link("https://example.com", expires_at=expiry)
    assert record.expires_at == expiry


def test_create_link_normalizes_naive_expiry_to_utc():
    # Regression: create_link() must not trust its caller to have already
    # normalized a naive datetime - models.py's validator does that for HTTP
    # requests, but shortener.py is meant to be callable directly (this whole
    # test file does exactly that), so it has to enforce this itself. Without
    # this, resolve() crashed with TypeError comparing naive vs. aware
    # datetimes - confirmed by direct reproduction before this fix.
    naive_future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    record = shortener.create_link("https://example.com", expires_at=naive_future)
    assert record.expires_at.tzinfo is not None
    shortener.resolve(record.code)  # must not raise TypeError


def test_resolve_expired_link_raises_link_expired(expired_link):
    # Rule 3: following an expired link is a distinct outcome (410) from an
    # unknown code (404) - the link existed and is deliberately gone.
    with pytest.raises(LinkExpiredError) as exc_info:
        shortener.resolve(expired_link.code)
    assert str(exc_info.value) == expired_link.code  # the actual code, not just any error


def test_resolve_at_the_exact_expiry_instant_is_expired(monkeypatch):
    # Boundary check: exactly AT expiry counts as expired (<=, not <) - a link
    # is not valid "up to and including" its expiry instant.
    from snip.store import LinkRecord, store

    frozen_now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return frozen_now

    monkeypatch.setattr(shortener, "datetime", FrozenDatetime)
    store.put(LinkRecord(code="exactly1", url="https://example.com", expires_at=frozen_now))

    with pytest.raises(LinkExpiredError):
        shortener.resolve("exactly1")


def test_resolve_expired_link_does_not_increment_clicks(expired_link):
    # Rule 4: an expired hit is not a follow - ties to SLI 5 (docs/slis.md),
    # clicks must equal actual follows.
    for _ in range(3):
        with pytest.raises(LinkExpiredError):
            shortener.resolve(expired_link.code)
    assert shortener.stats(expired_link.code).clicks == 0


def test_stats_on_expired_link_does_not_raise(expired_link):
    # Checking stats is a distinct concern from following - an owner should
    # be able to see final numbers after expiry.
    assert shortener.stats(expired_link.code).clicks == 0


def test_expired_code_is_not_freed_for_reuse(expired_link, monkeypatch):
    # Rule 5: create_link's existing collision-retry loop treats an expired
    # link's code as still taken - no special-casing for expired records.
    codes = iter([expired_link.code, "uniq99"])
    monkeypatch.setattr(shortener, "generate_code", lambda: next(codes))

    new_record = shortener.create_link("https://example.com/new")
    assert new_record.code == "uniq99"
