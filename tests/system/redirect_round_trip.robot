*** Settings ***
Documentation       System/E2E suite for the redirect round trip: create a link, follow it
...                 without following the redirect, then check its click count. The fact only a
...                 real process/socket proves: the create (POST), the follow (GET) and the
...                 stats read (GET) are three independent real connections into a server
...                 process holding its own memory -- unlike tests/api/'s TestClient, which
...                 shares the test's own Python object graph, so state "surviving" there proves
...                 nothing about a real deployment.
...
...                 Deliberately NOT covered here (see tests/unit/ and tests/api/ instead):
...                 - the 307 status code and Location header contract on their own: owned by
...                   tests/api/test_routes.py's test_follow_redirects_307_to_the_stored_url, no
...                   real socket needed for that.
...                 - the increment-by-one logic in isolation: owned by
...                   tests/unit/test_shortener.py's test_resolve_increments_clicks_by_one_per_call.
Library             RequestsLibrary
Library             Collections


*** Variables ***
${TARGET URL}       https://example.com/target


*** Test Cases ***
Create Then Follow Without Redirect Then Click Count Reflects It
    [Documentation]    Proves SLI 3 (Resolve correctness) and SLI 5 (Stats accuracy) together,
    ...    end-to-end, over the redirect round trip specifically: following the link stops at the
    ...    307 (never reaches example.com) and the click it recorded is visible on an
    ...    independent stats connection afterward.
    &{body}=    Create Dictionary    url=${TARGET URL}
    ${create}=    POST On Session    snip    /api/links    json=${body}    expected_status=201
    ${code}=    Set Variable    ${create.json()}[code]
    Should Be Equal As Integers    ${create.json()}[clicks]    0

    ${follow}=    GET On Session    snip    /${code}
    ...    expected_status=307    allow_redirects=${False}
    Should Be Equal    ${follow.headers}[Location]    ${TARGET URL}

    ${stats}=    GET On Session    snip    /api/links/${code}/stats    expected_status=200
    Should Be Equal As Integers    ${stats.json()}[clicks]    1
