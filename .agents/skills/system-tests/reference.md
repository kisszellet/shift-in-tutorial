# Robot Framework syntax used in snip's system suites

Concrete patterns, not a general Robot Framework tutorial. If you need syntax that isn't covered
here, that's a sign to check whether it's really needed at this layer before reaching for it.

## The shared fixture: `tests/system/__init__.robot`

A directory-level `__init__.robot` runs as the setup/teardown for every suite file in that
directory, for the whole `robot` invocation — one server for the whole `tests/system/` run, not
one per file.

```robotframework
*** Settings ***
Documentation       Shared fixture for every suite in tests/system/: starts snip as a real
...                 uvicorn subprocess once for the whole run and exposes a RequestsLibrary
...                 session named `snip` that every suite in this directory reuses.
Library             Process
Library             RequestsLibrary
Suite Setup         Start Real Snip Server
Suite Teardown      Stop Real Snip Server


*** Variables ***
${PORT}         8123
${BASE_URL}     http://127.0.0.1:${PORT}


*** Keywords ***
Start Real Snip Server
    ${process}=    Start Process    uvicorn    snip.main:app    --port    ${PORT}
    ...    stdout=${OUTPUT_DIR}/snip-server.log    stderr=STDOUT
    Set Suite Variable    ${SNIP_PROCESS}    ${process}
    Wait Until Keyword Succeeds    10x    0.5s    Server Is Ready
    Create Session    snip    ${BASE_URL}

Server Is Ready
    ${response}=    GET    ${BASE_URL}/openapi.json
    Should Be Equal As Integers    ${response.status_code}    200

Stop Snip Test Server
    Terminate Process    ${SNIP_PROCESS}
```

Every suite file in `tests/system/` can then assume:
- The server is already up.
- A RequestsLibrary session named `snip` already exists — use it directly, don't call
  `Create Session` again in your own suite.

## A suite file

```robotframework
*** Settings ***
Documentation       System/E2E suite for <flow name>: <one line on what real-process fact this
...                 proves that tests/api/ and tests/unit/ structurally can't>.
...
...                 Deliberately NOT covered here (see tests/unit/ and tests/api/ instead):
...                 - <thing>: owned by <file>, because <reason it doesn't need a real socket>.
Library             RequestsLibrary
Library             Collections


*** Variables ***
${TARGET URL}       https://example.com/target


*** Test Cases ***
Create Then Follow Then Stats Reflect The Real Follow
    [Documentation]    Proves SLI 3 (Resolve correctness) and SLI 5 (Stats accuracy) together,
    ...    end-to-end. The fact only a real process/socket proves: create (POST), follow (GET)
    ...    and the stats read (GET) are three independent real connections into a server process
    ...    holding its own memory -- unlike TestClient, which shares the test's own Python object
    ...    graph.
    &{body}=    Create Dictionary    url=${TARGET URL}
    ${create}=    POST On Session    snip    /api/links    json=${body}    expected_status=201
    ${code}=    Set Variable    ${create.json()}[code]
    Should Be Equal As Integers    ${create.json()}[clicks]    0

    ${follow}=    GET On Session    snip    /${code}
    ...    expected_status=307    allow_redirects=${False}
    Should Be Equal    ${follow.headers}[Location]    ${TARGET URL}

    ${stats}=    GET On Session    snip    /api/links/${code}/stats    expected_status=200
    Should Be Equal As Integers    ${stats.json()}[clicks]    1
```

## Idioms worth knowing

- **`POST On Session` / `GET On Session`** (RequestsLibrary): first argument is the session name
  (`snip`, from the shared fixture), second is the path relative to the session's base URL.
- **`expected_status=201`**: RequestsLibrary raises automatically if the status doesn't match —
  don't add a separate `Should Be Equal As Integers ... status_code` after it.
- **`allow_redirects=${False}`**: required on the follow request, or `requests` silently follows
  the 307 to `example.com` and you assert against the wrong response.
- **`${response.json()}[key]`**: dict/attribute access on the returned `Response` object works
  directly in Robot's variable syntax — no separate "parse JSON" step.
- **`Should Be Equal As Integers`**: use this (not `Should Be Equal`) for numeric fields like
  `clicks` — the JSON value round-trips as a Robot string otherwise and a string/int mismatch
  passes when it shouldn't.
- **`FOR ${i} IN RANGE n ... END`**: only reach for this if the suite genuinely needs N repeated
  real requests to prove something N=1 doesn't (see the "don't add a redundant case" note in
  SKILL.md) — it's easy to add a loop that just re-proves the single-request case slower.
- **`[Documentation]` on every test case**: name the SLI (`docs/slis.md`) and the one
  real-process/real-socket fact this case proves that a cheaper layer can't. This is what a
  reviewer checks to catch a redundant system case before it's merged.
