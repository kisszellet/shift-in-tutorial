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

Stop Real Snip Server
    Terminate Process    ${SNIP_PROCESS}
