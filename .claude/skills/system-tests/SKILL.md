---
name: system-tests
description: Write or change Robot Framework system tests for snip in tests/system/. Use when asked for a system test, an end-to-end or user-flow suite, a .robot file, or RequestsLibrary work. Covers the shared uvicorn fixture, driving the app over real HTTP, one suite per user-visible flow, and running what you write.
---

# Writing a snip system suite

System tests are the top of the pyramid in [docs/test-strategy.md](../../../docs/test-strategy.md):
about 15% of tests, run against the real app over a socket. They prove what a user sees. Anything
a unit or API test can prove belongs there instead (validation cases, response shapes).

Robot syntax, the full fixture and gotchas are in [reference.md](reference.md).

## Rules

1. **Reuse the shared fixture in `tests/system/__init__.robot`.** It starts one uvicorn server for
   the whole directory and gives every suite a `${BASE_URL}` and a RequestsLibrary session named
   `snip`. A suite never starts or stops a server and never hard-codes a port.
   - **That file does not exist yet** (checked 2026-10-26: `tests/system/` was empty). If it is
     still missing, create it first from "Shared fixture" in [reference.md](reference.md), run it,
     and tell the user you added it. Do not start a server inside a suite.
2. **Drive the app over real HTTP with RequestsLibrary.** Use the `snip` session.
3. **Never import `snip.*`.** No `Library    snip...`, no `Evaluate` that imports it, no Python
   helper that touches the store. Importing puts the test in the app's process and skips the HTTP
   layer, which is the thing this level exists to prove. If a test needs state, create it through
   the API.
4. **One suite per user-visible flow.** One `.robot` file per flow, named for it (for example
   `create_and_follow.robot`), with a `Documentation` line saying who does what and what they see.
   The tests inside are steps or variants of that flow, not unrelated checks.
5. **Share the server, not the data.** The server is shared across suites and its store is never
   reset, so each test creates its own links and asserts only on those. Never assume the list is
   empty or a global count.
6. **Run what you write.** See below. Writing a suite without running it does not count.

## Running what you write

```bash
source .venv/bin/activate
pip install -e ".[system]"                                  # once
robot --outputdir /tmp/robot-out tests/system               # whole directory
robot --outputdir /tmp/robot-out --test "<test name>" tests/system   # one test
```

- Put `--outputdir` outside the repo: Robot writes `output.xml`, `log.html` and `report.html`,
  none of which are gitignored. Check `git status` afterwards.
- Show the pass/fail summary. A new test must also be shown able to fail: break one assertion or
  mutate the app, see it go red, then undo it.
- Confirm the fixture cleaned up: `pgrep -fl "uvicorn snip.main"` should print nothing.
- A red system test is a red test: fix it or say clearly that you could not.

## Boundaries

- **Keep `[system]` out of the fast job.** CI step 2 and the Stop hook install only `[test]` and
  run only `tests/unit` and `tests/api`. Do not add `tests/system` to either.
- **Latency stays in `tests/gates/`** (pytest). SLI 1 is not measured from Robot.
- **Do not pin a known defect.** If a flow depends on behaviour covered by an open review finding
  (for example create-time validation, finding #2), say so instead of writing a test that passes
  on the broken behaviour.
