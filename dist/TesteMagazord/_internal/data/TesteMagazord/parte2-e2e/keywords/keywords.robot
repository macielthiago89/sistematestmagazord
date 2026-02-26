*** Settings ***
Resource    ../main/main.robot

*** Keywords ***
Gerar nome aleatório
    ${nome}    FakerLibrary.Name
    Set Global Variable    ${nome}

Gerar sobrenome aleatório
    ${sobrenome}    FakerLibrary.Last Name
    Set Global Variable    ${sobrenome}

Gerar CEP aleatório
    ${cep}    FakerLibrary.Postal Code
    Set Global Variable    ${cep}