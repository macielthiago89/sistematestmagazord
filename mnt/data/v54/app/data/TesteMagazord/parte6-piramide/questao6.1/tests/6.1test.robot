*** Settings ***
Documentation    Este caso de teste tem como objetivo adicionar um produto ao carrinho

Resource    ../main/main.robot

Test Setup    Test setup
Test Teardown    Test teardown    PIRAMIDEMAGAZORD    6.1test


*** Test Cases ***
6.1test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    6.1test    PIRAMIDEMAGAZORD
    Inserir um email invalido no campo de email
    Inserir um email valido no campo de email
    Inserir um telefone invalido no campo de telefone
    Inserir um telefone valido no campo de telefone
    Validar a data valida
