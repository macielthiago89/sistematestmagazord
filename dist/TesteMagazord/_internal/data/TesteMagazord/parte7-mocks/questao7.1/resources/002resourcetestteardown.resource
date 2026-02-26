*** Settings ***

Resource    ../main/main.robot

*** Keywords ***
Stop Mock Server
    Run Keyword And Ignore Error    Terminate Process    ${MOCK_PROC}
Reset Mock State
    ${r}=    POST On Session    mock    /__reset
    Should Be Equal As Integers    ${r.status_code}    200