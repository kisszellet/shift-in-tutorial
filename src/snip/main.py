"""snip HTTP API.

Run locally:
    uvicorn snip.main:app --reload --app-dir src
OpenAPI docs at /docs, schema at /openapi.json
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from . import shortener
from .models import CreateLinkRequest, LinkResponse
from .shortener import LinkNotFoundError

NOT_FOUND = {404: {"description": "No link found for the given code"}}

app = FastAPI(title="snip", version="0.1.0", description="A tiny URL shortener.")


@app.exception_handler(LinkNotFoundError)
def link_not_found(request: Request, exc: LinkNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"No link found for code '{exc}'"})


@app.post("/api/links", response_model=LinkResponse, status_code=201)
def create_link(req: CreateLinkRequest) -> LinkResponse:
    record = shortener.create_link(req.url)
    return LinkResponse.from_record(record)


@app.get("/api/links", response_model=list[LinkResponse])
def list_links() -> list[LinkResponse]:
    return [LinkResponse.from_record(r) for r in shortener.list_links()]


@app.get("/api/links/{code}/stats", response_model=LinkResponse, responses=NOT_FOUND)
def link_stats(code: str) -> LinkResponse:
    record = shortener.stats(code)
    return LinkResponse.from_record(record)


@app.get("/{code}", responses=NOT_FOUND)
def follow(code: str) -> RedirectResponse:
    record = shortener.resolve(code)
    return RedirectResponse(url=record.url, status_code=307)
