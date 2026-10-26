"""Unit tests for snip.shortener."""

import pytest

from snip import shortener
from snip.store import store


@pytest.fixture(autouse=True)
def clear_store():
    store._links.clear()
    yield
    store._links.clear()


def test_code_collision_does_not_overwrite_existing_link(monkeypatch):
    # SLI 3 / 5: a colliding code must never replace an existing link, and the
    # new link must be retried onto the next code (AAAAAA, AAAAAA, then BBBBBB).
    codes = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    monkeypatch.setattr(shortener, "generate_code", lambda: next(codes))

    first = shortener.create_link("https://first.example")
    shortener.resolve(first.code)

    second = shortener.create_link("https://second.example")

    surviving = store.get("AAAAAA")
    assert surviving.url == "https://first.example"
    assert surviving.clicks == 1
    assert second.code == "BBBBBB"
    assert store.get("BBBBBB").url == "https://second.example"


# --- SLI 2: unknown-code handling (unit support; the 404 mapping is API level) ---


def test_resolve_unknown_code_raises_keyerror():
    with pytest.raises(KeyError):
        shortener.resolve("nope12")


def test_stats_unknown_code_raises_keyerror():
    with pytest.raises(KeyError):
        shortener.stats("nope12")


# --- SLI 3: resolve returns the exact stored URL ---

VARIED_URLS = [
    "https://example.com",
    "https://example.com/",
    "https://example.com/path/?q=a&r=b%20c#frag",
    "http://example.com:8080/a/b/",
    "https://example.com/café/日本",
    "https://example.com/" + "a" * 2000,
]


@pytest.mark.parametrize("url", VARIED_URLS)
def test_resolve_returns_exact_url_that_was_created(url):
    created = shortener.create_link(url)

    assert shortener.resolve(created.code).url == url


def test_resolve_returns_each_links_own_url():
    a = shortener.create_link("https://a.example")
    b = shortener.create_link("https://b.example")

    assert shortener.resolve(a.code).url == "https://a.example"
    assert shortener.resolve(b.code).url == "https://b.example"


def test_generate_code_is_six_chars_from_the_alphabet():
    # Supports SLI 3: a code is used as a path segment, so it must be URL-safe.
    for _ in range(200):
        code = shortener.generate_code()
        assert len(code) == shortener.CODE_LENGTH == 6
        assert set(code) <= set(shortener.ALPHABET)


# --- SLI 5: stats accuracy (unit support; the proving level is API) ---


def test_new_link_starts_with_zero_clicks():
    assert shortener.create_link("https://example.com").clicks == 0


def test_resolve_increments_clicks_by_exactly_one():
    link = shortener.create_link("https://example.com")

    shortener.resolve(link.code)

    assert shortener.stats(link.code).clicks == 1


def test_n_follows_record_n_clicks():
    link = shortener.create_link("https://example.com")

    for _ in range(7):
        shortener.resolve(link.code)

    assert shortener.stats(link.code).clicks == 7


def test_stats_does_not_count_as_a_click():
    link = shortener.create_link("https://example.com")

    shortener.stats(link.code)
    shortener.stats(link.code)

    assert shortener.stats(link.code).clicks == 0


def test_clicks_are_counted_per_link():
    a = shortener.create_link("https://a.example")
    b = shortener.create_link("https://b.example")

    shortener.resolve(a.code)
    shortener.resolve(a.code)
    shortener.resolve(b.code)

    assert shortener.stats(a.code).clicks == 2
    assert shortener.stats(b.code).clicks == 1


def test_failed_follow_of_unknown_code_counts_for_no_link():
    link = shortener.create_link("https://example.com")

    with pytest.raises(KeyError):
        shortener.resolve("nope12")

    assert shortener.stats(link.code).clicks == 0


# --- not an SLI: list is covered lightly ---


def test_list_links_returns_every_created_link():
    a = shortener.create_link("https://a.example")
    b = shortener.create_link("https://b.example")

    assert {r.code for r in shortener.list_links()} == {a.code, b.code}
