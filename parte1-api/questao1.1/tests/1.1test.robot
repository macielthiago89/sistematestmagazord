*** Settings ***
Documentation    Este caso de teste tem como objetivo validar headers, não bloquear os testes e detectar limite de rate

Resource    ../main/main.robot

*** Test Cases ***
1.1test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    1.1test    APIMAGAZORD
    Validar headers rate limit
    Nao bloquear testes
    Detectar rate limit atingido