*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
Start Mock Server
    Create Directory    ${EXECDIR}${/}logs

    ${mock_script}=    Set Variable    ${CURDIR}${/}..${/}mocks${/}api_mock_server.py
    ${p}=    Start Process
    ...    python
    ...    ${mock_script}
    ...    stdout=${EXECDIR}${/}logs${/}mock_stdout.txt
    ...    stderr=${EXECDIR}${/}logs${/}mock_stderr.txt
    Set Suite Variable    ${MOCK_PROC}    ${p}

    Wait Until Keyword Succeeds    10x    1s    Healthcheck Mock

Healthcheck Mock
    Create Session    mock    ${BASE}
    ${r}=    GET On Session    mock    /__health
    Should Be Equal As Integers    ${r.status_code}    200