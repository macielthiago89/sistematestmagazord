*** Settings ***
Documentation    Este caso de teste tem como objetivo autenticar o token via post

Resource    ../main/main.robot

*** Test Cases ***
1.2test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    1.2test    APIMAGAZORD
    Autenticação que obtém token via POST /api/login