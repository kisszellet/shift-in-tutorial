# snip — test strategy (v1)

Status: **target**. No tests exist yet; this is the shape we will be held to, not a description of
the repo. Derived from [slis.md](slis.md), [quality-characteristics.md](quality-characteristics.md)
and [business-context.md](business-context.md).

## Principles

1. **Effort follows traffic.** Follow/redirect (`GET /{code}`) dominates traffic and carries
   SLIs 1–3, so it gets the most test effort at every level. Create gets the validation and
   security cases (SLI 4). Stats rides on the follow path (SLI 5).
2. **Each SLI has one level that proves it.** A test at a lower level may also cover it, but the
   named level is the one CI trusts. If a level can't honestly prove an SLI, the table says so.
3. **Push checks down.** Prove logic as low as it can be proved; keep higher levels for what only
   they can show (HTTP behaviour, a real running server, timing).
4. **Observable behaviour changes need a higher-level test** than a unit test (DoD).
5. **A test that can't fail doesn't count.** A new test for an SLI must go red against a
   hand-made mutant of the behaviour it claims to protect (e.g. redirect to the wrong URL, skip the
   click increment, accept a `javascript:` URL), then green on the real code.

## Target pyramid

Weights are the share of the test *count* we aim for, and a rough guide to where review effort goes.

| Level | Weight | What it covers | Runs |
|---|---|---|---|
| **Unit** | ~55% | Pure logic, no HTTP: code generation, store round trip, resolve/click increment, URL validation rules in the request model | every commit, seconds |
| **API / integration** | ~30% | App in-process over HTTP: status codes, redirect `Location`, 404s, response shapes, create → follow → stats flows | every commit, seconds |
| **System** | ~15% | The real app served over a socket, black-box: redirect hot path end to end, latency measurement, smoke after start-up | every PR in CI; slower |

Within each level, **at least half the tests target the redirect path** (SLIs 1–3 and the click
increment of SLI 5). Create/validation takes most of the remainder; list is covered lightly, since
no SLI measures it.

CI gates (M3b) sit on top of this: they are the pipeline checks that fail the build on an SLI, and
are fed by the System level (latency) and API level (correctness).

## SLI → proving level

| # | SLI | Target | Proving level | What the test does | Also covered by |
|---|-----|--------|---------------|--------------------|-----------------|
| 1 | Redirect latency | p95 < 50 ms | **System** | Hit `GET /{code}` repeatedly on a running server with a warm store; compute p95 server time; fail the gate above 50 ms | — (in-process timing is not trustworthy) |
| 2 | Redirect availability | ≥ 99.9% valid redirect or correct 404 | **API** for *correctness of the outcome*; **System** smoke for liveness | Known code → redirect; unknown code → 404; no input to `GET /{code}` produces a 5xx. The 99.9% *rate* itself can only be shown by production monitoring, not by tests | Unit: unknown-code handling |
| 3 | Resolve correctness | 100% exact stored URL | **API** | Create with varied URLs (query strings, fragments, unicode, trailing slashes, long URLs), follow, assert `Location` equals the input byte for byte | Unit: store round trip; System: one end-to-end case |
| 4 | Create validation | 100% invalid/unsafe rejected | **Unit** | Table-driven cases on the request model: bad schemes (`javascript:`, `data:`, `file:`), malformed, empty, missing host, oversized — all rejected; well-formed `http`/`https` accepted | API: rejected create returns 4xx and stores nothing |
| 5 | Stats accuracy | clicks == follows | **API** | Follow a link N times (and an unknown code, which must not count), then assert stats shows exactly N; verify list agrees with stats | Unit: resolve increments by exactly one |

## Gaps this strategy knowingly leaves

- **SLI 2's rate** is a production measurement. Tests prove each response is correct; they cannot
  prove 99.9% over time. Until monitoring exists, treat that SLI as *partly unproven*.
- **SLI 5 under concurrency**: sequential follows prove the count, not that parallel follows
  don't lose increments. Add a concurrent-follow test at API or System level once SLI 5 is gated.
- **SLI 4 is only as good as the case list.** "100%" means every case we thought of; revisit the
  list when the URL rules change.
- **Latency under load** is not covered: SLI 1 is measured sequentially on a warm store.

## Working rules

- Start new tests at the lowest level that can prove the behaviour; add a higher-level test only
  when the table calls for one or the change is observable over HTTP.
- Tests must not depend on each other or on leftover state; reset the in-memory store between tests.
- Name tests after the SLI or behaviour they protect so a failure points at what broke.
- Changing an SLI target or a proving level is a change to this document, reviewed like code.

## Open for the mob to decide

- Exact tooling per level (the starter ships none; pytest-style for Unit/API is the assumption).
- The System level's driver and where its latency gate runs in CI.
- Whether the 55/30/15 split is right once we see real test counts.
