# snip

A tiny URL shortener — the **starter application** for the Shift In tutorial. This branch is the
finale: the full quality pyramid (unit, API, one SLI-derived CI gate, Robot Framework system
tests), a `Stop` hook, and two working agents (`system-test-writer`, `example-mapping`) all in
place *before* the link-expiry feature ([issue #2](https://github.com/kisszellet/shift-in-tutorial/issues/2))
got built with them — tests generated and run in-loop, not bolted on after. See
`docs/link-expiry-acceptance-criteria.md` for the acceptance criteria this was built against.

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

## Run the tests

```bash
pip install -e ".[test]"
pytest tests/unit tests/api                   # fast suite - what the Stop hook runs
pytest tests/gates -s                         # SLI 1 gate: redirect p95 latency, real server
pytest --cov=snip --cov-report=term-missing   # coverage: a map of gaps, not a target
mutmut run && mutmut results                  # mutation testing on shortener.py

pip install -e ".[system]"
robot --outputdir robot-results tests/system/ # system tests, real server, real HTTP
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/links` | Create a short link from `{ "url": "...", "expires_at": "..." }` (`expires_at` optional) |
| GET | `/api/links` | List links |
| GET | `/api/links/{code}/stats` | Click stats for a code |
| GET | `/{code}` | Follow a short link (redirect, `404` if unknown, `410` if expired) |

## Where to look

- `docs/business-context.md`, `docs/quality-characteristics.md`, `docs/slis.md` — what "good" means.
- `docs/test-strategy.md` — the target test pyramid and per-SLI test-level mapping.
- `src/snip/` — the implementation.
- `tests/unit/`, `tests/api/` — unit tests and thin route-wiring tests.
- `tests/gates/` — the SLI 1 (redirect latency) CI gate. Not part of the pyramid, not run by the
  Stop hook; CI runs it on every push.
- `tests/system/` — Robot Framework system tests: the redirect hot path round trip. Maintained by
  the `system-test-writer` subagent, not written inline.
- `.claude/agents/system-test-writer.md` — the subagent that owns `tests/system/`.
- `.claude/skills/example-mapping/` — the `/example-mapping` skill: refines a rough feature
  request into confirmed acceptance criteria + BDD scenarios by interviewing you. Includes an
  input-inspection step for untrusted sources (e.g. a GitHub issue) before acting on them.
- `docs/link-expiry-acceptance-criteria.md` — a worked example of that skill's output, for the
  feature built in M5b.
