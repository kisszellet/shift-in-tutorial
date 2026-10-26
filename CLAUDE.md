# CLAUDE.md — snip

snip is an internal URL shortener: teams paste long links into chat, docs and slides, and snip
turns them into short codes and counts how often each is followed. Source in `src/snip/`.
Run: `uvicorn snip.main:app --reload --app-dir src` (activate `.venv` first).

What "good" means lives in `docs/` — [business-context.md](docs/business-context.md),
[quality-characteristics.md](docs/quality-characteristics.md), [slis.md](docs/slis.md). This file
distils them; if they disagree with it, they win.

## Who snip serves (priority order)

1. **Recipients** following short links — highest volume by far. Never trade their experience
   (speed, uptime, landing on the right page) for anything else.
2. **Employees** creating links for internal docs and dashboards. Lower volume, but this is where
   input-validation and security risk enters.
3. **Link owners** checking how often their link was followed.

Scope is four capabilities: create, follow (redirect), list, click stats. Anything beyond that
(e.g. the roadmap item *link expiry*) is a feature, not a tweak — it needs a story and acceptance
criteria first.

## Quality bar (highest priority first)

1. **Functional correctness** — a link resolves to the exact URL it was created for; click counts
   are accurate. Wins any conflict below it.
2. **Performance efficiency** — follow is the hot path and must be fast.
3. **Reliability / availability** — the redirect path must stay up; create may degrade briefly.
4. **Security** — accept only safe, well-formed URLs; no open redirect, no script-scheme abuse.
5. **Maintainability** — small, well-tested, readable by an agent and a human alike.

Consequences: when effort is split, weight it toward `GET /{code}`. Put create-side effort into
validation and security. Stats accuracy depends on the follow path incrementing reliably, so treat
that increment as part of the hot path, not a side effect.

## SLIs

These are the target, not a description of current code. They drive what we test and what CI gates on.

| # | SLI | Definition | Target |
|---|-----|------------|--------|
| 1 | Redirect latency | p95 server time to answer `GET /{code}` | < 50 ms |
| 2 | Redirect availability | share of `GET /{code}` returning a valid redirect or a correct 404 | ≥ 99.9% |
| 3 | Resolve correctness | share of follows redirecting to the exact stored URL | 100% |
| 4 | Create validation | share of invalid/unsafe create requests correctly rejected | 100% |
| 5 | Stats accuracy | recorded clicks equal actual follows | 100% |

SLIs 1–3 are the redirect hot path; test coverage is weighted there. A 404 for an unknown code is
a *correct* outcome for SLI 2 — a 500 is not.

## Working agreements

- **Definition of Ready:** a story has a clear actor, action and outcome; acceptance criteria are
  testable and agreed by the Three Amigos; impact on the SLIs above is understood. If a request
  lacks these, say what's missing before building.
- **Definition of Done:** code reviewed and merged via PR; tests at the appropriate level(s) pass
  in CI; SLI-affecting changes are reflected in the pipeline gates; any observable behaviour
  change is covered by at least one higher-level test than a unit test.
- **Name the SLI.** For every change, state which SLIs (1–5) it touches. If it touches none, say so.
- **SLI impact is part of acceptance criteria**, not an afterthought — including for new features.
- **Don't claim an SLI is met on the strength of reading code.** Say which test or gate shows it.
- **Report SLI gaps you notice; don't silently fix or paper over them.** The table is a target and
  the current code may not meet it.
- CI gates on SLIs: latency or correctness are the first gates to add. Don't loosen a target to
  make a gate pass.

## Stack conventions

Only what the docs and repo establish — extend this as conventions are decided:

- FastAPI app, package `snip` under `src/` (hence `--app-dir src`).
- The redirect route is `GET /{code}`; create/list/stats are under `/api/links`.
- Unknown code → a correct 404, never an unhandled error (SLI 2).
- Validate URLs at create time, rejecting unsafe schemes (SLI 4); never redirect to something that
  wasn't validated on the way in.
- Keep the codebase small enough to reason about whole (quality characteristic 5).
- Test layout and the SLI-to-test-level mapping live in [docs/test-strategy.md](docs/test-strategy.md).
