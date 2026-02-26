*** Settings ***
Documentation    Este caso de teste tem como objetivo adicionar um produto ao carrinho

Resource    ../main/main.robot

Test Setup    Test setup
Test Teardown    Test teardown    FRONTENDMAGAZORD    3.1test


*** Test Cases ***
3.1test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    3.1test    FRONTENDMAGAZORD
    Verificar por "texto visível"
    Verificar por "estrutura DOM (nth-child)"
    Verificar por "atributo parcial"
    Verificar por "hierarquia (parent > child)"
    Verificar por "XPath"
