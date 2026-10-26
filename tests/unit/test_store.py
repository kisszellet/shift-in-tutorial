"""Unit tests for snip.store."""

import pytest

from snip.store import LinkRecord, Store, store


@pytest.fixture(autouse=True)
def clear_store():
    store._links.clear()
    yield
    store._links.clear()


# --- SLI 2: unknown-code handling ---


def test_get_unknown_code_raises_keyerror():
    with pytest.raises(KeyError):
        store.get("nope12")


# --- SLI 3: store round trip ---


def test_put_then_get_returns_the_same_url():
    store.put(LinkRecord(code="abc123", url="https://example.com/a?b=c#d"))

    assert store.get("abc123").url == "https://example.com/a?b=c#d"


def test_records_under_different_codes_do_not_mix():
    store.put(LinkRecord(code="aaaaaa", url="https://a.example"))
    store.put(LinkRecord(code="bbbbbb", url="https://b.example"))

    assert store.get("aaaaaa").url == "https://a.example"
    assert store.get("bbbbbb").url == "https://b.example"


# --- SLI 3 / 5 support: exists backs the collision check in create_link ---


def test_exists_is_true_only_for_stored_codes():
    store.put(LinkRecord(code="abc123", url="https://example.com"))

    assert store.exists("abc123") is True
    assert store.exists("zzzzzz") is False


# --- SLI 5 support: get hands back the live record, so a click sticks ---


def test_get_returns_the_stored_record_not_a_copy():
    store.put(LinkRecord(code="abc123", url="https://example.com"))

    store.get("abc123").clicks += 1

    assert store.get("abc123").clicks == 1


# --- not an SLI: list is covered lightly ---


def test_all_returns_every_record_and_is_empty_when_nothing_stored():
    assert store.all() == []
    store.put(LinkRecord(code="aaaaaa", url="https://a.example"))
    store.put(LinkRecord(code="bbbbbb", url="https://b.example"))

    assert {r.code for r in store.all()} == {"aaaaaa", "bbbbbb"}


def test_separate_store_instances_do_not_share_state():
    other = Store()

    store.put(LinkRecord(code="abc123", url="https://example.com"))

    assert other.exists("abc123") is False
