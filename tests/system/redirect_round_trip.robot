*** Settings ***
Documentation     Flow: an employee shortens a link, a recipient follows it, and the follow is counted.
Library           RequestsLibrary

*** Variables ***
${TARGET}         https://example.com/docs?a=1&b=2#top

*** Test Cases ***
Following A Link Redirects And Counts One Click
    &{body}=       Create Dictionary    url=${TARGET}
    ${created}=    POST On Session    snip    /api/links    json=${body}    expected_status=201
    ${code}=       Set Variable    ${created.json()}[code]

    ${followed}=   GET On Session    snip    /${code}    expected_status=307    allow_redirects=${False}
    Should Be Equal    ${followed.headers}[location]    ${TARGET}

    ${stats}=      GET On Session    snip    /api/links/${code}/stats
    Should Be Equal As Integers    ${stats.json()}[clicks]    1
