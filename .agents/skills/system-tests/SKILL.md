---
name: system-tests
description: How snip writes Robot Framework system/E2E suites in tests/system/ — black-box tests against a real running server, distinct from tests/api/'s in-process FastAPI TestClient. Use this whenever writing, reviewing, or extending anything under tests/system/, or deciding whether a new test belongs at the system level at all versus tests/unit/ or tests/api/. Covers reusing the shared uvicorn fixture in tests/system/__init__.robot, driving the app only over real HTTP with RequestsLibrary, never importing snip.* from a system suite, and structuring one suite per user-visible flow.
---

# Writing a system suite for snip

`tests/system/` is the thinnest, slowest, most expensive layer of the pyramid
(`docs/test-strategy.md` targets ~10% of tests here). It exists only for what a real process and a
real socket can prove that an in-process test can't — chiefly, that state survives across
independent connections into a server that isn't sharing the test's own Python object graph. If
what you're testing doesn't need that, it doesn't belong here.

## Before adding a case, check it isn't already owned elsewhere

- Status codes, response shape, redirect `Location` header, 404 contracts →
  `tests/api/test_routes.py` (FastAPI `TestClient`). No real socket needed to check a status code.
- Request-body validation → `tests/unit/test_models.py`.
- The resolve/increment logic itself, in isolation → `tests/unit/test_shortener.py`.
- Latency → `tests/gates/` (its own non-functional lane, not the pyramid).

A system case earns its place only when it proves something about the real HTTP + real process
boundary that those layers structurally can't — see `docs/test-strategy.md`'s SLI table for the
worked example (SLI 5: "system proves nothing between the follow and the stats read drops a
count"). If you can't name that fact for a case, it's redundant — don't add it.

## The four rules

1. **Reuse the shared uvicorn fixture in `tests/system/__init__.robot`.** A directory containing
   `__init__.robot` is itself a Robot suite, and its `Suite Setup`/`Suite Teardown` wrap every
   `.robot` file in that directory as one run — so the server starts once, every suite in the
   folder shares it, and it stops once at the end. Don't start your own subprocess per suite. If
   `tests/system/__init__.robot` doesn't exist yet, you're writing the first suite: create it with
   this shared setup/teardown before writing your suite, so every suite after yours can reuse it
   unchanged. See `reference.md` for the concrete pattern.
2. **Drive the app only over real HTTP, with RequestsLibrary.** Every interaction — create,
   follow, stats — goes through `POST On Session` / `GET On Session` against the real base URL,
   the same way an actual client would. This is what makes the layer prove anything: a shortcut
   that reaches around HTTP reaches around the exact boundary this layer exists to test.
3. **Never `import snip.*` from a system suite.** Not even for convenience (building a URL,
   reading a constant). The suite must only know the app as a black box on the other end of a
   socket — importing the package would let the suite silently depend on the same process/object
   graph tests/api/'s TestClient already covers, collapsing the distinction that justifies this
   layer existing at all.
4. **One suite per user-visible flow.** A flow is something a real user/client does end-to-end
   (e.g. "create a link, follow it, check its stats"), not a single endpoint and not "everything."
   Name the file after the flow (`create_follow_stats.robot`, not `test_links.robot`), and give
   each `Test Case` a `[Documentation]` naming the SLI it proves and the one real-process fact no
   cheaper layer proves — that's what stops the next author from duplicating tests/api/ here by
   accident.

## Always run what you write

A suite that hasn't executed against the real server isn't done — a plausible-looking `.robot`
file can still fail to start the fixture, hang on a bad readiness check, or assert against the
wrong session. Run it with `.venv/bin/robot tests/system/` (one-time setup:
`pip install -e ".[system]"`) and show the pass/fail output before calling the work finished.

## Syntax reference

`reference.md` in this skill has the actual Robot Framework syntax this project uses — the
Settings/Variables/Test Cases/Keywords table shapes, the RequestsLibrary keywords, session and
fixture patterns, and the assertion idioms (`Should Be Equal As Integers`, `expected_status=`,
`allow_redirects=${False}`, etc.) already established in this repo. Read it before writing a
suite; don't improvise syntax that isn't in it without good reason.
