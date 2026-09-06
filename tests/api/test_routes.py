"""Thin route-wiring tests: status codes and response shapes only. Per-case
input validation lives in tests/unit/test_models.py; this layer only proves
the HTTP wiring calls the right thing and shapes the response correctly
(docs/test-strategy.md: "one or two tests per endpoint, not per case")."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from snip.main import app
from snip.shortener import CODE_LENGTH
from snip.shortener import create_link as shortener_create_link

client = TestClient(app)


def test_create_link_returns_201_and_shape():
    resp = client.post("/api/links", json={"url": "https://example.com"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["url"] == "https://example.com"
    assert body["clicks"] == 0
    assert len(body["code"]) == CODE_LENGTH


def test_create_link_rejects_unsafe_url_with_422():
    resp = client.post("/api/links", json={"url": "javascript:alert(1)"})
    assert resp.status_code == 422


def test_list_links_returns_created_links():
    client.post("/api/links", json={"url": "https://example.com/a"})
    resp = client.get("/api/links")
    assert resp.status_code == 200
    assert any(link["url"] == "https://example.com/a" for link in resp.json())


def test_follow_redirects_to_stored_url():
    code = client.post("/api/links", json={"url": "https://example.com/target"}).json()["code"]
    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/target"


def test_follow_unknown_code_returns_404():
    resp = client.get("/doesnotexist", follow_redirects=False)
    assert resp.status_code == 404


def test_stats_reflects_follow_count():
    code = client.post("/api/links", json={"url": "https://example.com"}).json()["code"]
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)
    resp = client.get(f"/api/links/{code}/stats")
    assert resp.json()["clicks"] == 2


def test_create_link_rejects_past_expiry_with_422():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    resp = client.post("/api/links", json={"url": "https://example.com", "expires_at": past})
    assert resp.status_code == 422


def test_follow_expired_link_returns_410():
    # The API itself rejects a past expires_at at creation time (Rule 2), so
    # to test the follow-side wiring we go around it via the shortener layer
    # directly - deterministic, no real sleep needed to "wait for expiry."
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    record = shortener_create_link("https://example.com", expires_at=past)
    resp = client.get(f"/{record.code}", follow_redirects=False)
    assert resp.status_code == 410
