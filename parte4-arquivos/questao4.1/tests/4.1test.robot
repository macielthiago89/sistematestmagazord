*** Settings ***
Documentation    Este caso de teste tem como objetivo adicionar um produto ao carrinho

Resource    ../main/main.robot

Test Setup    Test setup
Test Teardown    Test teardown    ARQUIVOSMAGAZORD    4.1test


*** Test Cases ***
4.1test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    4.1test    ARQUIVOSMAGAZORD
    Gerar csv dinamico    10
    Gerar csv dinamico    100
    Gerar csv dinamico    1000
    Realizar o upload do arquivo valido "valido_10"
    Realizar o upload do arquivo csv "vazio"
    Realizar o upload do arquivo csv "formato inválido"
    Realizar o upload do arquivo csv "dados malformados"
    Validar upload do arquivo bem sucedido