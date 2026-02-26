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

Gerar email aleatório
    ${email}    FakerLibrary.Email
    Set Global Variable    ${email}

Gerar telefone aleatório
    ${telefone}    FakerLibrary.Phone Number
    Set Global Variable    ${telefone}

Gerar "${valor}" numero aleatorios
    ${numero}    FakerLibrary.Random Number    ${valor}
    Set Global Variable    ${numero}

Data atual no formato ddMmmYYYY
    ${out}=    Get Current Date    result_format=%d %b %Y
    RETURN    ${out}

Gerar endereço aleatório
    ${endereco}    FakerLibrary.Address
    Set Global Variable    ${endereco}
