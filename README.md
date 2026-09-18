# snip

A tiny URL shortener — the **starter application** for the Shift In tutorial. Past M2: a first
AI-reviewed PR has landed (see `docs/github-cli-notes.md`), but there are **still no tests and no
CI** — both arrive in M3a.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
uvicorn snip.main:app --reload --app-dir src
```

`pip`/`uvicorn` as bare commands only exist once a virtualenv is active — if you see "command not
found" for either, that's what's missing, not a broken install.

- Interactive docs: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/links` | Create a short link from `{ "url": "..." }` |
| GET | `/api/links` | List links |
| GET | `/api/links/{code}/stats` | Click stats for a code |
| GET | `/{code}` | Follow a short link (redirect) |

## Where to look

- `docs/business-context.md`, `docs/quality-characteristics.md`, `docs/slis.md` — what "good" means.
- `src/snip/` — the implementation.
- `tests/` — empty on purpose; you add tests during the workshop.
