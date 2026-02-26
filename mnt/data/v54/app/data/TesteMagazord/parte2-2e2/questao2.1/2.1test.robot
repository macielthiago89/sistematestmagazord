*** Settings ***
Documentation    Este caso de teste tem como objetivo realizar o checkout de um produto

Resource    ../main/main.robot

Test Setup    Test Setup Swag Labs
Test Teardown    Test teardown    E2EMAGAZORD    2.1test


*** Test Cases ***
2.1test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    2.1test    E2EMAGAZORD
    Adicionar o produto "Sauce Labs Backpack" ao carrinho
    Clique no botão "carrinho"
    Verificar se o produto "Sauce Labs Backpack" foi adicionado ao carrinho
    Clique no botão "Checkout"
    Inserir o campo "First Name" com o nome do usuario
    Inserir o campo "Last Name" com o sobrenome do usuario
    Inserir o campo "Postal Code" com o cep do usuario
    Clique no botão "Continue"
    Verificar se o produto "Sauce Labs Backpack" está presente na página de checkout
    Clique no botão "Finish"
    Verificar se a mensagem "Thank you for your order!" foi exibida
