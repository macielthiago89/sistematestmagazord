*** Settings ***
Documentation    Este caso de teste tem como objetivo adicionar um produto ao carrinho

Resource    ../main/main.robot

Test Setup    Test Setup Demoqa
Test Teardown    Test teardown    E2EMAGAZORD    2.2test


*** Test Cases ***
2.2test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    2.2test    E2EMAGAZORD
    Teste que abre nova aba via "New Tab"
    Navega para a nova aba
    Valida conteúdo da nova aba com o titulo "This is a sample page"
    Retorna para aba original
    Abre nova janela via "New Window"
    Gerencia múltiplas janelas simultaneamente
