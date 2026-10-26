"""API tests for snip's routes: status code and response structure only.

Input-validation cases belong in tests/unit/test_models.py.
"""

import pytest
from fastapi.testclient import TestClient

from snip.main import app
from snip.store import store


@pytest.fixture(autouse=True)
def clear_store():
    store._links.clear()
    yield
    store._links.clear()


@pytest.fixture
def client():
    return TestClient(app)


def create(client, url="https://example.com"):
    return client.post("/api/links", json={"url": url}).json()


# --- POST /api/links ---


def test_create_link_returns_201_with_code_url_and_clicks(client):
    response = client.post("/api/links", json={"url": "https://example.com"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"code", "url", "clicks"}
    assert isinstance(body["code"], str) and body["code"]
    assert isinstance(body["url"], str)
    assert isinstance(body["clicks"], int)


# --- GET /api/links ---


def test_list_links_returns_200_and_an_empty_list_when_nothing_exists(client):
    response = client.get("/api/links")

    assert response.status_code == 200
    assert response.json() == []


def test_list_links_returns_200_and_a_list_of_link_objects(client):
    create(client, "https://a.example")
    create(client, "https://b.example")

    response = client.get("/api/links")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) == 2
    assert all(set(item) == {"code", "url", "clicks"} for item in body)


# --- GET /api/links/{code}/stats ---


def test_stats_for_existing_link_returns_200_with_link_structure(client):
    code = create(client)["code"]

    response = client.get(f"/api/links/{code}/stats")

    assert response.status_code == 200
    assert set(response.json()) == {"code", "url", "clicks"}


def test_stats_for_unknown_code_returns_404_with_detail(client):
    response = client.get("/api/links/nope12/stats")

    assert response.status_code == 404
    assert "detail" in response.json()


# --- GET /{code} ---


def test_follow_existing_link_returns_307_with_a_location_header(client):
    code = create(client)["code"]

    response = client.get(f"/{code}", follow_redirects=False)

    assert response.status_code == 307
    assert "location" in response.headers


def test_follow_unknown_code_returns_404_with_detail(client):
    response = client.get("/nope12", follow_redirects=False)

    assert response.status_code == 404
    assert "detail" in response.json()
