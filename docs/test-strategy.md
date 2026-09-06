# Test strategy — snip (v1, authored in M1)

Written in M1, **before** any test existed, so tooling decisions in M3a/M3b/M4 have something to
be held accountable to. As of M4, every tier below is real — see `docs/mutation-testing-notes.md`
for what mutation testing found and `.claude/agents/system-test-writer.md` for who maintains the
system tier.

## Guiding rule

Coverage is a map of gaps, not a target. Cover **SLI-relevant and business-critical paths first**,
at the **lowest level that gives confidence**. A system/end-to-end test is only justified when a
unit test cannot exercise the behaviour (e.g. real HTTP routing, redirect status codes).

## Target pyramid shape

| Level | Tool | Weight | What lives here |
|---|---|---|---|
| Unit | pytest (M3a) | Majority of tests | `shortener.py` and `store.py` logic in isolation: code generation, collision handling, validation, click counting, lookup-miss behaviour. |
| API / integration | pytest + FastAPI `TestClient` (M3a) | A thin layer | Route wiring: status codes, request/response shapes — one or two tests per endpoint, not per case. |
| System | Robot Framework, via `system-test-writer` subagent (M4) | Thinnest layer, weighted toward SLIs 2, 3, 5 | `tests/system/`: one suite — the redirect hot path (create → follow → stats round trip). The only behaviour in this app that actually needs a real running process. Not SLI 1 (latency) — that's `tests/gates/`, which actually asserts on a measured value; this suite doesn't time anything. |

If a mob is about to write a system test for something already provable at the unit level, that's
the pyramid-inversion anti-pattern — stop and push the coverage down instead. This isn't
hypothetical: the first version of `tests/system/` also had a suite with two "cross-cutting"
cases (unknown-code 404, unsafe-URL rejection) — deleted after review, because both were
byte-for-byte identical in input and assertion to tests already in `tests/api/test_routes.py`.
`TestClient` already exercises the same in-process pipeline (routing, validation, exception
handling) that those cases claimed to be testing "end to end" — running the same check through a
real socket instead of an in-process one proved nothing a slower, flakier copy wouldn't. The
"one or two cross-cutting flows" this table originally promised turned out not to exist for this
app; that's the discipline working, not the plan falling short.

`tests/gates/` (M3b) sits outside this pyramid on purpose: it's not a coverage level, it's a single
SLI enforced directly in CI. Don't grow it into a parallel test suite — one gate per SLI that
actually needs a live process, not a place to restate what unit/API/system already cover.

## Per-SLI test mapping

| SLI | Primary level | Notes |
|---|---|---|
| Redirect latency (p95 < 50 ms) | CI gate (M3b) — `tests/gates/` | Needs a real running process; a unit test can't measure server-side latency meaningfully. Turned out lightweight enough to gate directly: spins up uvicorn, samples 50 real requests, measures p95 client-side over loopback. Not part of the Stop hook (M3a) — deliberately kept out of the fast in-loop path; CI is where a heavier check like this belongs. |
| Redirect availability (valid redirect, correct 404, or correct 410 once expired) | Unit | `resolve()` behaviour for known, unknown, and expired codes is a pure function test — no server needed. |
| Resolve correctness (exact URL match) | Unit | Create-then-resolve round trip on the store/shortener layer. |
| Create validation (unsafe/invalid URLs rejected) | Unit | Table-driven tests over valid/invalid/unsafe URL inputs against `create_link`. Highest-value suite in the app — this is where the one significant security risk lives. |
| Stats accuracy (clicks = follows) | Unit, plus one system check | Unit: click counter increments correctly per resolve call. System: one end-to-end "follow N times, check stats" flow, since it crosses the create/follow/stats boundary. |

## Mutation testing (M3a)

Run `mutmut` against `shortener.py` — it carries the highest-risk logic (validation, collision
handling, lookup). A green coverage report that still lets mutants survive means the tests assert
too little; treat a surviving mutant as a missing assertion, not a mutmut false positive, until
proven otherwise.

Results of the first real run: `docs/mutation-testing-notes.md`.

## Out of scope for this document

Load-testing infrastructure, persistence-layer testing (the store is in-memory by design), and the
link-expiry feature — that gets its own acceptance criteria via Example Mapping in M5a.

---
_v1 — M1, target shape only. As of M4: the System row's weight turned out thinner than planned —
"one or two cross-cutting flows" shrank to zero once each candidate was checked against
`tests/api/`, see the System row's note above. The document was right that the bar should be
high; it just hadn't been applied yet. Revisit if a future module finds the distribution doesn't
hold; that's a legitimate reason to change this document, not a reason to
quietly ignore it._
