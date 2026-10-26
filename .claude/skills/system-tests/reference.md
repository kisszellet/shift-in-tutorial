# Robot Framework reference for snip system tests

Nothing in `tests/system/` uses Robot yet. Everything below was written and run as a prototype
(Robot Framework 7.5, robotframework-requests 0.9.7, Python 3.14) on 2026-10-26: 3 tests, 3 passed,
no server left behind. Re-run it if you change a pattern.

## File anatomy

Four sections, each headed `*** Name ***`. Separate cells with 4 spaces (2 is the minimum). A
directory is a suite, `__init__.robot` is that directory's own settings, every other `.robot` file
is a child suite.

```robot
*** Settings ***       # Documentation, Library, Suite Setup/Teardown
*** Variables ***      # ${NAME}  value
*** Keywords ***       # reusable steps, defined in this file
*** Test Cases ***     # the tests
```

## Shared fixture (`tests/system/__init__.robot`)

```robot
*** Settings ***
Documentation     One real uvicorn server for every suite in this directory.
Library           Process
Library           RequestsLibrary
Suite Setup       Start Snip Server
Suite Teardown    Stop Snip Server

*** Keywords ***
Start Snip Server
    ${python}=    Evaluate    sys.executable    modules=sys
    ${port}=      Evaluate    __import__('socket').create_server(('127.0.0.1', 0)).getsockname()[1]
    Start Process    ${python}    -m    uvicorn    snip.main:app
    ...    --app-dir    ${EXECDIR}/src    --host    127.0.0.1    --port    ${port}
    ...    --log-level    warning    alias=snip    cwd=${EXECDIR}    stderr=STDOUT
    Set Suite Variable    ${BASE_URL}    http://127.0.0.1:${port}    children=True
    Create Session    snip    ${BASE_URL}
    Wait Until Keyword Succeeds    15s    0.2s    GET On Session    snip    /api/links

Stop Snip Server
    Terminate Process    snip
```

- `sys.executable` is the Python running `robot`, so it uses the active venv.
- Port 0 asks the OS for a free port.
- `children=True` is what makes `${BASE_URL}` visible in the child suites.
- `${EXECDIR}` is the directory `robot` was started from. Run it from the repo root.
- Expect a few `[ WARN ] Retrying ... Connection refused` lines at startup: that is the
  `Wait Until Keyword Succeeds` poll before uvicorn is listening. Not a failure.

## A flow suite (`tests/system/create_and_follow.robot`)

```robot
*** Settings ***
Documentation     Flow: an employee shortens a link and a recipient follows it.
Library           RequestsLibrary

*** Variables ***
${TARGET}         https://example.com/docs?a=1&b=2#top

*** Keywords ***
Create Link
    [Arguments]    ${url}
    &{body}=       Create Dictionary    url=${url}
    ${response}=   POST On Session    snip    /api/links    json=${body}    expected_status=201
    RETURN         ${response.json()}[code]

Follow Link
    [Arguments]    ${code}    ${status}=307
    ${response}=   GET On Session    snip    /${code}    expected_status=${status}    allow_redirects=${False}
    RETURN         ${response}

*** Test Cases ***
Created Link Redirects To The Original URL
    ${code}=       Create Link    ${TARGET}
    ${followed}=   Follow Link    ${code}
    Should Be Equal    ${followed.headers}[location]    ${TARGET}

Following A Link Is Counted
    ${code}=       Create Link    ${TARGET}
    Follow Link    ${code}
    Follow Link    ${code}
    ${stats}=      GET On Session    snip    /api/links/${code}/stats
    Should Be Equal As Integers    ${stats.json()}[clicks]    2

Unknown Code Is A 404
    Follow Link    nope12    status=404
```

## Syntax we use

| Need | Write |
|---|---|
| POST JSON | `POST On Session    snip    /api/links    json=${body}    expected_status=201` |
| GET | `GET On Session    snip    /api/links/${code}/stats` |
| Expect a non-2xx | `expected_status=404`. Without it, a 4xx/5xx fails the keyword. |
| Don't follow a redirect | `allow_redirects=${False}`. Needed to assert the 307 and `Location`. |
| Build a JSON body | `&{body}=    Create Dictionary    url=${url}` then `json=${body}` |
| Read the JSON body | `${response.json()}[code]` |
| Read a header | `${response.headers}[location]` (lookup is case-insensitive) |
| Return a value | `RETURN    ${value}` (RF 7) |
| Assert | `Should Be Equal`, `Should Be Equal As Integers` |
| Retry until ready | `Wait Until Keyword Succeeds    15s    0.2s    <keyword>    <args>` |
| Continue a long line | `...` at the start of the next line |
| Keyword arguments | `[Arguments]    ${code}    ${status}=307` (default after `=`) |

## Gotchas hit while prototyping

- **Do not pass `json=` a JSON string.** `json={"url": "${TARGET}"}` is encoded a second time and
  the app answers 422. Pass a dictionary (`json=${body}`).
- A bare `GET On Session ... /nope12` raises on 404. For a negative case say
  `expected_status=404`.
- `--dryrun` checks syntax and keyword names without running anything, so it reports pass even
  when an assertion would fail. It is not a substitute for a real run.
- The server is shared and never reset: links from earlier suites are still there.

## Commands

```bash
robot --outputdir /tmp/robot-out tests/system                         # all suites
robot --outputdir /tmp/robot-out --test "Unknown Code Is A 404" tests/system   # one test
robot --dryrun --outputdir /tmp/robot-out tests/system                # syntax only
```
