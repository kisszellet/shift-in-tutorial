"""snip HTTP API.

Run locally:
    uvicorn snip.main:app --reload --app-dir src
OpenAPI docs at /docs, schema at /openapi.json
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from . import shortener
from .models import CreateLinkRequest, LinkResponse

app = FastAPI(title="snip", version="0.1.0", description="A tiny URL shortener.")


@app.post("/api/links", response_model=LinkResponse, status_code=201)
def create_link(req: CreateLinkRequest) -> LinkResponse:
    record = shortener.create_link(req.url)
    return LinkResponse.from_record(record)


@app.get("/api/links", response_model=list[LinkResponse])
def list_links() -> list[LinkResponse]:
    return [LinkResponse.from_record(r) for r in shortener.list_links()]


@app.get("/api/links/{code}/stats", response_model=LinkResponse)
def link_stats(code: str) -> LinkResponse:
    try:
        record = shortener.stats(code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Link not found")
    return LinkResponse.from_record(record)


@app.get("/{code}")
def follow(code: str) -> RedirectResponse:
    try:
        record = shortener.resolve(code)
    except KeyError:
        raise HTTPException(status_code=404, detail="Link not found")
    return RedirectResponse(url=record.url, status_code=307)
