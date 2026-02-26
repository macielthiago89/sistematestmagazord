*** Settings ***
Documentation    Este caso de teste tem como objetivo adicionar um produto ao carrinho

Resource    ../main/main.robot

Test Setup    Start Mock Server
Test Teardown    Stop Mock Server


*** Test Cases ***
7.1test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    7.1test    MOCKSMAGAZORD
    GET /products - sucesso + schema
    POST /products - criar produto
    PUT /products/:id - atualizar produto
    DELETE /products/:id - deletar produto
    Erro 500 simulado
    Rate limit simulado (429 após 10 GETs)
