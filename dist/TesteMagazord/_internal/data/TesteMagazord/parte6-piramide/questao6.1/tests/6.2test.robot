*** Settings ***
Documentation    Este caso de teste tem como objetivo adicionar um produto ao carrinho

Resource    ../main/main.robot

Test Setup    Test setup
Test Teardown    Test teardown    E2EMAGAZORD    6.2test


*** Test Cases ***
6.2test
    [Documentation]
    ...    Pré condição:
    ...    
    ...    Usuario  e senha cadastrado
    [Tags]    regression    6.2test    E2EMAGAZORD
    Preencher o campo "First Name" com um nome aleatório
    Preencher o campo "Last Name" com um sobrenome aleatório
    Inserir um email valido no campo de email
    Selecione o Gender como "Male"
    Inserir um telefone valido no campo de telefone
    Preencha a data de nascimento com "01 Feb 1989"
    Selecionar subject "Math"
    Selecionar hobbies "1"
    Faça upload de um arquivo de imagem 
    Preencher o campo "Current Address" com um endereço aleatório
    Selecione o estado "NCR" e a cidade "Delhi"
    Clicar no botao submit
    Validar que o modal de confirmação foi exibido


