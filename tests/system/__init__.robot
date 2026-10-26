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
